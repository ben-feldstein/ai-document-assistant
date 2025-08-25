import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Search, Trash2, Eye, Download, Plus, X } from 'lucide-react'
import { api, endpoints } from '../lib/api'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

interface Document {
  id: number
  title: string
  source: string
  doc_metadata: any
  created_at: string
  updated_at: string
}

export default function Documents() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [previewDoc, setPreviewDoc] = useState<any>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const queryClient = useQueryClient()

  // Fetch documents
  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {

      const response = await api.get(endpoints.documents.list)
      return response.data || []
    },
    retry: 3
  })

  // Upload document mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      
      // Use the new file upload endpoint
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post(endpoints.documents.upload, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(progress)
          }
        }
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document uploaded successfully!')
      setUploadProgress(0)
      setIsUploading(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload document')
      setUploadProgress(0)
      setIsUploading(false)
    }
  })

  // Delete document mutation
  const deleteMutation = useMutation({
    mutationFn: async (docId: number) => {
      await api.delete(endpoints.documents.delete(docId))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document deleted successfully!')
    },
    onError: () => {
      toast.error('Failed to delete document')
    }
  })

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please upload a PDF, Word document, or text file')
      return
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB')
      return
    }

    setIsUploading(true)
    uploadMutation.mutate(file)
  }

  // Handle document deletion
  const handleDelete = (docId: number, title: string) => {
    if (window.confirm(`Are you sure you want to delete "${title}"?`)) {
      deleteMutation.mutate(docId)
    }
  }

  // Handle document preview
  const handlePreview = async (docId: number) => {
    try {
      const response = await api.get(`/corpus/doc/${docId}/preview`)
      setPreviewDoc(response.data.data)
      setIsPreviewOpen(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load document preview')
    }
  }

  // Filter documents based on search query
  const filteredDocuments = documents?.filter((doc: Document) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.source.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-600">Upload and manage your private documents</p>
        </div>
        <div className="mt-4 sm:mt-0">
          <label className="btn btn-primary cursor-pointer">
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
            <input
              type="file"
              className="hidden"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
          </label>
        </div>
      </div>

      {/* Upload Progress */}
      {isUploading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <LoadingSpinner size="sm" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">Uploading document...</p>
              <div className="mt-2 bg-blue-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-blue-700 mt-1">{uploadProgress}% complete</p>
            </div>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search documents by title or source..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Documents List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="text-center py-12">
          {searchQuery ? (
            <>
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No documents found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search terms or upload a new document.
              </p>
            </>
          ) : (
            <>
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No documents yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by uploading your first document to start interacting with AI.
              </p>
              <div className="mt-6">
                <label className="btn btn-primary cursor-pointer">
                  <Plus className="h-4 w-4 mr-2" />
                  Upload Document
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                  />
                </label>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredDocuments.map((doc: Document) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FileText className="h-8 w-8 text-blue-500 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                          <div className="text-sm text-gray-500">
                            {doc.doc_metadata?.file_size && formatFileSize(doc.doc_metadata.file_size)}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {doc.source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(doc.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => window.open(`/api/corpus/doc/${doc.id}/download`, '_blank')}
                          className="text-blue-600 hover:text-blue-900 transition-colors"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handlePreview(doc.id)}
                          className="text-green-600 hover:text-green-900 transition-colors"
                          title="Preview"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.title)}
                          className="text-red-600 hover:text-red-900 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Document Count */}
      {filteredDocuments.length > 0 && (
        <div className="text-sm text-gray-500 text-center">
          Showing {filteredDocuments.length} of {documents?.length || 0} documents
        </div>
      )}

      {/* Document Preview Modal */}
      {isPreviewOpen && previewDoc && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{previewDoc.title}</h2>
                <p className="text-sm text-gray-500">{previewDoc.original_filename}</p>
              </div>
              <button
                onClick={() => setIsPreviewOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-4">
                {/* File Info */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">File Type:</span>
                      <span className="ml-2 text-gray-900">{previewDoc.file_type}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">File Size:</span>
                      <span className="ml-2 text-gray-900">{formatFileSize(previewDoc.file_size)}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Uploaded:</span>
                      <span className="ml-2 text-gray-900">{formatDate(previewDoc.created_at)}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Source:</span>
                      <span className="ml-2 text-gray-900">{previewDoc.source}</span>
                    </div>
                  </div>
                </div>
                
                {/* Document Content */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Document Content</h3>
                  <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm text-gray-800 whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {previewDoc.text}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setIsPreviewOpen(false)}
                className="btn btn-outline"
              >
                Close
              </button>
              <button
                onClick={() => window.open(`/api/corpus/doc/${previewDoc.id}/download`, '_blank')}
                className="btn btn-primary"
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
