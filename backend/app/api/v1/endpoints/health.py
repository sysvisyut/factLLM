import os
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Health check endpoint exposing DB connectivity, storage status, and LLM configuration."""
    db_status = check_db_connection()
    storage_exists = os.path.exists(settings.STORAGE_DIR)
    
    return HealthResponse(
        status="ok" if db_status.get("status") == "healthy" else "degraded",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        storage={
            "path": settings.STORAGE_DIR,
            "available": storage_exists,
            "writable": os.access(settings.STORAGE_DIR, os.W_OK) if storage_exists else False
        }
    )
