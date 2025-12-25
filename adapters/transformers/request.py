"""
Request transformation utilities.
"""

import re
from typing import Any, Dict, Optional
from datetime import date, datetime
from uuid import UUID

from adapters.config import get_adapter_config


class RequestTransformer:
    """Transform frontend requests to backend format."""
    
    def __init__(self, config=None):
        """Initialize request transformer."""
        self.config = config or get_adapter_config()
    
    def transform_memory_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform memory creation/update request.
        
        Args:
            data: Frontend request data
        
        Returns:
            Transformed data for backend
        """
        transformed = data.copy()
        
        # Normalize date format
        if "memory_date" in transformed and transformed["memory_date"]:
            transformed["memory_date"] = self._normalize_date(
                transformed["memory_date"]
            )
        
        # Ensure tags is a list
        if "tags" in transformed:
            if isinstance(transformed["tags"], str):
                # Comma-separated string to list
                transformed["tags"] = [
                    tag.strip() for tag in transformed["tags"].split(",") if tag.strip()
                ]
            elif transformed["tags"] is None:
                transformed["tags"] = []
        
        # Ensure status is valid
        if "status" in transformed:
            valid_statuses = ["draft", "published", "archived"]
            if transformed["status"] not in valid_statuses:
                transformed["status"] = "draft"
        
        # Normalize media references
        if "media" in transformed and isinstance(transformed["media"], list):
            transformed["media"] = [
                self._normalize_media_ref(media) for media in transformed["media"]
            ]
        
        return transformed
    
    def transform_feed_filters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform feed filter parameters.
        
        Args:
            params: Frontend filter parameters
        
        Returns:
            Transformed parameters for backend
        """
        transformed = params.copy()
        
        # Normalize tags (comma-separated string to list)
        if "tags" in transformed and isinstance(transformed["tags"], str):
            transformed["tags"] = transformed["tags"]
            # Backend expects comma-separated string, so keep as is
        
        # Normalize date filters
        for date_field in ["memory_date_from", "memory_date_to"]:
            if date_field in transformed and transformed[date_field]:
                transformed[date_field] = self._normalize_datetime(
                    transformed[date_field]
                )
        
        # Ensure pagination defaults
        if "page" not in transformed:
            transformed["page"] = 1
        if "page_size" not in transformed:
            transformed["page_size"] = 20
        
        # Validate order_by
        if "order_by" in transformed:
            valid_orders = ["feed_score", "created_at", "memory_date"]
            if transformed["order_by"] not in valid_orders:
                transformed["order_by"] = "feed_score"
        
        # Validate order_direction
        if "order_direction" in transformed:
            if transformed["order_direction"] not in ["asc", "desc"]:
                transformed["order_direction"] = "desc"
        
        return transformed
    
    def transform_auth_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform authentication request.
        
        Args:
            data: Frontend request data
        
        Returns:
            Transformed data for backend
        """
        transformed = data.copy()
        
        # Ensure email is lowercase
        if "email" in transformed:
            transformed["email"] = transformed["email"].lower().strip()
        
        # Sanitize display_name
        if "display_name" in transformed:
            transformed["display_name"] = self._sanitize_string(
                transformed["display_name"]
            )
        
        # Sanitize family_name
        if "family_name" in transformed:
            transformed["family_name"] = self._sanitize_string(
                transformed["family_name"]
            )
        
        return transformed
    
    def transform_invite_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform invitation request.
        
        Args:
            data: Frontend request data
        
        Returns:
            Transformed data for backend
        """
        transformed = data.copy()
        
        # Normalize email
        if "email" in transformed:
            transformed["email"] = transformed["email"].lower().strip()
        
        # Validate role
        if "role" in transformed:
            valid_roles = ["adult", "teen", "child", "grandparent"]
            if transformed["role"] not in valid_roles:
                raise ValueError(f"Invalid role: {transformed['role']}")
        
        return transformed
    
    def _normalize_date(self, value: Any) -> Optional[str]:
        """
        Normalize date to ISO date string (YYYY-MM-DD).

        Args:
            value: Date value (string, date, datetime, or None)

        Returns:
            ISO date string or None
        """
        if value is None:
            return None

        # Already in YYYY-MM-DD format
        if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return value

        # Datetime object - convert to date
        if isinstance(value, datetime):
            return value.date().isoformat()

        # Date object
        if isinstance(value, date):
            return value.isoformat()

        # Parse datetime string
        if isinstance(value, str):
            try:
                # Try parsing as datetime (with or without timezone)
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.date().isoformat()
            except (ValueError, AttributeError):
                try:
                    # Try parsing as date
                    d = datetime.strptime(value, "%Y-%m-%d")
                    return d.date().isoformat()
                except ValueError:
                    return None

        return None
    
    def _normalize_datetime(self, value: Any) -> Optional[str]:
        """
        Normalize datetime to ISO datetime string.
        
        Args:
            value: Datetime value
        
        Returns:
            ISO datetime string or None
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            # Already ISO format
            if "T" in value or " " in value:
                return value
            # Date only - convert to datetime
            try:
                d = datetime.strptime(value, "%Y-%m-%d")
                return d.isoformat()
            except ValueError:
                return value
        
        if isinstance(value, datetime):
            return value.isoformat()
        
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time()).isoformat()
        
        return None
    
    def _normalize_media_ref(self, media: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize media reference.
        
        Args:
            media: Media reference dict
        
        Returns:
            Normalized media reference
        """
        normalized = media.copy()
        
        # Ensure required fields
        required_fields = ["storage_path", "file_name", "mime_type", "file_size"]
        for field in required_fields:
            if field not in normalized:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure file_size is int
        if "file_size" in normalized:
            try:
                normalized["file_size"] = int(normalized["file_size"])
            except (ValueError, TypeError):
                raise ValueError("file_size must be an integer")
        
        return normalized
    
    def _sanitize_string(self, value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum length (truncate if exceeded)
        
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove control characters
        value = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)
        
        # Strip whitespace
        value = value.strip()
        
        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value

