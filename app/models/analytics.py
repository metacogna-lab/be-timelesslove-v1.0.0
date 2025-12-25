"""
Analytics event and metric models.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class AnalyticsEvent(BaseModel):
    """Analytics event model from database."""
    
    id: UUID
    event_id: UUID
    event_type: str
    timestamp: datetime
    user_id: UUID
    family_unit_id: UUID
    session_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalyticsMetric(BaseModel):
    """Analytics metric model from database."""
    
    id: UUID
    metric_name: str
    metric_type: str = Field(..., pattern="^(count|gauge|histogram|timer)$")
    value: float
    labels: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventMetadata(BaseModel):
    """Base class for event metadata."""
    pass

