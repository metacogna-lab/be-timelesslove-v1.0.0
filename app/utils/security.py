"""
Security utilities for password generation, token generation, and validation.
"""

import secrets
import string
from typing import Optional


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Password length (default: 16)
    
    Returns:
        Secure random password string
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_username(base_name: str, length: int = 8) -> str:
    """
    Generate a username from a base name.
    
    Args:
        base_name: Base name to derive username from
        length: Length of random suffix
    
    Returns:
        Generated username
    """
    # Clean base name (lowercase, alphanumeric only)
    clean_base = ''.join(c for c in base_name.lower() if c.isalnum())
    if len(clean_base) > 10:
        clean_base = clean_base[:10]
    
    # Add random suffix
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))
    return f"{clean_base}_{suffix}"

