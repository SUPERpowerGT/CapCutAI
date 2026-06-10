from __future__ import annotations

import sys
from pathlib import Path

from app.config import LlmSettings


def generate_ai4video_reply(settings: LlmSettings, prompt: str) -> tuple[str, str]:
    repo_root = Path(__file__).resolve().parents[3]
    ai4video_root = repo_root / "AI4Video"
    if str(ai4video_root) not in sys.path:
        sys.path.insert(0, str(ai4video_root))

    from pipeline_api.config import API_KEYS, MODELS
    from pipeline_api.client import chat_completion

    model = settings.model or MODELS["vl"]
    api_key = settings.api_key or API_KEYS["vl"]
    if not api_key or api_key.startswith("<"):
        raise ValueError("AI4Video VL API key is not configured.")

    reply_text = chat_completion(
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        model=model,
        api_key=api_key,
        max_tokens=2048,
        temperature=0.2,
    ).strip()
    return reply_text, model
