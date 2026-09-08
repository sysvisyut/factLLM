import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
from app.core.logging import logger
from app.models import Base

# Determine connect_args based on DB dialect
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    try:
        # If postgres, attempt to enable pgvector extension if available
        if engine.dialect.name == "postgresql":
            with engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                except Exception as ext_err:
                    logger.warning(f"Could not enable pgvector extension (might already exist or insufficient privileges): {ext_err}")
                    conn.rollback()

        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables initialized successfully on {engine.dialect.name}.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}", exc_info=True)
        raise e


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict:
    """Verifies that the database connection is alive and healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "dialect": engine.dialect.name,
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
