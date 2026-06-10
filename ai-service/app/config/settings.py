import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class LlmSettings:
    provider: str
    model: str
    api_key: str
    base_url: str
    configured: bool
    mode: str


def _resolve_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower()


def _resolve_model(provider: str) -> str:
    if provider == "ai4video_vl":
        return os.getenv("AI4VIDEO_VL_MODEL") or os.getenv("LLM_MODEL") or "Qwen/Qwen3-VL-8B-Instruct"
    if provider == "gemini":
        return (
            os.getenv("GEMINI_MODEL")
            or os.getenv("LLM_MODEL")
            or "gemini-2.0-flash"
        )
    if provider == "openrouter":
        return os.getenv("OPENROUTER_MODEL") or os.getenv("LLM_MODEL") or "openrouter/auto"
    if provider == "groq":
        return os.getenv("GROQ_MODEL") or os.getenv("LLM_MODEL") or "llama-3.1-8b-instant"
    if provider == "ollama":
        return os.getenv("OLLAMA_MODEL") or os.getenv("LLM_MODEL") or "qwen2.5:7b"
    return os.getenv("LLM_MODEL") or ""


def _resolve_api_key(provider: str) -> str:
    if provider == "ai4video_vl":
        return os.getenv("AI4VIDEO_VL_API_KEY") or os.getenv("LLM_API_KEY") or _resolve_ai4video_config_key("vl")
    if provider == "gemini":
        return (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        )
    if provider == "openrouter":
        return os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or ""
    if provider == "groq":
        return os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY") or ""
    if provider == "ollama":
        return ""
    return ""


def _resolve_ai4video_config_key(key_name: str) -> str:
    try:
        repo_root = Path(os.getenv("CAPCUTAI_REPO_ROOT") or Path(__file__).resolve().parents[3])
        ai4video_root = repo_root / "AI4Video"
        if str(ai4video_root) not in sys.path:
            sys.path.insert(0, str(ai4video_root))
        from pipeline_api.config import API_KEYS

        value = API_KEYS.get(key_name, "")
        if value and not value.startswith("<"):
            return value
    except Exception:
        return ""
    return ""


def _resolve_base_url(provider: str) -> str:
    if provider == "ai4video_vl":
        return os.getenv("AI4VIDEO_API_BASE_URL") or "https://api.302.ai/v1/chat/completions"
    if provider == "openrouter":
        return os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
    if provider == "groq":
        return os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
    if provider == "ollama":
        return os.getenv("OLLAMA_BASE_URL") or "http://host.docker.internal:11434/v1"
    return ""


@lru_cache(maxsize=1)
def get_llm_settings() -> LlmSettings:
    provider = _resolve_provider()
    api_key = _resolve_api_key(provider)
    configured = (
        bool(api_key)
        if provider in {"ai4video_vl", "gemini", "openrouter", "groq"}
        else bool(_resolve_model(provider)) and bool(_resolve_base_url(provider))
    )
    mode = "local" if provider == "ollama" and configured else "live" if configured else "error"
    return LlmSettings(
        provider=provider,
        model=_resolve_model(provider),
        api_key=api_key,
        base_url=_resolve_base_url(provider),
        configured=configured,
        mode=mode,
    )
