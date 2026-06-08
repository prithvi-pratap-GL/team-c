from functools import lru_cache
import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):

    app_name: str = "Enterprise RAG Assistant"

    api_prefix: str = os.getenv("API_PREFIX")

    database_url: str = os.getenv("DATABASE_URL")

    secret_key: str = os.getenv("SECRET_KEY")

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: List[str] = [os.getenv("FRONTEND_URL1"),
        os.getenv("FRONTEND_URL2")        
    ]

    chunk_size: int = 1200
    chunk_overlap: int = 150
    max_sources: int = 5
    min_retrieval_score: float = 0.08

    # AI Model Configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL")
    embedding_dimension: int = 768
    reranker_model: str = os.getenv("RERANKER_MODEL")
    llm_model: str = os.getenv("LLM_MODEL")

    # Confidence Scoring Thresholds (calibrated for MS MARCO cross-encoder)
    # Reranker scores typically range from -5 to +5
    confidence_high_threshold: float = 3.0      # Highly relevant
    confidence_medium_threshold: float = 1.0    # Partially relevant
    confidence_low_threshold: float = -1.0      # Weakly relevant

    # Vector-only fallback thresholds (when reranking disabled)
    confidence_high_threshold_vector: float = 0.70  # Top 5-10% of embedding space
    confidence_medium_threshold_vector: float = 0.55 # In neighborhood


@lru_cache
def get_settings() -> Settings:
    cors_origins = os.getenv("CORS_ORIGINS")
    defaults = Settings()
    return Settings(
        database_url=os.getenv("DATABASE_URL", defaults.database_url),
        secret_key=os.getenv("SECRET_KEY", defaults.secret_key),
        algorithm=os.getenv("ALGORITHM", defaults.algorithm),
        access_token_expire_minutes=int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", defaults.access_token_expire_minutes)
        ),
        cors_origins=cors_origins.split(",") if cors_origins else defaults.cors_origins,
        embedding_model=os.getenv("EMBEDDING_MODEL", defaults.embedding_model),
        embedding_dimension=int(
            os.getenv("EMBEDDING_DIMENSION", defaults.embedding_dimension)
        ),
        reranker_model=os.getenv("RERANKER_MODEL", defaults.reranker_model),
        llm_model=os.getenv("LLM_MODEL", defaults.llm_model),
        confidence_high_threshold=float(
            os.getenv("CONFIDENCE_HIGH_THRESHOLD", defaults.confidence_high_threshold)
        ),
        confidence_medium_threshold=float(
            os.getenv("CONFIDENCE_MEDIUM_THRESHOLD", defaults.confidence_medium_threshold)
        ),
        confidence_low_threshold=float(
            os.getenv("CONFIDENCE_LOW_THRESHOLD", defaults.confidence_low_threshold)
        ),
        confidence_high_threshold_vector=float(
            os.getenv("CONFIDENCE_HIGH_THRESHOLD_VECTOR", defaults.confidence_high_threshold_vector)
        ),
        confidence_medium_threshold_vector=float(
            os.getenv("CONFIDENCE_MEDIUM_THRESHOLD_VECTOR", defaults.confidence_medium_threshold_vector)
        ),
    )
