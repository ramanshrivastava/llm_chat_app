from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings with proper validation."""
    
    # API Configuration
    LLM_API_KEY: str = Field(..., description="API key for LLM provider")
    LLM_API_ENDPOINT: str = Field(default="https://api.openai.com/v1", description="LLM API endpoint")
    LLM_MODEL: str = Field(default="gpt-4", description="Default LLM model")
    LLM_PROVIDER: str = Field(default="openai", description="LLM provider (openai, anthropic, gemini)")
    
    # Application Settings
    APP_ENV: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    PORT: int = Field(default=8000, description="Server port", ge=1, le=65535)
    HOST: str = Field(default="0.0.0.0", description="Server host")
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for security features")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expiration time", ge=1)
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"], description="Allowed CORS origins")
    API_REQUEST_TIMEOUT: int = Field(default=60, description="API request timeout in seconds", ge=1)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per minute", ge=1)
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds", ge=1)
    
    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, description="Database URL")
    
    @validator('LLM_PROVIDER')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'anthropic', 'gemini']
        if v.lower() not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v.lower()
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('LLM_API_KEY')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('LLM_API_KEY must be provided and at least 10 characters long')
        return v.strip()
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if not v or len(v.strip()) < 32:
            raise ValueError('SECRET_KEY must be provided and at least 32 characters long')
        return v.strip()

    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True

# Create a global settings object
settings = Settings() 