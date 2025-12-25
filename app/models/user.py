"""
User profile data models.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class UserProfile(BaseModel):
    """User profile model from database."""
    
    id: UUID
    family_unit_id: UUID
    role: str = Field(..., pattern="^(adult|teen|child|grandparent|pet)$")
    display_name: str
    avatar_url: Optional[str] = None
    preferences: dict = Field(default_factory=dict)
    is_family_creator: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Type alias for current user in API endpoints
# CurrentUser is compatible with TokenClaims but uses UUID for user_id
from app.utils.jwt import TokenClaims

class CurrentUser(BaseModel):
    """Current authenticated user model for API endpoints."""
    
    user_id: UUID  # Alias for sub
    family_unit_id: UUID
    role: str
    email: Optional[str] = None
    
    @classmethod
    def from_token_claims(cls, claims: TokenClaims, email: Optional[str] = None) -> "CurrentUser":
        """Create CurrentUser from TokenClaims."""
        return cls(
            user_id=UUID(claims.sub),
            family_unit_id=UUID(claims.family_unit_id),
            role=claims.role,
            email=email
        )

