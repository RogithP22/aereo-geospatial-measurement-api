import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aereo Geospatial Measurement API"
    API_V1_STR: str = "/api"
    
    # Database configuration (PostgreSQL / SQLite fallback)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aereo_geospatial.db")
    
    # File upload paths & limits
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 25  # 25 MB safety limit

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)