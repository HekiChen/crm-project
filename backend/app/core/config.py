"""
Application configuration using Pydantic Settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields for flexibility
    )
    
    # Application
    app_name: str = "CRM Backend API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment: development, testing, production")
    
    # API
    api_v1_str: str = "/api/v1"
    
    # Security
    secret_key: str = Field(description="Secret key for JWT token signing")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    
    # Database
    database_url: str = Field(description="PostgreSQL database URL")
    
    # Redis (optional for local development)
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching and Celery")
    
    # Celery (optional for local development)
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL")
    celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend URL")
    
    # CORS
    backend_cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Additional local development settings
    jwt_secret_key: Optional[str] = Field(default=None, description="Alternative JWT secret key field")
    jwt_algorithm: Optional[str] = Field(default=None, description="Alternative JWT algorithm field")
    log_level: str = Field(default="INFO", description="Logging level")
    reload: bool = Field(default=False, description="Enable auto-reload for development")


# Global settings instance
settings = Settings()