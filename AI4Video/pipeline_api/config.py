"""API 配置中心 —— 所有可调整的参数集中在此文件。

默认使用安全占位符与环境变量。
如需本地私有配置，可复制 `config.local.example.py` 为 `config.local.py`；
`config.local.py` 已被 gitignore 忽略，不会提交到仓库。
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

# ── 302.ai 接入点 ─────────────────────────────────────────────────────────────
API_BASE_URL: str = os.getenv(
    "AI4VIDEO_API_BASE_URL",
    "https://api.302.ai/v1/chat/completions",
)

# ── API Keys —— 使用前替换为真实密钥 ──────────────────────────────────────────
API_KEYS: dict[str, str] = {
    "vl":   os.getenv("AI4VIDEO_VL_API_KEY", "<API-KEY-VL>"),      # Qwen3-VL（视觉分析，步骤2）
    "omni": os.getenv("AI4VIDEO_OMNI_API_KEY", "<API-KEY-OMNI>"),  # Qwen3-Omni（ASR + 认知对齐，步骤3/4）
}

# ── 302.ai 上的模型标识符 ──────────────────────────────────────────────────────
MODELS: dict[str, str] = {
    "vl":   "Qwen/Qwen3-VL-8B-Instruct",
    "omni": "Qwen/Qwen3-Omni-30B-A3B-Instruct",
}

# ── 生成参数（max_tokens）─────────────────────────────────────────────────────
MAX_TOKENS: dict[str, int] = {
    "vl_shot":       512,   # 单帧关键帧 VL 分析
    "asr_chunk":    2048,   # 单个 60s 音频块 ASR
    "orchestrator": 4096,   # 认知对齐完整输出
}

# ── HTTP 客户端参数 ────────────────────────────────────────────────────────────
REQUEST_TIMEOUT_SEC: int = 180   # 单次请求超时（秒）
MAX_RETRIES:         int = 3     # 遇到 429/5xx 时的最大重试次数
RETRY_BACKOFF_SEC:   int = 5     # 指数退避基础等待时间（秒）

# ── ASR 分块参数（与本地版保持一致）─────────────────────────────────────────────
ASR_CHUNK_SEC:    int = 60      # 每块音频最大时长（60s 是 Omni ASR 稳定输出的上限）
ASR_SAMPLE_RATE:  int = 16000   # 采样率（Hz）


_config_local = None
_config_local_path = Path(__file__).with_name("config.local.py")

if _config_local_path.exists():
    spec = importlib.util.spec_from_file_location(
        "ai4video_pipeline_api_config_local", _config_local_path
    )
    if spec and spec.loader:
        _config_local = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_config_local)

if _config_local is not None:
    API_BASE_URL = getattr(_config_local, "API_BASE_URL", API_BASE_URL)
    API_KEYS = getattr(_config_local, "API_KEYS", API_KEYS)
    MODELS = getattr(_config_local, "MODELS", MODELS)
    MAX_TOKENS = getattr(_config_local, "MAX_TOKENS", MAX_TOKENS)
    REQUEST_TIMEOUT_SEC = getattr(
        _config_local, "REQUEST_TIMEOUT_SEC", REQUEST_TIMEOUT_SEC
    )
    MAX_RETRIES = getattr(_config_local, "MAX_RETRIES", MAX_RETRIES)
    RETRY_BACKOFF_SEC = getattr(
        _config_local, "RETRY_BACKOFF_SEC", RETRY_BACKOFF_SEC
    )
    ASR_CHUNK_SEC = getattr(_config_local, "ASR_CHUNK_SEC", ASR_CHUNK_SEC)
    ASR_SAMPLE_RATE = getattr(_config_local, "ASR_SAMPLE_RATE", ASR_SAMPLE_RATE)
