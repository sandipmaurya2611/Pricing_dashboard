from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./pricing.db"

    # JWT
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AI
    GROQ_API_KEY: str = ""

    # App
    APP_NAME: str = "Pricing Intelligence Dashboard"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1"
    ]

    # Mock E-Commerce
    MOCK_ECOMMERCE_FAILURE_RATE: float = 0.2

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

def get_llm_client():
    from openai import AsyncOpenAI
    
    return AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    ), "llama-3.3-70b-versatile"
