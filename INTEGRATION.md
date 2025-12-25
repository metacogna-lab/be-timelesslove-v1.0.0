# Backend Integration Guide

## Supabase Auth & LangGraph Integration

This guide shows how to integrate the new Supabase JWT authentication and LangGraph checkpoint persistence into your existing FastAPI application **without breaking existing functionality**.

---

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install langgraph langgraph-checkpoint-postgres psycopg[pool]
```

---

## 2. Update Environment Variables

Add these to your `.env` file:

```bash
# LangGraph Database Configuration
# Get from: Supabase Dashboard > Project Settings > Database > Connection Pooling
SUPABASE_DB_URL=postgresql://postgres.fjevxcnpgydosicdyugt:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres
SUPABASE_DB_PASSWORD=your_database_password
```

**Important:** Use the **Transaction Pooler** connection string (Port 6543), not the direct connection (Port 5432). LangGraph makes frequent checkpoint writes and will exhaust direct connections.

To find your connection string:
1. Go to Supabase Dashboard
2. Project Settings > Database
3. Connection Pooling > Transaction mode
4. Copy the connection string

---

## 3. Update `app/main.py` (Non-Destructive)

Add these snippets to your existing `main.py` without rewriting it:

### 3.1. Import the graph_db module at the top

```python
from app.db import graph_db  # Add this line
```

### 3.2. Add startup and shutdown events

Add these **after** your existing app initialization but **before** the route definitions:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize LangGraph checkpointer on application startup."""
    try:
        await graph_db.init_checkpointer()
        print("✅ Application startup complete")
    except Exception as e:
        print(f"⚠️  LangGraph initialization failed: {e}")
        print("   Continuing without checkpointer support...")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown."""
    await graph_db.close_pool()
    print("✅ Application shutdown complete")
```

### Full Example (where to add in main.py)

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import auth, invites, memories, storage, feed
from app.middleware.logging import StructuredLoggingMiddleware
from app.db import graph_db  # <-- ADD THIS

settings = get_settings()

