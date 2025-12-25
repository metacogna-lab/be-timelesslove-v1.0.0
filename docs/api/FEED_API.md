# Feed & Interaction API Documentation

## Overview

The Feed & Interaction API provides endpoints for viewing the memory feed with engagement-based ordering, reacting to memories with emojis, and creating threaded comments.

## Base URL

```
/api/v1/feed
```

## Authentication

All endpoints require authentication via JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Feed Endpoints

### Get Memory Feed

Get a paginated feed of family memories with engagement-based ordering.

**Endpoint:** `GET /feed`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | `published` | Filter by memory status: `draft`, `published`, `archived` |
| `user_id` | UUID | No | - | Filter by memory creator |
| `tags` | string | No | - | Comma-separated list of tags to filter by |
| `memory_date_from` | ISO date | No | - | Filter memories from this date |
| `memory_date_to` | ISO date | No | - | Filter memories to this date |
| `search_query` | string | No | - | Search in title and description |
| `order_by` | string | No | `feed_score` | Sort by: `feed_score`, `created_at`, `memory_date` |
| `order_direction` | string | No | `desc` | Sort direction: `asc`, `desc` |
| `page` | integer | No | `1` | Page number (1-indexed) |
| `page_size` | integer | No | `20` | Items per page (1-100) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001",
      "family_unit_id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Family Vacation 2024",
      "description": "Amazing trip to the beach",
      "memory_date": "2024-07-15",
      "location": "Beach Resort",
      "tags": ["vacation", "beach", "family"],
      "status": "published",
      "created_at": "2024-07-15T10:00:00Z",
      "updated_at": "2024-07-15T10:00:00Z",
      "media": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440003",
          "storage_path": "memories/2024/07/photo.jpg",
          "file_name": "photo.jpg",
          "mime_type": "image/jpeg",
          "thumbnail_path": "thumbnails/2024/07/photo_thumb.jpg",
          "processing_status": "completed"
        }
      ],
      "reaction_count": 5,
      "comment_count": 3,
      "reactions_by_emoji": {
        "👍": 3,
        "❤️": 2
      },
      "user_reactions": ["👍"],
      "top_comments": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440004",
          "memory_id": "550e8400-e29b-41d4-a716-446655440000",
          "user_id": "550e8400-e29b-41d4-a716-446655440001",
          "parent_comment_id": null,
          "content": "Great memories!",
          "created_at": "2024-07-15T11:00:00Z",
          "updated_at": "2024-07-15T11:00:00Z",
          "deleted_at": null,
          "reply_count": 1,
          "replies": []
        }
      ],
      "feed_score": 0.85
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "has_more": true
  },
  "total_count": 95,
  "has_more": true
}
```

**Feed Score Calculation:**

The feed score combines time-based recency and engagement metrics:

- **Time Score**: Exponential decay based on hours since creation
  - Last 24 hours: 100% weight
  - 1-7 days: 70% weight
  - 7-30 days: 40% weight
  - 30+ days: 20% weight

- **Engagement Score**: Weighted sum of reactions and comments
  - Reactions: 1.0x weight
  - Comments: 2.0x weight
  - Normalized using log scale

- **Final Score**: `(time_score * 0.6) + (engagement_score * 0.4)`

**Error Responses:**

- `400 Bad Request`: Invalid filter parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

---

## Reaction Endpoints

### Create Reaction

Add an emoji reaction to a memory.

**Endpoint:** `POST /feed/memories/{memory_id}/reactions`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |

**Request Body:**

```json
{
  "emoji": "👍"
}
```

**Supported Emojis:**

- `👍` (thumbs_up)
- `❤️` (heart)
- `😂` (laughing)
- `😮` (surprised)
- `😢` (sad)
- `🎉` (celebration)
- `🔥` (fire)
- `💯` (hundred)

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440005",
  "memory_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "emoji": "👍",
  "created_at": "2024-07-15T12:00:00Z",
  "updated_at": "2024-07-15T12:00:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Reaction already exists, invalid emoji, or memory not found
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

### Delete Reaction

Remove a reaction from a memory.

**Endpoint:** `DELETE /feed/memories/{memory_id}/reactions/{reaction_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |
| `reaction_id` | UUID | The reaction ID |

**Response:** `200 OK`

```json
{
  "message": "Reaction deleted"
}
```

**Error Responses:**

- `400 Bad Request`: Reaction not found or user doesn't own it
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

### Get Reactions

Get all reactions for a memory.

**Endpoint:** `GET /feed/memories/{memory_id}/reactions`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440005",
    "memory_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "emoji": "👍",
    "created_at": "2024-07-15T12:00:00Z",
    "updated_at": "2024-07-15T12:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440006",
    "memory_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "emoji": "❤️",
    "created_at": "2024-07-15T12:05:00Z",
    "updated_at": "2024-07-15T12:05:00Z"
  }
]
```

**Error Responses:**

- `400 Bad Request`: Memory not found or access denied
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

---

## Comment Endpoints

### Create Comment

Create a comment on a memory. Supports threaded replies via `parent_comment_id`.

**Endpoint:** `POST /feed/memories/{memory_id}/comments`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |

**Request Body:**

```json
{
  "content": "This is a great memory!",
  "parent_comment_id": null
}
```

**Request Body Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Comment content (1-5000 characters) |
| `parent_comment_id` | UUID | No | Parent comment ID for threaded replies (max 3 levels) |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440007",
  "memory_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "parent_comment_id": null,
  "content": "This is a great memory!",
  "created_at": "2024-07-15T13:00:00Z",
  "updated_at": "2024-07-15T13:00:00Z",
  "deleted_at": null,
  "reply_count": 0,
  "replies": []
}
```

