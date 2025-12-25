"""
Service for logging feed interaction metrics.
"""

from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from app.services.analytics_service import get_analytics_service


logger = logging.getLogger(__name__)


async def log_feed_interaction(
    user_id: UUID,
    family_unit_id: UUID,
    interaction_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[UUID] = None
) -> None:
    """
    Log a feed interaction event.
    
    Args:
        user_id: The user ID
        family_unit_id: The family unit ID
        interaction_type: Type of interaction (feed_view, reaction_created, etc.)
        metadata: Additional metadata about the interaction
        session_id: Optional session identifier
    """
    try:
        analytics = get_analytics_service()
        
        # Emit analytics event
        await analytics.emit_event(
            event_type=interaction_type,
            user_id=user_id,
            family_unit_id=family_unit_id,
            metadata=metadata,
            session_id=session_id
        )
        
        # Also record as metric
        await analytics.increment_counter(
            metric_name="feed_interactions",
            labels={
                "interaction_type": interaction_type,
                "family_unit_id": str(family_unit_id)
            }
        )
        
    except Exception as e:
        # Don't fail the request if metrics logging fails
        logger.error(f"Failed to log feed interaction: {e}", exc_info=True)


# Interaction types
INTERACTION_TYPES = {
    "feed_view": "User viewed the feed",
    "reaction_created": "User created a reaction",
    "reaction_deleted": "User deleted a reaction",
    "comment_created": "User created a comment",
    "comment_updated": "User updated a comment",
    "comment_deleted": "User deleted a comment",
    "memory_viewed": "User viewed a memory detail",
    "memory_shared": "User shared a memory"
}

