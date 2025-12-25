"""
Invitation API endpoints for creating and managing family invitations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_db, get_current_user
from app.dependencies.rbac import require_invite_permission
from app.schemas.invite import (
    CreateInviteRequest,
    InviteResponse,
    ValidateInviteResponse,
    AcceptInviteRequest,
)
from app.services.invite_service import (
    create_invitation,
    validate_invitation,
    get_invitation_by_token,
)
from app.services.user_service import check_user_exists
from app.utils.jwt import TokenClaims
from app.api.v1.auth import register_user
from supabase import Client
from app.config import get_settings


router = APIRouter()
settings = get_settings()


@router.post("", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    request: CreateInviteRequest,
    current_user: TokenClaims = Depends(require_invite_permission),
    db: Client = Depends(get_db)
):
    """
    Create a new invitation (Adult or Grandparent only).
    
    Generates a secure token and returns an invitation link.
    """
    
    # Check if user with this email already exists
    if await check_user_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create invitation
    invite = await create_invitation(
        family_unit_id=current_user.family_unit_id,
        invited_by=current_user.sub,
        email=request.email,
        role=request.role
    )
    
    # Generate invite link (frontend will handle email sending)
    invite_link = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:5173'}/accept-invite?token={invite.token}"
    
    return InviteResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        token=invite.token,
        invite_link=invite_link,
        expires_at=invite.expires_at,
        status=invite.status,
        created_at=invite.created_at
    )


@router.get("/{token}", response_model=ValidateInviteResponse)
async def validate_invite(
    token: str,
    db: Client = Depends(get_db)
):
    """
    Validate an invitation token.
    
    Returns invitation details if valid, error message if invalid.
    """
    is_valid, invite, error_message = await validate_invitation(token)
    
    if not is_valid:
        return ValidateInviteResponse(
            valid=False,
            message=error_message
        )
    
    return ValidateInviteResponse(
        valid=True,
        invite=InviteResponse(
            id=invite.id,
            email=invite.email,
            role=invite.role,
            token=invite.token,
            invite_link="",  # Not needed for validation
            expires_at=invite.expires_at,
            status=invite.status,
            created_at=invite.created_at
        )
    )


@router.post("/{token}/accept", response_model=InviteResponse, status_code=status.HTTP_200_OK)
async def accept_invite(
    token: str,
    request: AcceptInviteRequest,
    db: Client = Depends(get_db)
):
    """
    Accept an invitation and create user account.
    
    Validates the invitation token, creates user account with pre-assigned role,
    and marks invitation as accepted.
    """
    # Validate invitation
    is_valid, invite, error_message = await validate_invitation(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message or "Invalid or expired invitation"
        )
    
    # Verify email matches invitation
    if request.email != invite.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match invitation"
        )
    
    # Register user with invitation role and family unit
    from app.services.invite_service import accept_invitation
    from uuid import UUID
    
    # Register user (this will create auth user and profile)
    from app.api.v1.auth import register_user
    from uuid import UUID
    
    register_response = await register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role=invite.role,
        family_unit_id=UUID(str(invite.family_unit_id)),
        is_family_creator=False
    )
    
    # Mark invitation as accepted
    await accept_invitation(invite.id)
    
    # Return invitation details
    return InviteResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        token=invite.token,
        invite_link="",
        expires_at=invite.expires_at,
        status="accepted",
        created_at=invite.created_at
    )

