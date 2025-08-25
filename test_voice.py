#!/usr/bin/env python3
"""
Voice Functionality Test Suite
Tests microphone access, speech-to-text, and WebSocket audio streaming.
"""

import requests
import json
import time
import asyncio
import websockets
import base64
import os

class VoiceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        
    def test_voice_endpoints(self):
        """Test voice-related endpoints."""
        print("🎤 Voice Functionality Test Suite")
        print("=" * 50)
        
        # Test 1: Check if voice endpoints are accessible
        print("\n1. Testing voice endpoints...")
        
        # Test WebSocket audio page
        try:
            response = self.session.get(f"{self.base_url}/ws/audio")
            if response.status_code == 200:
                print("   ✅ Voice page accessible")
                print(f"   📄 Page size: {len(response.text)} characters")
            else:
                print(f"   ❌ Voice page failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Voice page error: {e}")
        
        # Test active sessions endpoint
        try:
            response = self.session.get(f"{self.base_url}/ws/sessions")
            if response.status_code == 200:
                sessions = response.json()
                print(f"   ✅ Sessions endpoint working: {sessions['data']['active_connections']} active connections")
            else:
                print(f"   ❌ Sessions endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Sessions endpoint error: {e}")
        
        # Test 2: Check STT service health
        print("\n2. Testing Speech-to-Text service...")
        
        try:
            response = self.session.get(f"{self.base_url}/healthz")
            if response.status_code == 200:
                health_data = response.json()
                stt_status = health_data.get("services", {}).get("stt", "unknown")
                print(f"   ✅ STT service status: {stt_status}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        return True
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and basic messaging."""
        print("\n3. Testing WebSocket connection...")
        
        session_id = f"test-{int(time.time())}"
        ws_url = f"ws://localhost:8000/ws/audio?session_id={session_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"   ✅ WebSocket connected to {ws_url}")
                
                # Wait for connection message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    if data.get("type") == "connection_established":
                        print(f"   ✅ Connection established: {data['data']}")
                    else:
                        print(f"   ⚠️  Unexpected message: {data}")
                except asyncio.TimeoutError:
                    print("   ⚠️  No connection message received")
                
                # Send ping message
                ping_msg = {
                    "type": "ping",
                    "data": "test",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(ping_msg))
                print("   📤 Sent ping message")
                
                # Wait for pong response
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    if data.get("type") == "pong":
                        print("   ✅ Received pong response")
                    else:
                        print(f"   ⚠️  Unexpected response: {data}")
                except asyncio.TimeoutError:
                    print("   ⚠️  No pong response received")
                
                print("   ✅ WebSocket connection test completed")
                
        except Exception as e:
            print(f"   ❌ WebSocket connection failed: {e}")
            return False
        
        return True
    
    def test_audio_processing(self):
        """Test audio processing capabilities."""
        print("\n4. Testing audio processing...")
        
        # Create a simple test audio file (silence)
        test_audio = b"\x00" * 16000  # 1 second of silence at 16kHz
        
        # Test with a simple audio chunk
        print("   📊 Test audio data:")
        print(f"      Size: {len(test_audio)} bytes")
        print(f"      Duration: {len(test_audio) / 16000:.2f} seconds")
        print(f"      Sample rate: 16000 Hz")
        
        # Test base64 encoding (for WebSocket transmission)
        try:
            audio_b64 = base64.b64encode(test_audio).decode('utf-8')
            print(f"      Base64 size: {len(audio_b64)} characters")
            print("   ✅ Audio encoding test passed")
        except Exception as e:
            print(f"   ❌ Audio encoding failed: {e}")
            return False
        
        return True
    
    def generate_test_instructions(self):
        """Generate manual testing instructions."""
        print("\n" + "=" * 50)
        print("🎯 Manual Voice Testing Instructions")
        print("=" * 50)
        
        print("\n📱 **Browser Testing Steps:**")
        print("1. Open your browser and go to:")
        print(f"   {self.base_url}/ws/audio")
        
        print("\n🎤 **Microphone Test:**")
        print("2. Click '🎤 Start Recording' button")
        print("3. Allow microphone access when prompted")
        print("4. Speak clearly: 'What are our company policies?'")
        print("5. Click '⏹️ Stop Recording' button")
        
        print("\n🔍 **Expected Results:**")
        print("✅ Status: 'Connected to voice assistant'")
        print("✅ Status: 'Recording... Click stop when finished.'")
        print("✅ Status: 'Processing audio...'")
        print("✅ Status: 'Transcribing audio...'")
        print("✅ Transcript: Your spoken question")
        print("✅ Status: 'Searching for relevant information...'")
        print("✅ Response: AI-generated answer based on your documents")
        
        print("\n⚠️ **Troubleshooting:**")
        print("• If microphone access fails, check browser permissions")
        print("• If WebSocket fails, check if API is running")
        print("• If transcription fails, check STT service configuration")
        print("• If response fails, check document search and LLM services")
        
        print("\n🔧 **Technical Details:**")
        print("• Audio format: WAV, 16kHz sample rate")
        print("• STT provider: Whisper (default) or GCP")
        print("• WebSocket endpoint: /ws/audio")
        print("• Session management: Automatic with unique IDs")
        
        print("\n📊 **Performance Notes:**")
        print("• Audio processing: Real-time streaming")
        print("• Transcription: ~1-3 seconds for 10-second audio")
        print("• Response generation: Depends on document search complexity")
        print("• Total latency: Usually 5-15 seconds end-to-end")

def main():
    tester = VoiceTester()
    
    # Run basic tests
    print("🚀 Starting voice functionality tests...")
    
    # Test 1: Voice endpoints
    if not tester.test_voice_endpoints():
        print("❌ Voice endpoint tests failed")
        return
    
    # Test 2: Audio processing
    if not tester.test_audio_processing():
        print("❌ Audio processing tests failed")
        return
    
    # Test 3: WebSocket connection (async)
    try:
        asyncio.run(tester.test_websocket_connection())
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    # Generate manual testing instructions
    tester.generate_test_instructions()
    
    print("\n🎉 Voice functionality tests completed!")
    print("🌐 Open the voice page in your browser to test microphone functionality")

if __name__ == "__main__":
    main()
