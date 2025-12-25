/**
 * TypeScript types for Timeless Love API
 */

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

export interface FileUploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}
