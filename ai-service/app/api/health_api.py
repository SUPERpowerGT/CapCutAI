from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_llm_settings

router = APIRouter(prefix="/internal", tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_llm_settings()
    return {
        "service": "capcutai-ai-service",
        "status": "UP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "llm": {
            "provider": settings.provider,
            "model": settings.model,
            "mode": settings.mode,
            "configured": settings.configured,
        },
    }
