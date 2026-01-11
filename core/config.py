import os
from typing import Optional

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./whatsapp_platform.db")
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "WhatsApp Platform API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "WhatsApp automation and messaging platform"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000",
    ]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    # WhatsApp
    WHATSAPP_API_URL: Optional[str] = os.getenv("WHATSAPP_API_URL")
    WHATSAPP_WEBHOOK_URL: Optional[str] = os.getenv("WHATSAPP_WEBHOOK_URL")
    
    # Redis (for caching and sessions)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"

settings = Settings()
