"""
Pydantic validation schemas for frontend requests.
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator, EmailStr


class FrontendMemoryRequest(BaseModel):
    """Frontend memory creation/update request schema."""
    
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    memory_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)
    location: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    media: Optional[List[dict]] = Field(default_factory=list)
    
    @field_validator("memory_date")
    @classmethod
    def validate_memory_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate memory date format."""
        if v is None:
            return None
        
        # Should be YYYY-MM-DD format
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("memory_date must be in YYYY-MM-DD format")
        
        return v
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> List[str]:
        """Validate tags."""
        if v is None:
            return []
        
        # Filter out empty tags
        return [tag.strip() for tag in v if tag and tag.strip()]


class FrontendFeedFilters(BaseModel):
    """Frontend feed filter parameters."""
    
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    user_id: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated
    search_query: Optional[str] = Field(None, max_length=500)
    order_by: str = Field(default="feed_score", pattern="^(feed_score|created_at|memory_date)$")
    order_direction: str = Field(default="desc", pattern="^(asc|desc)$")
    memory_date_from: Optional[str] = None
    memory_date_to: Optional[str] = None


class FrontendAuthRequest(BaseModel):
    """Frontend authentication request schema."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)
    family_name: Optional[str] = Field(None, max_length=255)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email."""
        return v.lower().strip()


class FrontendInviteRequest(BaseModel):
    """Frontend invitation request schema."""
    
    email: EmailStr
    role: str = Field(..., pattern="^(adult|teen|child|grandparent)$")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email."""
        return v.lower().strip()


class FrontendCommentRequest(BaseModel):
    """Frontend comment creation request."""
    
    content: str = Field(..., min_length=1, max_length=5000)
    parent_comment_id: Optional[str] = None


class FrontendReactionRequest(BaseModel):
    """Frontend reaction creation request."""
    
    emoji: str = Field(..., min_length=1, max_length=10)
    
    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        """Validate emoji is in allowed list."""
        valid_emojis = ["👍", "❤️", "😂", "😮", "😢", "🎉", "🔥", "💯"]
        if v not in valid_emojis:
            raise ValueError(f"Emoji must be one of: {', '.join(valid_emojis)}")
        return v