**Error Responses:**

- `400 Bad Request`: Invalid content, nesting depth exceeded, or memory not found
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

### Update Comment

Update a comment's content.

**Endpoint:** `PUT /feed/memories/{memory_id}/comments/{comment_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |
| `comment_id` | UUID | The comment ID |

**Request Body:**

```json
{
  "content": "Updated comment content"
}
```

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440007",
  "memory_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "parent_comment_id": null,
  "content": "Updated comment content",
  "created_at": "2024-07-15T13:00:00Z",
  "updated_at": "2024-07-15T13:30:00Z",
  "deleted_at": null,
  "reply_count": 0,
  "replies": []
}
```

**Error Responses:**

- `400 Bad Request`: Comment not found, user doesn't own it, or invalid content
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

### Delete Comment

Soft-delete a comment. Users can delete their own comments, or adults can delete any comment in their family.

**Endpoint:** `DELETE /feed/memories/{memory_id}/comments/{comment_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |
| `comment_id` | UUID | The comment ID |

**Response:** `200 OK`

```json
{
  "message": "Comment deleted"
}
```

**Error Responses:**

- `400 Bad Request`: Comment not found or access denied
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

### Get Comments

Get comments for a memory, optionally with nested replies.

**Endpoint:** `GET /feed/memories/{memory_id}/comments`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `memory_id` | UUID | The memory ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_replies` | boolean | No | `true` | Include nested replies |
| `limit` | integer | No | - | Maximum number of top-level comments (1-100) |

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440007",
    "memory_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "parent_comment_id": null,
    "content": "This is a great memory!",
    "created_at": "2024-07-15T13:00:00Z",
    "updated_at": "2024-07-15T13:00:00Z",
    "deleted_at": null,
    "reply_count": 2,
    "replies": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440008",
        "memory_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440002",
        "parent_comment_id": "550e8400-e29b-41d4-a716-446655440007",
        "content": "I agree!",
        "created_at": "2024-07-15T13:10:00Z",
        "updated_at": "2024-07-15T13:10:00Z",
        "deleted_at": null,
        "reply_count": 0,
        "replies": []
      }
    ]
  }
]
```

**Error Responses:**

- `400 Bad Request`: Memory not found or access denied
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Server error

---

## Metrics Logging

All feed interactions are automatically logged for analytics:

- **feed_view**: User viewed the feed
- **reaction_created**: User created a reaction
- **reaction_deleted**: User deleted a reaction
- **comment_created**: User created a comment
- **comment_updated**: User updated a comment
- **comment_deleted**: User deleted a comment

Metrics are logged asynchronously and do not affect request performance.

---

## Rate Limiting

Currently, no rate limiting is enforced. This will be added in a future phase.

---

## Security Considerations

1. **Family Scoping**: All endpoints enforce family unit access control. Users can only interact with memories in their family.

2. **Ownership Validation**: Users can only modify their own reactions and comments (except adults can delete any comment in their family).

3. **Content Validation**: Comment content is validated for length and non-empty after trimming.

4. **Nesting Limits**: Comment threading is limited to 3 levels to prevent deep nesting.

5. **Soft Deletes**: Comments are soft-deleted (marked with `deleted_at`) to preserve thread structure.

---

## Example Usage

### Get Feed with Filters

```bash
curl -X GET "https://api.example.com/api/v1/feed?status=published&tags=vacation,beach&page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

### Create Reaction

```bash
curl -X POST "https://api.example.com/api/v1/feed/memories/550e8400-e29b-41d4-a716-446655440000/reactions" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"emoji": "👍"}'
```

### Create Comment

```bash
curl -X POST "https://api.example.com/api/v1/feed/memories/550e8400-e29b-41d4-a716-446655440000/comments" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "This is a great memory!"}'
```

### Create Reply

```bash
curl -X POST "https://api.example.com/api/v1/feed/memories/550e8400-e29b-41d4-a716-446655440000/comments" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I agree!",
    "parent_comment_id": "550e8400-e29b-41d4-a716-446655440007"
  }'
```

