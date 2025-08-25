"""WebSocket audio routes for real-time voice interaction."""

import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import HTMLResponse

from api.services.orchestrator import orchestrator_service
from api.services.rate_limit import rate_limit_service
from api.services.stt import stt_service
from jose import jwt
from jose.exceptions import JWTError
from api.utils.config import settings
from api.models.db import get_db
from api.models.entities import User, Membership
from sqlalchemy.orm import Session

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and audio sessions."""
    
    def __init__(self):
        self.active_connections: dict = {}  # session_id -> WebSocket
        self.audio_buffers: dict = {}  # session_id -> list of audio chunks
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.audio_buffers[session_id] = []
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": f"Connected with session ID: {session_id}",
            "timestamp": asyncio.get_event_loop().time()
        }))
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific WebSocket connection."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
    
    def add_audio_chunk(self, session_id: str, audio_data: bytes):
        """Add an audio chunk to the buffer for a session."""
        if session_id in self.audio_buffers:
            self.audio_buffers[session_id].append(audio_data)
    
    def get_audio_buffer(self, session_id: str) -> list:
        """Get the audio buffer for a session."""
        return self.audio_buffers.get(session_id, [])
    
    def clear_audio_buffer(self, session_id: str):
        """Clear the audio buffer for a session."""
        if session_id in self.audio_buffers:
            self.audio_buffers[session_id].clear()


# Global connection manager
manager = ConnectionManager()


@router.get("/audio", response_class=HTMLResponse)
async def get_audio_page():
    """Serve a simple HTML page for testing WebSocket audio."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Policy Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .controls { margin: 20px 0; }
            button { padding: 10px 20px; margin: 5px; font-size: 16px; }
            .recording { background-color: #ff4444; color: white; }
            .transcript { margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px; }
            .response { margin: 20px 0; padding: 15px; background-color: #e8f5e8; border-radius: 5px; }
            .status { margin: 10px 0; padding: 10px; background-color: #e3f2fd; border-radius: 5px; }
            .error { background-color: #ffebee; color: #c62828; }
        </style>
    </head>
    <body>
        <h1>AI Voice Policy Assistant</h1>
        <p>Click the microphone button and ask a question about policies or regulations.</p>
        
        <div class="controls">
            <button id="startBtn">🎤 Start Recording</button>
            <button id="stopBtn" disabled>⏹️ Stop Recording</button>
            <button id="clearBtn">🗑️ Clear</button>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
        <div id="transcript" class="transcript" style="display: none;"></div>
        <div id="response" class="response" style="display: none;"></div>
        
        <script>
            let mediaRecorder;
            let audioChunks = [];
            let ws;
            let sessionId = 'demo-' + Date.now();
            
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const clearBtn = document.getElementById('clearBtn');
            const statusDiv = document.getElementById('status');
            const transcriptDiv = document.getElementById('transcript');
            const responseDiv = document.getElementById('response');
            
            function showStatus(message, isError = false) {
                statusDiv.style.display = 'block';
                statusDiv.textContent = message;
                statusDiv.className = 'status ' + (isError ? 'error' : '');
            }
            
            function showTranscript(text) {
                transcriptDiv.style.display = 'block';
                transcriptDiv.textContent = 'Transcript: ' + text;
            }
            
            function showResponse(text) {
                responseDiv.style.display = 'block';
                responseDiv.textContent = 'Response: ' + text;
            }
            
            function appendResponse(text) {
                if (responseDiv.style.display === 'none') {
                    responseDiv.style.display = 'block';
                    responseDiv.textContent = 'Response: ' + text;
                } else {
                    responseDiv.textContent += text;
                }
            }
            
            startBtn.addEventListener('click', async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    
                    // Try to use a supported audio format
                    const mimeTypes = [
                        'audio/webm;codecs=opus',
                        'audio/webm',
                        'audio/ogg;codecs=opus',
                        'audio/ogg'
                    ];
                    
                    let selectedMimeType = null;
                    for (const mimeType of mimeTypes) {
                        if (MediaRecorder.isTypeSupported(mimeType)) {
                            selectedMimeType = mimeType;
                            break;
                        }
                    }
                    
                    if (!selectedMimeType) {
                        throw new Error('No supported audio format found');
                    }
                    
                    console.log(`Using audio format: ${selectedMimeType}`);
                    mediaRecorder = new MediaRecorder(stream, { mimeType: selectedMimeType });
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            console.log('Audio data available, size:', event.data.size);
                            // Convert audio data to base64 and send immediately
                            const reader = new FileReader();
                            reader.onload = () => {
                                const base64Audio = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
                                console.log('Sending audio chunk, data length:', base64Audio.length);
                                
                                if (ws && ws.readyState === WebSocket.OPEN) {
                                    ws.send(JSON.stringify({
                                        type: 'audio_chunk',
                                        data: base64Audio,
                                        format: 'webm',
                                        sample_rate: 16000
                                    }));
                                    
                                    // Send process_audio message to trigger transcription
                                    setTimeout(() => {
                                        if (ws && ws.readyState === WebSocket.OPEN) {
                                            console.log('Sending process_audio message');
                                            ws.send(JSON.stringify({
                                                type: 'process_audio'
                                            }));
                                        }
                                    }, 100);
                                }
                            };
                            reader.readAsDataURL(event.data);
                        }
                    };
                    
                    mediaRecorder.start();
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                    showStatus('Recording... Click stop when finished.');

                    
                } catch (error) {
                    showStatus('Error accessing microphone: ' + error.message, true);
                }
            });
            
            stopBtn.addEventListener('click', () => {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    showStatus('Processing audio...');
                }
            });
            
            clearBtn.addEventListener('click', () => {
                transcriptDiv.style.display = 'none';
                responseDiv.style.display = 'none';
                statusDiv.style.display = 'none';
            });
            
            // WebSocket connection
            function connectWebSocket() {
                // Get JWT token from localStorage (set after login)
                const token = localStorage.getItem('jwt_token');
                if (!token) {
                    showStatus('Please log in first to use voice features', true);
                    return;
                }
                
                ws = new WebSocket(`ws://localhost:8000/ws/audio?session_id=${sessionId}&token=${token}`);
                
                ws.onopen = () => {
                    showStatus('Connected to voice assistant');
                };
                
                ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    
                    switch (message.type) {
                        case 'connection_established':
                            showStatus(message.data);
                            break;
                        case 'status':
                            showStatus(message.data);
                            break;
                        case 'transcript':
                            showTranscript(message.data);
                            break;
                        case 'token':
                            appendResponse(message.data);
                            break;
                        case 'chat_response':
                            showResponse(message.data);
                            break;
                        case 'final':
                            showStatus('Response complete');
                            break;
                        case 'error':
                            showStatus(message.data, true);
                            break;
                    }
                };
                
                ws.onclose = () => {
                    showStatus('Disconnected from voice assistant', true);
                    setTimeout(connectWebSocket, 3000);
                };
                
                ws.onerror = (error) => {
                    showStatus('WebSocket error: ' + error.message, true);
                };
            }
            
            // Connect on page load
            connectWebSocket();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.websocket("/audio")
