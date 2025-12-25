"""
Pydantic schemas for memory requests and responses.
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class MediaReference(BaseModel):
    """Media reference for memory creation."""
    
    storage_path: str
    file_name: str
    mime_type: str
    file_size: int  # Bytes
    
    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size."""
        from app.config import get_settings
        settings = get_settings()
        max_size = settings.media_max_file_size_mb * 1024 * 1024
        if v > max_size:
            raise ValueError(f"File size exceeds maximum of {settings.media_max_file_size_mb}MB")
        if v <= 0:
            raise ValueError("File size must be positive")
        return v


class CreateMemoryRequest(BaseModel):
    """Create memory request schema."""
    
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    memory_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    tags: List[str] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    media: List[MediaReference] = Field(default_factory=list)
    
    @field_validator("media")
    @classmethod
    def validate_media_size(cls, v: List[MediaReference]) -> List[MediaReference]:
        """Validate total media size."""
        from app.config import get_settings
        settings = get_settings()
        max_total_size = settings.media_max_memory_size_mb * 1024 * 1024
        total_size = sum(m.file_size for m in v)
        if total_size > max_total_size:
            raise ValueError(
                f"Total media size exceeds maximum of {settings.media_max_memory_size_mb}MB"
            )
        return v


class UpdateMemoryRequest(BaseModel):
    """Update memory request schema."""
    
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    memory_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")


class MemoryResponse(BaseModel):
    """Memory response schema."""
    
    id: UUID
    user_id: UUID
    family_unit_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    memory_date: Optional[date] = None
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str
    created_at: str
    updated_at: str
    modified_by: Optional[UUID] = None
    media: List[dict] = Field(default_factory=list)


class MediaResponse(BaseModel):
    """Media response schema."""
    
    id: UUID
    memory_id: UUID
    storage_path: str
    storage_bucket: str
    file_name: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_path: Optional[str] = None
    processing_status: str
    created_at: str
    updated_at: str


class AddMediaRequest(BaseModel):
    """Add media to memory request schema."""
    
    storage_path: str
    file_name: str
    mime_type: str
    file_size: int
    
    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size."""
        from app.config import get_settings
        settings = get_settings()
        max_size = settings.media_max_file_size_mb * 1024 * 1024
        if v > max_size:
            raise ValueError(f"File size exceeds maximum of {settings.media_max_file_size_mb}MB")
        if v <= 0:
            raise ValueError("File size must be positive")
        return v


class UploadUrlRequest(BaseModel):
    """Request for upload URL generation."""
    
    memory_id: UUID
    file_name: str
    mime_type: str


class UploadUrlResponse(BaseModel):
    """Response with upload URL."""
    
    upload_url: str
    storage_path: str
    expires_in: int


class AccessUrlResponse(BaseModel):
    """Response with access URL."""
    
    access_url: str
    expires_in: int

