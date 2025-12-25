"""
Authentication API endpoints for registration, login, and token management.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_db, get_current_user
from app.dependencies.rbac import (
    require_child_provision_permission,
    require_pet_creation_permission
)
from app.schemas.auth import (
    AdultRegisterRequest,
    TeenRegisterRequest,
    GrandparentRegisterRequest,
    ChildProvisionRequest,
    PetRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterResponse,
    TokenResponse,
    ChildProvisionResponse,
    PetRegisterResponse,
)
from app.services.auth_service import generate_tokens, validate_refresh_token, revoke_refresh_token
from app.services.user_service import (
    create_user_profile,
    get_user_profile,
    check_user_exists,
    get_user_profile_by_email,
)
from app.services.family_service import create_family_unit
from app.services.invite_service import get_invitation_by_token, accept_invitation
from app.utils.jwt import TokenClaims, get_jwt_config
from app.utils.security import generate_secure_password, generate_username
from app.db.supabase import get_supabase_service_client


router = APIRouter()


async def register_user(
    email: str,
    password: str,
    display_name: str,
    role: str,
    family_unit_id: Optional[UUID] = None,
    is_family_creator: bool = False,
    family_name: Optional[str] = None
) -> RegisterResponse:
    """
    Internal function to register a user with Supabase Auth and create profile.
    
    Args:
        email: User email
        password: User password
        display_name: Display name
        role: User role
        family_unit_id: Existing family unit ID (if joining)
        is_family_creator: Whether creating new family
        family_name: Family name (if creating new family)
    
    Returns:
        RegisterResponse with user info and tokens
    """
    service_client = get_supabase_service_client()
    
    # Check if user already exists
    if await check_user_exists(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create Supabase Auth user
    try:
        auth_response = service_client.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
        
        user_id = UUID(auth_response.user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )
    
    # Create family unit if this is the first user
    if is_family_creator:
        family_unit = await create_family_unit(user_id, family_name)
        family_unit_id = family_unit.id
    elif not family_unit_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="family_unit_id required for non-creator users"
        )
    
    # Create user profile
    user_profile = await create_user_profile(
        user_id=user_id,
        role=role,
        display_name=display_name,
        family_unit_id=family_unit_id,
        is_family_creator=is_family_creator
    )
    
    # Generate tokens
    access_token, refresh_token = await generate_tokens(
        str(user_id),
        role,
        str(family_unit_id)
    )
    
    config = get_jwt_config()
    
    return RegisterResponse(
        user_id=str(user_id),
        email=email,
        role=role,
        family_unit_id=str(family_unit_id),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=config.access_token_expire_seconds
        )
    )


@router.post("/register/adult", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_adult(
    request: AdultRegisterRequest,
    db: Client = Depends(get_db)
):
    """
    Register a new adult user (self-signup).
    
    Creates a new family unit if this is the first user.
    """
    return await register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role="adult",
        is_family_creator=True,
        family_name=request.family_name
    )


@router.post("/register/teen", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_teen(
    request: TeenRegisterRequest,
    db: Client = Depends(get_db)
):
    """
    Register a new teenager user (self-signup).
    
    Creates a new family unit if this is the first user.
    """
    return await register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role="teen",
        is_family_creator=True,
        family_name=request.family_name
    )


@router.post("/register/grandparent", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_grandparent(
    request: GrandparentRegisterRequest,
    db: Client = Depends(get_db)
):
    """
    Register a new grandparent user (self-signup).
    
    Creates a new family unit if this is the first user.
    """
    return await register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role="grandparent",
        is_family_creator=True,
        family_name=request.family_name
    )


@router.post("/register/child", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_child(
    request: TeenRegisterRequest,  # Child uses same schema as teen for registration
    invite_token: str,
    db: Client = Depends(get_db)
):
    """
    Register a child user via invitation token.
    
    Child accounts are typically created by adults via invitation.
    """
    # Validate invitation
    invite = await get_invitation_by_token(invite_token)
    if not invite or invite.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token"
        )
    
    if invite.role != "child":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation is not for a child account"
        )
    
    # Register user
    response = await register_user(
        email=request.email,
        password=request.password,
        display_name=request.display_name,
        role="child",
        family_unit_id=invite.family_unit_id,
        is_family_creator=False
    )
    
    # Mark invitation as accepted
    await accept_invitation(invite.id)
    
    return response


@router.post("/provision/child", response_model=ChildProvisionResponse, status_code=status.HTTP_201_CREATED)
async def provision_child(
    request: ChildProvisionRequest,
    current_user: TokenClaims = Depends(require_child_provision_permission),
    db: Client = Depends(get_db)
):
    """
    Provision a child account (Adult only).
    
    Generates username and password for child account.
    """
    
    # Generate credentials
    username = request.email or generate_username(request.display_name)
    password = generate_secure_password()
    
    # Create user with generated credentials
    service_client = get_supabase_service_client()
    
    try:
        auth_response = service_client.auth.sign_up({
            "email": username if "@" in username else f"{username}@timelesslove.local",
            "password": password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create child account"
            )
        
        user_id = UUID(auth_response.user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create child account: {str(e)}"
        )
    
    # Create user profile
    user_profile = await create_user_profile(
        user_id=user_id,
        role="child",
        display_name=request.display_name,
        family_unit_id=UUID(current_user.family_unit_id),
        is_family_creator=False
    )
    
    return ChildProvisionResponse(
        user_id=str(user_id),
        username=username,
        password=password,
        display_name=request.display_name,
        family_unit_id=current_user.family_unit_id
    )


@router.post("/register/pet", response_model=PetRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_pet(
    request: PetRegisterRequest,
    current_user: TokenClaims = Depends(require_pet_creation_permission),
    db: Client = Depends(get_db)
):
    """
    Create a pet profile (Adult or Grandparent only).
    
    Pet profiles don't require authentication - they're read-only.
    """
    # Create minimal auth user for pet (required for foreign key constraint)
    # Pet accounts cannot log in - they're read-only
    service_client = get_supabase_service_client()
    
    # Generate unique email for pet (won't be used for login)
    from uuid import uuid4
    pet_email = f"pet_{uuid4()}@timelesslove.local"
    pet_password = generate_secure_password(32)  # Long random password
    
    try:
        auth_response = service_client.auth.sign_up({
            "email": pet_email,
            "password": pet_password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create pet account"
            )
        
        pet_id = UUID(auth_response.user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create pet account: {str(e)}"
        )
    
    # Create pet profile
    user_profile = await create_user_profile(
        user_id=pet_id,
        role="pet",
        display_name=request.display_name,
        family_unit_id=UUID(current_user.family_unit_id),
        is_family_creator=False,
        preferences={"avatar_url": request.avatar_url} if request.avatar_url else {}
    )
    
    # Simulate email notification (log only)
    print(f"[SIMULATED EMAIL] Pet profile created: {request.display_name} in family {current_user.family_unit_id}")
    
    return PetRegisterResponse(
        pet_id=str(pet_id),
        display_name=request.display_name,
        family_unit_id=current_user.family_unit_id
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Client = Depends(get_db)
):
    """
    Login with email and password.
    
    Authenticates with Supabase Auth and returns custom JWT tokens.
    """
    service_client = get_supabase_service_client()
    
    try:
        # Authenticate with Supabase
        auth_response = service_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_id = UUID(auth_response.user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Get user profile
    user_profile = await get_user_profile(user_id)
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Generate tokens
    access_token, refresh_token = await generate_tokens(
        str(user_id),
        user_profile.role,
        str(user_profile.family_unit_id)
    )
    
    config = get_jwt_config()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.access_token_expire_seconds
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Client = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Implements token rotation - issues new refresh token and revokes old one.
    """
    # Validate refresh token
    claims = await validate_refresh_token(request.refresh_token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Revoke old refresh token
    await revoke_refresh_token(request.refresh_token)
    
    # Generate new tokens
    access_token, refresh_token = await generate_tokens(
        claims.sub,
        claims.role,
        claims.family_unit_id
    )
    
    config = get_jwt_config()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.access_token_expire_seconds
    )

