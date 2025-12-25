# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the backend API for Timeless Love, a family social platform built with FastAPI and Supabase. The system supports multiple user roles (Adult, Teen, Child, Grandparent, Pet) with strict role-based access control and family unit management.

**Python Version**: Requires Python 3.13 (specified in `pyproject.toml`)

## Development Commands

Always use `bun` as the package manager (per user's global instructions), but note this is a Python project.

### Running the Application

**IMPORTANT**: Always run from the `backend/` directory and use the virtual environment.

```bash
# Activate virtual environment first
source venv/bin/activate

# Start development server with auto-reload
uvicorn app.main:app --reload

# Start on specific port
uvicorn app.main:app --reload --port 8000

# Production server (4 workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Common Issues**:
- If you get `ModuleNotFoundError: No module named 'app'`:
  1. Ensure you're in the `backend/` directory: `pwd` should show `.../backend`
  2. Activate the virtual environment: `source venv/bin/activate`
  3. Kill any stale uvicorn processes: `pkill -f uvicorn`
  4. Run uvicorn again from the backend directory

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run tests with coverage
pytest --cov=app tests/

# Run specific test class or function
pytest tests/test_auth.py::TestRegistration::test_register_adult -v
```

### Database Setup

```bash
# Apply all migrations and setup Supabase
python3 scripts/setup_complete.sh

# Check Supabase readiness
./scripts/check_supabase_readiness.sh

# Apply migrations manually
./scripts/apply_migrations_and_bucket.sh

# Verify Supabase setup
python3 scripts/verify_supabase.py

# Populate test data
python3 scripts/populate_test_data.py
```

### Configuration & Utilities

```bash
# Generate/update Supabase configuration
python3 scripts/supabase_config.py

# Generate OpenAPI schema
python3 scripts/generate_openapi.py

# Validate authentication configuration
./scripts/validate_auth_config.py

# Test auth integration end-to-end
./scripts/test_auth_integration.sh
```

## Architecture

### Core Principles (from AGENTS.md)

Backend agents must prioritize:
- **Data integrity over convenience** - Strict validation at every boundary
- **Security and role enforcement** - RBAC on every endpoint
- **Observable, traceable behavior** - Structured logging with context
- **Clear API contracts** - Versioned, documented, predictable responses
- **Future readiness** - Emit structured events for analytics/intelligence systems

### Project Structure

```
app/
├── api/v1/              # API route handlers (auth, invites, memories, storage, feed)
├── models/              # Database models and Pydantic schemas
├── schemas/             # Request/response validation schemas
├── services/            # Business logic layer
├── utils/               # Utilities (JWT, security, media processing)
├── db/                  # Database clients (Supabase, LangGraph)
├── middleware/          # Custom middleware (logging)
├── dependencies/        # FastAPI dependency injection
├── workers/             # Background task workers
├── config.py            # Configuration from environment variables
├── dependencies.py      # Core dependencies (auth, database)
└── main.py              # FastAPI application entry point

adapters/                # Adapter layer for frontend-backend integration
├── api/                 # API endpoint adapters (auth, memories, feed, storage, invites)
├── transformers/        # Request/response transformation
├── validators/          # Pydantic validation schemas
├── middleware/          # Logging and sanitization
├── client.py            # HTTP client for backend communication
└── config.py            # Adapter configuration

db/migrations/           # SQL migration files (numbered)
scripts/                 # Automation scripts
tests/                   # Pytest test files
docs/                    # Documentation
```

### Authentication & Authorization

**JWT Token System:**
- Access tokens: 15-minute expiry (for API requests)
- Refresh tokens: 7-day expiry (for token renewal)
- Custom JWT implementation using python-jose
- Token claims include: `sub` (user_id), `role`, `family_unit_id`, `type` (access/refresh)

**Two Authentication Options:**
1. **Backend JWT** (existing) - Backend generates tokens after registration/login
2. **Supabase JWT** (new) - Frontend handles auth via Supabase, backend only verifies

**Dependencies:**
- `get_current_user()` - Returns `TokenClaims` from Bearer token (backend JWT)
- `get_current_user_model()` - Returns `CurrentUser` model (UUID-based)
- `verify_supabase_token()` - Verifies Supabase frontend tokens (new)
- `get_db()` - Supabase client (respects RLS)
- `get_service_db()` - Supabase service client (bypasses RLS)

**RBAC Utilities** (`app/services/rbac.py`):
- `@require_role(*roles)` - Enforce specific roles
- `@require_adult` - Adult-only endpoints
- `@require_family_member` - Validate same family unit
- Helper functions: `can_manage_family()`, `can_invite_members()`, `can_provision_children()`, `can_create_pets()`, `can_delete_content()`, `can_edit_content()`

### Service Layer Pattern

All business logic lives in `app/services/`. API endpoints are thin wrappers that:
1. Validate input (via Pydantic schemas)
2. Extract authenticated user (via dependencies)
3. Call service layer functions
4. Return standardized responses

**Key Services:**
- `auth_service.py` - Token generation/validation
- `user_service.py` - User profile CRUD
- `family_service.py` - Family unit management
- `invite_service.py` - Invitation system with expiring tokens
- `memory_service.py` - Memory/post creation and management
- `feed_service.py` - Feed generation and filtering
- `reaction_service.py` - Likes/reactions on memories
- `comment_service.py` - Comments on memories
- `storage_service.py` - Supabase storage integration
- `media_processor.py` - Image/video processing (thumbnails, metadata)
- `analytics_service.py` - Usage metrics and event tracking
- `rbac.py` - Role-based access control utilities

### Database Architecture

**Supabase Integration:**
- PostgreSQL database with Row Level Security (RLS)
- Migrations in `db/migrations/` (numbered SQL files)
- Two client types:
  - Regular client: Respects RLS for user-scoped queries
  - Service client: Bypasses RLS for admin operations

**Key Tables:**
- `user_profiles` - User identity, roles, family membership
- `family_units` - Family groupings
- `invitations` - Invitation tokens with expiry
- `memories` - Posts/memories with media
- `reactions` - Likes on memories
- `comments` - Comments on memories
- `analytics_events` - Event tracking for intelligence layer

**LangGraph Integration:**
- Checkpoint persistence for conversational AI flows
- PostgreSQL connection pooling (Transaction mode, Port 6543)
- Automatic initialization via startup events in `app/main.py`
- Access via `get_graph_checkpointer()` dependency
- See `INTEGRATION.md` for detailed setup instructions

### Role-Based Access Control

**Roles:** adult, teen, child, grandparent, pet

**Permission Matrix:**
- **Adults:** Full family management, can provision children, delete any content
- **Grandparents:** Invite members, create pets, delete own content
- **Teens:** Create content, delete own content, manage own profile
- **Children:** Create content (with restrictions), edit own content only
- **Pets:** Profile-only, no content creation/editing

**Family Unit Isolation:**
- All resources scoped to `family_unit_id`
- Every authenticated endpoint validates family membership
- RLS policies enforce database-level isolation

### API Versioning

All endpoints under `/api/v1/` prefix. Version configured in `app/config.py` via `API_VERSION` env var.

**Endpoint Groups:**
- `/api/v1/auth` - Registration, login, token refresh
- `/api/v1/invites` - Family invitations
- `/api/v1/memories` - Memory CRUD and interactions
- `/api/v1/storage` - File uploads and signed URLs
- `/api/v1/feed` - Personalized feed

### Adapter Layer

The adapter layer (`adapters/`) provides a clean, validated interface between the React frontend and FastAPI backend. It handles request/response transformation, data validation, error translation, and structured logging.

**Adapter Endpoints** (mounted at `/adaptor/v1/`):
- `/adaptor/v1/auth` - Authentication adapters with transformation
- `/adaptor/v1/memories` - Memory CRUD adapters
- `/adaptor/v1/feed` - Feed and interaction adapters
- `/adaptor/v1/storage` - Storage URL adapters
- `/adaptor/v1/invites` - Invitation adapters

**Key Features:**
- Request/response transformation (date normalization, field mapping)
- Pydantic validation for all requests
- Error translation to frontend-consumable format
- Input/output sanitization
- Structured logging for all operations
- Token passthrough (Supabase JWT tokens)

**Usage:**
- Frontend should use adapter endpoints (`/adaptor/v1/*`) for validated, transformed requests
- Original backend endpoints (`/api/v1/*`) remain available for direct access
- Adapter automatically calls backend endpoints and transforms responses

See `adapters/Adapter Integration.md` for detailed documentation.

### Configuration Management

Settings loaded via Pydantic from `.env` file (see `.env.example`):

**Required:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Public anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (for admin operations)
- `JWT_SECRET_KEY` - Minimum 32 bytes for token signing

**Optional:**
- `JWT_ALGORITHM` - Default: HS256
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Default: 15
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Default: 7
- `ENVIRONMENT` - development/staging/production
- `DEBUG` - true/false (controls OpenAPI docs visibility)
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `SUPABASE_DB_URL` - Transaction pooler URL for LangGraph (Port 6543)
- `SUPABASE_DB_PASSWORD` - Database password for LangGraph

**Media Processing Configuration:**
- `MEDIA_MAX_FILE_SIZE_MB` - Default: 50
- `MEDIA_MAX_MEMORY_SIZE_MB` - Default: 200
- `MEDIA_THUMBNAIL_SIZE` - Default: 400
- `MEDIA_UPLOAD_URL_EXPIRES_SECONDS` - Default: 300 (5 minutes)
- `MEDIA_ACCESS_URL_EXPIRES_SECONDS` - Default: 3600 (1 hour)

**Production Configuration:**
- Copy `.env.production.example` to `.env.production` for production deployments
- Set `DEBUG=false` to disable API documentation endpoints in production
- Update `CORS_ORIGINS` to include only your actual frontend domains
- Use Transaction Pooler (Port 6543) for `SUPABASE_DB_URL` in production

### Testing Strategy

**Test Files:**
- `test_auth.py` - Registration, login, token management
- `test_rbac.py` - Role-based access control enforcement
- `test_invites.py` - Invitation flow
- `test_memories.py` - Memory creation and interactions
- `test_feed.py` - Feed generation logic
- `test_storage.py` - File upload and storage
- `test_contracts.py` - API contract validation
- `test_supabase_auth.py` - Supabase JWT verification (19 test cases)
- `test_graph_db.py` - LangGraph database integration (13 test cases)

**Fixtures** (in `conftest.py`):
- `client` - TestClient for API calls
- `mock_settings` - Test configuration
- `mock_supabase_client` - Mocked Supabase client
- `sample_access_token` - Valid JWT for testing
- `sample_refresh_token` - Valid refresh token

**Running Tests:**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_auth.py -v

# Specific test class/function
pytest tests/test_auth.py::TestRegistration::test_register_adult -v

# With coverage
pytest --cov=app tests/
```

### Middleware

**StructuredLoggingMiddleware** (`app/middleware/logging.py`):
- Logs every request with context (request_id, user_id, method, path, duration)
- Enables tracing and debugging
- Required for observability

### Event Emission

Services emit structured events for analytics/intelligence:
- User lifecycle events (created, updated)
- Memory events (created, liked, commented)
- Family events (member joined, invited)

Events stored in `analytics_events` table for future ML/analytics processing.

## Development Guidelines

1. **Never bypass security checks** - All endpoints must validate authentication and family membership
2. **Use service layer** - Keep API endpoints thin, logic in services
3. **Validate at boundaries** - Use Pydantic schemas for all input/output
4. **Log with context** - Include request_id, user_id, relevant IDs
5. **Maintain API contracts** - Breaking changes require new API version
6. **Test RBAC rigorously** - Every role combination must be tested
7. **Emit events** - Important state changes should emit analytics events
8. **Document decisions** - Update AGENTS.md for behavioral changes

### Adapter Development Guidelines

When working with the adapter layer:

1. **Use adapter endpoints for frontend** - Frontend should use `/adaptor/v1/*` endpoints for validated, transformed requests
2. **Maintain transformation logic** - Update transformers when backend API changes
3. **Validate all inputs** - Adapter validates before calling backend, but backend also validates (double validation for security)
4. **Translate errors** - All backend errors must be translated to frontend format via `ErrorTransformer`
5. **Log all operations** - Adapter logs all requests, responses, and errors with structured data
6. **Sanitize data** - All inputs and outputs are sanitized to prevent injection
7. **Don't leak backend details** - Adapter must not expose backend implementation details to frontend
8. **Version adapters** - Adapter versioning follows API versioning (`/adaptor/v1/`, `/adaptor/v2/`, etc.)
9. **Test transformations** - All request/response transformations must be tested
10. **Update documentation** - Keep `Adapter Integration.md` up to date with endpoint mappings

## Production Deployment

The codebase is designed to be production-ready with:
- Structured logging for observability
- Role-based access control enforcement
- Token rotation for security
- Media processing with size limits
- CORS configuration
- Health check endpoints (`/health`)
- API documentation (`/docs`, `/redoc` - only in debug mode)

**Deployment Options:**
- AWS Lightsail (see `AWS_LIGHTSAIL_DEPLOYMENT.md`)
- Railway, Render, Fly.io
- Docker + Docker Compose (see `Dockerfile.production`, `docker-compose.production.yml`)

**Deployment Checklist:**
1. Copy `.env.production.example` to `.env.production` and configure all variables
2. Set `DEBUG=false` and `ENVIRONMENT=production`
3. Update `CORS_ORIGINS` with your actual frontend domains
4. Use Transaction Pooler (Port 6543) for `SUPABASE_DB_URL`
5. Generate strong `JWT_SECRET_KEY` (minimum 32 bytes)
6. Apply all database migrations via `scripts/setup_complete.sh`
7. Verify Supabase setup with `scripts/verify_supabase.py`
8. Test health endpoint: `curl https://your-domain.com/health`

## Frontend Integration

API serves a React Vite frontend with:
- CORS-ready endpoints (configure in `CORS_ORIGINS`)
- JSON responses with consistent error format
- Bearer token authentication (JWT in Authorization header)
- OpenAPI schema for client generation

### Adapter Layer Integration

The adapter layer provides a clean interface for frontend integration:

**Recommended Approach:**
- Frontend should use adapter endpoints (`/adaptor/v1/*`) for all API calls
- Adapter handles request transformation, validation, and error translation
- Adapter maintains backward compatibility with backend API contracts

**Adapter Benefits:**
- Consistent error format across all endpoints
- Automatic data validation and normalization
- Input/output sanitization
- Structured logging for debugging
- Versioned API support

**Configuration:**
- Adapter uses `BACKEND_API_BASE_URL` environment variable (defaults to `http://localhost:8000`)
- Adapter version matches API version (`/adaptor/v1/` for API v1)
- All adapter operations are logged with request IDs for tracing

See `adapters/Adapter Integration.md` for complete integration guide, endpoint mappings, and examples.

## Key Documentation Files

- `README.md` - Quick start guide
- `AGENTS.md` - Backend agent behavior principles
- `INTEGRATION.md` - Supabase Auth and LangGraph integration
- `AWS_LIGHTSAIL_DEPLOYMENT.md` - AWS deployment guide
- `adapters/Adapter Integration.md` - Adapter layer documentation
- `scripts/README.md` - Automation scripts documentation
- `.env.example` - Development environment template
- `.env.production.example` - Production environment template
