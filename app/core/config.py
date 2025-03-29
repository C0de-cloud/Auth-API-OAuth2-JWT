import os
from datetime import timedelta
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Auth API"
    API_PREFIX: str = "/api"
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt-please-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MongoDB Settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "auth_db")
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    
    # Security Settings
    PASSWORD_HASH_ROUNDS: int = 12
    
    class Config:
        env_file = ".env"


settings = Settings()


def get_token_expire_time(minutes: Optional[int] = None) -> timedelta:
    """Returns the token expiration time."""
    if minutes is None:
        minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    return timedelta(minutes=minutes) 