"""
Configuration Management
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Sherlocke Homes"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API Keys - Keywords AI Gateway (Required for Hackathon)
    # Updated to match Joseph's naming convention
    KEYWORDS_API_KEY: Optional[str] = None  # Your Keywords AI API key (Joseph's framework)

    # Perplexity API for profile analysis (Joseph's profile_analyzer.py)
    PERPLEXITY_API_KEY: Optional[str] = None

    # AI Model Configuration
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7

    # Compliance
    FANNIE_MAE_GUIDE_PATH: str = "../Fannie Mae December 10, 2025 Selling Guide.pdf"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = "../.env"  # Look in project root
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


settings = Settings()
