"""
Response transformation utilities.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


class ResponseTransformer:
    """Transform backend responses to frontend format."""
    
    def transform_memory_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform memory response.
        
        Args:
            data: Backend response data
        
        Returns:
            Transformed data for frontend
        """
        transformed = data.copy()
        
        # Ensure all UUIDs are strings
        for field in ["id", "user_id", "family_unit_id", "modified_by"]:
            if field in transformed and transformed[field]:
                transformed[field] = str(transformed[field])
        
        # Ensure media list is properly formatted
        if "media" in transformed and isinstance(transformed["media"], list):
            transformed["media"] = [
                self._transform_media_item(media) for media in transformed["media"]
            ]
        
        # Ensure tags is a list
        if "tags" not in transformed:
            transformed["tags"] = []
        elif not isinstance(transformed["tags"], list):
            transformed["tags"] = []
        
        return transformed
    
    def transform_feed_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform feed response.
        
        Args:
            data: Backend response data
        
        Returns:
            Transformed data for frontend
        """
        transformed = data.copy()
        
        # Transform items
        if "items" in transformed and isinstance(transformed["items"], list):
            transformed["items"] = [
                self._transform_feed_item(item) for item in transformed["items"]
            ]
        
        # Ensure pagination structure
        if "pagination" not in transformed:
            transformed["pagination"] = {}
        
        pagination = transformed["pagination"]
        
        # Calculate total_pages if not present
        if "total_pages" not in pagination:
            page = pagination.get("page", 1)
            page_size = pagination.get("page_size", 20)
            total_count = transformed.get("total_count", 0)
            if total_count and page_size:
                pagination["total_pages"] = (total_count + page_size - 1) // page_size
            else:
                pagination["total_pages"] = 0
        
        # Ensure has_more
        if "has_more" not in transformed:
            page = pagination.get("page", 1)
            total_pages = pagination.get("total_pages", 0)
            transformed["has_more"] = page < total_pages
        
        return transformed
    
    def transform_auth_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform authentication response.
        
        Args:
            data: Backend response data
        
        Returns:
            Transformed data for frontend
        """
        transformed = data.copy()
        
        # Ensure UUIDs are strings
        for field in ["user_id", "family_unit_id"]:
            if field in transformed and transformed[field]:
                transformed[field] = str(transformed[field])
        
        # Ensure tokens structure
        if "tokens" in transformed:
            tokens = transformed["tokens"]
            if isinstance(tokens, dict):
                # Ensure token_type is present
                if "token_type" not in tokens:
                    tokens["token_type"] = "bearer"
        
        return transformed
    
    def transform_invite_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform invitation response.
        
        Args:
            data: Backend response data
        
        Returns:
            Transformed data for frontend
        """
        transformed = data.copy()
        
        # Ensure UUIDs are strings
        if "id" in transformed:
            transformed["id"] = str(transformed["id"])
        
        # Ensure dates are ISO strings
        for date_field in ["expires_at", "created_at"]:
            if date_field in transformed and transformed[date_field]:
                transformed[date_field] = self._normalize_datetime_string(
                    transformed[date_field]
                )
        
        return transformed
    
    def transform_list_response(
        self, data: List[Dict[str, Any]], item_transformer=None
    ) -> List[Dict[str, Any]]:
        """
        Transform list response.
        
        Args:
            data: List of items from backend
            item_transformer: Optional function to transform each item
        
        Returns:
            Transformed list
        """
        if item_transformer:
            return [item_transformer(item) for item in data]
        return data
    
    def _transform_feed_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single feed item."""
        transformed = item.copy()
        
        # Ensure UUIDs are strings
        for field in ["id", "user_id", "family_unit_id"]:
            if field in transformed and transformed[field]:
                transformed[field] = str(transformed[field])
        
        # Ensure media_urls is present (for backward compatibility)
        if "media" in transformed and isinstance(transformed["media"], list):
            # Extract URLs if available
            media_urls = []
            for media in transformed["media"]:
                if isinstance(media, dict):
                    # Try to get URL from various possible fields
                    url = (
                        media.get("url")
                        or media.get("access_url")
                        or media.get("storage_path")
                    )
                    if url:
                        media_urls.append(url)
            transformed["media_urls"] = media_urls
        
        # Ensure counts are integers
        for count_field in ["reaction_count", "comment_count"]:
            if count_field in transformed:
                try:
                    transformed[count_field] = int(transformed[count_field])
                except (ValueError, TypeError):
                    transformed[count_field] = 0
        
        # Ensure reactions_by_emoji is a dict
        if "reactions_by_emoji" not in transformed:
            transformed["reactions_by_emoji"] = {}
        
        # Ensure user_reactions is a list
        if "user_reactions" not in transformed:
            transformed["user_reactions"] = []
        
        # Ensure top_comments is a list
        if "top_comments" not in transformed:
            transformed["top_comments"] = []
        
        return transformed
    
    def _transform_media_item(self, media: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single media item."""
        transformed = media.copy()
        
        # Ensure UUIDs are strings
        for field in ["id", "memory_id"]:
            if field in transformed and transformed[field]:
                transformed[field] = str(transformed[field])
        
        # Ensure numeric fields are proper types
        for field in ["file_size", "width", "height", "duration"]:
            if field in transformed and transformed[field] is not None:
                try:
                    transformed[field] = int(transformed[field])
                except (ValueError, TypeError):
                    transformed[field] = None
        
        return transformed
    
    def _normalize_datetime_string(self, value: Any) -> str:
        """
        Normalize datetime to ISO string.
        
        Args:
            value: Datetime value (string, datetime, or None)
        
        Returns:
            ISO datetime string
        """
        if value is None:
            return ""
        
        if isinstance(value, str):
            return value
        
        if isinstance(value, datetime):
            return value.isoformat()
        
        return str(value)

