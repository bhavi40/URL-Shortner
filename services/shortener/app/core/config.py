from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # App
    BASE_URL: str = "http://localhost:8002"
    APP_NAME: str = "Shortener Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Short code
    SHORT_CODE_LENGTH: int = 6
    MAX_RETRIES_SHORT_CODE: int = 5
    
    # Plan limits
    FREE_PLAN_MAX_LINKS: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()