from app.config import LlmSettings
from app.providers.gemini_provider import generate_gemini_reply
from app.providers.openai_compatible_provider import generate_openai_compatible_reply


def generate_llm_reply(settings: LlmSettings, prompt: str) -> tuple[str, str]:
    if settings.provider == "gemini":
        return generate_gemini_reply(settings, prompt)
    if settings.provider in {"openrouter", "groq", "ollama"}:
        return generate_openai_compatible_reply(settings, prompt)
    raise ValueError(f"Unsupported LLM provider: {settings.provider}")
