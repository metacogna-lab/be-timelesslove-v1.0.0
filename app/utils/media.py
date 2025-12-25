"""
Media utilities for validation, MIME type handling, and file operations.
"""

from typing import Optional, Tuple
import re


# Allowed MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm"
}

ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

# File extensions mapping
MIME_TYPE_EXTENSIONS = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/webp": [".webp"],
    "video/mp4": [".mp4"],
    "video/webm": [".webm"]
}


def is_allowed_mime_type(mime_type: str) -> bool:
    """
    Check if MIME type is allowed.
    
    Args:
        mime_type: MIME type string
    
    Returns:
        True if allowed, False otherwise
    """
    return mime_type.lower() in ALLOWED_MIME_TYPES


def is_image(mime_type: str) -> bool:
    """Check if MIME type is an image."""
    return mime_type.lower() in ALLOWED_IMAGE_TYPES


def is_video(mime_type: str) -> bool:
    """Check if MIME type is a video."""
    return mime_type.lower() in ALLOWED_VIDEO_TYPES


def validate_file_name(file_name: str) -> bool:
    """
    Validate file name to prevent path traversal.
    
    Args:
        file_name: File name to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Prevent path traversal
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        return False
    
    # Check for valid characters (alphanumeric, dots, hyphens, underscores)
    if not re.match(r"^[a-zA-Z0-9._-]+$", file_name):
        return False
    
    return True


def validate_storage_path(path: str) -> bool:
    """
    Validate storage path to prevent path traversal.
    
    Args:
        path: Storage path to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Prevent path traversal
    if ".." in path:
        return False
    
    # Path should match expected structure: {family_unit_id}/{memory_id}/{file_name}
    parts = path.split("/")
    if len(parts) < 3:
        return False
    
    # Validate each part is a valid UUID or file name
    for part in parts:
        if not validate_file_name(part):
            return False
    
    return True


def get_file_extension(file_name: str) -> Optional[str]:
    """
    Get file extension from file name.
    
    Args:
        file_name: File name
    
    Returns:
        File extension (with dot) or None
    """
    if "." not in file_name:
        return None
    
    return "." + file_name.rsplit(".", 1)[1].lower()


def get_mime_type_from_extension(extension: str) -> Optional[str]:
    """
    Get MIME type from file extension.
    
    Args:
        extension: File extension (with or without dot)
    
    Returns:
        MIME type or None if not found
    """
    if not extension.startswith("."):
        extension = "." + extension
    
    extension = extension.lower()
    
    for mime_type, extensions in MIME_TYPE_EXTENSIONS.items():
        if extension in extensions:
            return mime_type
    
    return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

