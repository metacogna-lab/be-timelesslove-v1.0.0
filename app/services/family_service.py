"""
Family unit service for family operations.
"""

from typing import Optional
from uuid import UUID
from supabase import Client
from app.db.supabase import get_supabase_service_client
from app.models.family import FamilyUnit


async def create_family_unit(
    created_by: UUID,
    name: Optional[str] = None
) -> FamilyUnit:
    """
    Create a new family unit.
    
    Args:
        created_by: User UUID who is creating the family
        name: Optional family name
    
    Returns:
        Created FamilyUnit
    """
    service_client = get_supabase_service_client()
    
    family_data = {
        "created_by": str(created_by),
        "name": name
    }
    
    result = service_client.table("family_units").insert(family_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create family unit")
    
    return FamilyUnit(**result.data[0])


async def get_family_unit(family_unit_id: UUID) -> Optional[FamilyUnit]:
    """
    Get family unit by ID.
    
    Args:
        family_unit_id: Family unit UUID
    
    Returns:
        FamilyUnit if found, None otherwise
    """
    service_client = get_supabase_service_client()
    
    result = service_client.table("family_units").select("*").eq(
        "id", str(family_unit_id)
    ).single().execute()
    
    if not result.data:
        return None
    
    return FamilyUnit(**result.data)

