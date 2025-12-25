"""
Application configuration from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str  # JWT secret for validating Supabase tokens
    supabase_db_url: Optional[str] = None  # Transaction pooler URL for LangGraph
    supabase_db_password: Optional[str] = None  # Database password
    supabase_jwt_secret: Optional[str] = None
    supabase_access_token: Optional[str] = None
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    
    # Application Configuration
    environment: str = "development"
    debug: str = "false"
    api_version: str = "v1"
    
    # CORS Configuration (comma-separated string)
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Media Processing Configuration
    media_max_file_size_mb: int = 50
    media_max_memory_size_mb: int = 200
    media_thumbnail_size: int = 400
    media_upload_url_expires_seconds: int = 300  # 5 minutes
    media_access_url_expires_seconds: int = 3600  # 1 hour
    
    # Storage Configuration
    storage_bucket_name: str = "memories"
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug.lower() == "true"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra environment variables not defined in the model
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

