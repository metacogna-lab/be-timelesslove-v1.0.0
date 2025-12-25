# Authentication API Documentation

## Overview

The Authentication API provides endpoints for user registration, login, token management, and account provisioning. All endpoints return JSON responses and follow RESTful conventions.

**Base URL**: `/api/v1/auth`

## Authentication

Most endpoints require authentication via JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

## Endpoints

### Register Adult

**POST** `/api/v1/auth/register/adult`

Register a new adult user. Creates a new family unit if this is the first user.

**Request Body**:
```json
{
  "email": "adult@example.com",
  "password": "SecurePass123!",
  "display_name": "John Doe",
  "family_name": "The Doe Family"
}
```

**Response** (201 Created):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "adult@example.com",
  "role": "adult",
  "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input, email already exists
- `500 Internal Server Error`: Server error

---

### Register Teenager

**POST** `/api/v1/auth/register/teen`

Register a new teenager user. Creates a new family unit if this is the first user.

**Request Body**: Same as Register Adult

**Response**: Same format as Register Adult with `role: "teen"`

---

### Register Grandparent

**POST** `/api/v1/auth/register/grandparent`

Register a new grandparent user. Creates a new family unit if this is the first user.

**Request Body**: Same as Register Adult

**Response**: Same format as Register Adult with `role: "grandparent"`

---

### Register Child (via Invitation)

**POST** `/api/v1/auth/register/child?invite_token=<token>`

Register a child user via invitation token.

**Query Parameters**:
- `invite_token` (required): Invitation token

**Request Body**:
```json
{
  "email": "child@example.com",
  "password": "SecurePass123!",
  "display_name": "Jane Doe"
}
```

**Response**: Same format as Register Adult with `role: "child"`

**Error Responses**:
- `400 Bad Request`: Invalid or expired invitation token
- `400 Bad Request`: Invitation is not for a child account

---

### Provision Child Account

**POST** `/api/v1/auth/provision/child`

Provision a child account (Adult only). Generates username and password.

**Authentication**: Required (Adult role)

**Request Body**:
```json
{
  "display_name": "Little Doe",
  "email": "child@example.com"
}
```

**Response** (201 Created):
```json
{
  "user_id": "770e8400-e29b-41d4-a716-446655440000",
  "username": "child_abc123",
  "password": "Xy9$kL2mN4pQ6rS",
  "display_name": "Little Doe",
  "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Credentials provided. Store securely. Password cannot be retrieved."
}
```

**Error Responses**:
- `403 Forbidden`: Only adults can provision child accounts
- `400 Bad Request`: Invalid input

---

### Register Pet Profile

**POST** `/api/v1/auth/register/pet`

Create a pet profile (Adult only). Pet profiles are read-only and don't require authentication.

**Authentication**: Required (Adult role)

**Request Body**:
```json
{
  "display_name": "Fluffy",
  "avatar_url": "https://example.com/pet-avatar.jpg"
}
```

**Response** (201 Created):
```json
{
  "pet_id": "880e8400-e29b-41d4-a716-446655440000",
  "display_name": "Fluffy",
  "family_unit_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Pet profile created. Email notification simulated."
}
```

**Error Responses**:
- `403 Forbidden`: Only adults can create pet profiles

---

### Login

**POST** `/api/v1/auth/login`

Authenticate with email and password. Returns access and refresh tokens.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid email or password
- `404 Not Found`: User profile not found

---

### Refresh Token

**POST** `/api/v1/auth/refresh`

Refresh access token using refresh token. Implements token rotation.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token

---

## Invitation Endpoints

### Create Invitation

**POST** `/api/v1/invites`

Create a new invitation (Adult only).

**Authentication**: Required (Adult role)

**Request Body**:
```json
{
  "email": "invitee@example.com",
  "role": "teen"
}
```

**Response** (201 Created):
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "email": "invitee@example.com",
  "role": "teen",
  "token": "abc123xyz789...",
  "invite_link": "http://localhost:5173/accept-invite?token=abc123xyz789...",
  "expires_at": "2024-01-15T12:00:00Z",
  "status": "pending",
  "created_at": "2024-01-08T12:00:00Z"
}
```

**Error Responses**:
- `403 Forbidden`: Only adults can create invitations
- `400 Bad Request`: User with email already exists

---

### Validate Invitation

**GET** `/api/v1/invites/{token}`

Validate an invitation token.

**Path Parameters**:
- `token` (required): Invitation token

**Response** (200 OK):
```json
{
  "valid": true,
  "invite": {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "email": "invitee@example.com",
    "role": "teen",
    "token": "abc123xyz789...",
    "invite_link": "",
    "expires_at": "2024-01-15T12:00:00Z",
    "status": "pending",
    "created_at": "2024-01-08T12:00:00Z"
  }
}
```

**Error Response** (200 OK with valid=false):
```json
{
  "valid": false,
  "message": "Invitation has expired"
}
```

---

### Accept Invitation

**POST** `/api/v1/invites/{token}/accept`

Accept an invitation and create user account.

**Path Parameters**:
- `token` (required): Invitation token

**Request Body**:
```json
{
  "email": "invitee@example.com",
  "password": "SecurePass123!",
  "display_name": "Invited User"
}
```

**Response** (200 OK):
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "email": "invitee@example.com",
  "role": "teen",
  "token": "abc123xyz789...",
  "invite_link": "",
  "expires_at": "2024-01-15T12:00:00Z",
  "status": "accepted",
  "created_at": "2024-01-08T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid or expired invitation
- `400 Bad Request`: Email does not match invitation

---

## Error Codes

### Standard HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
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

## Request/Response Examples

### Complete Registration Flow

1. **Register Adult**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/adult \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "SecurePass123!",
    "display_name": "Parent User",
    "family_name": "The Example Family"
  }'
```

2. **Login**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "SecurePass123!"
  }'
```

3. **Create Invitation** (with access token):
```bash
curl -X POST http://localhost:8000/api/v1/invites \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "email": "teen@example.com",
    "role": "teen"
  }'
```

4. **Accept Invitation**:
```bash
curl -X POST "http://localhost:8000/api/v1/invites/{token}/accept" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teen@example.com",
    "password": "SecurePass123!",
    "display_name": "Teen User"
  }'
```

---

## Security Considerations

1. **Password Requirements**:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one digit

2. **Token Security**:
   - Access tokens expire in 15 minutes
   - Refresh tokens expire in 7 days
   - Tokens are rotated on refresh
   - Store tokens securely (not in localStorage)

3. **Rate Limiting**:
   - Login and registration endpoints should be rate-limited (future implementation)

4. **HTTPS**:
   - All endpoints must be accessed over HTTPS in production

---

## OpenAPI Specification

See `docs/api/openapi.yaml` for complete OpenAPI 3.0 specification.