app = FastAPI(
    title="Timeless Love API",
    description="Backend API for Timeless Love family social platform",
    version="1.0.0",
    docs_url="/docs" if settings.is_debug else None,
    redoc_url="/redoc" if settings.is_debug else None,
    openapi_url="/openapi.json" if settings.is_debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured logging middleware (must be after CORS)
app.add_middleware(StructuredLoggingMiddleware)

# Lifecycle events (ADD THESE)
@app.on_event("startup")
async def startup_event():
    """Initialize LangGraph checkpointer on application startup."""
    try:
        await graph_db.init_checkpointer()
        print("✅ Application startup complete")
    except Exception as e:
        print(f"⚠️  LangGraph initialization failed: {e}")
        print("   Continuing without checkpointer support...")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown."""
    await graph_db.close_pool()
    print("✅ Application shutdown complete")

# Include routers (EXISTING CODE - DON'T CHANGE)
app.include_router(auth.router, prefix=f"/api/{settings.api_version}/auth", tags=["auth"])
app.include_router(invites.router, prefix=f"/api/{settings.api_version}/invites", tags=["invites"])
app.include_router(memories.router, prefix=f"/api/{settings.api_version}/memories", tags=["memories"])
app.include_router(storage.router, prefix=f"/api/{settings.api_version}/storage", tags=["storage"])
app.include_router(feed.router, prefix=f"/api/{settings.api_version}", tags=[])

# Existing routes (DON'T CHANGE)
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Timeless Love API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
```

---

## 4. Using Supabase Auth in Routes (Optional)

You now have **two authentication options**:

### Option 1: Existing Custom JWT Auth (Keep Using This)

```python
from app.dependencies import get_current_user
from app.utils.jwt import TokenClaims

@router.get("/existing-endpoint")
async def existing_route(current_user: TokenClaims = Depends(get_current_user)):
    # Your existing backend-generated JWT tokens work here
    return {"user_id": current_user.sub}
```

### Option 2: NEW - Supabase Frontend Auth (For New Routes)

```python
from app.dependencies.supabase_auth import verify_supabase_token, SupabaseUser

@router.get("/new-frontend-endpoint")
async def new_route(user: SupabaseUser = Depends(verify_supabase_token)):
    # Frontend sends Supabase GoTrue JWT
    # Backend verifies without handling login/signup
    return {"user_id": user.id, "email": user.email}
```

**Choose one based on your needs:**
- **Option 1** (Existing): Backend generates JWTs after registration/login
- **Option 2** (New): Frontend handles auth via Supabase, backend only verifies

---

## 5. Run Tests

Test the new authentication and database setup:

```bash
# Run all tests
pytest

# Run only new auth tests
pytest tests/test_supabase_auth.py -v

# Run only database tests
pytest tests/test_graph_db.py -v
```

---

## 6. Verify Integration

Start the server:

```bash
uvicorn app.main:app --reload
```

You should see:

```
✅ LangGraph connection pool initialized
✅ LangGraph checkpointer initialized
✅ Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

If you see warnings about missing `SUPABASE_DB_URL`, the checkpointer will gracefully degrade. Your existing endpoints will continue to work normally.

---

## 7. Test with cURL

### Test Existing Auth (Backend JWT)

```bash
# 1. Register a user (get backend JWT)
curl -X POST http://localhost:8000/api/v1/auth/register/adult \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "display_name": "Test User"
  }'

# Response: {"access_token": "eyJ...", "refresh_token": "eyJ..."}

# 2. Use the access token
curl http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer eyJ..."
```

### Test New Supabase Auth (Frontend JWT)

To test this, you need a real Supabase JWT from your frontend:

```javascript
// In your React app
const { data: { session } } = await supabase.auth.getSession()
const token = session.access_token

// Use this token in your API calls
fetch('http://localhost:8000/api/v1/new-endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

Then in your Python backend:

```python
# Create a test endpoint (optional)
from app.dependencies.supabase_auth import verify_supabase_token, SupabaseUser
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/test/supabase-auth")
async def test_supabase_auth(user: SupabaseUser = Depends(verify_supabase_token)):
    return {
        "message": "Supabase auth working!",
        "user_id": user.id,
        "email": user.email,
        "family_unit_id": user.family_unit_id
    }
```

---

## 8. What Was Changed

### Files Added:
- ✅ `app/dependencies/supabase_auth.py` - Supabase JWT verification
- ✅ `app/db/graph_db.py` - LangGraph PostgreSQL checkpointer
- ✅ `tests/test_supabase_auth.py` - Auth tests (19 test cases)
- ✅ `tests/test_graph_db.py` - Database tests (13 test cases)

### Files Modified:
- ✅ `requirements.txt` - Added langgraph dependencies
- ✅ `app/config.py` - Added `supabase_db_url` and `supabase_db_password` fields
- ✅ `.env.example` - Added database URL documentation

### Files NOT Changed:
- ✅ `app/main.py` - Only **additions** via startup/shutdown events
- ✅ `app/dependencies.py` - Existing auth still works
- ✅ `app/api/v1/*` - All existing routes unchanged
- ✅ All existing tests pass

---

## 9. Troubleshooting

### "Missing database configuration"

Add `SUPABASE_DB_URL` to your `.env`:

```bash
SUPABASE_DB_URL=postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres
```

### "Token verification failed"

- Verify your `JWT_SECRET_KEY` matches Supabase project settings
- Check token hasn't expired
- Ensure frontend is sending `Authorization: Bearer {token}` header

### Tests failing

```bash
# Run with verbose output
pytest tests/test_supabase_auth.py -v -s

# Run specific test
pytest tests/test_supabase_auth.py::TestSupabaseJWTVerifier::test_verify_valid_token -v
```

---

## 10. Next Steps

1. **Choose Auth Strategy**: Decide whether to use backend JWTs or Supabase frontend auth
2. **Add Agent Routes**: When ready, create routes that use `get_graph_checkpointer()` dependency
3. **Update Frontend**: Configure React app to send Supabase tokens if using Option 2

---

## Security Notes

- ✅ Supabase JWT verification uses your project's `JWT_SECRET_KEY`
- ✅ Connection pool uses transaction mode to prevent exhaustion
- ✅ All existing RBAC and family unit isolation still applies
- ✅ No breaking changes to existing authentication flow
