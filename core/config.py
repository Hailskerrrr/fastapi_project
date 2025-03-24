from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "URL Shortener"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if v == "your-secret-key-here":
            raise ValueError("Please set a secure SECRET_KEY in your environment variables")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
