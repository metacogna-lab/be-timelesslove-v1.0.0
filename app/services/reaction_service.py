"""
Service for managing memory reactions.
"""

from uuid import UUID
from typing import List, Dict
from datetime import datetime
from app.db.supabase import get_supabase_admin
from app.models.feed import MemoryReaction
from app.schemas.feed import CreateReactionRequest


class ReactionService:
    """Service for memory reaction operations."""

    def __init__(self):
        self.supabase = get_supabase_admin()
    
    async def create_reaction(
        self,
        memory_id: UUID,
        user_id: UUID,
        family_unit_id: UUID,
        request: CreateReactionRequest
    ) -> MemoryReaction:
        """
        Create a reaction to a memory.
        
        Args:
            memory_id: The memory ID
            user_id: The user ID creating the reaction
            family_unit_id: The user's family unit ID (for validation)
            request: Reaction creation request
            
        Returns:
            Created reaction
            
        Raises:
            ValueError: If memory not found or not in family
            ValueError: If reaction already exists
        """
        # Verify memory exists and is in user's family
        memory = await self.memory_service.get_memory(memory_id, family_unit_id)
        if not memory:
            raise ValueError("Memory not found or access denied")
        
        # Check if reaction already exists
        existing = self.supabase.table("memory_reactions").select("*").eq(
            "memory_id", str(memory_id)
        ).eq("user_id", str(user_id)).eq("emoji", request.emoji).execute()
        
        if existing.data:
            raise ValueError("Reaction already exists")
        
        # Create reaction
        result = self.supabase.table("memory_reactions").insert({
            "memory_id": str(memory_id),
            "user_id": str(user_id),
            "emoji": request.emoji
        }).execute()
        
        if not result.data:
            raise ValueError("Failed to create reaction")
        
        return MemoryReaction(**result.data[0])
    
    async def delete_reaction(
        self,
        reaction_id: UUID,
        user_id: UUID,
        family_unit_id: UUID
    ) -> None:
        """
        Delete a reaction.
        
        Args:
            reaction_id: The reaction ID
            user_id: The user ID (must own the reaction)
            family_unit_id: The user's family unit ID (for validation)
            
        Raises:
            ValueError: If reaction not found or user doesn't own it
        """
        # Verify reaction exists and user owns it
        result = self.supabase.table("memory_reactions").select("*").eq(
            "id", str(reaction_id)
        ).eq("user_id", str(user_id)).execute()
        
        if not result.data:
            raise ValueError("Reaction not found or access denied")
        
        # Delete reaction
        self.supabase.table("memory_reactions").delete().eq(
            "id", str(reaction_id)
        ).execute()
    
    async def get_reactions_for_memory(
        self,
        memory_id: UUID,
        family_unit_id: UUID
    ) -> List[MemoryReaction]:
        """
        Get all reactions for a memory.
        
        Args:
            memory_id: The memory ID
            family_unit_id: The user's family unit ID (for validation)
            
        Returns:
            List of reactions
        """
        # Verify memory is in family
        memory = await self.memory_service.get_memory(memory_id, family_unit_id)
        if not memory:
            raise ValueError("Memory not found or access denied")
        
        result = self.supabase.table("memory_reactions").select("*").eq(
            "memory_id", str(memory_id)
        ).order("created_at", desc=False).execute()
        
        return [MemoryReaction(**item) for item in result.data]
    
    async def get_reactions_by_emoji(
        self,
        memory_id: UUID,
        family_unit_id: UUID
    ) -> Dict[str, int]:
        """
        Get reaction counts grouped by emoji.
        
        Args:
            memory_id: The memory ID
            family_unit_id: The user's family unit ID (for validation)
            
        Returns:
            Dictionary mapping emoji to count
        """
        reactions = await self.get_reactions_for_memory(memory_id, family_unit_id)
        
        counts: Dict[str, int] = {}
        for reaction in reactions:
            counts[reaction.emoji] = counts.get(reaction.emoji, 0) + 1
        
        return counts
    
    async def get_user_reactions(
        self,
        memory_id: UUID,
        user_id: UUID,
        family_unit_id: UUID
    ) -> List[str]:
        """
        Get emojis that a user has reacted with on a memory.
        
        Args:
            memory_id: The memory ID
            user_id: The user ID
            family_unit_id: The user's family unit ID (for validation)
            
        Returns:
            List of emoji strings
        """
        # Verify memory is in family
        memory = await self.memory_service.get_memory(memory_id, family_unit_id)
        if not memory:
            raise ValueError("Memory not found or access denied")
        
        result = self.supabase.table("memory_reactions").select("emoji").eq(
            "memory_id", str(memory_id)
        ).eq("user_id", str(user_id)).execute()
        
        return [item["emoji"] for item in result.data]

