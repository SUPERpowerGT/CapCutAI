"""通用 API 客户端 —— 所有模型调用的唯一 HTTP 出口。

上层模块（vl_processor / asr_processor / orchestrator）只负责
构建 messages payload，实际的网络请求、鉴权、重试均在此处理。

设计原则：
  - 与模型无关：通过参数传入 model / api_key，不硬编码
  - 统一重试策略：对 429 / 5xx 做指数退避重试，其他错误立即抛出
  - 单一职责：只负责「发请求 → 返回 content 文本」，解析逻辑留给调用方
"""

from __future__ import annotations

import time
from typing import Any

import requests

from pipeline_api.config import (
    API_BASE_URL,
    MAX_RETRIES,
    REQUEST_TIMEOUT_SEC,
    RETRY_BACKOFF_SEC,
)

# HTTP 状态码：遇到这些才做重试，其余视为不可恢复错误
_RETRIABLE_STATUS = {429, 500, 502, 503, 504}


class APIError(Exception):
    """API 调用失败时抛出，携带状态码和响应片段。"""


def chat_completion(
    messages: list[dict[str, Any]],
    model: str,
    api_key: str,
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> str:
    """调用 302.ai chat completions 端点，返回助手回复的纯文本内容。

    Args:
        messages:    符合 OpenAI 格式的消息列表（支持文本 / image_url / audio_url）。
        model:       302.ai 上的模型标识符（见 config.MODELS）。
        api_key:     对应模型的 Bearer API Key（见 config.API_KEYS）。
        max_tokens:  最大输出 token 数。
        temperature: 采样温度；0.1 接近确定性输出，适合结构化 JSON 任务。

    Returns:
        模型输出的纯文本字符串（choices[0].message.content）。

    Raises:
        APIError: 超过最大重试次数，或遇到不可恢复的 HTTP 错误。
    """
    payload: dict[str, Any] = {
        "model":       model,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                API_BASE_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SEC,
            )

            if resp.status_code == 200:
                data: dict = resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError) as e:
                    raise APIError(f"响应格式异常，无法提取 content: {data}") from e

            if resp.status_code in _RETRIABLE_STATUS:
                delay = RETRY_BACKOFF_SEC * (2 ** (attempt - 1))
                print(
                    f"[APIClient] HTTP {resp.status_code}，"
                    f"第 {attempt}/{MAX_RETRIES} 次重试（等待 {delay}s）..."
                )
                time.sleep(delay)
                last_exc = APIError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                continue

            # 其余状态码（400, 401, 403 等）不重试
            raise APIError(
                f"HTTP {resp.status_code} [{model}]: {resp.text[:500]}"
            )

        except requests.exceptions.Timeout:
            delay = RETRY_BACKOFF_SEC * (2 ** (attempt - 1))
            print(f"[APIClient] 请求超时，第 {attempt}/{MAX_RETRIES} 次重试（等待 {delay}s）...")
            time.sleep(delay)
            last_exc = APIError("Request timeout")

        except requests.exceptions.ConnectionError as e:
            raise APIError(f"连接失败: {e}") from e

    raise APIError(
        f"已达最大重试次数 ({MAX_RETRIES})，最后错误: {last_exc}"
    ) from last_exc
