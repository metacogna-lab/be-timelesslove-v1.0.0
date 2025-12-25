"""
Service for memory feed operations with engagement-based ordering.
"""

from uuid import UUID
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from app.db.supabase import get_supabase_admin
from app.models.feed import MemoryEngagement
from app.schemas.feed import FeedFilterParams, FeedPaginationParams, MemoryFeedItem
from app.services.reaction_service import ReactionService
from app.services.comment_service import CommentService


class FeedService:
    """Service for memory feed operations."""

    # Feed scoring weights
    TIME_WEIGHT = 0.6
    ENGAGEMENT_WEIGHT = 0.4
    REACTION_WEIGHT = 1.0
    COMMENT_WEIGHT = 2.0

    def __init__(self):
        self.supabase = get_supabase_admin()
        self.reaction_service = ReactionService()
        self.comment_service = CommentService()
    
    async def get_feed(
        self,
        family_unit_id: UUID,
        user_id: UUID,
        filters: FeedFilterParams,
        pagination: FeedPaginationParams
    ) -> Dict:
        """
        Get paginated memory feed with engagement-based ordering.
        
        Args:
            family_unit_id: The user's family unit ID
            user_id: The current user ID (for user-specific reactions)
            filters: Filter parameters
            pagination: Pagination parameters
            
        Returns:
            Dictionary with feed items and pagination info
        """
        # Build base query
        query = self.supabase.table("memories").select(
            "*, memory_media(*), user_profiles!memories_user_id_fkey(display_name, avatar_url)"
        ).eq("family_unit_id", str(family_unit_id))
        
        # Apply filters
        if filters.status:
            query = query.eq("status", filters.status)
        else:
            # Default to published only
            query = query.eq("status", "published")
        
        if filters.user_id:
            query = query.eq("user_id", str(filters.user_id))
        
        if filters.tags:
            query = query.contains("tags", filters.tags)
        
        if filters.memory_date_from:
            query = query.gte("memory_date", filters.memory_date_from.isoformat())
        
        if filters.memory_date_to:
            query = query.lte("memory_date", filters.memory_date_to.isoformat())
        
        # Note: Search query will be applied after fetching (see below)
        # For production, consider using Postgres full-text search
        
        # Get all matching memories (we'll calculate scores and sort in Python)
        # For large datasets, this should be done in SQL, but for MVP we'll do it here
        result = query.execute()
        
        memories = result.data
        
        # Apply search query filter if provided (filter in Python)
        if filters.search_query:
            search_lower = filters.search_query.lower()
            memories = [
                m for m in memories
                if (m.get("title", "") or "").lower().find(search_lower) >= 0 or
                   (m.get("description", "") or "").lower().find(search_lower) >= 0
            ]
        
        # Calculate engagement scores for each memory
        feed_items = []
        for memory in memories:
            memory_id = UUID(memory["id"])
            
            # Get engagement metrics
            engagement = await self._calculate_engagement(memory_id, family_unit_id)
            
            # Calculate feed score
            feed_score = await self._calculate_feed_score(
                memory["created_at"],
                engagement
            )
            
            # Get user's reactions
            user_reactions = await self.reaction_service.get_user_reactions(
                memory_id, user_id, family_unit_id
            )
            
            # Get top-level comments (limit to 3 for feed preview)
            comments = await self.comment_service.get_comments_for_memory(
                memory_id, family_unit_id, include_replies=False, limit=3
            )
            
            # Format media
            media = []
            for media_item in memory.get("memory_media", []):
                media.append({
                    "id": media_item["id"],
                    "storage_path": media_item["storage_path"],
                    "file_name": media_item["file_name"],
                    "mime_type": media_item["mime_type"],
                    "thumbnail_path": media_item.get("thumbnail_path"),
                    "processing_status": media_item["processing_status"]
                })
            
            feed_item = MemoryFeedItem(
                id=UUID(memory["id"]),
                user_id=UUID(memory["user_id"]),
                family_unit_id=UUID(memory["family_unit_id"]),
                title=memory.get("title"),
                description=memory.get("description"),
                memory_date=memory.get("memory_date"),
                location=memory.get("location"),
                tags=memory.get("tags", []),
                status=memory["status"],
                created_at=memory["created_at"],
                updated_at=memory["updated_at"],
                media=media,
                reaction_count=engagement.reaction_count,
                comment_count=engagement.comment_count,
                reactions_by_emoji=engagement.reactions_by_emoji,
                user_reactions=user_reactions,
                top_comments=[],  # Will be populated from comments
                feed_score=feed_score
            )
            
            feed_items.append(feed_item)
        
        # Sort by feed score or other criteria
        reverse = filters.order_direction == "desc"
        
        if filters.order_by == "feed_score":
            feed_items.sort(key=lambda x: x.feed_score, reverse=reverse)
        elif filters.order_by == "created_at":
            feed_items.sort(key=lambda x: x.created_at, reverse=reverse)
        elif filters.order_by == "memory_date":
            feed_items.sort(
                key=lambda x: x.memory_date or "",
                reverse=reverse
            )
        
        # Apply pagination
        total_count = len(feed_items)
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        paginated_items = feed_items[start_idx:end_idx]
        
        # Populate top comments for paginated items
        for item in paginated_items:
            comments = await self.comment_service.get_comments_for_memory(
                item.id, family_unit_id, include_replies=False, limit=3
            )
            # Convert to response format
            from app.schemas.feed import CommentResponse
            item.top_comments = [
                CommentResponse(
                    id=c.id,
                    memory_id=c.memory_id,
                    user_id=c.user_id,
                    parent_comment_id=c.parent_comment_id,
                    content=c.content,
                    created_at=c.created_at.isoformat(),
                    updated_at=c.updated_at.isoformat(),
                    deleted_at=c.deleted_at.isoformat() if c.deleted_at else None,
                    reply_count=c.reply_count,
                    replies=[]
                )
                for c in comments
            ]
        
        return {
            "items": paginated_items,
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_pages": (total_count + pagination.page_size - 1) // pagination.page_size,
                "has_more": end_idx < total_count
            },
            "total_count": total_count,
            "has_more": end_idx < total_count
        }
    
    async def _calculate_engagement(
        self,
        memory_id: UUID,
        family_unit_id: UUID
    ) -> MemoryEngagement:
        """Calculate engagement metrics for a memory."""
        # Get reaction counts by emoji
        reactions_by_emoji = await self.reaction_service.get_reactions_by_emoji(
            memory_id, family_unit_id
        )
        
        # Get total reaction count
        reaction_count = sum(reactions_by_emoji.values())
        
        # Get unique reactors count
        reactions = await self.reaction_service.get_reactions_for_memory(
            memory_id, family_unit_id
        )
        unique_reactors = len(set(r.user_id for r in reactions))
        
        # Get comment count (top-level only)
        comments = await self.comment_service.get_comments_for_memory(
            memory_id, family_unit_id, include_replies=False
        )
        comment_count = len(comments)
        
        return MemoryEngagement(
            memory_id=memory_id,
            reaction_count=reaction_count,
            comment_count=comment_count,
            unique_reactors=unique_reactors,
            reactions_by_emoji=reactions_by_emoji,
            feed_score=0.0  # Will be calculated separately
        )
    
    async def _calculate_feed_score(
        self,
        created_at_str: str,
        engagement: MemoryEngagement
    ) -> float:
        """
        Calculate feed score combining time decay and engagement.
        
        Args:
            created_at_str: ISO format timestamp string
            engagement: Engagement metrics
            
        Returns:
            Feed score (higher = more relevant)
        """
        # Parse creation time
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=created_at.tzinfo)
        hours_ago = (now - created_at).total_seconds() / 3600
        
        # Calculate time score with exponential decay
        time_score = 1.0 / (1.0 + hours_ago / 24.0)  # Decay over 24 hours
        
        # Apply time decay multipliers
        if hours_ago <= 24:
            time_multiplier = 1.0
        elif hours_ago <= 168:  # 7 days
            time_multiplier = 0.7
        elif hours_ago <= 720:  # 30 days
            time_multiplier = 0.4
        else:
            time_multiplier = 0.2
        
        time_score *= time_multiplier
        
        # Calculate engagement score
        engagement_score = (
            engagement.reaction_count * self.REACTION_WEIGHT +
            engagement.comment_count * self.COMMENT_WEIGHT
        )
        
        # Normalize engagement score (log scale to prevent domination)
        import math
        if engagement_score > 0:
            engagement_score = math.log1p(engagement_score)  # log(1 + x)
        
        # Combine scores
        feed_score = (
            time_score * self.TIME_WEIGHT +
            engagement_score * self.ENGAGEMENT_WEIGHT
        )
        
        return feed_score

