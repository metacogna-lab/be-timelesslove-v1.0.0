---
title: Getting Started
description: Quick start guide for Timeless Love backend development
sidebar:
  order: 1
---

# Getting Started

Welcome to the Timeless Love backend! This guide will help you set up your development environment and make your first API call.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Supabase account and project
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd timelesslove-alpha/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

### 2. Required Environment Variables

Edit `.env` with your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-minimum-32-bytes
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Configuration
ENVIRONMENT=development
DEBUG=true
API_VERSION=v1

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Supabase Setup

Ensure your Supabase project has:
- Database migrations applied (see `db/migrations/`)
- Storage bucket `memories` created
- Row Level Security (RLS) policies enabled

See [Supabase Setup Guide](../supabase/README.md) for detailed instructions.

## Running the Server

### Development Mode

```bash
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000` with auto-reload enabled.

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## First API Call

### 1. Register a User

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

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "parent@example.com",
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

### 2. Use the Access Token

```bash
# Store the access token
export ACCESS_TOKEN="your-access-token-here"

# Get your profile
curl -X GET http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API route handlers
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic
│   ├── utils/           # Utilities (JWT, security)
│   ├── db/              # Database clients
│   └── main.py          # FastAPI application
├── docs/                # Documentation
├── tests/               # Test files
├── db/migrations/       # Database migrations
└── requirements.txt    # Python dependencies
```

## Next Steps

- Read the [Architecture Overview](./architecture/overview.md) to understand the system design
- Explore [Authentication](./features/authentication.md) for JWT and role-based access
- Check out [API Reference](../api/AUTH_API.md) for detailed endpoint documentation
- Review [Development Guidelines](./development/contributing.md) for contributing

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Database Connection Errors**
- Check Supabase credentials in `.env`
- Verify Supabase project is active
- Ensure migrations are applied

**JWT Errors**
- Verify `JWT_SECRET_KEY` is set and at least 32 bytes
- Check token expiration settings

**CORS Errors**
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Restart the server after changing CORS settings

## Getting Help

- Check the [API Documentation](../api/)
- Review [Security Policies](../security/RBAC_POLICY.md)
- See [Supabase Configuration](../supabase/PROJECT_CONFIG.md)

