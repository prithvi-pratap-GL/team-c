import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.db_models import SessionLocal, create_tables
from app.models.schemas import HealthResponse
from app.routers import auth, chat, feedback, ingest
from app.routers import users, admin
from app.services.auth_service import seed_demo_users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(ingest.router, prefix=settings.api_prefix)
app.include_router(feedback.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.on_event("startup")
def startup() -> None:
    create_tables()
    db = SessionLocal()
    try:
        seed_demo_users(db)
        _seed_demo_departments(db)
    finally:
        db.close()

    from app.rag.ingestion.qdrant_client_manager import QdrantClientManager
    qdrant_manager = QdrantClientManager()
    qdrant_manager.create_collection()
    logger.info("Qdrant collection and indexes initialized")


def _seed_demo_departments(db) -> None:
    from app.models import db_models

    default_departments = [
        {"name": "engineering", "description": "Engineering & Development"},
        {"name": "hr", "description": "Human Resources"},
        {"name": "operations", "description": "Operations"},
        {"name": "product_support", "description": "Product Support"},
    ]
    for dept_data in default_departments:
        existing = db.query(db_models.Department).filter(
            db_models.Department.name == dept_data["name"]
        ).first()
        if not existing:
            db.add(db_models.Department(**dept_data, is_active=True))
    db.commit()


@app.get("/", response_model=HealthResponse)
def root():
    return {"message": "Backend Running", "timestamp": datetime.utcnow()}
