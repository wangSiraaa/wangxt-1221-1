from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "矿山尾矿库安全监测系统"
    DEBUG: bool = True

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_NAME: str = "tailings_monitor"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
