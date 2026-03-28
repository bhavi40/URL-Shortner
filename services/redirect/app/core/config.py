from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database — read only access to urlshortener
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour cache TTL

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "127.0.0.1:9092"
    KAFKA_TOPIC_CLICKS: str = "click-events"

    # App
    BASE_URL: str = "http://localhost:8003"
    APP_NAME: str = "Redirect Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()