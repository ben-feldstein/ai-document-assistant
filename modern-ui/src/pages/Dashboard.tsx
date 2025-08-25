import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  FileText, 
  MessageSquare, 
  Mic, 
  Users, 
  TrendingUp, 
  Clock,
  Plus,
  Search,
  Brain
} from 'lucide-react'
import { api, endpoints } from '../lib/api'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'

interface SystemStatus {
  cache: {
    used_memory: string
    connected_clients: number
    total_commands_processed: number
    keyspace_hits: number
    keyspace_misses: number
  }
  search: {
    default_k: number
    max_context_length: number
  }
  llm: {
    primary: {
      state: string
      fail_counter: number
      last_failure_time: string | null
    }
    fallback: {
      state: string
      fail_counter: number
      last_failure_time: string | null
    }
  }
  stt: {
    provider: string
    model_size: string
    language: string
    model_loaded: boolean
  }
  vectorizer: {
    model_name: string
    embedding_dimensions: number
    batch_size: number
    model_loaded: boolean
    max_seq_length: number
  }
  database: {
    organization_id: number
    organization_users: number
    organization_documents: number
    organization_embeddings: number
    security_note: string
  }
}

export default function Dashboard() {
  const { data: systemStatus, isLoading } = useQuery<SystemStatus>({
    queryKey: ['systemStatus'],
    queryFn: async () => {
      console.log('Fetching system status from:', endpoints.admin.systemStatus)
      const response = await api.get(endpoints.admin.systemStatus)
      console.log('System status response:', response.data)
      return response.data.data
    },
    retry: false,
  })

  // Fetch chat stats
  const { data: chatStats } = useQuery({
    queryKey: ['chatStats'],
    queryFn: async () => {
      try {
        console.log('Fetching chat stats from:', endpoints.chat.stats)
        const response = await api.get(endpoints.chat.stats)
        console.log('Chat stats response:', response.data)
        return response.data.data
      } catch (error) {
        console.error('Error fetching chat stats:', error)
        return { total_queries: 0, cache_hit_rate: 0 }
      }
    },
    retry: false,
  })

  const quickActions = [
    {
      name: 'Upload Document',
      description: 'Add PDFs, Word docs, or text files',
      icon: Plus,
      href: '/documents',
      color: 'bg-blue-500',
      textColor: 'text-blue-600'
    },
    {
      name: 'AI Chat',
      description: 'Ask questions about your documents',
      icon: Brain,
      href: '/chat',
      color: 'bg-blue-500',
      textColor: 'text-blue-600'
    },
    {
      name: 'Voice Assistant',
      description: 'Talk to your documents hands-free',
      icon: Mic,
      href: '/voice',
      color: 'bg-green-500',
      textColor: 'text-green-600'
    },
    {
      name: 'Manage Documents',
      description: 'View and organize your document library',
      icon: Search,
      href: '/documents',
      color: 'bg-purple-500',
      textColor: 'text-purple-600'
    }
  ]

  // Debug logging
  console.log('Dashboard data:', { systemStatus, chatStats })
  
  const stats = [
    {
      name: 'Total Documents',
      value: systemStatus?.database?.organization_documents || 0,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      name: 'Organization Members',
      value: systemStatus?.database?.organization_users || 0,
      icon: Users,
      color: 'text-accent-600',
      bgColor: 'bg-accent-100'
    },
    {
      name: 'AI Conversations',
      value: chatStats?.total_queries || 0,
      icon: MessageSquare,
      color: 'text-success-600',
      bgColor: 'bg-success-100'
    },
    {
      name: 'Voice Sessions',
      value: chatStats?.total_queries || 0, // Using chat queries as proxy for voice sessions
      icon: Mic,
      color: 'text-warning-600',
      bgColor: 'bg-warning-100'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Welcome to your AI Document Assistant</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-success-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-500">System Online</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="group block p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${action.color} group-hover:scale-110 transition-transform`}>
                  <action.icon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 group-hover:text-gray-700">
                    {action.name}
                  </h3>
                  <p className="text-sm text-gray-500">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity & System Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">System is ready for AI interactions</p>
                <p className="text-xs text-gray-500">Just now</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-success-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Voice assistant initialized</p>
                <p className="text-xs text-gray-500">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="h-2 w-2 bg-accent-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">Document search engine active</p>
                <p className="text-xs text-gray-500">5 minutes ago</p>
              </div>
            </div>
          </div>
        </div>

        {/* System Information */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Information</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className="text-sm font-medium text-success-600">Operational</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Last Updated:</span>
              <span className="text-sm text-gray-900">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">API Version:</span>
              <span className="text-sm text-gray-900">v1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Uptime:</span>
              <span className="text-sm text-gray-900">99.9%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
              <Brain className="h-5 w-5 text-blue-600" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-blue-900">Getting Started</h3>
            <p className="text-blue-700 mt-1">
              Ready to explore? Start by uploading your first document or try chatting with the AI assistant to get insights from your content.
            </p>
            <div className="mt-4 flex space-x-3">
              <Link
                to="/documents"
                className="btn-primary text-sm"
              >
                Upload Document
              </Link>
              <Link
                to="/chat"
                className="btn-outline text-sm"
              >
                Try AI Chat
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