async def websocket_audio(
    websocket: WebSocket,
    session_id: str = Query(..., description="Unique session identifier"),
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time voice interaction.
    
    This endpoint handles:
    - Audio streaming from client
    - Real-time transcription
    - Streaming AI responses
    - Session management
    """
    try:
        # Authenticate the user first
        try:
            # Decode JWT token to get user ID
            
            # Decode token
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            user_id = int(payload.get("sub"))
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            # Get user and organization info
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                await websocket.close(code=4001, reason="User not found")
                return
            
            # Get user's organization ID
            membership = db.query(Membership).filter(Membership.user_id == user_id).first()
            if not membership:
                await websocket.close(code=4001, reason="User not in any organization")
                return
            
            org_id = membership.org_id
            print(f"DEBUG: Authenticated user {user_id} for organization {org_id}")
            
        except JWTError:
            await websocket.close(code=4001, reason="Invalid token")
            return
        except Exception as e:
            print(f"DEBUG: Authentication error: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect the WebSocket
        await manager.connect(websocket, session_id)
        
        # Process incoming messages
        while True:
            try:
                # Receive message from client - use the most flexible approach
                raw_message = await websocket.receive()
                print(f"DEBUG: Raw message received: {raw_message}")
                
                if raw_message.get("type") == "websocket.receive":
                    if "text" in raw_message:
                        # Text message (JSON string)
                        data = raw_message["text"]
                        print(f"DEBUG: Processing text data: {data[:200]}...")
                        try:
                            message = json.loads(data)
                            print(f"DEBUG: Parsed message type: {message.get('type')}")
                            message_type = message.get("type")
                        except json.JSONDecodeError as e:
                            print(f"DEBUG: Failed to parse text as JSON: {e}")
                            continue
                    elif "bytes" in raw_message:
                        # Binary message - this is raw audio data, not JSON
                        print(f"DEBUG: Received binary audio data, length: {len(raw_message['bytes'])} bytes")
                        # For binary audio, we need to handle it directly
                        # The browser should send a text message first with metadata
                        print(f"DEBUG: Binary audio received, but no metadata message found")
                        continue
                    else:
                        print(f"DEBUG: Message has no text or bytes: {raw_message}")
                        continue
                elif raw_message.get("type") == "websocket.disconnect":
                    print("DEBUG: WebSocket disconnect message received")
                    break
                else:
                    print(f"DEBUG: Unknown message type: {raw_message.get('type')}")
                    continue

                
                if message_type == "audio_chunk":
                    # Handle audio chunk
                    audio_data_base64 = message.get("data", "")
                    format_type = message.get("format", "wav")
                    sample_rate = message.get("sample_rate", 16000)
                    
                    print(f"DEBUG: Received audio chunk - base64 data length: {len(audio_data_base64)}, format: {format_type}, sample_rate: {sample_rate}")
                    
                    try:
                        # Decode base64 audio data
                        import base64
                        audio_data = base64.b64decode(audio_data_base64)
                        print(f"DEBUG: Decoded audio data length: {len(audio_data)} bytes")
                        
                        # Add to audio buffer
                        manager.add_audio_chunk(session_id, audio_data)
                    except Exception as e:
                        print(f"DEBUG: Error decoding base64 audio data: {e}")
                        await manager.send_message(session_id, {
                            "type": "error",
                            "data": f"Failed to decode audio data: {str(e)}",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        continue
                    
                    # Send acknowledgment
                    await manager.send_message(session_id, {
                        "type": "audio_received",
                        "data": f"Received {len(audio_data)} bytes of audio",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                elif message_type == "process_audio":
                    # Process accumulated audio
                    audio_chunks = manager.get_audio_buffer(session_id)
                    
                    if not audio_chunks:
                        await manager.send_message(session_id, {
                            "type": "error",
                            "data": "No audio data to process",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        continue
                    
                    # Combine audio chunks
                    combined_audio = b"".join(audio_chunks)
                    print(f"DEBUG: Processing {len(audio_chunks)} audio chunks, total size: {len(combined_audio)} bytes")
                    
                    # Process through orchestrator
                    try:

                        # Use the full orchestrator for real AI responses
                        await manager.send_message(session_id, {
                            "type": "status",
                            "data": "Processing your voice query with AI...",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        
                        # Use the orchestrator for full AI processing with real org_id
                        async for response_chunk in orchestrator_service.handle_voice_query(
                            combined_audio,
                            org_id=org_id,  # Real organization ID from authentication
                            user_id=user_id,  # Real user ID from authentication
                            session_id=session_id
                        ):
                            await manager.send_message(session_id, response_chunk)
                            
                    except Exception as e:
                        await manager.send_message(session_id, {
                            "type": "error",
                            "data": f"Error processing audio: {str(e)}",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                    
                    # Clear audio buffer after processing
                    manager.clear_audio_buffer(session_id)
                    
                elif message_type == "ping":
                    # Handle ping for connection health
                    await manager.send_message(session_id, {
                        "type": "pong",
                        "data": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                else:
                    # Unknown message type
                    await manager.send_message(session_id, {
                        "type": "error",
                        "data": f"Unknown message type: {message_type}",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
            except json.JSONDecodeError:
                await manager.send_message(session_id, {
                    "type": "error",
                    "data": "Invalid JSON message",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        import traceback
        print(f"WebSocket error for session {session_id}: {e}")
        print(f"Full traceback:\n{traceback.format_exc()}")
    finally:
        # Clean up connection
        manager.disconnect(session_id)


@router.get("/sessions")
async def get_active_sessions():
    """Get information about active WebSocket sessions."""
    return {
        "ok": True,
        "data": {
            "active_connections": len(manager.active_connections),
            "sessions": list(manager.active_connections.keys())
        }
    }
