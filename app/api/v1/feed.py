"""
API endpoints for memory feed and interactions.
"""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from app.dependencies import get_current_user, get_current_user_model
from app.models.user import CurrentUser
from app.dependencies.rbac import exclude_pets_for_current_user
from app.schemas.feed import (
    CreateReactionRequest,
    ReactionResponse,
    CreateCommentRequest,
    UpdateCommentRequest,
    CommentResponse,
    FeedFilterParams,
    FeedPaginationParams,
    FeedResponse,
    MemoryFeedItem
)
from app.services.reaction_service import ReactionService
from app.services.comment_service import CommentService
from app.services.feed_service import FeedService
from app.services.metrics import log_feed_interaction


router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=FeedResponse)
async def get_feed(
    status: Optional[str] = Query(None, pattern="^(draft|published|archived)$"),
    user_id: Optional[UUID] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated
    memory_date_from: Optional[str] = Query(None),
    memory_date_to: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    order_by: str = Query("feed_score", pattern="^(feed_score|created_at|memory_date)$"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user_model),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get paginated memory feed with engagement-based ordering.
    
    Supports filtering by status, user, tags, date range, and search query.
    Results are ordered by feed score (time + engagement) by default.
    """
    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    # Parse dates if provided
    from datetime import datetime
    date_from = None
    date_to = None
    if memory_date_from:
        date_from = datetime.fromisoformat(memory_date_from)
    if memory_date_to:
        date_to = datetime.fromisoformat(memory_date_to)
    
    filters = FeedFilterParams(
        status=status,
        user_id=user_id,
        tags=tag_list,
        memory_date_from=date_from,
        memory_date_to=date_to,
        search_query=search_query,
        order_by=order_by,
        order_direction=order_direction
    )
    
    pagination = FeedPaginationParams(page=page, page_size=page_size)
    
    feed_service = FeedService()
    result = await feed_service.get_feed(
        current_user.family_unit_id,
        current_user.user_id,
        filters,
        pagination
    )
    
    # Log feed view
    background_tasks.add_task(
        log_feed_interaction,
        user_id=current_user.user_id,
        family_unit_id=current_user.family_unit_id,
        interaction_type="feed_view",
        metadata={"page": page, "page_size": page_size, "filters": filters.model_dump(), "items_returned": len(result.get("items", []))}
    )
    
    return FeedResponse(**result)


@router.post("/memories/{memory_id}/reactions", response_model=ReactionResponse)
async def create_reaction(
    memory_id: UUID,
    request: CreateReactionRequest,
    current_user: CurrentUser = Depends(exclude_pets_for_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create a reaction to a memory.
    
    Supported emojis: 👍, ❤️, 😂, 😮, 😢, 🎉, 🔥, 💯
    Each user can have one reaction per emoji type per memory.
    """
    reaction_service = ReactionService()
    
    try:
        reaction = await reaction_service.create_reaction(
            memory_id,
            current_user.user_id,
            current_user.family_unit_id,
            request
        )
        
        # Log reaction creation
        background_tasks.add_task(
            log_feed_interaction,
            user_id=current_user.user_id,
            family_unit_id=current_user.family_unit_id,
            interaction_type="reaction_created",
            metadata={"memory_id": str(memory_id), "emoji": request.emoji}
        )
        
        return ReactionResponse(
            id=reaction.id,
            memory_id=reaction.memory_id,
            user_id=reaction.user_id,
            emoji=reaction.emoji,
            created_at=reaction.created_at.isoformat(),
            updated_at=reaction.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/memories/{memory_id}/reactions/{reaction_id}")
async def delete_reaction(
    memory_id: UUID,
    reaction_id: UUID,
    current_user: CurrentUser = Depends(get_current_user_model),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Delete a reaction.
    
    Users can only delete their own reactions.
    """
    reaction_service = ReactionService()
    
    try:
        await reaction_service.delete_reaction(
            reaction_id,
            current_user.user_id,
            current_user.family_unit_id
        )
        
        # Log reaction deletion
        background_tasks.add_task(
            log_feed_interaction,
            user_id=current_user.user_id,
            family_unit_id=current_user.family_unit_id,
            interaction_type="reaction_deleted",
            metadata={"memory_id": str(memory_id), "reaction_id": str(reaction_id)}
        )
        
        return {"message": "Reaction deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memories/{memory_id}/reactions", response_model=list[ReactionResponse])
async def get_reactions(
    memory_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get all reactions for a memory.
    """
    reaction_service = ReactionService()
    
    try:
        reactions = await reaction_service.get_reactions_for_memory(
            memory_id,
            current_user.family_unit_id
        )
        
        return [
            ReactionResponse(
                id=r.id,
                memory_id=r.memory_id,
                user_id=r.user_id,
                emoji=r.emoji,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat()
            )
            for r in reactions
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/memories/{memory_id}/comments", response_model=CommentResponse)
async def create_comment(
    memory_id: UUID,
    request: CreateCommentRequest,
    current_user: CurrentUser = Depends(exclude_pets_for_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create a comment on a memory.
    
    Supports threaded comments via parent_comment_id.
    Maximum nesting depth: 3 levels.
    """
    comment_service = CommentService()
    
    try:
        comment = await comment_service.create_comment(
            memory_id,
            current_user.user_id,
            current_user.family_unit_id,
            request
        )
        
        # Log comment creation
        background_tasks.add_task(
            log_feed_interaction,
            user_id=current_user.user_id,
            family_unit_id=current_user.family_unit_id,
            interaction_type="comment_created",
            metadata={
                "memory_id": str(memory_id),
                "comment_id": str(comment.id),
                "parent_comment_id": str(request.parent_comment_id) if request.parent_comment_id else None,
                "is_reply": request.parent_comment_id is not None,
                "content_length": len(request.content)
            }
        )
        
        return CommentResponse(
            id=comment.id,
            memory_id=comment.memory_id,
            user_id=comment.user_id,
            parent_comment_id=comment.parent_comment_id,
            content=comment.content,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat(),
            deleted_at=comment.deleted_at.isoformat() if comment.deleted_at else None,
            reply_count=0,
            replies=[]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/memories/{memory_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    memory_id: UUID,
    comment_id: UUID,
    request: UpdateCommentRequest,
    current_user: CurrentUser = Depends(get_current_user_model),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Update a comment.
    
    Users can only update their own comments.
    """
    comment_service = CommentService()
    
    try:
        comment = await comment_service.update_comment(
            comment_id,
            current_user.user_id,
            current_user.family_unit_id,
            request
        )
        
        # Log comment update
        background_tasks.add_task(
            log_feed_interaction,
            user_id=current_user.user_id,
            family_unit_id=current_user.family_unit_id,
            interaction_type="comment_updated",
            metadata={"memory_id": str(memory_id), "comment_id": str(comment_id)}
        )
        
        return CommentResponse(
            id=comment.id,
            memory_id=comment.memory_id,
            user_id=comment.user_id,
            parent_comment_id=comment.parent_comment_id,
            content=comment.content,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat(),
            deleted_at=comment.deleted_at.isoformat() if comment.deleted_at else None,
            reply_count=0,
            replies=[]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/memories/{memory_id}/comments/{comment_id}")
async def delete_comment(
    memory_id: UUID,
    comment_id: UUID,
    current_user: CurrentUser = Depends(get_current_user_model),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Soft-delete a comment.
    
    Users can delete their own comments, or adults can delete any comment in their family.
    """
    comment_service = CommentService()
    
    try:
        await comment_service.delete_comment(
            comment_id,
            current_user.user_id,
            current_user.family_unit_id,
            current_user.role
        )
        
        # Log comment deletion
        background_tasks.add_task(
            log_feed_interaction,
            user_id=current_user.user_id,
            family_unit_id=current_user.family_unit_id,
            interaction_type="comment_deleted",
            metadata={"memory_id": str(memory_id), "comment_id": str(comment_id), "deleted_by_owner": True}
        )
        
        return {"message": "Comment deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memories/{memory_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    memory_id: UUID,
    include_replies: bool = Query(True),
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get comments for a memory.
    
    Returns top-level comments with nested replies if include_replies=true.
    """
    comment_service = CommentService()
    
    try:
        comments = await comment_service.get_comments_for_memory(
            memory_id,
            current_user.family_unit_id,
            include_replies=include_replies,
            limit=limit
        )
        
        def convert_to_response(comment):
            """Recursively convert CommentWithReplies to CommentResponse."""
            return CommentResponse(
                id=comment.id,
                memory_id=comment.memory_id,
                user_id=comment.user_id,
                parent_comment_id=comment.parent_comment_id,
                content=comment.content,
                created_at=comment.created_at.isoformat(),
                updated_at=comment.updated_at.isoformat(),
                deleted_at=comment.deleted_at.isoformat() if comment.deleted_at else None,
                reply_count=comment.reply_count,
                replies=[convert_to_response(reply) for reply in comment.replies]
            )
        
        return [convert_to_response(c) for c in comments]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

