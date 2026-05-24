from functools import lru_cache

from google import genai

from app.config import LlmSettings


@lru_cache(maxsize=4)
def _get_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)


def generate_gemini_reply(settings: LlmSettings, prompt: str) -> tuple[str, str]:
    client = _get_gemini_client(settings.api_key)
    response = client.models.generate_content(
        model=settings.model,
        contents=prompt,
    )
    reply_text = (response.text or "").strip()
    return reply_text, settings.model
