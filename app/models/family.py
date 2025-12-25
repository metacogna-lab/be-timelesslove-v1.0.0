"""
Family unit data models.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class FamilyUnit(BaseModel):
    """Family unit model from database."""
    
    id: UUID
    name: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

