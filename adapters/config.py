"""
Adapter configuration and settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class AdapterConfig(BaseSettings):
    """Adapter configuration from environment variables."""
    
    # Adapter version
    adapter_version: str = "v1"
    
    # Backend API configuration
    # When adapter runs in same process, use localhost for internal routing
    # Set BACKEND_API_BASE_URL environment variable to override
    backend_api_base_url: str = os.getenv(
        "BACKEND_API_BASE_URL",
        "http://localhost:8000"
    )
    backend_api_version: str = os.getenv("API_VERSION", "v1")
    
    # Request/response settings
    request_timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 1.0
    
    # Logging configuration
    log_requests: bool = True
    log_responses: bool = True
    log_errors: bool = True
    log_level: str = "INFO"
    
    # Validation settings
    strict_validation: bool = True
    sanitize_inputs: bool = True
    sanitize_outputs: bool = True
    
    # Error handling
    expose_internal_errors: bool = False
    default_error_message: str = "An error occurred processing your request"
    
    @property
    def backend_api_url(self) -> str:
        """Get full backend API URL."""
        return f"{self.backend_api_base_url}/api/{self.backend_api_version}"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Global config instance
_adapter_config: Optional[AdapterConfig] = None


def get_adapter_config() -> AdapterConfig:
    """Get or create adapter configuration instance."""
    global _adapter_config
    if _adapter_config is None:
        _adapter_config = AdapterConfig()
    return _adapter_config

