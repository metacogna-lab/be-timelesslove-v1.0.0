"""
Invitation data models.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class Invite(BaseModel):
    """Invitation model from database."""
    
    id: UUID
    family_unit_id: UUID
    invited_by: UUID
    email: EmailStr
    role: str = Field(..., pattern="^(adult|teen|child|grandparent|pet)$")
    token: str
    status: str = Field(..., pattern="^(pending|accepted|expired|revoked)$")
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

