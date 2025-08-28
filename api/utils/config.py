"""Configuration management for the AI Voice Policy Assistant."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+psycopg://user:pass@postgres:5432/proxi"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # JWT Authentication
    jwt_secret: str = Field(default="your-super-secret-jwt-key-change-in-production", description="JWT secret key for token signing")
    jwt_expires_in: int = 3600
    jwt_refresh_expires_in: int = 86400
    
    # Mock Mode Configuration
    mock_mode: bool = Field(default=False, description="Enable mock mode for development/testing")
    mock_ai_responses: bool = Field(default=False, description="Use mock AI responses instead of real API calls")
    mock_document_processing: bool = Field(default=False, description="Use mock document processing for testing")
    
    # OpenAI/LLM Configuration
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    openai_timeout: int = 30
    
    # Embedding Model
    embed_model: str = "all-MiniLM-L6-v2"  # Compatible with sentence-transformers
    embed_dims: int = 384  # Dimension for all-MiniLM-L6-v2
    embed_batch_size: int = 32
    
    # Speech-to-Text
    stt_provider: str = "whisper"  # "whisper" or "gcp"
    gcp_project_id: Optional[str] = None
    gcp_credentials_path: Optional[str] = None
    
    # Rate Limiting
    default_rpm: int = 60
    default_burst: int = 10
    
    # Caching
    response_cache_ttl: int = 86400  # 24 hours
    search_cache_ttl: int = 3600     # 1 hour
    
    # Monitoring
    prometheus_port: int = 9090
    grafana_port: int = 3000
    
    # Feature Flags
    enable_tts: bool = False
    enable_fallback_llm: bool = True
    enable_circuit_breaker: bool = True
    
    # Development
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL with fallback to default."""
    return os.getenv("DATABASE_URL", settings.database_url)


def get_redis_url() -> str:
    """Get Redis URL with fallback to default."""
    return os.getenv("REDIS_URL", settings.redis_url)


def get_openai_config() -> dict:
    """Get OpenAI configuration."""
    return {
        "base_url": settings.openai_base_url,
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "max_tokens": settings.openai_max_tokens,
        "timeout": settings.openai_timeout,
    }
