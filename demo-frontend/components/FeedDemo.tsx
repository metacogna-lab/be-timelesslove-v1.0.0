'use client'

import { useState, useEffect } from 'react'
import { apiRequest, APIError } from '@/lib/api-client'
import type { FeedResponse, FeedItem, Memory, Media } from '@/lib/types'

export default function FeedDemo() {
  const [feed, setFeed] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadFeed()
  }, [])

  async function loadFeed() {
    try {
      setLoading(true)
      setError(null)

      const response = await apiRequest<FeedResponse>(
        '/api/v1/feed?limit=20&offset=0&status=published'
      )

      setFeed(response.items)
    } catch (err) {
      console.error('Feed error:', err)

      if (err instanceof APIError) {
        setError(`Failed to load feed: ${err.detail}`)
      } else {
        setError('Failed to load feed')
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading feed...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadFeed}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (feed.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <p className="text-gray-600 text-lg mb-2">No memories yet</p>
        <p className="text-gray-500 text-sm">Upload your first memory to get started!</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Feed</h2>
        <button
          onClick={loadFeed}
          className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-6">
        {feed.map((item) => (
          <MemoryCard key={item.memory.id} item={item} onUpdate={loadFeed} />
        ))}
      </div>
    </div>
  )
}

function MemoryCard({ item, onUpdate }: { item: FeedItem; onUpdate: () => void }) {
  const { memory, reactions, comments, reaction_counts, comment_count } = item
  const [showComments, setShowComments] = useState(false)

  async function handleReaction(emoji: string) {
    try {
      await apiRequest(`/api/v1/feed/memories/${memory.id}/reactions`, {
        method: 'POST',
        body: JSON.stringify({ emoji }),
      })

      onUpdate()
    } catch (err) {
      console.error('Reaction error:', err)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">{memory.title}</h3>
        {memory.description && (
          <p className="text-gray-600 mb-4">{memory.description}</p>
        )}

        <div className="flex flex-wrap gap-2 text-sm text-gray-500">
          {memory.location && (
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {memory.location}
            </span>
          )}
          {memory.memory_date && (
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {new Date(memory.memory_date).toLocaleDateString()}
            </span>
          )}
        </div>

        {memory.tags && memory.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {memory.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Media Gallery */}
      {memory.media.length > 0 && (
        <MediaGallery media={memory.media} />
      )}

      {/* Reactions */}
      <div className="p-6 border-t">
        <div className="flex items-center gap-4 mb-4">
          {['❤️', '👍', '😊', '🎉', '👏'].map((emoji) => (
            <button
              key={emoji}
              onClick={() => handleReaction(emoji)}
              className="flex items-center gap-2 px-3 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition"
            >
              <span className="text-xl">{emoji}</span>
              <span className="text-sm font-medium text-gray-700">
                {reaction_counts[emoji] || 0}
              </span>
            </button>
          ))}
        </div>

        {/* Comments Toggle */}
        <button
          onClick={() => setShowComments(!showComments)}
          className="text-sm text-gray-600 hover:text-gray-900 font-medium"
        >
          {comment_count} {comment_count === 1 ? 'comment' : 'comments'}
        </button>

        {/* Comments (when expanded) */}
        {showComments && comments.length > 0 && (
          <div className="mt-4 space-y-3">
            {comments.map((comment) => (
              <div key={comment.id} className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-800">{comment.content}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(comment.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function MediaGallery({ media }: { media: Media[] }) {
  const [urls, setUrls] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadUrls() {
      const urlMap: Record<string, string> = {}

      try {
        await Promise.all(
          media.map(async (m) => {
            const response = await apiRequest<{ access_url: string }>(
              `/api/v1/storage/media/${m.id}/url`
            )
            urlMap[m.id] = response.access_url
          })
        )

        setUrls(urlMap)
      } catch (err) {
        console.error('Failed to load media URLs:', err)
      } finally {
        setLoading(false)
      }
    }

    loadUrls()
  }, [media])

  if (loading) {
    return (
      <div className="aspect-video bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const gridClass =
    media.length === 1
      ? 'grid-cols-1'
      : media.length === 2
      ? 'grid-cols-2'
      : 'grid-cols-2 md:grid-cols-3'

  return (
    <div className={`grid ${gridClass} gap-2 p-2 bg-gray-50`}>
      {media.map((m) => (
        <div key={m.id} className="aspect-square relative bg-gray-200 rounded-lg overflow-hidden">
          {urls[m.id] ? (
            m.mime_type.startsWith('image/') ? (
              <img
                src={urls[m.id]}
                alt={m.file_name}
                className="w-full h-full object-cover"
              />
            ) : m.mime_type.startsWith('video/') ? (
              <video
                src={urls[m.id]}
                controls
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-500">
                <p className="text-sm">Unsupported media type</p>
              </div>
            )
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
