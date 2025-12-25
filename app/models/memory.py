"""
Memory and media data models.
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID


class MemoryMedia(BaseModel):
    """Memory media model from database."""
    
    id: UUID
    memory_id: UUID
    storage_path: str
    storage_bucket: str = "memories"
    file_name: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_path: Optional[str] = None
    processing_status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Memory(BaseModel):
    """Memory model from database."""
    
    id: UUID
    user_id: UUID
    family_unit_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    memory_date: Optional[date] = None
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str = Field(..., pattern="^(draft|published|archived)$")
    created_at: datetime
    updated_at: datetime
    modified_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class MemoryWithMedia(Memory):
    """Memory model with associated media."""
    
    media: List[MemoryMedia] = Field(default_factory=list)

