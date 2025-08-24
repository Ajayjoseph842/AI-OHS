from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import Base, engine, init_extensions
from app.api.v1.auth import router as auth_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.training import router as training_router
from app.api.v1.export import router as export_router

app = FastAPI(title="Hazero API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting Hazero API...")
    # Create tables (simple for MVP; replace with Alembic in production)
    Base.metadata.create_all(bind=engine)
    # Ensure extensions
    init_extensions(engine)

# Mount versioned API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chatbot_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")

@app.get("/healthz")
def healthcheck() -> dict:
    return {"status": "ok"}