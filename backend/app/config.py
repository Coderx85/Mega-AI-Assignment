from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./face_detection.db"
    model_config = {"env_prefix": "APP_", "env_file": ".env"}

settings = Settings()
