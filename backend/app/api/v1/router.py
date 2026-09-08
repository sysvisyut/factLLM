from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    documents,
    facts,
    relationships,
    issues,
    analytics
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(facts.router)
api_router.include_router(relationships.router)
api_router.include_router(issues.router)
api_router.include_router(analytics.router)
