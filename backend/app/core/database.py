from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine import Engine
from loguru import logger

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_extensions(engine: Engine) -> None:
    """Initialize database extensions (pgvector). Safe to call repeatedly."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception as exc:
        logger.warning(f"Skipping extension init: {exc}")