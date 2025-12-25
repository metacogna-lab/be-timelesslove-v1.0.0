"""
Service for managing memory comments.
"""

from uuid import UUID
from typing import List, Optional
from datetime import datetime
from app.db.supabase import get_supabase_admin
from app.models.feed import MemoryComment, CommentWithReplies
from app.schemas.feed import CreateCommentRequest, UpdateCommentRequest


class CommentService:
    """Service for memory comment operations."""

    MAX_NESTING_DEPTH = 3

    def __init__(self):
        self.supabase = get_supabase_admin()
    
    async def create_comment(
        self,
        memory_id: UUID,
        user_id: UUID,
        family_unit_id: UUID,
        request: CreateCommentRequest
    ) -> MemoryComment:
        """
        Create a comment on a memory.
        
        Args:
            memory_id: The memory ID
            user_id: The user ID creating the comment
            family_unit_id: The user's family unit ID (for validation)
            request: Comment creation request
            
        Returns:
            Created comment
            
        Raises:
            ValueError: If memory not found or not in family
            ValueError: If nesting depth exceeded
        """
        # Verify memory exists and is in user's family
        memory = await self.memory_service.get_memory(memory_id, family_unit_id)
        if not memory:
            raise ValueError("Memory not found or access denied")
        
        # Check nesting depth if this is a reply
        if request.parent_comment_id:
            depth = await self._get_comment_depth(request.parent_comment_id)
            if depth >= self.MAX_NESTING_DEPTH:
                raise ValueError(f"Maximum nesting depth of {self.MAX_NESTING_DEPTH} exceeded")
        
        # Create comment
        comment_data = {
            "memory_id": str(memory_id),
            "user_id": str(user_id),
            "content": request.content
        }
        
        if request.parent_comment_id:
            comment_data["parent_comment_id"] = str(request.parent_comment_id)
        
        result = self.supabase.table("memory_comments").insert(comment_data).execute()
        
        if not result.data:
            raise ValueError("Failed to create comment")
        
        return MemoryComment(**result.data[0])
    
    async def update_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
        family_unit_id: UUID,
        request: UpdateCommentRequest
    ) -> MemoryComment:
        """
        Update a comment.
        
        Args:
            comment_id: The comment ID
            user_id: The user ID (must own the comment)
            family_unit_id: The user's family unit ID (for validation)
            request: Comment update request
            
        Returns:
            Updated comment
            
        Raises:
            ValueError: If comment not found or user doesn't own it
        """
        # Verify comment exists and user owns it
        result = self.supabase.table("memory_comments").select("*").eq(
            "id", str(comment_id)
        ).eq("user_id", str(user_id)).is_("deleted_at", "null").execute()
        
        if not result.data:
            raise ValueError("Comment not found or access denied")
        
        # Update comment
        result = self.supabase.table("memory_comments").update({
            "content": request.content,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(comment_id)).execute()
        
        if not result.data:
            raise ValueError("Failed to update comment")
        
        return MemoryComment(**result.data[0])
    
    async def delete_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
        family_unit_id: UUID,
        user_role: str
    ) -> None:
        """
        Soft-delete a comment.
        
        Args:
            comment_id: The comment ID
            user_id: The user ID
            family_unit_id: The user's family unit ID (for validation)
            user_role: The user's role (for permission check)
            
        Raises:
            ValueError: If comment not found or access denied
        """
        # Get comment to verify ownership/family
        result = self.supabase.table("memory_comments").select(
            "*, memories!inner(family_unit_id)"
        ).eq("id", str(comment_id)).is_("deleted_at", "null").execute()
        
        if not result.data:
            raise ValueError("Comment not found")
        
        comment = result.data[0]
        memory_family_id = comment["memories"]["family_unit_id"]
        
        # Check permission: user owns comment OR user is adult in same family
        can_delete = (
            comment["user_id"] == str(user_id) or
            (user_role == "adult" and memory_family_id == str(family_unit_id))
        )
        
        if not can_delete:
            raise ValueError("Access denied")
        
        # Soft delete
        self.supabase.table("memory_comments").update({
            "deleted_at": datetime.utcnow().isoformat()
        }).eq("id", str(comment_id)).execute()
    
    async def get_comments_for_memory(
        self,
        memory_id: UUID,
        family_unit_id: UUID,
        include_replies: bool = True,
        limit: Optional[int] = None
    ) -> List[CommentWithReplies]:
        """
        Get comments for a memory, optionally with nested replies.
        
        Args:
            memory_id: The memory ID
            family_unit_id: The user's family unit ID (for validation)
            include_replies: Whether to include nested replies
            limit: Maximum number of top-level comments to return
            
        Returns:
            List of comments with nested replies
        """
        # Verify memory is in family
        memory = await self.memory_service.get_memory(memory_id, family_unit_id)
        if not memory:
            raise ValueError("Memory not found or access denied")
        
        # Get all comments for memory (not deleted)
        query = self.supabase.table("memory_comments").select("*").eq(
            "memory_id", str(memory_id)
        ).is_("deleted_at", "null").order("created_at", desc=False)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        
        comments = [MemoryComment(**item) for item in result.data]
        
        if include_replies:
            return self._build_comment_tree(comments)
        else:
            # Return only top-level comments
            top_level = [c for c in comments if c.parent_comment_id is None]
            return [CommentWithReplies(**c.model_dump(), replies=[]) for c in top_level]
    
    async def _get_comment_depth(self, comment_id: UUID) -> int:
        """Get the nesting depth of a comment."""
        depth = 0
        current_id = comment_id
        
        while current_id and depth < self.MAX_NESTING_DEPTH:
            result = self.supabase.table("memory_comments").select(
                "parent_comment_id"
            ).eq("id", str(current_id)).execute()
            
            if not result.data:
                break
            
            parent_id = result.data[0].get("parent_comment_id")
            if parent_id:
                depth += 1
                current_id = UUID(parent_id)
            else:
                break
        
        return depth
    
    def _build_comment_tree(
        self,
        comments: List[MemoryComment]
    ) -> List[CommentWithReplies]:
        """Build a tree structure from flat comment list."""
        # Create map of comments by ID
        comment_map: dict[UUID, CommentWithReplies] = {}
        
        # Initialize all comments
        for comment in comments:
            comment_map[comment.id] = CommentWithReplies(
                **comment.model_dump(),
                replies=[],
                reply_count=0
            )
        
        # Build tree
        top_level: List[CommentWithReplies] = []
        
        for comment in comments:
            comment_with_replies = comment_map[comment.id]
            
            if comment.parent_comment_id:
                # Add to parent's replies
                parent = comment_map.get(comment.parent_comment_id)
                if parent:
                    parent.replies.append(comment_with_replies)
                    parent.reply_count += 1
            else:
                # Top-level comment
                top_level.append(comment_with_replies)
        
        return top_level

