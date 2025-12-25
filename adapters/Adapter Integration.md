# Adapter Integration Guide

## Overview

The Adapter Layer provides a clean, validated interface between the React Vite frontend and FastAPI backend. It handles request/response transformation, data validation, error translation, and structured logging without modifying existing frontend or backend code.

## Architecture

```
┌─────────────┐
│  Frontend   │
│  (React)    │
└──────┬──────┘
       │ HTTP Requests
       │ (Supabase tokens)
       ▼
┌─────────────────────────────────────┐
│      Adapter Layer                  │
│  ┌───────────────────────────────┐ │
│  │ Request Transformer           │ │
│  │ - Data normalization         │ │
│  │ - Field mapping               │ │
│  │ - Validation                  │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Backend Client                │ │
│  │ - HTTP client to FastAPI      │ │
│  │ - Token passthrough           │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Response Transformer          │ │
│  │ - Format conversion           │ │
│  │ - Field mapping               │ │
│  │ - Error translation           │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Logger & Events               │ │
│  │ - Structured logging          │ │
│  │ - Event emission               │ │
│  └───────────────────────────────┘ │
└──────┬─────────────────────────────┘
       │ HTTP Requests
       │ (Supabase tokens)
       ▼
┌─────────────┐
│   Backend   │
│  (FastAPI)  │
└─────────────┘
```

## Package Structure

```
backend/adapters/
├── __init__.py
├── config.py              # Adapter configuration
├── client.py               # HTTP client to backend
├── transformers/
│   ├── __init__.py
│   ├── request.py          # Request transformation
│   ├── response.py         # Response transformation
│   └── errors.py           # Error translation
├── validators/
│   ├── __init__.py
│   └── schemas.py          # Pydantic validation schemas
├── middleware/
│   ├── __init__.py
│   ├── logging.py          # Structured logging
│   └── sanitization.py    # Input/output sanitization
└── api/
    ├── __init__.py
    ├── auth.py             # Auth endpoint adapters
    ├── memories.py         # Memory endpoint adapters
    ├── feed.py             # Feed endpoint adapters
    ├── storage.py          # Storage endpoint adapters
    └── invites.py          # Invite endpoint adapters
```

## Integration Options

### Option 1: FastAPI Router (Recommended)

Mount adapter routers in `app/main.py`:

```python
from adapters.api import auth_adapter, memories_adapter, feed_adapter, storage_adapter, invites_adapter

# Mount adapter routers
app.include_router(auth_adapter, prefix=f"/adaptor/{settings.api_version}/auth", tags=["adaptor-auth"])
app.include_router(memories_adapter, prefix=f"/adaptor/{settings.api_version}/memories", tags=["adaptor-memories"])
app.include_router(feed_adapter, prefix=f"/adaptor/{settings.api_version}/feed", tags=["adaptor-feed"])
app.include_router(storage_adapter, prefix=f"/adaptor/{settings.api_version}/storage", tags=["adaptor-storage"])
app.include_router(invites_adapter, prefix=f"/adaptor/{settings.api_version}/invites", tags=["adaptor-invites"])
```

### Option 2: Library Usage

Use adapter as a library in your own FastAPI routes:

```python
from adapters.client import AdapterClient
from adapters.transformers.request import RequestTransformer
from adapters.transformers.response import ResponseTransformer

async def my_endpoint(request: MyRequest, token: str):
    transformer = RequestTransformer()
    client = AdapterClient()
    
    transformed = transformer.transform_memory_request(request.dict())
    response = await client.request("POST", "/memories", token=token, json=transformed)
    return response_transformer.transform_memory_response(response.json())
```

## API Endpoint Mapping

### Authentication Endpoints

| Frontend Need | Adapter Endpoint | Backend Endpoint |
|--------------|------------------|------------------|
| Register adult | `POST /adaptor/v1/auth/register/adult` | `POST /api/v1/auth/register/adult` |
| Register teen | `POST /adaptor/v1/auth/register/teen` | `POST /api/v1/auth/register/teen` |
| Register grandparent | `POST /adaptor/v1/auth/register/grandparent` | `POST /api/v1/auth/register/grandparent` |

### Memory Endpoints

| Frontend Need | Adapter Endpoint | Backend Endpoint |
|--------------|------------------|------------------|
| Create memory | `POST /adaptor/v1/memories` | `POST /api/v1/memories` |
| Get memory | `GET /adaptor/v1/memories/{id}` | `GET /api/v1/memories/{id}` |
| Update memory | `PUT /adaptor/v1/memories/{id}` | `PUT /api/v1/memories/{id}` |
| Delete memory | `DELETE /adaptor/v1/memories/{id}` | `DELETE /api/v1/memories/{id}` |
| List memories | `GET /adaptor/v1/memories` | `GET /api/v1/memories` |

### Feed Endpoints

