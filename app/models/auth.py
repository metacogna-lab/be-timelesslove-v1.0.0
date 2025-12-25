"""
Authentication-related data models.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class AuthUser(BaseModel):
    """Supabase Auth user model."""
    
    id: UUID
    email: EmailStr
    email_confirmed_at: Optional[str] = None

