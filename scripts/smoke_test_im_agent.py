import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional


BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:38080")
MAX_ATTEMPTS = int(os.environ.get("SMOKE_MAX_ATTEMPTS", "20"))
RETRY_DELAY_SECONDS = float(os.environ.get("SMOKE_RETRY_DELAY_SECONDS", "1"))


def request_json(path: str, payload: Optional[dict] = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        BACKEND_BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def post(path: str, payload: dict) -> dict:
    return request_json(path, payload)


def get(path: str) -> dict:
    return request_json(path)


def wait_for_backend() -> dict:
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return get("/api/health")
        except (urllib.error.HTTPError, urllib.error.URLError) as exception:
            last_error = exception
            if attempt == MAX_ATTEMPTS:
                break
            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        f"Backend health check failed after {MAX_ATTEMPTS} attempts: {last_error}"
    ) from last_error


def main() -> None:
    health = wait_for_backend()
    created = post("/api/conversations", {"title": "Scaffold Smoke Test"})
    conversation_id = created["data"]["conversationId"]
    sent = post(
        f"/api/conversations/{conversation_id}/messages",
        {"content": "hi agent"},
    )
    messages = get(f"/api/conversations/{conversation_id}/messages")

    result = {
        "health": health,
        "conversationId": conversation_id,
        "sendMessage": sent,
        "messages": messages,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
