import logging

from fastapi import FastAPI

from app.api.health_api import router as health_router
from app.api.internal_agent_api import router as agent_router
from app.config import get_llm_settings


logger = logging.getLogger(__name__)


app = FastAPI(
    title="CapCutAI AI Service",
    version="0.1.0",
    description="Scaffold AI service for IM conversation reply generation."
)

app.include_router(health_router)
app.include_router(agent_router)


@app.on_event("startup")
def log_startup_config() -> None:
    settings = get_llm_settings()
    logger.warning(
        "ai-service llm config: provider=%s model=%s mode=%s configured=%s",
        settings.provider,
        settings.model,
        settings.mode,
        settings.configured,
    )
