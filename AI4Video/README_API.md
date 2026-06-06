# 多模态视频分析流水线 —— API 版

基于 302.ai 代理 API 的视频剪辑结构分析系统。与本地版（`pipeline.py`）输出完全一致的弹性 JSON 模板，无需本地 GPU 和模型权重。

---

## 目录

- [与本地版的区别](#与本地版的区别)
- [快速开始](#快速开始)
- [流水线流程](#流水线流程)
- [模块结构](#模块结构)
- [API 调用规范](#api-调用规范)
  - [请求格式](#请求格式)
  - [多模态内容类型](#多模态内容类型)
  - [重试与错误处理](#重试与错误处理)
- [配置参数说明](#配置参数说明)
- [扩展其他模型](#扩展其他模型)
- [更换 API 服务商](#更换-api-服务商)

---

## 与本地版的区别

| 组件 | 本地版 (`pipeline.py`) | API 版 (`pipeline_api.py`) |
|------|----------------------|--------------------------|
| 步骤1 音频特征提取 | Librosa，本地执行 | Librosa，本地执行（相同） |
| 步骤2 语音识别 ASR | Qwen3-Omni，加载本地权重 | Qwen3-Omni，302.ai API |
| 步骤3 镜头边界检测 | 像素差算法，本地执行 | 像素差算法，本地执行（相同） |
| 步骤3 关键帧语义分析 | Qwen3-VL，加载本地权重 | Qwen3-VL，302.ai API |
| 步骤4 认知对齐 | Qwen3-Omni，加载本地权重 | Qwen3-Omni，302.ai API |
| GPU 要求 | 80GB 显存 | 无 |
| 模型权重 | 本地约 60GB | 无 |
| 输出格式 | 与 API 版完全一致 | 与本地版完全一致 |

步骤1 的音频提取（PyAV）、BPM 检测（Librosa）、镜头边界检测（像素差）、关键帧提取（PyAV）均在本地运行，无需 GPU，也不消耗 API 额度。

---

## 快速开始

### 1. 安装依赖

```bash
pip install requests numpy soundfile librosa av
```

### 2. 填写 API Key

编辑 `pipeline_api/config.py`，将占位符替换为真实密钥：

```python
API_KEYS: dict[str, str] = {
    "vl":   "sk-xxxxxxxx",   # Qwen3-VL，用于步骤3视觉分析
    "omni": "sk-xxxxxxxx",   # Qwen3-Omni，用于步骤2 ASR 和步骤4认知对齐
}
```

### 3. 运行

```bash
# 完整运行
python pipeline_api.py data/your_video.mp4

# 自定义输出目录
python pipeline_api.py data/your_video.mp4 --output-dir /tmp/my_output

# 分析所有镜头（默认采样至 30 个）
python pipeline_api.py data/your_video.mp4 --analyze-all-shots

# 英文 ASR
python pipeline_api.py data/your_video.mp4 --language English
```

### 4. CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--output-dir PATH` | `outputs/pipeline_api/<stem>` | 自定义输出目录 |
| `--max-shots N` | 30 | VL API 分析的最大镜头数，超出时均匀采样 |
| `--analyze-all-shots` | False | 分析全部镜头，忽略 `--max-shots` |
| `--language LANG` | Chinese | ASR 语言提示（Chinese / English / Japanese）|
| `--diff-threshold F` | 0.25 | 镜头边界像素差检测阈值（0~1）|

### 5. 输出文件

```
outputs/pipeline_api/<video_stem>/
├── elastic_template.json   ★ 最终弹性模板
├── step1_audio.json        音频特征（BPM / 节拍 / 高潮点）
├── step2_transcript.json   ASR 转录（全文 + 句级时间戳）
├── step3_visual.json       视觉分镜（镜头列表 + 字幕信息）
├── <video_stem>.wav        音频缓存（供 ASR 分块使用）
└── keyframes/              各镜头关键帧截图
    ├── shot_000_0ms.jpg
    └── ...
```

---

## 流水线流程

```
输入视频 (.mp4)
      │
      ├──▶ 步骤1  音频特征提取（本地，Librosa）
      │          BPM / 节拍时间戳 / 高潮能量点
      │          提取 16kHz 单声道 WAV 缓存供步骤2使用
      │          → step1_audio.json
      │
      ├──▶ 步骤2  语音识别 ASR（Qwen3-Omni API）
      │          将 WAV 切为 60s 分块 → 逐块 base64 编码 → audio_url 调用
      │          按时间偏移合并各块结果
      │          → step2_transcript.json
      │
      ├──▶ 步骤3  视觉分析（本地算法 + Qwen3-VL API）
      │          像素差算法检测镜头边界（本地）
      │          PyAV 提取每镜头中点关键帧（本地）
      │          关键帧 base64 编码 → image_url 逐帧调用 VL API
      │          → step3_visual.json + keyframes/
      │
      ▼
步骤4  认知对齐与弹性映射（Qwen3-Omni API + Python 确定性换算）
      ├── Phase A.5：ASR-VL 时间戳对齐（本地，口播→镜头归属）
      ├── Phase B：Omni API 推理（叙事阶段划分 + 转场注释）
      └── Phase C：Python 数学换算（节拍偏移 / 时间比例 / 阶段分配）
      → elastic_template.json
```

### 各步骤 API 调用次数

| 步骤 | 调用模型 | 调用次数 |
|------|---------|---------|
| 步骤2 ASR | Qwen3-Omni | `ceil(视频时长 / 60)` 次（每块 60s）|
| 步骤3 VL | Qwen3-VL | `min(镜头数, max_shots)` 次（每帧 1 次）|
| 步骤4 认知对齐 | Qwen3-Omni | 1 次 |

341s 视频 + 30 个镜头的典型用量：Omni 约 7 次，VL 约 30 次，共约 37 次 API 调用。

---

## 模块结构

```
pipeline_api/
├── __init__.py          包初始化
├── config.py            所有可调参数的唯一入口（Key / 模型 ID / 超时 / 分块）
├── client.py            通用 HTTP 客户端（鉴权 / 重试 / 错误处理）
├── vl_processor.py      步骤3：VL 图像理解（本地关键帧提取 + API 推理）
├── asr_processor.py     步骤2：ASR 语音识别（本地分块 + API 推理）
└── orchestrator.py      步骤4：认知对齐（Prompt 构建 + API 调用 + 数学换算）

pipeline_api.py          CLI 入口（四步骤串行执行 + 耗时汇总）
```

**依赖关系**（单向，无循环）：

```
pipeline_api.py
  └── pipeline_api/{vl_processor, asr_processor, orchestrator}
        └── pipeline_api/client          ← 唯一 HTTP 出口
        └── pipeline_api/config          ← 唯一配置入口
        └── pipeline/{visual_processor, text_processor, orchestrator, ...}
                                         ← 复用 Prompt / 解析 / 数据类（无模型加载）
```

---

## API 调用规范

### 请求格式

所有模型调用均通过 `pipeline_api/client.py` 中的 `chat_completion()` 函数统一发出，遵循 OpenAI Chat Completions 格式：

```
POST https://api.302.ai/v1/chat/completions
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "model": "Qwen/Qwen3-VL-8B-Instruct",
  "messages": [...],
  "max_tokens": 512,
  "temperature": 0.1
}
```

成功响应取 `choices[0].message.content` 作为返回文本。

### 多模态内容类型

上层模块只负责构建 `messages` 列表，`client.py` 不感知内容类型。目前使用三种内容格式：

#### 纯文本（认知对齐 / 测试）

```python
messages = [
    {"role": "user", "content": "你的提示词文本"}
]
```

#### 图像理解（步骤3，Qwen3-VL）

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,<BASE64>"}
            },
            {"type": "text", "text": "分析这张关键帧的剪辑语义..."}
        ]
    }
]
```

图像编码规则：
- 格式：JPEG / PNG，均编码为 `data:image/<mime>;base64,<data>`
- 由 `vl_processor._encode_image_b64()` 负责，自动识别后缀

#### 音频理解（步骤2，Qwen3-Omni）

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "audio_url",
                "audio_url": {"url": "data:audio/wav;base64,<BASE64>"}
            },
            {"type": "text", "text": "请识别音频内容并以 JSON 格式输出..."}
        ]
    }
]
```

音频编码规则：
- 格式：16kHz 单声道 PCM16 WAV
- 每块不超过 60s（Omni 稳定输出的上限；超过 180s 时 JSON 输出失稳）
- 由 `asr_processor._encode_audio_b64()` 负责，使用 `soundfile` 写入内存

### 重试与错误处理

`client.py` 对以下状态码自动重试，其余状态码立即抛出 `APIError`：

| HTTP 状态码 | 含义 | 处理方式 |
|------------|------|---------|
| 429 | 速率限制 | 指数退避重试 |
| 500 / 502 / 503 / 504 | 服务端错误 | 指数退避重试 |
| 400 / 401 / 403 等 | 请求或鉴权错误 | 立即抛出，不重试 |
| Timeout | 请求超时 | 指数退避重试 |
| ConnectionError | 网络不通 | 立即抛出，不重试 |

退避公式：`wait = RETRY_BACKOFF_SEC × 2^(attempt-1)`，默认第 1/2/3 次分别等待 5s / 10s / 20s。

VL 和 ASR 的单帧/单块调用捕获所有异常后返回默认值，**不会因单帧失败中断整条流水线**：

```python
# vl_processor.py —— 单帧失败返回默认字段
except Exception as e:
    return _parse_shot_json("")   # 返回安全默认值

# asr_processor.py —— 单块失败跳过，继续下一块
except Exception as e:
    return []
```

---

## 配置参数说明

所有参数集中在 `pipeline_api/config.py`，其他模块不硬编码任何值。

```python
# ── 接入点 ────────────────────────────────────────────────────────────────────
API_BASE_URL = "https://api.302.ai/v1/chat/completions"

# ── API Keys ──────────────────────────────────────────────────────────────────
API_KEYS = {
    "vl":   "sk-...",   # 步骤3 Qwen3-VL 视觉分析
    "omni": "sk-...",   # 步骤2 ASR + 步骤4 认知对齐
}

# ── 模型标识符（302.ai 平台上的 ID）──────────────────────────────────────────
MODELS = {
    "vl":   "Qwen/Qwen3-VL-8B-Instruct",
    "omni": "Qwen/Qwen3-Omni-30B-A3B-Instruct",
}

# ── 各场景最大输出 token 数 ───────────────────────────────────────────────────
MAX_TOKENS = {
    "vl_shot":    512,    # 单帧 VL 分析（结构化 JSON，不需要很长）
    "asr_chunk":  2048,   # 单块 60s ASR（长音频句子多）
    "orchestrator": 4096, # 认知对齐（完整 JSON 输出）
}

# ── HTTP 客户端 ───────────────────────────────────────────────────────────────
REQUEST_TIMEOUT_SEC = 180   # 单次请求超时（秒）
MAX_RETRIES         = 3     # 429/5xx 最大重试次数
RETRY_BACKOFF_SEC   = 5     # 指数退避基础等待（秒）

# ── ASR 分块 ──────────────────────────────────────────────────────────────────
ASR_CHUNK_SEC   = 60      # 每块最大时长（60s 是 Omni 稳定输出的上限）
ASR_SAMPLE_RATE = 16000   # 采样率（Hz）
```

---

## 扩展其他模型

以新增一个**视频摘要模型**（`summary`）为例，完整流程如下：

### 第一步：在 `config.py` 注册模型

```python
API_KEYS["summary"] = "<YOUR_SUMMARY_API_KEY>"

MODELS["summary"] = "SomeVendor/video-summarizer-7b"

MAX_TOKENS["summary"] = 1024
```

### 第二步：创建处理器模块

新建 `pipeline_api/summary_processor.py`：

```python
from pipeline_api.client import chat_completion
from pipeline_api.config import API_KEYS, MAX_TOKENS, MODELS


def run_summary_api(transcript_text: str) -> str:
    """调用摘要模型，对口播文本生成结构化摘要。"""
    messages = [
        {
            "role": "user",
            "content": f"请对以下视频口播内容生成三句话摘要：\n\n{transcript_text}",
        }
    ]
    return chat_completion(
        messages=messages,
        model=MODELS["summary"],
        api_key=API_KEYS["summary"],
        max_tokens=MAX_TOKENS["summary"],
    )
```

**设计要点**：
- 只负责构建 `messages` 并调用 `chat_completion()`，不处理 HTTP 细节
- 多模态内容（图像 / 音频）按上文「多模态内容类型」格式拼装 `content` 列表
- 解析逻辑写在本模块内，不污染 `client.py`

### 第三步：在主流水线中接入

在 `pipeline_api.py` 的 `run_pipeline_api()` 中增加步骤：

```python
_print_step(5, "视频摘要 (SomeVendor API)")
t0 = time.perf_counter()
from pipeline_api.summary_processor import run_summary_api
summary = run_summary_api(transcript.full_text)
step_times["步骤5 视频摘要"] = time.perf_counter() - t0
print(f"[Summary-API] {summary}")
print(f"[步骤5] 耗时: {_fmt(step_times['步骤5 视频摘要'])}")
```

### 替换现有模型（如换用更大的 VL 模型）

只需修改 `config.py` 中的 `MODELS["vl"]` 和 `API_KEYS["vl"]`，所有调用该 key 的处理器自动生效，无需修改其他文件：

```python
MODELS["vl"] = "Qwen/Qwen3-VL-72B-Instruct"   # 换更大的模型
API_KEYS["vl"] = "sk-new-key-for-72b"
MAX_TOKENS["vl_shot"] = 1024                    # 酌情调大输出长度
```

---

## 更换 API 服务商

如果需要从 302.ai 切换到其他兼容 OpenAI 格式的服务商（如官方 DashScope、Hugging Face Inference、SiliconFlow 等），需要修改以下内容：

### 必须修改

**`pipeline_api/config.py`**：

```python
# 1. 换接入点 URL
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# 2. 换 API Key（格式视服务商而定）
API_KEYS = {
    "vl":   "sk-new-provider-key",
    "omni": "sk-new-provider-key",
}

# 3. 换模型标识符（不同服务商的 model ID 不同）
MODELS = {
    "vl":   "qwen-vl-max",              # DashScope 上的模型 ID
    "omni": "qwen3-omni-30b-a3b",       # 服务商文档中查找
}
```

### 可能需要修改

**`pipeline_api/client.py`**（仅当服务商的响应格式不同时）：

```python
# 默认取法（OpenAI 标准格式）
return data["choices"][0]["message"]["content"]

# 若服务商返回非标准格式，在此处适配
# 例如某些服务商返回 data["output"]["text"]
```

**`pipeline_api/{vl,asr}_processor.py`**（仅当服务商的多模态字段名不同时）：

```python
# 当前使用 OpenAI image_url 格式（302.ai / 官方 Qwen 均兼容）
{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}

# 若服务商要求不同字段名（如 "image" 而非 "image_url"），在对应 processor 中修改
```

### 无需修改

- `pipeline_api/orchestrator.py` —— Prompt 构建与服务商无关
- `pipeline/` 下所有本地组件 —— 纯算法，不涉及网络
- `pipeline_api.py` 主流程 —— 步骤逻辑与服务商无关

### 兼容性速查

| 服务商 | URL 格式 | 鉴权格式 | 多模态格式 | 是否兼容 |
|--------|---------|---------|-----------|---------|
| 302.ai | `/v1/chat/completions` | `Bearer sk-xxx` | OpenAI image_url / audio_url | 当前使用 |
| DashScope（官方）| `/compatible-mode/v1/chat/completions` | `Bearer sk-xxx` | OpenAI image_url | 兼容，仅改 URL + Key + model |
| SiliconFlow | `/v1/chat/completions` | `Bearer sk-xxx` | OpenAI image_url | 兼容，仅改 URL + Key + model |
| Hugging Face | `/v1/chat/completions` | `Bearer hf-xxx` | OpenAI image_url | 兼容，仅改 URL + Key + model |
| 非 OpenAI 兼容 | 自定义 | 自定义 | 自定义 | 需修改 `client.py` 适配 |
