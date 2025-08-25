import React, { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Play, Square, Loader2, Volume2, Settings } from 'lucide-react'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface VoiceMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  audioUrl?: string
}

export default function Voice() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [messages, setMessages] = useState<VoiceMessage[]>([])
  const [transcript, setTranscript] = useState('')
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  
  const audioRef = useRef<HTMLAudioElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize WebSocket connection
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      toast.error('Please log in to use voice features')
      return
    }

    const ws = new WebSocket(`ws://localhost:8000/ws/audio?token=${token}`)
    
    ws.onopen = () => {
      setIsConnected(true)
      toast.success('Voice connection established')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'transcript') {
          setTranscript(data.data)
        } else if (data.type === 'response') {
          const assistantMessage: VoiceMessage = {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.data,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, assistantMessage])
          setIsProcessing(false)
        } else if (data.type === 'error') {
          toast.error(data.data)
          setIsProcessing(false)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      toast.error('Voice connection lost')
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
      toast.error('Voice connection error')
    }

    setWsConnection(ws)

    return () => {
      ws.close()
    }
  }, [])

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data])
        }
      }

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        setAudioBlob(audioBlob)
        setAudioChunks([])
        
        // Send audio to WebSocket
        if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
          const reader = new FileReader()
          reader.onload = () => {
            const base64Audio = reader.result as string
            wsConnection.send(JSON.stringify({
              type: 'audio',
              data: base64Audio.split(',')[1], // Remove data:audio/webm;base64, prefix
              mimeType: 'audio/webm'
            }))
          }
          reader.readAsDataURL(audioBlob)
        }
      }

      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
      setTranscript('')
      toast.success('Recording started')
    } catch (error) {
      console.error('Failed to start recording:', error)
      toast.error('Failed to access microphone')
    }
  }

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop()
      mediaRecorder.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
      setIsProcessing(true)
      
      // Add user message
      if (transcript.trim()) {
        const userMessage: VoiceMessage = {
          id: Date.now().toString(),
          role: 'user',
          content: transcript,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, userMessage])
        setTranscript('')
      }
    }
  }

  // Play audio
  const playAudio = () => {
    if (audioRef.current && audioBlob) {
      const audioUrl = URL.createObjectURL(audioBlob)
      audioRef.current.src = audioUrl
      audioRef.current.play()
      setIsPlaying(true)
    }
  }

  // Stop audio
  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setIsPlaying(false)
    }
  }

  // Clear messages
  const clearMessages = () => {
    if (window.confirm('Are you sure you want to clear the voice conversation?')) {
      setMessages([])
    }
  }

  // Format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Voice Assistant</h1>
          <p className="text-gray-600">Talk to your documents with voice commands</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          <button
            onClick={clearMessages}
            className="btn btn-outline"
            disabled={messages.length === 0}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Voice Controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex flex-col items-center space-y-4">
          {/* Recording Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={!isConnected || isProcessing}
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg scale-110'
                : 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg'
            } ${!isConnected || isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isRecording ? (
              <Square className="h-8 w-8" />
            ) : (
              <Mic className="h-8 w-8" />
            )}
          </button>

          {/* Status */}
          <div className="text-center">
            {isRecording ? (
              <p className="text-red-600 font-medium">Recording... Click to stop</p>
            ) : isProcessing ? (
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-blue-600">Processing...</span>
              </div>
            ) : (
              <p className="text-gray-600">Click to start recording</p>
            )}
          </div>

          {/* Audio Playback */}
          {audioBlob && (
            <div className="flex items-center space-x-2">
              <button
                onClick={isPlaying ? stopAudio : playAudio}
                className="btn btn-outline"
              >
                {isPlaying ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {isPlaying ? 'Stop' : 'Play'} Recording
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Live Transcript */}
      {transcript && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Live Transcript:</h3>
          <p className="text-blue-800">{transcript}</p>
        </div>
      )}

      {/* Messages */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Conversation</h3>
        </div>
        
        <div className="max-h-96 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <Volume2 className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No voice messages yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Start recording to begin your voice conversation.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && (
                      <Volume2 className="h-4 w-4 mt-1 text-blue-500 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                    {message.role === 'user' && (
                      <Mic className="h-4 w-4 mt-1 text-blue-200 flex-shrink-0" />
                    )}
                  </div>
                  <div className="text-xs opacity-70 mt-2">
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">How to use:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Click the microphone button to start recording</li>
          <li>• Speak clearly about your documents</li>
          <li>• Click the stop button when finished</li>
          <li>• The AI will process your voice and respond</li>
          <li>• You can play back your recordings</li>
        </ul>
      </div>

      {/* Hidden audio element */}
      <audio ref={audioRef} onEnded={() => setIsPlaying(false)} />
    </div>
  )
}
