import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { User, Building, Shield, Bell, Palette, Key, LogOut, Save, Edit3 } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import toast from 'react-hot-toast'

interface UserProfile {
  id: number
  email: string
  org_name: string
  created_at: string
  last_login?: string
}

interface OrganizationSettings {
  name: string
  plan: string
  max_documents: number
  max_users: number
  features: string[]
}

export default function Settings() {
  const { user, logout } = useAuth()
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [isEditingOrg, setIsEditingOrg] = useState(false)
  const [profileForm, setProfileForm] = useState({
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [orgForm, setOrgForm] = useState({
    name: '',
    description: ''
  })
  const queryClient = useQueryClient()

  // Fetch user profile
  const { data: userProfile, isLoading: isLoadingProfile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const response = await api.get('/auth/me')
      return response.data.data
    }
  })

  // Fetch organization settings
  const { data: orgSettings, isLoading: isLoadingOrg } = useQuery({
    queryKey: ['org-settings'],
    queryFn: async () => {
      const response = await api.get('/admin/org-settings')
      return response.data.data
    }
  })

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.put('/auth/profile', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] })
      toast.success('Profile updated successfully!')
      setIsEditingProfile(false)
      setProfileForm(prev => ({ ...prev, currentPassword: '', newPassword: '', confirmPassword: '' }))
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    }
  })

  // Update organization mutation
  const updateOrgMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.put('/admin/org', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-settings'] })
      toast.success('Organization updated successfully!')
      setIsEditingOrg(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update organization')
    }
  })

  // Handle profile form submission
  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (profileForm.newPassword && profileForm.newPassword !== profileForm.confirmPassword) {
      toast.error('New passwords do not match')
      return
    }

    const updateData: any = {}
    if (profileForm.email !== user?.email) {
      updateData.email = profileForm.email
    }
    if (profileForm.newPassword) {
      updateData.current_password = profileForm.currentPassword
      updateData.new_password = profileForm.newPassword
    }

    if (Object.keys(updateData).length > 0) {
      updateProfileMutation.mutate(updateData)
    }
  }

  // Handle organization form submission
  const handleOrgSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateOrgMutation.mutate(orgForm)
  }

  // Initialize forms when data loads
  React.useEffect(() => {
    if (userProfile) {
      setProfileForm(prev => ({ ...prev, email: userProfile.email }))
    }
    if (orgSettings) {
      setOrgForm(prev => ({ ...prev, name: orgSettings.name, description: orgSettings.description || '' }))
    }
  }, [userProfile, orgSettings])

  if (isLoadingProfile || isLoadingOrg) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account and organization preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Profile */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <User className="h-5 w-5 mr-2 text-blue-500" />
              User Profile
            </h2>
            <button
              onClick={() => setIsEditingProfile(!isEditingProfile)}
              className="btn btn-outline btn-sm"
            >
              <Edit3 className="h-4 w-4 mr-2" />
              {isEditingProfile ? 'Cancel' : 'Edit'}
            </button>
          </div>

          {isEditingProfile ? (
            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={profileForm.email}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Password
                </label>
                <input
                  type="password"
                  value={profileForm.currentPassword}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, currentPassword: e.target.value }))}
                  className="input w-full"
                  placeholder="Required to change password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  value={profileForm.newPassword}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, newPassword: e.target.value }))}
                  className="input w-full"
                  placeholder="Leave blank to keep current"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={profileForm.confirmPassword}
                  onChange={(e) => setProfileForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  className="input w-full"
                  placeholder="Confirm new password"
                />
              </div>

              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={updateProfileMutation.isPending}
                >
                  {updateProfileMutation.isPending ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditingProfile(false)}
                  className="btn btn-outline"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-500">Email:</span>
                <p className="text-gray-900">{userProfile?.email}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Member Since:</span>
                <p className="text-gray-900">
                  {userProfile?.created_at ? new Date(userProfile.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Last Login:</span>
                <p className="text-gray-900">
                  {userProfile?.last_login ? new Date(userProfile.last_login).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Organization Settings */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <Building className="h-5 w-5 mr-2 text-green-500" />
              Organization
            </h2>
            <button
              onClick={() => setIsEditingOrg(!isEditingOrg)}
              className="btn btn-outline btn-sm"
            >
              <Edit3 className="h-4 w-4 mr-2" />
              {isEditingOrg ? 'Cancel' : 'Edit'}
            </button>
          </div>

          {isEditingOrg ? (
            <form onSubmit={handleOrgSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Organization Name
                </label>
                <input
                  type="text"
                  value={orgForm.name}
                  onChange={(e) => setOrgForm(prev => ({ ...prev, name: e.target.value }))}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={orgForm.description}
                  onChange={(e) => setOrgForm(prev => ({ ...prev, description: e.target.value }))}
                  className="input w-full"
                  rows={3}
                  placeholder="Optional organization description"
                />
              </div>

              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={updateOrgMutation.isPending}
                >
                  {updateOrgMutation.isPending ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditingOrg(false)}
                  className="btn btn-outline"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-500">Name:</span>
                <p className="text-gray-900">{orgSettings?.name}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Plan:</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {orgSettings?.plan || 'Basic'}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Document Limit:</span>
                <p className="text-gray-900">{orgSettings?.max_documents || 'Unlimited'}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">User Limit:</span>
                <p className="text-gray-900">{orgSettings?.max_users || 'Unlimited'}</p>
              </div>
            </div>
          )}
        </div>

        {/* Security & Privacy */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 flex items-center mb-4">
            <Shield className="h-5 w-5 mr-2 text-purple-500" />
            Security & Privacy
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">Two-Factor Authentication</p>
                <p className="text-xs text-gray-500">Add an extra layer of security</p>
              </div>
              <button className="btn btn-outline btn-sm">Enable</button>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">Session Management</p>
                <p className="text-xs text-gray-500">View and manage active sessions</p>
              </div>
              <button className="btn btn-outline btn-sm">Manage</button>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">Data Export</p>
                <p className="text-xs text-gray-500">Download your data</p>
              </div>
              <button className="btn btn-outline btn-sm">Export</button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 flex items-center mb-4">
            <Bell className="h-5 w-5 mr-2 text-orange-500" />
            Notifications
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Email Notifications</p>
                <p className="text-xs text-gray-500">Receive updates via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Document Updates</p>
                <p className="text-xs text-gray-500">Notify when documents are processed</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">System Alerts</p>
                <p className="text-xs text-gray-500">Important system notifications</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-lg font-medium text-red-900 mb-4">Danger Zone</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-red-900">Sign Out</p>
            <p className="text-xs text-red-700">Sign out of your account</p>
          </div>
          <button
            onClick={logout}
            className="btn bg-red-600 hover:bg-red-700 text-white"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}
