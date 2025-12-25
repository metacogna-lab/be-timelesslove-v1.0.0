# Standard Error Responses

## Overview

All API endpoints follow a consistent error response format to enable predictable error handling in the frontend.

## Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors, the response includes field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## HTTP Status Codes

### 400 Bad Request

Returned when:
- Request body validation fails
- Invalid parameter values
- Business logic validation fails (e.g., duplicate reaction, invalid invite token)

**Example**:
```json
{
  "detail": "Reaction already exists"
}
```

### 401 Unauthorized

Returned when:
- Missing or invalid JWT token
- Expired access token
- Malformed authentication header

**Example**:
```json
{
  "detail": "Invalid or expired token: Token has expired"
}
```

**Headers**:
- `WWW-Authenticate: Bearer` - Indicates Bearer token authentication required

### 403 Forbidden

Returned when:
- User lacks required role for operation
- User lacks required permission
- Access to resource in different family unit
- Operation not allowed for user's role

**Example**:
```json
{
  "detail": "Operation requires adult role"
}
```

### 404 Not Found

Returned when:
- Resource not found (memory, user, invite, etc.)
- Invalid resource ID format

**Example**:
```json
{
  "detail": "Memory not found"
}
```

### 409 Conflict

Returned when:
- Resource already exists (e.g., user with email already registered)
- Concurrent modification conflicts

**Example**:
```json
{
  "detail": "User with this email already exists"
}
```

### 422 Unprocessable Entity

Returned when:
- Request body structure is valid but data validation fails
- Pydantic validation errors

**Example**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error

Returned when:
- Unexpected server error
- Database connection failures
- External service failures

**Example**:
```json
{
  "detail": "Internal server error"
}
```

## Error Categories

### Authentication Errors

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Invalid token | Token is malformed or invalid |
| 401 | Expired token | Access token has expired |
| 401 | Missing token | Authorization header not provided |

### Authorization Errors

| Status | Error | Description |
|--------|-------|-------------|
| 403 | Insufficient role | User lacks required role |
| 403 | Permission denied | User lacks required permission |
| 403 | Family access denied | Resource belongs to different family |

### Validation Errors

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Invalid input | Request data validation failed |
| 400 | Missing required field | Required field not provided |
| 422 | Validation error | Pydantic validation failed |

### Resource Errors

| Status | Error | Description |
|--------|-------|-------------|
| 404 | Not found | Resource does not exist |
| 409 | Already exists | Resource already exists |
| 400 | Invalid state | Resource in invalid state for operation |

### Business Logic Errors

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Duplicate reaction | User already reacted with this emoji |
| 400 | Invalid invite | Invite token invalid or expired |
| 400 | Nesting depth exceeded | Comment nesting depth limit reached |

## Error Handling Best Practices

### Frontend

1. **Check status code first**: Handle errors by status code category
2. **Display user-friendly messages**: Map technical errors to user-friendly text
3. **Retry logic**: Implement retry for 500 errors with exponential backoff
4. **Token refresh**: Automatically refresh on 401 errors
5. **Validation feedback**: Show field-level errors for 422 responses

### Backend

1. **Consistent format**: Always use `{"detail": "message"}` structure
2. **Clear messages**: Provide actionable error messages
3. **Log errors**: Log all errors with context for debugging
4. **Don't expose internals**: Avoid exposing internal implementation details
5. **Security**: Don't leak sensitive information in error messages

## Example Error Handling

### JavaScript/TypeScript

```typescript
try {
  const response = await fetch('/api/v1/memories', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(memoryData)
  });

  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 401:
        // Refresh token or redirect to login
        await refreshToken();
        break;
      case 403:
        // Show permission denied message
        showError('You do not have permission to perform this action');
        break;
      case 404:
        // Show not found message
        showError('Resource not found');
        break;
      case 422:
        // Show validation errors
        showValidationErrors(error.detail);
        break;
      default:
        // Show generic error
        showError(error.detail || 'An error occurred');
    }
  }
} catch (error) {
  // Network or other errors
  showError('Network error. Please try again.');
}
```

### Python

```python
import httpx

try:
    response = httpx.post(
        "/api/v1/memories",
        json=memory_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    error_detail = e.response.json().get("detail", "Unknown error")
    
    if e.response.status_code == 401:
        # Handle authentication error
        refresh_token()
    elif e.response.status_code == 403:
        # Handle authorization error
        raise PermissionError(error_detail)
    elif e.response.status_code == 404:
        # Handle not found
        raise NotFoundError(error_detail)
    else:
        # Handle other errors
        raise APIError(error_detail)
```

## Error Response Examples

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 8}
    }
  ]
}
```

### Business Logic Error (400)

```json
{
  "detail": "Reaction already exists. Each user can have one reaction per emoji per memory."
}
```

### Permission Error (403)

```json
{
  "detail": "Operation requires adult role"
}
```

### Not Found Error (404)

```json
{
  "detail": "Memory not found or access denied"
}
```

## Error Codes Reference

For programmatic error handling, use HTTP status codes. The API does not use custom error codes beyond standard HTTP status codes.

## Monitoring and Logging

All errors are:
- Logged with structured logging including request ID, user ID, and error details
- Tracked in analytics metrics (`api_request_errors`)
- Monitored for patterns and trends

## Future Enhancements

- Custom error codes for specific business logic errors
- Error code enumeration for frontend mapping
- Retry-after headers for rate limiting
- Error correlation IDs for support requests

