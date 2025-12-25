# Frontend Integration Guide - Memories & Storage

Complete guide for integrating your React frontend with the Timeless Love backend and Supabase "memories" bucket.

---

## Table of Contents
1. [Authentication Setup](#authentication-setup)
2. [File Upload Flow](#file-upload-flow)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [TypeScript Types](#typescript-types)
5. [React Examples](#react-examples)
6. [Error Handling](#error-handling)

---

## Authentication Setup

### Option 1: Supabase Frontend Auth (Recommended for New Apps)

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// lib/api-client.ts
export async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token || null
}

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getAuthToken()

  return fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
}
```

### Option 2: Backend JWT Auth (Existing)

```typescript
// lib/api-client.ts
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem('access_token')

  return fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
}
```

---

## File Upload Flow

### Complete Upload Process (3 Steps)

```typescript
/**
 * Step 1: Get signed upload URL from backend
 * Step 2: Upload file directly to Supabase Storage
 * Step 3: Create memory with storage path
 */

async function uploadMemoryWithMedia(
  memoryData: CreateMemoryData,
  files: File[]
): Promise<MemoryResponse> {

  // Step 1: Get upload URLs for each file
  const uploadUrls = await Promise.all(
    files.map(async (file) => {
      const response = await apiRequest('/api/v1/storage/upload-url', {
        method: 'POST',
        body: JSON.stringify({
          file_name: file.name,
          mime_type: file.type,
          memory_id: crypto.randomUUID(), // Generate temp ID
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get upload URL')
      }

      return await response.json() as UploadUrlResponse
    })
  )

  // Step 2: Upload files to Supabase Storage
  await Promise.all(
    uploadUrls.map(async ({ upload_url }, index) => {
      const file = files[index]

      const uploadResponse = await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      })

      if (!uploadResponse.ok) {
        throw new Error(`Failed to upload ${file.name}`)
      }
    })
  )

  // Step 3: Create memory with media references
  const mediaRefs = uploadUrls.map(({ storage_path }, index) => ({
    storage_path,
    file_name: files[index].name,
    mime_type: files[index].type,
    file_size: files[index].size,
  }))

  const response = await apiRequest('/api/v1/memories', {
    method: 'POST',
    body: JSON.stringify({
      ...memoryData,
      media: mediaRefs,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to create memory')
  }

  return await response.json()
}
```

---

## API Endpoints Reference

### 1. Memories Management

#### Create Memory
```typescript
POST /api/v1/memories
Authorization: Bearer {token}

Request:
{
  "title": "Family Vacation 2024",
  "description": "Amazing trip to the beach",
  "memory_date": "2024-07-15T10:30:00Z",
  "location": "Santa Monica Beach",
  "tags": ["vacation", "beach", "summer"],
  "status": "published",
  "media": [
    {
      "storage_path": "{family_id}/{memory_id}/beach.jpg",
      "file_name": "beach.jpg",
      "mime_type": "image/jpeg",
      "file_size": 2048576
    }
  ]
}

Response (201):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "family_unit_id": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Family Vacation 2024",
  "description": "Amazing trip to the beach",
  "memory_date": "2024-07-15T10:30:00Z",
  "location": "Santa Monica Beach",
  "tags": ["vacation", "beach", "summer"],
  "status": "published",
  "created_at": "2024-12-23T10:00:00Z",
  "updated_at": "2024-12-23T10:00:00Z",
  "modified_by": "660e8400-e29b-41d4-a716-446655440001",
  "media": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "memory_id": "550e8400-e29b-41d4-a716-446655440000",
      "storage_path": "770e8400.../beach.jpg",
      "storage_bucket": "memories",
      "file_name": "beach.jpg",
      "mime_type": "image/jpeg",
      "file_size": 2048576,
      "width": 1920,
      "height": 1080,
      "thumbnail_path": "770e8400.../beach_thumb.jpg",
      "processing_status": "completed",
      "created_at": "2024-12-23T10:00:00Z",
      "updated_at": "2024-12-23T10:00:00Z"
    }
  ]
}
```

#### Get Memory
```typescript
GET /api/v1/memories/{memoryId}
Authorization: Bearer {token}

Response (200):
{
  "id": "550e8400-...",
  "title": "Family Vacation 2024",
  // ... full memory object with media
}
```

#### Update Memory
```typescript
PUT /api/v1/memories/{memoryId}
Authorization: Bearer {token}

Request:
{
  "title": "Updated Title",
  "description": "Updated description",
  "tags": ["vacation", "beach"]
}

Response (200): Updated memory object
```

#### Delete Memory
```typescript
DELETE /api/v1/memories/{memoryId}
Authorization: Bearer {token}

Response (204): No Content
```

#### List Memories
```typescript
GET /api/v1/memories?limit=20&offset=0&status=published
Authorization: Bearer {token}

Response (200):
[
  {
    "id": "550e8400-...",
    "title": "Family Vacation 2024",
    // ... memory object
  },
  // ... more memories
]
```

### 2. Storage Management

#### Get Upload URL
```typescript
POST /api/v1/storage/upload-url
Authorization: Bearer {token}

Request:
{
  "memory_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "beach.jpg",
  "mime_type": "image/jpeg"
}

Response (200):
{
  "upload_url": "https://...supabase.co/storage/v1/object/memories/...",
  "storage_path": "{family_id}/{memory_id}/beach.jpg",
  "expires_in": 300
}
```

#### Get Access URL
```typescript
GET /api/v1/storage/access-url?storage_path={family_id}/{memory_id}/beach.jpg
Authorization: Bearer {token}

Response (200):
{
  "access_url": "https://...supabase.co/storage/v1/object/sign/memories/...",
  "expires_in": 3600
}
```

#### Get Media URL by ID
```typescript
GET /api/v1/storage/media/{mediaId}/url
Authorization: Bearer {token}

Response (200):
{
  "access_url": "https://...supabase.co/storage/v1/object/sign/memories/...",
  "expires_in": 3600
}
```

### 3. Feed & Social Interactions

#### Get Feed
```typescript
GET /api/v1/feed?limit=20&offset=0&status=published
Authorization: Bearer {token}

Response (200):
{
  "items": [
    {
      "memory": { /* memory object */ },
      "reactions": [
        {
          "id": "reaction-id",
          "emoji": "❤️",
          "user_id": "user-id",
          "created_at": "2024-12-23T10:00:00Z"
        }
      ],
      "comments": [
        {
          "id": "comment-id",
          "content": "Great photo!",
          "user_id": "user-id",
          "parent_comment_id": null,
          "created_at": "2024-12-23T10:00:00Z"
        }
      ],
      "reaction_counts": {
        "❤️": 5,
        "👍": 3
      },
      "comment_count": 12
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### Create Reaction
```typescript
POST /api/v1/feed/memories/{memoryId}/reactions
Authorization: Bearer {token}

Request:
{
  "emoji": "❤️"
}

Response (201):
{
  "id": "reaction-id",
  "memory_id": "memory-id",
  "user_id": "user-id",
  "emoji": "❤️",
  "created_at": "2024-12-23T10:00:00Z"
}
```

#### Create Comment
```typescript
POST /api/v1/feed/memories/{memoryId}/comments
Authorization: Bearer {token}

Request:
{
  "content": "Beautiful photo!",
  "parent_comment_id": null  // Optional, for nested replies
}

Response (201):
{
  "id": "comment-id",
  "memory_id": "memory-id",
  "user_id": "user-id",
  "content": "Beautiful photo!",
  "parent_comment_id": null,
  "created_at": "2024-12-23T10:00:00Z"
}
```

---

## TypeScript Types

```typescript
// types/memory.ts

export interface Memory {
  id: string
  user_id: string
  family_unit_id: string
  title: string
  description?: string
  memory_date?: string
  location?: string
  tags?: string[]
  status: 'draft' | 'published' | 'archived'
  created_at: string
  updated_at: string
  modified_by?: string
  media: Media[]
}

export interface Media {
  id: string
  memory_id: string
  storage_path: string
  storage_bucket: string
  file_name: string
  mime_type: string
  file_size: number
  width?: number
  height?: number
  duration?: number
  thumbnail_path?: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface CreateMemoryRequest {
  title: string
  description?: string
  memory_date?: string
  location?: string
  tags?: string[]
  status?: 'draft' | 'published' | 'archived'
  media: MediaReference[]
}

export interface MediaReference {
  storage_path: string
  file_name: string
  mime_type: string
  file_size: number
}

export interface UploadUrlRequest {
  memory_id: string
  file_name: string
  mime_type: string
}

export interface UploadUrlResponse {
  upload_url: string
  storage_path: string
  expires_in: number
}

export interface AccessUrlResponse {
  access_url: string
  expires_in: number
}

export interface Reaction {
  id: string
  memory_id: string
  user_id: string
  emoji: string
  created_at: string
}

export interface Comment {
  id: string
  memory_id: string
  user_id: string
  content: string
  parent_comment_id?: string
  created_at: string
  updated_at: string
}

export interface FeedItem {
  memory: Memory
  reactions: Reaction[]
  comments: Comment[]
  reaction_counts: Record<string, number>
  comment_count: number
}

export interface FeedResponse {
  items: FeedItem[]
  total: number
  page: number
  page_size: number
}
```

---

## React Examples

### Upload Memory with Files

```typescript
// components/MemoryUpload.tsx
import { useState } from 'react'
import { apiRequest } from '@/lib/api-client'
import type { CreateMemoryRequest, Memory } from '@/types/memory'

export function MemoryUpload() {
  const [files, setFiles] = useState<File[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setUploading(true)

    try {
      // Step 1: Get upload URLs
      const memoryId = crypto.randomUUID()
      const uploadPromises = files.map(async (file) => {
        const res = await apiRequest('/api/v1/storage/upload-url', {
          method: 'POST',
          body: JSON.stringify({
            memory_id: memoryId,
            file_name: file.name,
            mime_type: file.type,
          }),
        })

        if (!res.ok) throw new Error('Failed to get upload URL')
        return { file, ...(await res.json()) }
      })

      const uploadUrls = await Promise.all(uploadPromises)

      // Step 2: Upload files to Supabase Storage
      await Promise.all(
        uploadUrls.map(async ({ file, upload_url }) => {
          const res = await fetch(upload_url, {
            method: 'PUT',
            body: file,
            headers: { 'Content-Type': file.type },
          })

          if (!res.ok) throw new Error(`Failed to upload ${file.name}`)
        })
      )

      // Step 3: Create memory with media references
      const media = uploadUrls.map(({ storage_path, file }) => ({
        storage_path,
        file_name: file.name,
        mime_type: file.type,
        file_size: file.size,
      }))

      const memoryRes = await apiRequest('/api/v1/memories', {
        method: 'POST',
        body: JSON.stringify({
          title,
          description,
          status: 'published',
          media,
        } as CreateMemoryRequest),
      })

      if (!memoryRes.ok) throw new Error('Failed to create memory')

      const memory: Memory = await memoryRes.json()
      console.log('Memory created:', memory)

      // Reset form
      setFiles([])
      setTitle('')
      setDescription('')

      alert('Memory uploaded successfully!')
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed: ' + (error as Error).message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block mb-2">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          className="w-full px-4 py-2 border rounded"
        />
      </div>

      <div>
        <label className="block mb-2">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-4 py-2 border rounded"
          rows={4}
        />
      </div>

      <div>
        <label className="block mb-2">Upload Files</label>
        <input
          type="file"
          multiple
          accept="image/*,video/*"
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
          className="w-full"
        />
        {files.length > 0 && (
          <p className="text-sm text-gray-600 mt-2">
            {files.length} file(s) selected
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={uploading || !title || files.length === 0}
        className="px-6 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
      >
        {uploading ? 'Uploading...' : 'Create Memory'}
      </button>
    </form>
  )
}
```

### Display Memories Feed

```typescript
// components/MemoriesFeed.tsx
import { useEffect, useState } from 'react'
import { apiRequest } from '@/lib/api-client'
import type { FeedItem } from '@/types/memory'

export function MemoriesFeed() {
  const [feed, setFeed] = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadFeed() {
      try {
        const res = await apiRequest('/api/v1/feed?limit=20&offset=0')
        if (!res.ok) throw new Error('Failed to load feed')

        const data = await res.json()
        setFeed(data.items)
      } catch (error) {
        console.error('Feed error:', error)
      } finally {
        setLoading(false)
      }
    }

    loadFeed()
  }, [])

  if (loading) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      {feed.map((item) => (
        <MemoryCard key={item.memory.id} item={item} />
      ))}
    </div>
  )
}

function MemoryCard({ item }: { item: FeedItem }) {
  const { memory, reactions, comments, reaction_counts } = item

  async function handleReaction(emoji: string) {
    const res = await apiRequest(
      `/api/v1/feed/memories/${memory.id}/reactions`,
      {
        method: 'POST',
        body: JSON.stringify({ emoji }),
      }
    )

    if (res.ok) {
      // Refresh feed or update local state
      console.log('Reaction added')
    }
  }

  return (
    <div className="border rounded-lg p-6 bg-white shadow">
      <h2 className="text-2xl font-bold mb-2">{memory.title}</h2>
      <p className="text-gray-600 mb-4">{memory.description}</p>

      {/* Media Gallery */}
      {memory.media.length > 0 && (
        <MediaGallery media={memory.media} />
      )}

      {/* Reactions */}
      <div className="flex gap-4 mt-4">
        {Object.entries(reaction_counts).map(([emoji, count]) => (
          <button
            key={emoji}
            onClick={() => handleReaction(emoji)}
            className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 hover:bg-gray-200"
          >
            <span>{emoji}</span>
            <span>{count}</span>
          </button>
        ))}
      </div>

      {/* Comment Count */}
      <p className="text-sm text-gray-500 mt-4">
        {item.comment_count} comments
      </p>
    </div>
  )
}
```

### Media Gallery with Signed URLs

```typescript
// components/MediaGallery.tsx
import { useEffect, useState } from 'react'
import { apiRequest } from '@/lib/api-client'
import type { Media } from '@/types/memory'

export function MediaGallery({ media }: { media: Media[] }) {
  const [urls, setUrls] = useState<Record<string, string>>({})

  useEffect(() => {
    async function loadUrls() {
      const urlMap: Record<string, string> = {}

      await Promise.all(
        media.map(async (m) => {
          const res = await apiRequest(
            `/api/v1/storage/media/${m.id}/url`
          )

          if (res.ok) {
            const data = await res.json()
            urlMap[m.id] = data.access_url
          }
        })
      )

      setUrls(urlMap)
    }

    loadUrls()
  }, [media])

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {media.map((m) => (
        <div key={m.id} className="aspect-square relative">
          {urls[m.id] ? (
            m.mime_type.startsWith('image/') ? (
              <img
                src={urls[m.id]}
                alt={m.file_name}
                className="w-full h-full object-cover rounded"
              />
            ) : (
              <video
                src={urls[m.id]}
                controls
                className="w-full h-full object-cover rounded"
              />
            )
          ) : (
            <div className="w-full h-full bg-gray-200 rounded flex items-center justify-center">
              Loading...
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
```

---

## Error Handling

```typescript
// lib/api-errors.ts

export class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    message?: string
  ) {
    super(message || detail)
    this.name = 'APIError'
  }
}

export async function handleAPIResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))

    throw new APIError(
      response.status,
      error.detail || 'An error occurred',
      error.message
    )
  }

  return response.json()
}

// Usage:
try {
  const memory = await handleAPIResponse<Memory>(
    await apiRequest('/api/v1/memories/123')
  )
} catch (error) {
  if (error instanceof APIError) {
    if (error.status === 401) {
      // Redirect to login
    } else if (error.status === 403) {
      alert('Access denied')
    } else {
      alert(error.detail)
    }
  }
}
```

---

## Environment Variables

```bash
# .env.local

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase (if using Supabase auth)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## Quick Start Checklist

- [ ] Set up authentication (Supabase or Backend JWT)
- [ ] Configure API client with auth headers
- [ ] Implement file upload flow (3 steps)
- [ ] Create TypeScript types for API responses
- [ ] Build memory creation form
- [ ] Implement feed display with signed URLs
- [ ] Add reactions and comments
- [ ] Handle errors and loading states
- [ ] Test with Supabase "memories" bucket

---

## Storage Bucket Configuration

Your Supabase "memories" bucket should have:

```sql
-- RLS Policies for memories bucket
CREATE POLICY "Users can upload to their family folder"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'memories' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can view their family content"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'memories' AND
  (storage.foldername(name))[1] IN (
    SELECT family_unit_id::text
    FROM user_profiles
    WHERE id = auth.uid()
  )
);
```

---

## API Base URL by Environment

```typescript
// lib/config.ts
export const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? 'https://api.timelesslove.app'
    : 'http://localhost:8000'
```

---

**Ready to integrate?** All these endpoints are already implemented in your backend. Just follow the upload flow and you're good to go!
