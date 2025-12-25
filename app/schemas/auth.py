"""
Pydantic schemas for authentication requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Base registration request schema."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)
    family_name: Optional[str] = Field(None, max_length=255)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class AdultRegisterRequest(RegisterRequest):
    """Adult registration request."""
    pass


class TeenRegisterRequest(RegisterRequest):
    """Teenager registration request."""
    pass


class GrandparentRegisterRequest(RegisterRequest):
    """Grandparent registration request."""
    pass


class ChildProvisionRequest(BaseModel):
    """Child account provisioning request (Adult only)."""
    
    display_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None  # Optional email for child


class PetRegisterRequest(BaseModel):
    """Pet profile creation request."""
    
    display_name: str = Field(..., min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response schema."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires


class RegisterResponse(BaseModel):
    """Registration response schema."""
    
    user_id: str
    email: str
    role: str
    family_unit_id: str
    tokens: TokenResponse


class ChildProvisionResponse(BaseModel):
    """Child provisioning response schema."""
    
    user_id: str
    username: str  # Generated username (email or username)
    password: str  # Generated password (one-time display)
    display_name: str
    family_unit_id: str
    message: str = "Credentials provided. Store securely. Password cannot be retrieved."


class PetRegisterResponse(BaseModel):
    """Pet profile creation response schema."""
    
    pet_id: str
    display_name: str
    family_unit_id: str
    message: str = "Pet profile created. Email notification simulated."

