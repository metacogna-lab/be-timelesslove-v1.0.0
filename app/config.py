"""
Application configuration from environment variables.

Supports multi-provider AI configuration with model selection by complexity:
- simple: Fast, cheap tasks (tag extraction, classification)
- standard: Balanced tasks (summarization, analysis)
- complex: High-quality reasoning (narrative generation, insights)
"""

import os
import sys
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import ValidationError, field_validator
from dotenv import load_dotenv

# Determine environment and load appropriate .env file
env = os.getenv("ENVIRONMENT", "development")

# Load environment-specific .env file if it exists
env_file_map = {
    "production": ".env.production",
    "staging": ".env.staging",
    "test": ".env.test",
    "development": ".env.local",
}

env_file = env_file_map.get(env, ".env")

# Try to load environment-specific file, fallback to .env
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to .env if specific file doesn't exist
    load_dotenv(".env", override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    supabase_db_url: Optional[str] = None
    supabase_db_password: Optional[str] = None
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

    # Data directory path for persistent storage
    # Development (local): ./data
    # Production (server): /data/timeless-love-data
    data_directory_path: str = "./data"
    
    # CORS Configuration
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,timelesslove.ai")
    
    # Media Processing Configuration
    media_max_file_size_mb: int = 50
    media_max_memory_size_mb: int = 200
    media_thumbnail_size: int = 400
    media_upload_url_expires_seconds: int = 300
    media_access_url_expires_seconds: int = 3600
    
    # Storage Configuration
    storage_bucket_name: str = "memories"

    # Cloudflare Tunnel
    cloudflare_tunnel_token: Optional[str] = None
    cloudflare_tunnel_id: Optional[str] = None

    # ============================================
    # AI/Intelligence Layer Configuration
    # ============================================
    # Provider selection: openai, anthropic, gemini
    intelligence_primary_provider: str = "openai"
    intelligence_fallback_provider: str = "gemini"

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_org_id: Optional[str] = None
    openai_model_simple: str = "gpt-4o-mini"
    openai_model_standard: str = "gpt-4o"
    openai_model_complex: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model_simple: str = "claude-3-5-haiku-latest"
    anthropic_model_standard: str = "claude-sonnet-4-20250514"
    anthropic_model_complex: str = "claude-opus-4-20250514"

    # Google Gemini Configuration
    gemini_api_key: Optional[str] = None
    gemini_model_simple: str = "gemini-2.0-flash-lite"
    gemini_model_standard: str = "gemini-2.0-flash"
    gemini_model_complex: str = "gemini-2.5-pro-preview-06-05"
    gemini_embedding_model: str = "text-embedding-004"

    # Intelligence Processing Configuration
    intelligence_redis_url: Optional[str] = None
    intelligence_cache_enabled: bool = True
    intelligence_cache_ttl_hours: int = 24
    intelligence_async_processing: bool = True
    intelligence_job_queue_size: int = 100
    intelligence_max_concurrent_jobs: int = 5

    # Rate limiting (requests per minute)
    intelligence_rate_limit_openai: int = 60
    intelligence_rate_limit_anthropic: int = 50
    intelligence_rate_limit_gemini: int = 60

    # Token limits by complexity
    intelligence_max_tokens_simple: int = 500
    intelligence_max_tokens_standard: int = 2000
    intelligence_max_tokens_complex: int = 4000

    # Feature Flags
    intelligence_tag_extraction_enabled: bool = True
    intelligence_feed_ranking_enabled: bool = True
    intelligence_media_intelligence_enabled: bool = True
    intelligence_content_moderation_enabled: bool = True
    intelligence_family_insights_enabled: bool = True

    # Vector Search
    vector_index: str = "timelesslove-embeddings"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug.lower() == "true"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_model(
        self,
        complexity: Literal["simple", "standard", "complex"] = "standard",
        provider: Optional[str] = None
    ) -> str:
        """
        Get the appropriate model for a given complexity level and provider.

        Args:
            complexity: Task complexity - simple, standard, or complex
            provider: AI provider - openai, anthropic, or gemini.
                     Defaults to intelligence_primary_provider.

        Returns:
            Model identifier string for the specified provider and complexity.
        """
        provider = provider or self.intelligence_primary_provider

        model_map = {
            "openai": {
                "simple": self.openai_model_simple,
                "standard": self.openai_model_standard,
                "complex": self.openai_model_complex,
            },
            "anthropic": {
                "simple": self.anthropic_model_simple,
                "standard": self.anthropic_model_standard,
                "complex": self.anthropic_model_complex,
            },
            "gemini": {
                "simple": self.gemini_model_simple,
                "standard": self.gemini_model_standard,
                "complex": self.gemini_model_complex,
            },
        }

        if provider not in model_map:
            raise ValueError(f"Unknown provider: {provider}. Use openai, anthropic, or gemini.")

        return model_map[provider].get(complexity, model_map[provider]["standard"])

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """
        Get the API key for a given provider.

        Args:
            provider: AI provider - openai, anthropic, or gemini.
                     Defaults to intelligence_primary_provider.

        Returns:
            API key string or None if not configured.
        """
        provider = provider or self.intelligence_primary_provider

        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
        }

        return key_map.get(provider)

    def get_max_tokens(self, complexity: Literal["simple", "standard", "complex"] = "standard") -> int:
        """Get max tokens for a given complexity level."""
        token_map = {
            "simple": self.intelligence_max_tokens_simple,
            "standard": self.intelligence_max_tokens_standard,
            "complex": self.intelligence_max_tokens_complex,
        }
        return token_map.get(complexity, self.intelligence_max_tokens_standard)

    def get_embedding_model(self, provider: Optional[str] = None) -> str:
        """Get the embedding model for a given provider."""
        provider = provider or self.intelligence_primary_provider

        embedding_map = {
            "openai": self.openai_embedding_model,
            "gemini": self.gemini_embedding_model,
            # Anthropic doesn't have embeddings, fallback to OpenAI
            "anthropic": self.openai_embedding_model,
        }

        return embedding_map.get(provider, self.openai_embedding_model)

    @property
    def has_intelligence_provider(self) -> bool:
        """Check if at least one AI provider is configured."""
        return bool(
            self.openai_api_key or
            self.anthropic_api_key or
            self.gemini_api_key
        )

    model_config = {
        "env_file": ".env",  # Pydantic will also check this
        "case_sensitive": False,
        "extra": "ignore",
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except ValidationError as e:
            # Extract missing required fields
            missing_fields = []
            for error in e.errors():
                if error["type"] == "missing":
                    field_name = error.get("loc", ["unknown"])[-1]
                    missing_fields.append(field_name.upper())
            
            if missing_fields:
                env_file = env_file_map.get(os.getenv("ENVIRONMENT", "development"), ".env")
                error_msg = (
                    f"\n❌ Missing required environment variables:\n"
                    f"   {', '.join(missing_fields)}\n\n"
                    f"💡 To fix this:\n"
                    f"   1. Create a {env_file} file in the backend directory\n"
                    f"   2. Add the missing variables (see .env.local.example for reference)\n"
                    f"   3. Or set them as environment variables\n\n"
                    f"📝 Required variables:\n"
                )
                required_vars = [
                    "SUPABASE_URL",
                    "SUPABASE_ANON_KEY", 
                    "SUPABASE_SERVICE_ROLE_KEY",
                    "SUPABASE_JWT_SECRET",
                    "JWT_SECRET_KEY"
                ]
                for var in required_vars:
                    error_msg += f"   - {var}\n"
                error_msg += f"\nSee docs/ENV_MANAGEMENT.md for more information.\n"
                print(error_msg, file=sys.stderr)
            raise
    return _settings