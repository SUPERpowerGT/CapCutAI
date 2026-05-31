"""API 配置中心 —— 所有可调整的参数集中在此文件。

运行前必须填写 API_KEYS 中的真实 Key；
如需切换模型或调整推理参数，只需修改此文件，其他模块无需改动。
"""

# ── 302.ai 接入点 ─────────────────────────────────────────────────────────────
API_BASE_URL: str = "https://api.302.ai/v1/chat/completions"

# ── API Keys —— 使用前替换为真实密钥 ──────────────────────────────────────────
API_KEYS: dict[str, str] = {
    "vl":   "<API-KEY-VL>",    # Qwen3-VL（视觉分析，步骤2）
    "omni": "<API-KEY-OMNI>",  # Qwen3-Omni（ASR + 认知对齐，步骤3/4）
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
