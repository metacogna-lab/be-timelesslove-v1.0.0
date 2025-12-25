'use client'

/**
 * Demo Frontend for Timeless Love
 * Tests backend API integration and Supabase storage
 */

import { useState, useEffect } from 'react'
import { supabase, isAuthenticated } from '@/lib/api-client'
import MemoryUploadDemo from '@/components/MemoryUploadDemo'
import FeedDemo from '@/components/FeedDemo'
import AuthDemo from '@/components/AuthDemo'

export default function Home() {
  const [authenticated, setAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'upload' | 'feed'>('upload')

  useEffect(() => {
    checkAuth()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(() => {
      checkAuth()
    })

    return () => subscription.unsubscribe()
  }, [])

  async function checkAuth() {
    const isAuth = await isAuthenticated()
    setAuthenticated(isAuth)
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!authenticated) {
    return <AuthDemo />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Timeless Love - Demo
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Test backend API and Supabase storage integration
              </p>
            </div>
            <button
              onClick={() => supabase.auth.signOut()}
              className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('upload')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition
                ${activeTab === 'upload'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Upload Memory
            </button>
            <button
              onClick={() => setActiveTab('feed')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition
                ${activeTab === 'feed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Feed
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' ? (
          <MemoryUploadDemo onSuccess={() => setActiveTab('feed')} />
        ) : (
          <FeedDemo />
        )}
      </div>

      {/* Footer */}
      <footer className="mt-16 border-t bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">API Status</h3>
              <p className="text-sm text-gray-600">
                Backend: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Supabase: Connected ✓
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Features</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>✓ File upload with progress</li>
                <li>✓ Memory creation</li>
                <li>✓ Feed display</li>
                <li>✓ Reactions & comments</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Documentation</h3>
              <p className="text-sm text-gray-600">
                See FRONTEND_INTEGRATION.md for complete API reference
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
