import json
from urllib import request

from app.config import LlmSettings


def generate_openai_compatible_reply(settings: LlmSettings, prompt: str) -> tuple[str, str]:
    payload = json.dumps(
        {
            "model": settings.model,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    http_request = request.Request(
        url=f"{settings.base_url}/chat/completions",
        data=payload,
        method="POST",
        headers=headers,
    )

    with request.urlopen(http_request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))

    reply_text = (
        body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    )
    return reply_text, settings.model
