from functools import lru_cache
import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    app_name: str = "Enterprise RAG Assistant"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./rag_backend.db"

    secret_key: str = "change-me-for-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    chunk_size: int = 1200
    chunk_overlap: int = 150
    max_sources: int = 5
    min_retrieval_score: float = 0.08


@lru_cache
def get_settings() -> Settings:
    cors_origins = os.getenv("CORS_ORIGINS")
    return Settings(
        database_url=os.getenv("DATABASE_URL", Settings().database_url),
        secret_key=os.getenv("SECRET_KEY", Settings().secret_key),
        algorithm=os.getenv("ALGORITHM", Settings().algorithm),
        access_token_expire_minutes=int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", Settings().access_token_expire_minutes)
        ),
        cors_origins=cors_origins.split(",") if cors_origins else Settings().cors_origins,
    )
