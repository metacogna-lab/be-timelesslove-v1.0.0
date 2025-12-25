"""
Invitation service for managing family invitations.
"""

from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from supabase import Client
from app.db.supabase import get_supabase_service_client
from app.models.invite import Invite


async def create_invitation(
    family_unit_id: UUID,
    invited_by: UUID,
    email: str,
    role: str,
    expires_in_days: int = 7
) -> Invite:
    """
    Create a new invitation.
    
    Args:
        family_unit_id: Family unit UUID
        invited_by: User UUID who is sending the invite
        email: Invitee email
        role: Proposed role for invitee
        expires_in_days: Days until expiration (default: 7)
    
    Returns:
        Created Invite with token
    """
    service_client = get_supabase_service_client()
    
    # Generate secure token
    token = await generate_invite_token()
    
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    invite_data = {
        "family_unit_id": str(family_unit_id),
        "invited_by": str(invited_by),
        "email": email,
        "role": role,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "status": "pending"
    }
    
    result = service_client.table("invites").insert(invite_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise ValueError("Failed to create invitation")

    return Invite(**result.data[0])  # type: ignore


async def generate_invite_token() -> str:
    """
    Generate a secure invitation token.
    
    Returns:
        URL-safe base64 token string
    """
    import secrets
    import base64
    
    token_bytes = secrets.token_bytes(32)
    token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    # Remove padding
    token = token.rstrip('=')
    return token


async def get_invitation_by_token(token: str) -> Optional[Invite]:
    """
    Get invitation by token.
    
    Args:
        token: Invitation token
    
    Returns:
        Invite if found and valid, None otherwise
    """
    service_client = get_supabase_service_client()
    
    result = service_client.table("invites").select("*").eq("token", token).single().execute()
    
    if not result.data:
        return None

    invite = Invite(**result.data[0])  # type: ignore
    
    # Check expiration
    if invite.expires_at < datetime.utcnow():
        if invite.status == "pending":
            # Mark as expired
            await update_invitation_status(invite.id, "expired")
        return None
    
    return invite


async def validate_invitation(token: str) -> tuple[bool, Optional[Invite], Optional[str]]:
    """
    Validate an invitation token.
    
    Args:
        token: Invitation token
    
    Returns:
        Tuple of (is_valid, invite, error_message)
    """
    invite = await get_invitation_by_token(token)
    
    if not invite:
        return False, None, "Invitation not found"
    
    if invite.status != "pending":
        return False, invite, f"Invitation is {invite.status}"
    
    if invite.expires_at < datetime.utcnow():
        return False, invite, "Invitation has expired"
    
    return True, invite, None


async def accept_invitation(invite_id: UUID) -> None:
    """
    Mark an invitation as accepted.
    
    Args:
        invite_id: Invitation UUID
    """
    service_client = get_supabase_service_client()
    
    service_client.table("invites").update({
        "status": "accepted",
        "accepted_at": datetime.utcnow().isoformat()
    }).eq("id", str(invite_id)).execute()


async def update_invitation_status(invite_id: UUID, status: str) -> None:
    """
    Update invitation status.
    
    Args:
        invite_id: Invitation UUID
        status: New status (pending, accepted, expired, revoked)
    """
    service_client = get_supabase_service_client()
    
    service_client.table("invites").update({
        "status": status
    }).eq("id", str(invite_id)).execute()

