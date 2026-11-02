from fastapi import APIRouter, Depends

from app.api.deps import get_app_container
from app.core.config import get_settings
from app.db.session import ping_database
from app.services.container import Container

router = APIRouter(tags=["health"])


@router.get("/health")
def health(c: Container = Depends(get_app_container)):
    settings = get_settings()
    db_ok = ping_database()
    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "ok" if db_ok else "unavailable",
        "ai_provider": c.ai.primary.name,
        "ai_fallback": c.ai.fallback.name if c.ai.fallback else None,
        "embedding_provider": c.embeddings.provider_name,
        "vector_store": c.vector_store.name,
    }
