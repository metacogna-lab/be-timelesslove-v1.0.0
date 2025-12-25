"""
Feed interaction models (reactions and comments).
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class MemoryReaction(BaseModel):
    """Memory reaction model from database."""
    
    id: UUID
    memory_id: UUID
    user_id: UUID
    emoji: str = Field(..., min_length=1, max_length=10)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MemoryComment(BaseModel):
    """Memory comment model from database."""
    
    id: UUID
    memory_id: UUID
    user_id: UUID
    parent_comment_id: Optional[UUID] = None
    content: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommentWithReplies(MemoryComment):
    """Comment model with nested replies."""
    
    replies: List['CommentWithReplies'] = Field(default_factory=list)
    reply_count: int = 0


# Update forward reference
CommentWithReplies.model_rebuild()


class MemoryEngagement(BaseModel):
    """Engagement metrics for a memory."""
    
    memory_id: UUID
    reaction_count: int = 0
    comment_count: int = 0
    unique_reactors: int = 0
    reactions_by_emoji: dict[str, int] = Field(default_factory=dict)
    feed_score: float = 0.0

