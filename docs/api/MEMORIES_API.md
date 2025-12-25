# Memories API Documentation

## Overview

The Memories API provides endpoints for creating, managing, and accessing memories with associated media files. Media files are stored in Supabase Storage and accessed via signed URLs.

**Base URL**: `/api/v1/memories`

## Authentication

All endpoints require authentication via JWT Bearer token:

```
Authorization: Bearer <access_token>
```

## Endpoints

### Create Memory

**POST** `/api/v1/memories`

Create a new memory with media references.

**Request Body**:
```json
{
  "title": "Family Vacation",
  "description": "Our trip to the beach",
  "memory_date": "2024-01-15",
  "location": "Beach Resort",
  "tags": ["vacation", "beach", "family"],
  "status": "published",
  "media": [
    {
      "storage_path": "660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo.jpg",
      "file_name": "photo.jpg",
      "mime_type": "image/jpeg",
      "file_size": 2048576
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "Family Vacation",
  "description": "Our trip to the beach",
  "memory_date": "2024-01-15",
  "location": "Beach Resort",
  "tags": ["vacation", "beach", "family"],
  "status": "published",
  "created_at": "2024-01-20T12:00:00Z",
  "updated_at": "2024-01-20T12:00:00Z",
  "modified_by": null,
  "media": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "memory_id": "770e8400-e29b-41d4-a716-446655440002",
      "storage_path": "660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo.jpg",
      "storage_bucket": "memories",
      "file_name": "photo.jpg",
      "mime_type": "image/jpeg",
      "file_size": 2048576,
      "width": null,
      "height": null,
      "duration": null,
      "thumbnail_path": null,
      "processing_status": "pending",
      "created_at": "2024-01-20T12:00:00Z",
      "updated_at": "2024-01-20T12:00:00Z"
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input, file not found in storage, file size exceeded
- `403 Forbidden`: Access denied
- `500 Internal Server Error`: Server error

---

### Get Memory

**GET** `/api/v1/memories/{memory_id}`

Get memory details with associated media.

**Response** (200 OK): Same format as Create Memory response

**Error Responses**:
- `404 Not Found`: Memory not found
- `403 Forbidden`: Access denied

---

### Update Memory

**PUT** `/api/v1/memories/{memory_id}`

Update memory metadata.

**Request Body**:
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "tags": ["updated", "tags"],
  "status": "published"
}
```

**Response** (200 OK): Updated memory with media

**Error Responses**:
- `404 Not Found`: Memory not found
- `403 Forbidden`: Access denied or insufficient permissions

---

### Delete Memory

**DELETE** `/api/v1/memories/{memory_id}`

Delete a memory (cascades to media files).

**Response** (204 No Content)

**Error Responses**:
- `404 Not Found`: Memory not found
- `403 Forbidden`: Access denied or insufficient permissions

---

### List Memories

**GET** `/api/v1/memories?limit=20&offset=0&status=published`

List memories for the user's family unit.

**Query Parameters**:
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (draft, published, archived)

**Response** (200 OK):
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "Family Vacation",
    "description": "Our trip to the beach",
    "memory_date": "2024-01-15",
    "location": "Beach Resort",
    "tags": ["vacation", "beach", "family"],
    "status": "published",
    "created_at": "2024-01-20T12:00:00Z",
    "updated_at": "2024-01-20T12:00:00Z",
    "modified_by": null,
    "media": []
  }
]
```

---

### Add Media to Memory

**POST** `/api/v1/memories/{memory_id}/media`

Add media to an existing memory.

**Request Body**:
```json
{
  "storage_path": "660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo2.jpg",
  "file_name": "photo2.jpg",
  "mime_type": "image/jpeg",
  "file_size": 1536000
}
```

**Response** (201 Created):
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "memory_id": "770e8400-e29b-41d4-a716-446655440002",
  "storage_path": "660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo2.jpg",
  "storage_bucket": "memories",
  "file_name": "photo2.jpg",
  "mime_type": "image/jpeg",
  "file_size": 1536000,
  "width": null,
  "height": null,
  "duration": null,
  "thumbnail_path": null,
  "processing_status": "pending",
  "created_at": "2024-01-20T12:05:00Z",
  "updated_at": "2024-01-20T12:05:00Z"
}
```

---

### Remove Media from Memory

**DELETE** `/api/v1/memories/{memory_id}/media/{media_id}`

