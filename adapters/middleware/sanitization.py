"""
Input/output sanitization utilities.
"""

import re
import html
from typing import Any, Dict, List, Optional


class Sanitizer:
    """Sanitize inputs and outputs."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum length
        
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
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """
        Sanitize dictionary recursively.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
        
        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            sanitized_key = Sanitizer.sanitize_string(str(key))
            
            # Sanitize value
            if isinstance(value, str):
                sanitized[sanitized_key] = Sanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[sanitized_key] = Sanitizer.sanitize_dict(
                    value, max_depth - 1
                )
            elif isinstance(value, list):
                sanitized[sanitized_key] = Sanitizer.sanitize_list(
                    value, max_depth - 1
                )
            else:
                # Keep other types as-is (numbers, booleans, None)
                sanitized[sanitized_key] = value
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any], max_depth: int = 10) -> List[Any]:
        """
        Sanitize list recursively.
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
        
        Returns:
            Sanitized list
        """
        if max_depth <= 0:
            return []
        
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(Sanitizer.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(Sanitizer.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(Sanitizer.sanitize_list(item, max_depth - 1))
            else:
                sanitized.append(item)
        
        return sanitized
    
    @staticmethod
    def escape_html(value: str) -> str:
        """
        Escape HTML entities.
        
        Args:
            value: String to escape
        
        Returns:
            Escaped string
        """
        return html.escape(value)
    
    @staticmethod
    def remove_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from dictionary.
        
        Args:
            data: Dictionary to clean
        
        Returns:
            Dictionary with sensitive fields removed
        """
        sensitive_fields = {
            "password",
            "token",
            "access_token",
            "refresh_token",
            "secret",
            "api_key",
            "authorization",
        }
        
        cleaned = data.copy()
        
        for key in list(cleaned.keys()):
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                cleaned[key] = "[REDACTED]"
            elif isinstance(cleaned[key], dict):
                cleaned[key] = Sanitizer.remove_sensitive_data(cleaned[key])
            elif isinstance(cleaned[key], list):
                cleaned[key] = [
                    Sanitizer.remove_sensitive_data(item) if isinstance(item, dict) else item
                    for item in cleaned[key]
                ]
        
        return cleaned

