import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import get_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure storage directory exists
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_DIR, "uploads"), exist_ok=True)
    
    # Initialize Database Tables
    logger.info("Initializing FACTMESH database tables...")
    init_db()
    logger.info("FACTMESH application ready.")
    
    yield
    
    # Shutdown
    logger.info("FACTMESH application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root health endpoint for convenience
app.add_api_route("/health", get_health, methods=["GET"], tags=["Health"])

# Include v1 API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