| Frontend Need | Adapter Endpoint | Backend Endpoint |
|--------------|------------------|------------------|
| Get feed | `GET /adaptor/v1/feed` | `GET /api/v1/feed` |
| Create reaction | `POST /adaptor/v1/feed/memories/{id}/reactions` | `POST /api/v1/feed/memories/{id}/reactions` |
| Delete reaction | `DELETE /adaptor/v1/feed/memories/{id}/reactions/{reaction_id}` | `DELETE /api/v1/feed/memories/{id}/reactions/{reaction_id}` |
| Get reactions | `GET /adaptor/v1/feed/memories/{id}/reactions` | `GET /api/v1/feed/memories/{id}/reactions` |
| Create comment | `POST /adaptor/v1/feed/memories/{id}/comments` | `POST /api/v1/feed/memories/{id}/comments` |
| Get comments | `GET /adaptor/v1/feed/memories/{id}/comments` | `GET /api/v1/feed/memories/{id}/comments` |

### Storage Endpoints

| Frontend Need | Adapter Endpoint | Backend Endpoint |
|--------------|------------------|------------------|
| Get upload URL | `POST /adaptor/v1/storage/upload-url` | `POST /api/v1/storage/upload-url` |
| Get access URL | `GET /adaptor/v1/storage/access-url` | `GET /api/v1/storage/access-url` |
| Get media URL | `GET /adaptor/v1/storage/media/{id}/url` | `GET /api/v1/storage/media/{id}/url` |

### Invitation Endpoints

| Frontend Need | Adapter Endpoint | Backend Endpoint |
|--------------|------------------|------------------|
| Create invite | `POST /adaptor/v1/invites` | `POST /api/v1/invites` |
| Validate invite | `GET /adaptor/v1/invites/{token}` | `GET /api/v1/invites/{token}` |
| Accept invite | `POST /adaptor/v1/invites/{token}/accept` | `POST /api/v1/invites/{token}/accept` |

## Request/Response Examples

### Memory Creation

**Frontend Request:**
```json
POST /adaptor/v1/memories
Authorization: Bearer <supabase_token>

{
  "title": "Family Vacation",
  "description": "Amazing trip to the beach",
  "memory_date": "2024-07-15",
  "tags": ["vacation", "beach"],
  "status": "published",
  "media": [
    {
      "storage_path": "family_id/memory_id/photo.jpg",
      "file_name": "photo.jpg",
      "mime_type": "image/jpeg",
      "file_size": 2048576
    }
  ]
}
```

**Adapter Processing:**
1. Validates request using `FrontendMemoryRequest` schema
2. Sanitizes input data
3. Transforms date format (if needed)
4. Calls backend API
5. Transforms response
6. Sanitizes output
7. Returns to frontend

**Frontend Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "family_unit_id": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Family Vacation",
  "description": "Amazing trip to the beach",
  "memory_date": "2024-07-15",
  "tags": ["vacation", "beach"],
  "status": "published",
  "created_at": "2024-12-23T10:00:00Z",
  "updated_at": "2024-12-23T10:00:00Z",
  "media": [...]
}
```

### Feed Retrieval

**Frontend Request:**
```json
GET /adaptor/v1/feed?page=1&page_size=20&status=published&order_by=feed_score
Authorization: Bearer <supabase_token>
```

**Frontend Response:**
```json
{
  "items": [
    {
      "id": "memory-id",
      "title": "Memory Title",
      "feed_score": 0.95,
      "reaction_count": 5,
      "comment_count": 3,
      "reactions_by_emoji": {
        "❤️": 3,
        "👍": 2
      },
      "user_reactions": ["❤️"],
      "top_comments": [...]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "has_more": true,
  "total_count": 100
}
```

## Error Handling

### Error Response Format

All errors are returned in a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "status_code": 400,
    "details": {
      "field": "memory_date",
      "reason": "Date must be in YYYY-MM-DD format"
    }
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Input validation failed | 400, 422 |
| `UNAUTHORIZED` | Authentication required | 401 |
| `FORBIDDEN` | Access denied | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `CONFLICT` | Resource conflict | 409 |
| `NETWORK_ERROR` | Network/connection error | N/A |
| `INTERNAL_ERROR` | Server error | 500 |

### Example Error Responses

**Validation Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "status_code": 400,
    "details": {
      "validation_errors": [
        {
          "field": "memory_date",
          "message": "memory_date must be in YYYY-MM-DD format"
        }
      ]
    }
  }
}
```

**Authentication Error:**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required",
    "status_code": 401,
    "details": {
      "message": "Invalid or expired token"
    }
  }
}
```

## Data Transformation

### Date Normalization

The adapter automatically normalizes date formats:

- **Input**: Accepts ISO date strings (`YYYY-MM-DD`), datetime strings, or date objects
- **Output**: Always returns ISO date strings (`YYYY-MM-DD`) for dates, ISO datetime strings for timestamps

### Field Name Mapping

Currently, both frontend and backend use `snake_case`, so no field name transformation is needed. The adapter ensures consistency.

### UUID Format

All UUIDs are normalized to strings in responses, ensuring frontend compatibility.

## Configuration

### Environment Variables

The adapter uses the following configuration (via `AdapterConfig`):

```python
# Backend API
BACKEND_API_BASE_URL=http://localhost:8000  # Default
API_VERSION=v1  # Default

