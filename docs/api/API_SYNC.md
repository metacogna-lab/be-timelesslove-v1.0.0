# API Documentation Sync with Frontend Data Model

## Overview

This document tracks the synchronization between backend API documentation and the frontend data model defined in `docs/FRONTEND_DATAMODEL.md`.

## Data Model Alignment

### Family Units

**Frontend Model** (`family_units`):
- `id` (UUID)
- `name` (string, nullable)
- `created_by` (UUID)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Backend API**: No direct CRUD endpoint (created during registration)
- ✅ Aligned: Structure matches database schema

### User Profiles

**Frontend Model** (`user_profiles`):
- `id` (UUID) - matches `auth.users.id`
- `family_unit_id` (UUID)
- `role` (enum: adult, teen, child, grandparent, pet)
- `display_name` (string)
- `avatar_url` (string, nullable)
- `preferences` (JSONB object)
- `is_family_creator` (boolean)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Backend API**: Created via registration endpoints
- ✅ Aligned: All fields match
- ✅ API: `/api/v1/auth/register/{role}` creates user profile

### Memories

**Frontend Model** (`memories`):
- `id` (UUID)
- `user_id` (UUID)
- `family_unit_id` (UUID)
- `title` (string, nullable)
- `description` (string, nullable)
- `memory_date` (date, nullable)
- `location` (string, nullable)
- `tags` (array of strings)
- `status` (enum: draft, published, archived)
- `created_at` (timestamp)
- `updated_at` (timestamp)
- `modified_by` (UUID, nullable)

**Backend API**: `/api/v1/memories`
- ✅ Aligned: All fields match
- ✅ API: CRUD operations available
- ✅ Response includes `media` array

### Memory Media

**Frontend Model** (`memory_media`):
- `id` (UUID)
- `memory_id` (UUID)
- `storage_path` (string)
- `storage_bucket` (string)
- `file_name` (string)
- `mime_type` (string)
- `file_size` (integer)
- `width` (integer, nullable)
- `height` (integer, nullable)
- `duration` (integer, nullable)
- `thumbnail_path` (string, nullable)
- `processing_status` (enum: pending, processing, completed, failed)
- `metadata` (JSONB object)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Backend API**: `/api/v1/memories/{memory_id}/media`
- ✅ Aligned: All fields match
- ✅ API: Create and delete operations available

### Reactions

**Frontend Model** (`memory_reactions`):
- `id` (UUID)
- `memory_id` (UUID)
- `user_id` (UUID)
- `emoji` (string)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Backend API**: `/api/v1/feed/memories/{memory_id}/reactions`
- ✅ Aligned: All fields match
- ✅ API: Create, delete, and list operations available

### Comments

**Frontend Model** (`memory_comments`):
- `id` (UUID)
- `memory_id` (UUID)
- `user_id` (UUID)
- `parent_comment_id` (UUID, nullable)
- `content` (string)
- `created_at` (timestamp)
- `updated_at` (timestamp)
- `deleted_at` (timestamp, nullable)

**Backend API**: `/api/v1/feed/memories/{memory_id}/comments`
- ✅ Aligned: All fields match
- ✅ API: CRUD operations available
- ✅ Response includes `reply_count` and nested `replies`

### Invites

**Frontend Model** (`invites`):
- `id` (UUID)
- `family_unit_id` (UUID)
- `invited_by` (UUID)
- `email` (string)
- `role` (enum)
- `token` (string)
- `status` (enum: pending, accepted, expired, revoked)
- `expires_at` (timestamp)
- `accepted_at` (timestamp, nullable)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Backend API**: `/api/v1/invites`
- ✅ Aligned: All fields match
- ✅ API: Create, validate, and accept operations available

## API Endpoint Mapping

### Authentication

| Frontend Need | Backend Endpoint | Status |
|--------------|------------------|--------|
| Register adult | `POST /api/v1/auth/register/adult` | ✅ |
| Register teen | `POST /api/v1/auth/register/teen` | ✅ |
| Register grandparent | `POST /api/v1/auth/register/grandparent` | ✅ |
| Register child (via invite) | `POST /api/v1/auth/register/child` | ✅ |
| Login | `POST /api/v1/auth/login` | ✅ |
| Refresh token | `POST /api/v1/auth/refresh` | ✅ |

