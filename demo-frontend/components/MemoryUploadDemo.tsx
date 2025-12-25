'use client'

import { useState } from 'react'
import { apiRequest, uploadFile, APIError } from '@/lib/api-client'
import type {
  CreateMemoryRequest,
  Memory,
  UploadUrlResponse,
  FileUploadProgress,
} from '@/lib/types'

interface Props {
  onSuccess?: () => void
}

export default function MemoryUploadDemo({ onSuccess }: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [tags, setTags] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [uploadProgress, setUploadProgress] = useState<FileUploadProgress[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(e.target.files || [])
    setFiles(selectedFiles)
    setUploadProgress(
      selectedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'uploading',
      }))
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setUploading(true)
    setError(null)
    setSuccess(false)

    try {
      // Step 1: Get upload URLs for each file
      const memoryId = crypto.randomUUID()

      const uploadUrlPromises = files.map(async (file, index) => {
        const response = await apiRequest<UploadUrlResponse>(
          '/api/v1/storage/upload-url',
          {
            method: 'POST',
            body: JSON.stringify({
              memory_id: memoryId,
              file_name: file.name,
              mime_type: file.type,
            }),
          }
        )

        return { file, index, ...response }
      })

      const uploadUrls = await Promise.all(uploadUrlPromises)

      // Step 2: Upload files to Supabase Storage
      await Promise.all(
        uploadUrls.map(async ({ file, index, upload_url }) => {
          await uploadFile(upload_url, file, (progress) => {
            setUploadProgress((prev) =>
              prev.map((p, i) =>
                i === index ? { ...p, progress } : p
              )
            )
          })

          setUploadProgress((prev) =>
            prev.map((p, i) =>
              i === index ? { ...p, status: 'completed', progress: 100 } : p
            )
          )
        })
      )

      // Step 3: Create memory with media references
      const mediaRefs = uploadUrls.map(({ storage_path, file }) => ({
        storage_path,
        file_name: file.name,
        mime_type: file.type,
        file_size: file.size,
      }))

      const tagArray = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)

      const memoryRequest: CreateMemoryRequest = {
        title,
        description: description || undefined,
        location: location || undefined,
        tags: tagArray.length > 0 ? tagArray : undefined,
        status: 'published',
        media: mediaRefs,
      }

      const memory = await apiRequest<Memory>('/api/v1/memories', {
        method: 'POST',
        body: JSON.stringify(memoryRequest),
      })

      console.log('Memory created:', memory)

      setSuccess(true)

      // Reset form
      setTimeout(() => {
        setTitle('')
        setDescription('')
        setLocation('')
        setTags('')
        setFiles([])
        setUploadProgress([])
        setSuccess(false)

        if (onSuccess) {
          onSuccess()
        }
      }, 2000)
    } catch (err) {
      console.error('Upload error:', err)

      if (err instanceof APIError) {
        setError(`API Error (${err.status}): ${err.detail}`)
      } else {
        setError((err as Error).message || 'Upload failed')
      }

      setUploadProgress((prev) =>
        prev.map((p) => ({ ...p, status: 'error', error: 'Upload failed' }))
      )
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Upload Memory
        </h2>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-semibold">Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            <p className="font-semibold">Success!</p>
            <p className="text-sm mt-1">Memory created successfully</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              disabled={uploading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              placeholder="Family Vacation 2024"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={uploading}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              placeholder="Amazing trip to the beach..."
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              disabled={uploading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              placeholder="Santa Monica Beach"
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              disabled={uploading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              placeholder="vacation, beach, summer"
            />
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Files *
            </label>
            <input
              type="file"
              multiple
              accept="image/*,video/*"
              onChange={handleFileChange}
              disabled={uploading}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
            />
            <p className="text-xs text-gray-500 mt-2">
              Supported formats: JPG, PNG, GIF, MP4, WebM (max 50MB per file)
            </p>
          </div>

          {/* Upload Progress */}
          {uploadProgress.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">
                Upload Progress:
              </p>
              {uploadProgress.map((progress, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 truncate max-w-xs">
                      {progress.file.name}
                    </span>
                    <span
                      className={`font-medium ${
                        progress.status === 'completed'
                          ? 'text-green-600'
                          : progress.status === 'error'
                          ? 'text-red-600'
                          : 'text-blue-600'
                      }`}
                    >
                      {progress.status === 'completed'
                        ? '✓ Done'
                        : progress.status === 'error'
                        ? '✗ Failed'
                        : `${Math.round(progress.progress)}%`}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        progress.status === 'completed'
                          ? 'bg-green-500'
                          : progress.status === 'error'
                          ? 'bg-red-500'
                          : 'bg-blue-500'
                      }`}
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={uploading || !title || files.length === 0}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating Memory...
              </span>
            ) : (
              'Create Memory'
            )}
          </button>
        </form>

        {/* Info */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>How it works:</strong> Files are uploaded directly to Supabase Storage via signed URLs,
            then linked to the memory record in the database. This ensures fast, secure uploads.
          </p>
        </div>
      </div>
    </div>
  )
}
