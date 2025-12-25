"""
Pydantic schemas for invitation requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID


class CreateInviteRequest(BaseModel):
    """Create invitation request schema."""

    email: EmailStr
    role: str = Field(..., pattern="^(adult|teen|child|grandparent)$", description="Role must be one of: adult, teen, child, grandparent")


class InviteResponse(BaseModel):
    """Invitation response schema."""
    
    id: UUID
    email: EmailStr
    role: str
    token: str
    invite_link: str
    expires_at: datetime
    status: str
    created_at: datetime


class ValidateInviteResponse(BaseModel):
    """Invite validation response schema."""
    
    valid: bool
    invite: Optional[InviteResponse] = None
    message: Optional[str] = None


class AcceptInviteRequest(BaseModel):
    """Accept invitation request schema."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)