### Memories

| Frontend Need | Backend Endpoint | Status |
|--------------|------------------|--------|
| List memories | `GET /api/v1/memories` | ✅ |
| Get memory | `GET /api/v1/memories/{id}` | ✅ |
| Create memory | `POST /api/v1/memories` | ✅ |
| Update memory | `PUT /api/v1/memories/{id}` | ✅ |
| Delete memory | `DELETE /api/v1/memories/{id}` | ✅ |
| Add media | `POST /api/v1/memories/{id}/media` | ✅ |
| Delete media | `DELETE /api/v1/memories/{id}/media/{media_id}` | ✅ |

### Feed

| Frontend Need | Backend Endpoint | Status |
|--------------|------------------|--------|
| Get feed | `GET /api/v1/feed` | ✅ |
| Create reaction | `POST /api/v1/feed/memories/{id}/reactions` | ✅ |
| Delete reaction | `DELETE /api/v1/feed/memories/{id}/reactions/{reaction_id}` | ✅ |
| Get reactions | `GET /api/v1/feed/memories/{id}/reactions` | ✅ |
| Create comment | `POST /api/v1/feed/memories/{id}/comments` | ✅ |
| Update comment | `PUT /api/v1/feed/memories/{id}/comments/{comment_id}` | ✅ |
| Delete comment | `DELETE /api/v1/feed/memories/{id}/comments/{comment_id}` | ✅ |
| Get comments | `GET /api/v1/feed/memories/{id}/comments` | ✅ |

### Storage

| Frontend Need | Backend Endpoint | Status |
|--------------|------------------|--------|
| Get upload URL | `POST /api/v1/storage/upload-url` | ✅ |
| Get access URL | `GET /api/v1/storage/access-url` | ✅ |
| Get media URL | `GET /api/v1/storage/media/{media_id}/url` | ✅ |

### Invites

| Frontend Need | Backend Endpoint | Status |
|--------------|------------------|--------|
| Create invite | `POST /api/v1/invites` | ✅ |
| Validate invite | `GET /api/v1/invites/{token}` | ✅ |
| Accept invite | `POST /api/v1/invites/{token}/accept` | ✅ |

## Response Format Alignment

### Standard Response Fields

All API responses include:
- ✅ Consistent field naming (snake_case)
- ✅ ISO 8601 timestamps
- ✅ UUID format for IDs
- ✅ Nullable fields properly marked

### Pagination

Feed and list endpoints use consistent pagination:
- ✅ `page` and `page_size` query parameters
- ✅ Response includes `pagination` object with `has_more` flag
- ✅ Optional `total_count` for UI display

### Error Responses

All errors follow standard format:
- ✅ `{"detail": "message"}` structure
- ✅ HTTP status codes (400, 401, 403, 404, 422, 500)
- ✅ Validation errors as array of field errors

## Validation Rules

### Email Validation
- ✅ RFC 5322 compliant
- ✅ Backend and frontend use same validation

### Password Validation
- ✅ Minimum 8 characters
- ✅ Backend enforces, frontend should validate

### File Upload
- ✅ MIME type validation
- ✅ File size limits (50MB per file, 200MB per memory)
- ✅ Allowed types: JPEG, PNG, GIF, WebP, MP4, WebM

## Security Alignment

### Authentication
- ✅ JWT tokens with 15-minute access, 7-day refresh
- ✅ Token rotation on refresh
- ✅ Bearer token format

### Authorization
- ✅ Role-based access control
- ✅ Family unit scoping
- ✅ Ownership validation

## Sync Status

**Last Sync**: 2025-12-22
**Status**: ✅ All models aligned
**Notes**: 
- All frontend data model fields are supported by backend API
- All API endpoints match frontend requirements
- Response formats are consistent
- Error handling is standardized

## Future Sync Checklist

When updating either frontend data model or backend API:

1. ✅ Update this document
2. ✅ Update OpenAPI specification
3. ✅ Update frontend TypeScript types
4. ✅ Run contract tests
5. ✅ Update API documentation

