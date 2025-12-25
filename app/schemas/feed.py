"""
Feed interaction request/response schemas.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# Valid emoji list
VALID_EMOJIS = {
    "👍": "thumbs_up",
    "❤️": "heart",
    "😂": "laughing",
    "😮": "surprised",
    "😢": "sad",
    "🎉": "celebration",
    "🔥": "fire",
    "💯": "hundred"
}


class CreateReactionRequest(BaseModel):
    """Request schema for creating a reaction."""
    
    emoji: str = Field(..., min_length=1, max_length=10)
    
    @field_validator('emoji')
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        """Validate emoji is in allowed list."""
        if v not in VALID_EMOJIS:
            raise ValueError(f"Emoji must be one of: {', '.join(VALID_EMOJIS.keys())}")
        return v


class ReactionResponse(BaseModel):
    """Response schema for a reaction."""
    
    id: UUID
    memory_id: UUID
    user_id: UUID
    emoji: str
    created_at: str
    updated_at: str


class CreateCommentRequest(BaseModel):
    """Request schema for creating a comment."""
    
    content: str = Field(..., min_length=1, max_length=5000)
    parent_comment_id: Optional[UUID] = None
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty after trimming."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Comment content cannot be empty")
        if len(trimmed) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")
        return trimmed


class UpdateCommentRequest(BaseModel):
    """Request schema for updating a comment."""
    
    content: str = Field(..., min_length=1, max_length=5000)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty after trimming."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Comment content cannot be empty")
        if len(trimmed) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")
        return trimmed


class CommentResponse(BaseModel):
    """Response schema for a comment."""
    
    id: UUID
    memory_id: UUID
    user_id: UUID
    parent_comment_id: Optional[UUID] = None
    content: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None
    reply_count: int = 0
    replies: List['CommentResponse'] = Field(default_factory=list)


# Update forward reference
CommentResponse.model_rebuild()


class FeedFilterParams(BaseModel):
    """Query parameters for feed filtering."""
    
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    user_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    memory_date_from: Optional[datetime] = None
    memory_date_to: Optional[datetime] = None
    search_query: Optional[str] = None
    order_by: str = Field(default="feed_score", pattern="^(feed_score|created_at|memory_date)$")
    order_direction: str = Field(default="desc", pattern="^(asc|desc)$")


class FeedPaginationParams(BaseModel):
    """Pagination parameters for feed."""
    
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    cursor: Optional[str] = None  # For cursor-based pagination


class MemoryFeedItem(BaseModel):
    """A single memory item in the feed."""
    
    id: UUID
    user_id: UUID
    family_unit_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    memory_date: Optional[str] = None
    location: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str
    created_at: str
    updated_at: str
    media: List[dict] = Field(default_factory=list)
    reaction_count: int = 0
    comment_count: int = 0
    reactions_by_emoji: dict[str, int] = Field(default_factory=dict)
    user_reactions: List[str] = Field(default_factory=list)  # Emojis the current user reacted with
    top_comments: List[CommentResponse] = Field(default_factory=list)  # Top-level comments only
    feed_score: float = 0.0


class FeedResponse(BaseModel):
    """Response schema for paginated feed."""
    
    items: List[MemoryFeedItem]
    pagination: dict
    total_count: Optional[int] = None
    has_more: bool