Remove media from a memory.

**Response** (204 No Content)

**Error Responses**:
- `404 Not Found`: Memory or media not found
- `403 Forbidden`: Access denied

---

## Storage Endpoints

### Generate Upload URL

**POST** `/api/v1/storage/upload-url`

Generate signed URL for uploading media to Supabase Storage.

**Request Body**:
```json
{
  "memory_id": "770e8400-e29b-41d4-a716-446655440002",
  "file_name": "photo.jpg",
  "mime_type": "image/jpeg"
}
```

**Response** (200 OK):
```json
{
  "upload_url": "https://...supabase.co/storage/v1/object/sign/memories/...",
  "storage_path": "660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo.jpg",
  "expires_in": 300
}
```

**Error Responses**:
- `400 Bad Request`: Invalid file name or MIME type
- `403 Forbidden`: Access denied

---

### Generate Access URL

**GET** `/api/v1/storage/access-url?storage_path={path}&expires_in=3600`

Generate signed URL for accessing media from Supabase Storage.

**Query Parameters**:
- `storage_path` (required): Path to file in storage
- `expires_in` (optional): URL expiration in seconds (default: 3600)

**Response** (200 OK):
```json
{
  "access_url": "https://...supabase.co/storage/v1/object/sign/memories/...",
  "expires_in": 3600
}
```

**Error Responses**:
- `400 Bad Request`: Invalid storage path
- `403 Forbidden`: Access denied (path doesn't belong to user's family)

---

### Get Media URL by ID

**GET** `/api/v1/storage/media/{media_id}/url?expires_in=3600`

Get signed URL for a specific media file by media ID.

**Query Parameters**:
- `expires_in` (optional): URL expiration in seconds (default: 3600)

**Response** (200 OK): Same as Generate Access URL

**Error Responses**:
- `404 Not Found`: Media not found
- `403 Forbidden`: Access denied

---

## Media Processing Status

Media files are processed asynchronously after upload. Check the `processing_status` field:

- **pending**: Uploaded, processing not started
- **processing**: Currently being processed
- **completed**: Thumbnail generated, metadata extracted
- **failed**: Processing failed (check `metadata.error`)

When `processing_status` is `completed`, the `thumbnail_path` field will contain the path to the generated thumbnail.

---

## Error Codes

### Standard HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Complete Upload Flow Example

```bash
# 1. Create memory
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Memory",
    "status": "published"
  }'

# 2. Get upload URL
curl -X POST http://localhost:8000/api/v1/storage/upload-url \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "770e8400-e29b-41d4-a716-446655440002",
    "file_name": "photo.jpg",
    "mime_type": "image/jpeg"
  }'

# 3. Upload file directly to Supabase Storage using upload_url
curl -X POST "<upload_url>" \
  -F "file=@photo.jpg"

# 4. Register media with backend
curl -X POST http://localhost:8000/api/v1/memories/770e8400-e29b-41d4-a716-446655440002/media \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path": "660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo.jpg",
    "file_name": "photo.jpg",
    "mime_type": "image/jpeg",
    "file_size": 2048576
  }'

# 5. Get access URL for displaying media
curl -X GET "http://localhost:8000/api/v1/storage/access-url?storage_path=660e8400-e29b-41d4-a716-446655440001/770e8400-e29b-41d4-a716-446655440002/photo.jpg" \
  -H "Authorization: Bearer <token>"
```

---

## File Size Limits

- **Per File**: 50MB maximum
- **Per Memory**: 200MB total (sum of all media files)

Exceeding these limits will result in `400 Bad Request` errors.

## Allowed File Types

### Images
- `image/jpeg` (.jpg, .jpeg)
- `image/png` (.png)
- `image/gif` (.gif)
- `image/webp` (.webp)

### Videos
- `video/mp4` (.mp4)
- `video/webm` (.webm)

---

## Security Considerations

1. **Family Scoping**: All memories and media are scoped to family units
2. **Signed URLs**: Time-limited access (5 min for uploads, 1 hour for access)
3. **Path Validation**: Storage paths validated to prevent path traversal
4. **File Type Validation**: Only whitelisted MIME types allowed
5. **Size Limits**: Enforced both client-side and server-side
6. **RLS Policies**: Database-level access control

---

## OpenAPI Specification

See `docs/api/openapi.yaml` for complete OpenAPI 3.0 specification including all memory and storage endpoints.

