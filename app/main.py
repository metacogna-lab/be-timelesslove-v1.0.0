"""
FastAPI application entry point.
"""

import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import auth, invites, memories, storage, feed
from app.middleware.logging import StructuredLoggingMiddleware

# Load environment variables from .env file
dotenv.load_dotenv()

# Adapter layer integration
from adapters.api import auth_adapter, memories_adapter, feed_adapter, storage_adapter, invites_adapter

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

# Include backend routers (original API endpoints)
app.include_router(auth.router, prefix=f"/api/{settings.api_version}/auth", tags=["auth"])
app.include_router(invites.router, prefix=f"/api/{settings.api_version}/invites", tags=["invites"])
app.include_router(memories.router, prefix=f"/api/{settings.api_version}/memories", tags=["memories"])
app.include_router(storage.router, prefix=f"/api/{settings.api_version}/storage", tags=["storage"])
app.include_router(feed.router, prefix=f"/api/{settings.api_version}", tags=[])

# Include adapter routers (frontend-facing adapters with transformation layer)
app.include_router(auth_adapter, prefix=f"/adaptor/{settings.api_version}/auth", tags=["adaptor-auth"])
app.include_router(memories_adapter, prefix=f"/adaptor/{settings.api_version}/memories", tags=["adaptor-memories"])
app.include_router(feed_adapter, prefix=f"/adaptor/{settings.api_version}/feed", tags=["adaptor-feed"])
app.include_router(storage_adapter, prefix=f"/adaptor/{settings.api_version}/storage", tags=["adaptor-storage"])
app.include_router(invites_adapter, prefix=f"/adaptor/{settings.api_version}/invites", tags=["adaptor-invites"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Timeless Love API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

