import React, { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Bot, User, Loader2, RefreshCw, MessageSquare } from 'lucide-react'
import { api, endpoints } from '../lib/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    title: string
    source: string
    snippet: string
  }>
}

interface ChatResponse {
  response: string
  sources?: Array<{
    title: string
    source: string
    snippet: string
  }>
  tokens_in: number
  tokens_out: number
  cached: boolean
  latency_ms: number
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  // Fetch chat history
  const { data: chatHistory, isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat-history'],
    queryFn: async () => {
      try {
        const response = await api.get(endpoints.chat.history)
        return response.data.data || []
      } catch (error) {
        console.log('No chat history available')
        return []
      }
    },
    retry: false
  })

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: async (message: string) => {

      
      const response = await api.post(endpoints.chat.send, {
        text: message
      })
      return response.data
    },
    onSuccess: (data: ChatResponse) => {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)
      
      // Invalidate chat history
      queryClient.invalidateQueries({ queryKey: ['chat-history'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to get AI response')
      setIsTyping(false)
    }
  })

  // Load chat history on mount
  useEffect(() => {
    if (chatHistory && chatHistory.length > 0) {
      const formattedMessages: Message[] = chatHistory.map((msg: any) => ({
        id: msg.id || Date.now().toString(),
        role: msg.role || 'user',
        content: msg.content || msg.message || '',
        timestamp: new Date(msg.timestamp || Date.now()),
        sources: msg.sources
      }))
      setMessages(formattedMessages)
    }
  }, [chatHistory])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle send message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)

    // Send to AI
    chatMutation.mutate(inputMessage.trim())
  }

  // Handle enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // Clear chat history
  const clearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      setMessages([])
      queryClient.invalidateQueries({ queryKey: ['chat-history'] })
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
    <div className="flex flex-col h-[calc(100vh-200px)] max-h-[800px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Chat</h1>
          <p className="text-gray-600">Ask questions about your uploaded documents</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={clearChat}
            className="btn btn-outline"
            disabled={messages.length === 0}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Clear Chat
          </button>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="h-full flex flex-col">
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Start a conversation</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Ask questions about your documents to get AI-powered insights.
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
                        <Bot className="h-4 w-4 mt-1 text-blue-500 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        
                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-500 mb-2">Sources:</p>
                            <div className="space-y-2">
                              {message.sources.map((source, index) => (
                                <div key={index} className="text-xs bg-white rounded p-2 border">
                                  <p className="font-medium text-gray-700">{source.title}</p>
                                  <p className="text-gray-500 text-xs">{source.source}</p>
                                  <p className="text-gray-600 mt-1">{source.snippet}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      {message.role === 'user' && (
                        <User className="h-4 w-4 mt-1 text-blue-200 flex-shrink-0" />
                      )}
                    </div>
                    <div className="text-xs opacity-70 mt-2">
                      {formatTime(message.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <div className="flex items-center space-x-2">
                    <Bot className="h-4 w-4 text-blue-500" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your documents..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  disabled={isTyping}
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="btn btn-primary px-6 self-end"
              >
                {isTyping ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>

      {/* Quick Suggestions */}
      {messages.length === 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Try asking:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              "What are the main topics covered in my documents?",
              "Can you summarize the key findings?",
              "What are the most important recommendations?",
              "How do the documents relate to each other?"
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setInputMessage(suggestion)}
                className="text-left p-3 text-sm text-gray-600 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
