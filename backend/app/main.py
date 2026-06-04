from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.db_models import SessionLocal, create_tables
from app.models.schemas import HealthResponse
from app.routers import auth, chat, feedback, ingest
from app.services.auth_service import seed_demo_users


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


@app.on_event("startup")
def startup() -> None:
    create_tables()
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()


@app.get("/", response_model=HealthResponse)
def root():
    return {"message": "Backend Running", "timestamp": datetime.utcnow()}