# Request settings
REQUEST_TIMEOUT_SECONDS=30  # Default
MAX_RETRIES=3  # Default

# Logging
LOG_REQUESTS=true  # Default
LOG_RESPONSES=true  # Default
LOG_ERRORS=true  # Default

# Validation
STRICT_VALIDATION=true  # Default
SANITIZE_INPUTS=true  # Default
SANITIZE_OUTPUTS=true  # Default

# Error handling
EXPOSE_INTERNAL_ERRORS=false  # Default
DEFAULT_ERROR_MESSAGE="An error occurred processing your request"  # Default
```

### Configuration Override

You can override configuration programmatically:

```python
from adapters.config import AdapterConfig

config = AdapterConfig(
    backend_api_base_url="https://api.example.com",
    request_timeout_seconds=60,
    log_requests=False,
)
```

## Logging

### Structured Logging

All adapter operations are logged with structured data:

**Request Log:**
```json
{
  "request_id": "uuid",
  "method": "POST",
  "path": "/memories",
  "user_id": "user-uuid",
  "timestamp": "2024-12-23T10:00:00Z"
}
```

**Response Log:**
```json
{
  "request_id": "uuid",
  "status_code": 201,
  "duration_ms": 125.5,
  "timestamp": "2024-12-23T10:00:00Z"
}
```

**Error Log:**
```json
{
  "request_id": "uuid",
  "error_type": "HTTPStatusError",
  "error_message": "400 Bad Request",
  "status_code": 400,
  "timestamp": "2024-12-23T10:00:00Z"
}
```

### Log Levels

- **INFO**: Normal operations (requests, responses)
- **ERROR**: Errors and exceptions
- **DEBUG**: Detailed debugging information (if enabled)

## Security

### Input Sanitization

All inputs are sanitized by default:
- Control characters removed
- String length limits enforced
- HTML entities escaped (if needed)
- Sensitive data redacted in logs

### Output Sanitization

All outputs are sanitized:
- Sensitive fields removed (passwords, tokens)
- Control characters removed
- Data structure validated

### Token Handling

- Supabase tokens are passed through to backend
- Tokens are never logged or exposed
- Token validation handled by backend

## Versioning

The adapter supports API versioning via URL prefix:

- **v1**: `/adaptor/v1/*`
- **v2**: `/adaptor/v2/*` (future)

Version-specific transformers and validators can be implemented as needed.

## Testing

### Unit Tests

Test individual components:

```python
from adapters.transformers.request import RequestTransformer

def test_memory_request_transformation():
    transformer = RequestTransformer()
    data = {"memory_date": "2024-07-15", "tags": "beach,summer"}
    result = transformer.transform_memory_request(data)
    assert result["memory_date"] == "2024-07-15"
    assert result["tags"] == ["beach", "summer"]
```

### Integration Tests

Test full request/response cycle:

```python
from adapters.client import AdapterClient

async def test_create_memory():
    async with AdapterClient() as client:
        response = await client.request(
            "POST",
            "/memories",
            token="test-token",
            json={"title": "Test", "status": "draft"}
        )
        assert response.status_code == 201
```

## Migration Guide

### From Direct Backend Calls

If your frontend currently calls backend directly:

1. **Update API base URL**: Change from `/api/v1/*` to `/adaptor/v1/*`
2. **No code changes needed**: Adapter maintains backward compatibility
3. **Test thoroughly**: Verify all endpoints work correctly
4. **Monitor logs**: Check adapter logs for any issues

### Gradual Migration

You can migrate gradually:
- Keep existing endpoints active
- Route new features through adapter
- Migrate endpoints one by one
- Remove old endpoints when migration complete

## Troubleshooting

### Common Issues

**Issue**: 401 Unauthorized errors
- **Solution**: Ensure Supabase token is passed in Authorization header

**Issue**: Validation errors
- **Solution**: Check request format matches schema (see examples above)

**Issue**: Network errors
- **Solution**: Verify backend is running and accessible at `BACKEND_API_BASE_URL`

**Issue**: Timeout errors
- **Solution**: Increase `REQUEST_TIMEOUT_SECONDS` in configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("adapters").setLevel(logging.DEBUG)
```

## Best Practices

1. **Always use adapter endpoints** for new features
2. **Validate requests** before sending (adapter also validates)
3. **Handle errors gracefully** using error response format
4. **Monitor logs** for performance and errors
5. **Keep adapter updated** with backend API changes

## Support

For issues or questions:
1. Check logs for detailed error information
2. Review this documentation
3. Check backend API documentation
4. Review adapter source code

## Future Enhancements

- [ ] Request/response caching (if needed)
- [ ] Rate limiting
- [ ] Request batching
- [ ] GraphQL support
- [ ] WebSocket adapter
- [ ] Metrics and monitoring dashboard

