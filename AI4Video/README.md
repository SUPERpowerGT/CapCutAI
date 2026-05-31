# 多模态视频结构提取流水线

基于 Qwen3 系列多模态大模型的视频剪辑结构分析系统。输入一段 `.mp4` 视频，自动输出一份**弹性 JSON 模板**——记录视频的叙事骨架、每个镜头的剪辑逻辑与 BGM 节拍对齐关系，供下游 AI 剪辑 Agent 将同一剪辑风格复用到新视频上。

---

## 目录

- [项目目标](#项目目标)
- [系统架构](#系统架构)
- [环境配置](#环境配置)
- [快速开始](#快速开始)
- [流水线详解](#流水线详解)
  - [步骤1：音频特征提取](#步骤1音频特征提取)
  - [步骤2：语音识别 ASR](#步骤2语音识别-asr)
  - [步骤3：视觉分镜分析](#步骤3视觉分镜分析)
  - [步骤4：认知对齐与弹性映射](#步骤4认知对齐与弹性映射)
- [输出数据结构](#输出数据结构)
  - [step1\_audio.json](#step1_audiojson)
  - [step2\_transcript.json](#step2_transcriptjson)
  - [step3\_visual.json](#step3_visualjson)
  - [elastic\_template.json（最终产物）](#elastic_templatejson最终产物)
- [CLI 参数说明](#cli-参数说明)
- [设计原则](#设计原则)
- [下游使用示例](#下游使用示例)
- [常见问题](#常见问题)

---

## 项目目标

短视频剪辑存在「可复用风格」：同一个节奏模板（如知识口播的钩子→痛点→方案→CTA 结构，或高燃混剪的铺垫→高潮卡点节奏）可以套用到无数内容不同的视频上。

本流水线将这种「风格」从样例视频中解构出来，形成一份**与内容无关、与时间解耦**的 JSON 蓝图。下游 LLM Agent 拿到新剧本文案和新 BGM 时，读取这份 JSON，在 Remotion 或 HyperFrames 等「视频即代码」框架下，将原片风格精准复刻到新视频。

---

## 系统架构

```
输入视频 (.mp4)
      │
      ├──▶ 步骤1  音频特征提取 (Librosa + PyAV)
      │          BPM / 节拍时间戳 / 高潮能量点
      │          → step1_audio.json
      │
      ├──▶ 步骤2  语音识别 ASR (Qwen3-Omni，分块推理)
      │          口播文字 + 句级时间戳
      │          → step2_transcript.json
      │
      ├──▶ 步骤3  视觉分镜分析 (像素差检测 + Qwen3-VL)
      │          镜头边界 / 关键帧 / 逐镜语义标注
      │          → step3_visual.json + keyframes/
      │
      ▼
步骤4  认知对齐与弹性映射 (Qwen3-Omni)
      ├── Phase A：ASR（与步骤2合并，共享 Omni 实例）
      ├── Phase A.5：ASR-VL 时间戳对齐（口播→镜头对齐）
      ├── Phase B：LLM 叙事推理（输出时间边界 + 语义字段）
      └── Python 确定性换算（镜头阶段分配 / 节拍偏移）
      → elastic_template.json  ◀── 最终交付物
```

### 模型分工

| 组件 | 模型 / 工具 | 职责 | 输出 |
|------|------------|------|------|
| 音频处理 | Librosa + PyAV | BPM 检测、节拍追踪、能量高潮检测 | 节拍时间戳数组 |
| 音频提取 | PyAV（无需系统 ffmpeg）| 从 mp4 提取 16kHz 单声道 WAV | .wav 文件 |
| 视觉检测 | 像素差算法（纯 NumPy）| 镜头边界检测 | 边界时间戳列表 |
| 视觉理解 | Qwen3-VL-8B | 关键帧语义分析 | 景别 / 情绪 / 剪辑用途等 |
| 语音识别 | Qwen3-Omni-30B | 分块 ASR + 句级时间戳 | 口播文字 + 时间戳 |
| 认知对齐 | Qwen3-Omni-30B | 叙事阶段划分 / 风格判断 / 转场与音效推荐 | 语义 JSON |
| 数学换算 | Python（确定性）| 时间比例计算 / 节拍偏移计算 / 镜头阶段分配 | 最终数值字段 |

---

## 环境配置

### Python 版本

Python 3.10 或更高版本。

### 安装依赖

```bash
# 核心深度学习框架
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate

# Qwen 专用工具包
pip install qwen-vl-utils[decord]
pip install qwen-omni-utils

# 音视频处理（无需系统级 ffmpeg）
pip install av           # PyAV，用于音频提取和关键帧抽取
pip install soundfile    # WAV 文件读写
pip install librosa      # BPM 和节拍分析

# 其他依赖
pip install numpy jsonschema

# 可选：Flash Attention 2（大幅提升推理速度，需 CUDA 11.8+）
pip install flash-attn --no-build-isolation
# 若安装 flash-attn 失败，pipeline 自动降级至 sdpa
```

### 模型权重

流水线需要以下三个本地模型（按需修改 `pipeline.py` 顶部的路径配置）：

```python
# pipeline.py 顶部配置区
ASR_MODEL_PATH  = "/path/to/Qwen3-ASR-1.7B"            # 独立 ASR 后端（备用）
VLM_MODEL_PATH  = "/path/to/Qwen3-VL-8B-Instruct"      # 视觉分析
OMNI_MODEL_PATH = "/path/to/Qwen3-Omni-30B-A3B-Instruct" # ASR + 认知对齐
```

| 模型 | 显存需求 | 用途 |
|------|---------|------|
| Qwen3-VL-8B-Instruct | ~16GB | 关键帧图像理解（步骤3）|
| Qwen3-Omni-30B-A3B-Instruct | ~40GB | 语音识别 + 认知对齐（步骤4）|

> 两个模型顺序加载、推理完成后立即释放显存，不同时占用。

### 硬件要求

- GPU：80GB 显存（单卡）或多卡自动分片（`device_map="auto"`）
- 存储：模型权重约 60GB，输出文件约 100MB/视频

---

## 快速开始

```bash
# 完整运行（需要模型权重）
python pipeline.py data/your_video.mp4

# Mock 模式（无需任何模型，秒级完成，用于验证流程）
python pipeline.py data/your_video.mp4 --mock

# 指定输出目录
python pipeline.py data/your_video.mp4 --output-dir /tmp/my_output

# 分析所有镜头（默认最多采样 30 个）
python pipeline.py data/your_video.mp4 --analyze-all-shots
```

运行结束后，输出目录中包含：

```
outputs/pipeline/<video_stem>/
├── elastic_template.json   ★ 最终弹性模板（下游 Agent 的输入）
├── step1_audio.json        中间产物：音频特征
├── step2_transcript.json   中间产物：语音转录
├── step3_visual.json       中间产物：视觉分镜
├── <video_stem>.wav        音频缓存（可复用）
└── keyframes/              各镜头关键帧截图
    ├── shot_000_0ms.jpg
    ├── shot_001_840ms.jpg
    └── ...
```

---

## 流水线详解

### 步骤1：音频特征提取

**文件**：`pipeline/audio_processor.py`  
**工具**：PyAV（音频提取）+ Librosa（音乐分析）

#### 处理逻辑

1. **音频提取**：通过 PyAV 将视频的音轨解码并重采样为 16kHz 单声道 PCM16 WAV，不依赖系统级 `ffmpeg` 二进制。

2. **BPM 与节拍追踪**：使用 Librosa 的 `beat_track` 函数，基于动态规划节拍追踪算法，检测全局 BPM 并输出每个节拍的精准毫秒时间戳。

3. **高潮点（Drops）检测**：
   - 计算音频起始强度（Onset Strength）并做平滑处理
   - 用均值 + 1.5 倍标准差设定能量突变阈值
   - 提取超过阈值的局部极大值，按能量强度降序排列
   - 保留彼此间距不小于 2 秒、强度最高的前 3 个峰值

   高潮点是音乐能量爆发的时刻（如鼓点加速、和弦转换），在步骤4中作为叙事阶段自然分界的参考锚点。

#### 为什么需要 Drops？

不同视频的 BGM 时长不同，绝对时间无法跨视频复用。Drops 是音乐结构中的「功能性节点」：新 BGM 的第一个高潮点往往对应叙事的转折点。通过将叙事阶段边界与 Drops 对齐（`bgm_alignment_rule`），同一叙事结构可以自动适配任意 BPM 和时长的新 BGM。

---

### 步骤2：语音识别 ASR

**文件**：`pipeline/text_processor.py`  
**模型**：Qwen3-Omni-30B（共享实例，与步骤4合并加载）

#### 处理逻辑

步骤2 默认**合并**到步骤4的 Omni 模型实例中执行（`asr_backend=qwen3-omni`），避免重复加载 30B 模型（省约 30~60 秒）。执行时序：

```
加载 Omni 模型
  └── Phase A：分块 ASR（步骤2的内容）
  └── Phase A.5：ASR-VL 时间戳对齐
  └── Phase B：认知对齐推理（步骤4的内容）
卸载 Omni 模型
```

**分块策略**：将全长音频切为 60 秒一块，逐块输入 Omni：
- 每块附加中文提示词，要求 Omni 以 JSON 格式输出句级时间戳
- 解析返回的 JSON，将每个句子的 `start_sec/end_sec` 加上当前块的时间偏移，转换为相对于视频起点的绝对毫秒时间戳
- 拼接所有块的结果，得到完整转录

**为什么用 60 秒而非更长？**  
实验表明，Omni 在超过 180 秒的音频输入下无法稳定输出 JSON 格式的时间戳（返回 0 句）。60 秒是 Omni ASR JSON 输出的可靠上限。

#### ASR-VL 时间戳对齐（Phase A.5）

将 ASR 得到的句子按时间重叠对齐到 VL 分析的镜头：

```python
# 对每个镜头，找出时间上重叠的 ASR 句子
overlap_ratio = overlap_ms / sentence_duration_ms
if overlap_ratio >= 0.2:  # 超过 20% 重叠则归属此镜头
    shot_aligned_text.append(sentence.text)
```

阈值 0.2 的设计考量：Omni 的时间戳精度约 ±1~3 秒，宽松阈值容忍时间戳误差，同一句话可同时归属多个镜头（跨镜句子）。

对齐结果作为额外上下文注入步骤4的推理 Prompt：

```
[5] 38400~40320ms | B_ROLL_SEMANTIC | CALM | NARRATIVE_SUPPORT
    └ 口播: 哎呀，这大胖头鱼啊，拿这个铁锅用大酱炖...
```

这使 Omni 在划分叙事阶段时能感知「每个画面里说了什么」，大幅提升叙事阶段划分的准确性。

---

### 步骤3：视觉分镜分析

**文件**：`pipeline/visual_processor.py`  
**工具**：PyAV（关键帧提取）+ 像素差算法（镜头检测）+ Qwen3-VL-8B（图像理解）

#### 子步骤1：镜头边界检测（无模型，纯算法）

基于像素差（Pixel-Difference）的轻量检测器，不依赖深度学习模型：

1. 每隔 3 帧取一帧，降采样为 1/8 分辨率灰度图
2. 计算相邻帧的平均绝对像素差
3. 差值超过阈值（默认 0.25）且与上一镜头间距 ≥ 0.5 秒，则判定为新镜头

对于镜头数超过 30 的长视频，默认均匀采样至 30 个进行分析（使用 `--analyze-all-shots` 可关闭采样上限）。

#### 子步骤2：关键帧提取

取每个镜头时间范围的中点帧，用 PyAV 精确 seek 到对应 PTS 位置并导出为 JPEG。中点帧比首帧更能代表镜头的稳定画面内容。

#### 子步骤3：Qwen3-VL 单帧图像理解

对每张关键帧，以「专业 AI 视频剪辑师」的角色身份输入 Qwen3-VL，要求输出结构化剪辑元数据：

```json
{
  "shot_type": "A_ROLL_MEDIUM",
  "content_type": "PRESENTER",
  "emotional_tone": "HIGH_ENERGY",
  "b_roll_semantic_prompt": "主播面对镜头，白色书房背景，神情自信，手持产品",
  "camera_motion_effect": "静态",
  "editing_utility": "HOOK_OPENER",
  "has_caption": true,
  "caption_position_y_pct": 78,
  "caption_font_family": "Sans-Serif-Bold",
  "caption_highlight_style": "核心词使用黄色#FFD700加粗高亮"
}
```

各字段含义：

| 字段 | 可选值 | 剪辑意义 |
|------|--------|---------|
| `shot_type` | A_ROLL_CLOSE_UP / A_ROLL_MEDIUM / B_ROLL_SEMANTIC | 景别判断，影响下游素材选取 |
| `content_type` | PRESENTER / PRODUCT / SCENE / TEXT_GRAPHIC | 画面主体类型 |
| `emotional_tone` | HIGH_ENERGY / NEUTRAL / CALM | 决定转场速度和音效选择 |
| `b_roll_semantic_prompt` | 中文描述，≤50字 | **向量检索接口**：下游直接用此文本检索素材库 |
| `editing_utility` | HOOK_OPENER / NARRATIVE_SUPPORT / EMPHASIS_HIGHLIGHT / TRANSITION_BRIDGE | 该镜头在剪辑中的功能定位 |
| `caption_font_family` | Sans-Serif-Bold / Serif-Elegant / Handwritten / Monospace | 字幕字体族，通过多镜头投票聚合 |
| `caption_highlight_style` | 自然语言描述 | 关键词高亮规则，如「黄色#FFD700加粗」 |

#### 字幕样式聚合

所有镜头分析完成后，对有字幕的镜头做聚合统计：
- `position_y_percentage`：取各镜头字幕纵向位置的中位数
- `font_family_type`：取所有镜头字体族检测结果中的众数（投票）
- `highlight_strategy`：取第一个有效的高亮描述

---

### 步骤4：认知对齐与弹性映射

**文件**：`pipeline/orchestrator.py`  
**模型**：Qwen3-Omni-30B  
**关键设计**：LLM 只输出语义字段，所有数值字段由 Python 精确计算

#### LLM 推理的输入 Prompt

将前三步数据拼装为结构化 Prompt：

```
## 视频基本信息
- 总时长: 341012ms（341.0秒）
- BPM: 125.0
- 节拍时间点（前20个）: [480, 960, 1440, ...]
- 高潮能量点: [30336, 102560, 191936] ← 可作为叙事阶段自然分界参考

## 口播转录
  （已按镜头时间戳对齐，见分镜列表中「口播」字段）
  全文预览: 大家好，我是王冰冰。那这里呢就是查干湖...

## 视觉分镜（共30个镜头）
  [0] 0~840ms | B_ROLL_SEMANTIC | SCENE | NEUTRAL | HOOK_OPENER | 雪地冬日场景...
      └ 口播: （无）
  [1] 840~6240ms | A_ROLL_CLOSE_UP | PRESENTER | CALM | NARRATIVE_SUPPORT | 主播面部...
      └ 口播: 大家好，我是王冰冰。那这里呢就是查干湖...
  ...
```

#### LLM 输出的语义字段

Omni 按视频实际内容自主规划 2~4 个叙事阶段，**阶段名由 LLM 根据内容类型自主命名**：

| 视频类型 | 典型阶段命名 |
|---------|------------|
| 营销口播 / 知识分享 | PHASE_HOOK → PHASE_PROBLEM → PHASE_SOLUTION → PHASE_CTA |
| 影视混剪 / 高燃卡点 | PHASE_INTRO → PHASE_BUILDUP → PHASE_CLIMAX → PHASE_OUTRO |
| 生活记录 / Vlog | PHASE_OPENING → PHASE_STORY → PHASE_HIGHLIGHT → PHASE_ENDING |
| 短片 / 采访 | PHASE_SETUP → PHASE_CORE → PHASE_WRAP |

LLM 输出**时间边界**（而非镜头索引），附带每个镜头的转场与音效注释：

```json
{
  "storyline_phases": [
    { "phase_id": "PHASE_OPENING", "start_ms": 0, "end_ms": 30336, "energy_level": "HIGH", "narrative_goal": "...", "bgm_alignment_rule": "ALIGN_TO_BGM_START" }
  ],
  "per_shot_annotations": [
    { "shot_index": 0, "transition_type": "淡入淡出", "transition_duration_beats": 0.5, "audio_sfx_type": "NONE", "bgm_volume_behavior": "NORMAL" }
  ],
  "style_metadata": { ... },
  "visual_assets_rule": { ... }
}
```

#### Python 确定性数学换算

LLM 输出的时间边界经过 Python 的三步处理，转换为最终 JSON：

**1. 阶段边界规范化**：强制首阶段 `start_ms=0`，末阶段 `end_ms=total_ms`，相邻阶段首尾相接无空洞。

**2. 镜头阶段分配**（确定性，不依赖 LLM）：
```python
for phase in phases:
    if phase["start_ms"] <= shot.start_ms < phase["end_ms"]:
        belong_to_phase = phase["phase_id"]
```
按镜头起始时间落在哪个阶段的时间范围内确定归属，杜绝 LLM 幻觉。

**3. 节拍偏移量计算**：
```python
relative_beat_offset = sum(
    1 for beat in audio.beats_ms
    if phase_start_ms <= beat <= shot_trigger_ms
)
```
统计从阶段起点到镜头触发点之间经过了多少个节拍，得到与绝对时间无关的「节拍偏移量」。

**4. 转场与音效回填**：优先使用 LLM 的 `per_shot_annotations`，缺失时按规则推断：

| 剪辑用途 | 默认转场 | 默认转场时长 |
|---------|---------|-----------|
| HOOK_OPENER | 硬切 | 0.25 拍 |
| EMPHASIS_HIGHLIGHT | 缩放推进 | 0.5 拍 |
| TRANSITION_BRIDGE | 叠化 | 1.0 拍 |
| NARRATIVE_SUPPORT | 硬切 | 0.5 拍 |

| 情绪基调 | 默认音效 | 默认 BGM 行为 |
|---------|---------|-------------|
| HIGH_ENERGY | WHOOSH | NORMAL |
| NEUTRAL | NONE | DUCKING（为人声让路）|
| CALM | NONE | NORMAL |

---

## 输出数据结构

### `step1_audio.json`

```json
{
  "bpm": 125.0,
  "beats_ms": [480, 960, 1440, 1920, 2400, ...],
  "drops_ms": [30336, 102560, 191936],
  "duration_ms": 341012
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `bpm` | float | 每分钟节拍数，反映 BGM 整体速度 |
| `beats_ms` | int[] | 每个节拍的绝对毫秒时间戳，是弹性复用的基础计量单位 |
| `drops_ms` | int[] | 音频能量爆发点（高潮）的绝对时间戳，用作叙事阶段分界参考 |
| `duration_ms` | int | 视频总时长（毫秒） |

---

### `step2_transcript.json`

```json
{
  "full_text": "大家好，我是王冰冰。那这里呢就是查干湖最具特色的胖头鱼啦...",
  "sentences": [
    { "text": "大家好，我是王冰冰。", "start_ms": 14000, "end_ms": 15800 },
    { "text": "那这里呢就是查干湖最具特色的胖头鱼啦，个头大，分量还足。", "start_ms": 16000, "end_ms": 19800 }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `full_text` | string | 完整转录文本，所有句子拼接 |
| `sentences[].text` | string | 句子文字内容 |
| `sentences[].start_ms` | int | 句子起始时间（毫秒，相对视频起点）|
| `sentences[].end_ms` | int | 句子结束时间（毫秒）|

> 若视频以 BGM 为主无人声口播，`sentences` 为空列表属正常现象。

---

### `step3_visual.json`

```json
{
  "shots": [
    {
      "index": 0,
      "start_ms": 0,
      "end_ms": 840,
      "keyframe_path": "outputs/pipeline/.../keyframes/shot_000_0ms.jpg",
      "shot_type": "B_ROLL_SEMANTIC",
      "content_type": "SCENE",
      "emotional_tone": "NEUTRAL",
      "b_roll_semantic_prompt": "雪地里悬挂着系红绸带的鱼，旁有穿红衣女子，构图对称，色彩冷暖对比鲜明。",
      "camera_motion_effect": "静态",
      "editing_utility": "HOOK_OPENER"
    }
  ],
  "caption_info": {
    "font_family_type": "Sans-Serif-Bold",
    "css_style": "font-size: 36px; color: #FFFFFF; font-weight: bold;",
    "position_y_percentage": 50.0,
    "highlight_strategy": "核心词使用黄色#FFD700加粗"
  }
}
```

**`shots[]` 字段说明：**

| 字段 | 枚举值 / 类型 | 说明 |
|------|------------|------|
| `shot_type` | A_ROLL_CLOSE_UP / A_ROLL_MEDIUM / B_ROLL_SEMANTIC | A_ROLL 为有人物出镜，B_ROLL 为场景/产品镜头 |
| `content_type` | PRESENTER / PRODUCT / SCENE / TEXT_GRAPHIC | 画面主体内容类型 |
| `emotional_tone` | HIGH_ENERGY / NEUTRAL / CALM | 情绪基调，影响转场和音效选择 |
| `b_roll_semantic_prompt` | string（≤50字）| 纯视觉语义描述，**直接用于素材库向量检索** |
| `camera_motion_effect` | string | 运镜：静态 / 轻微放大 / 轻微缩小 / 左移 / 右移 / 震动 |
| `editing_utility` | HOOK_OPENER / NARRATIVE_SUPPORT / EMPHASIS_HIGHLIGHT / TRANSITION_BRIDGE | 该镜头的剪辑功能定位 |

---

### `elastic_template.json`（最终产物）

严格通过 JSON Schema（`pipeline/schema.py`）校验，由四个顶层模块组成。

#### 模块一：`style_metadata`

视频整体风格的语义标签。

```json
{
  "style_id": "life-vlog-winter-travel",
  "category": "Life_Record",
  "driving_mode": "TEXT_LOGIC_DRIVEN",
  "pacing_style": "STEADY_NARRATIVE",
  "visual_theme": "Natural_Outdoor",
  "sample_video_total_duration_ms": 341012,
  "tags": ["Vlog", "东北", "冬捕", "美食", "记者日常"]
}
```

| 字段 | 说明 |
|------|------|
| `style_id` | 全局唯一风格标识符（kebab-case），用于风格库检索 |
| `category` | 视频品类（Knowledge_Vlog / Product_Showcase / Life_Record / Movie_Montage 等）|
| `driving_mode` | **TEXT_LOGIC_DRIVEN**（口播/文案驱动，如知识科普）或 **AUDIO_VISUAL_EMOTION**（画面/音乐驱动，如混剪卡点）|
| `pacing_style` | HIGH_CONTRAST_FAST（快切对比）/ STEADY_NARRATIVE（平稳叙述）/ EMOTIONAL_SLOW（情感慢节奏）|
| `visual_theme` | 视觉主题（Minimalist_White / Dark_Cinematic / Natural_Outdoor / Vibrant_Color 等）|
| `sample_video_total_duration_ms` | 原始样本视频总时长，由 Python 填入，LLM 不参与 |
| `tags` | 内容标签，供检索过滤 |

---

#### 模块二：`storyline_structure`

视频的「章节目录」，由 LLM 自主规划，Python 填入精确时间数值。

```json
[
  {
    "phase_id": "PHASE_OPENING",
    "energy_level": "HIGH",
    "narrative_goal": "引入人物与场景，建立节日氛围与地域特色",
    "bgm_alignment_rule": "ALIGN_TO_BGM_START",
    "absolute_time_range": { "start_ms": 0, "end_ms": 30336, "duration_ms": 30336 },
    "relative_time_range": { "start_ratio": 0.0, "end_ratio": 0.089, "duration_ratio": 0.089 }
  },
  {
    "phase_id": "PHASE_STORY",
    "energy_level": "MEDIUM",
    "narrative_goal": "讲述冬捕文化与记者工作日常，穿插生活细节",
    "bgm_alignment_rule": "ALIGN_TO_FIRST_DROP",
    "absolute_time_range": { "start_ms": 30336, "end_ms": 191936, "duration_ms": 161600 },
    "relative_time_range": { "start_ratio": 0.089, "end_ratio": 0.5628, "duration_ratio": 0.4739 }
  }
]
```

| 字段 | 说明 |
|------|------|
| `phase_id` | 阶段标识符，格式 `PHASE_[A-Z][A-Z0-9_]*`，由 LLM 根据视频类型自主命名 |
| `energy_level` | LOW / MEDIUM / HIGH / PEAK，指导下游 Agent 在该阶段选择合适的剪辑密度 |
| `narrative_goal` | LLM 对该阶段叙事意图的文字描述，指导素材选取和剪辑风格 |
| `bgm_alignment_rule` | 复用时该阶段需对齐新 BGM 的哪个音频锚点（ALIGN_TO_BGM_START / FIRST_DROP 等）|
| `absolute_time_range` | 在原片中的绝对物理时间范围（毫秒），供理解参考 |
| `relative_time_range` | 归一化时间比例（0.0~1.0），**复用时按此比例拉伸到新视频时长** |

---

#### 模块三：`visual_assets_rule`

字幕排版规格，可直接映射为前端渲染代码。

```json
{
  "main_caption": {
    "font_family_type": "Sans-Serif-Bold",
    "css_style": "font-size: 36px; color: #FFFFFF; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);",
    "position_y_percentage": 78.0,
    "highlight_strategy": "核心关键词使用黄色（#FFD700）高亮显示"
  },
  "global_overlays": []
}
```

| 字段 | 说明 |
|------|------|
| `main_caption.font_family_type` | 字体族：Sans-Serif-Bold / Serif-Elegant / Handwritten / Monospace |
| `main_caption.css_style` | 可直接用于 Remotion `<Sequence>` style 属性的 CSS 字符串 |
| `main_caption.position_y_percentage` | 字幕纵向位置（0=顶部，100=底部），避开各平台 UI 安全区 |
| `main_caption.highlight_strategy` | 关键词高亮规则，供下游 LLM 生成带标注字幕时使用 |
| `global_overlays` | 全局覆盖层（进度条、水印、边框等），通常为空数组 |

---

#### 模块四：`dynamic_pacing_blueprint`

每个镜头的原子剪辑指令，是流水线最核心的输出。

```json
[
  {
    "belong_to_phase": "PHASE_STORY",
    "absolute_trigger_ms": 40320,
    "relative_beat_offset": 22,
    "shot_config": {
      "shot_type": "B_ROLL_SEMANTIC",
      "content_type": "SCENE",
      "emotional_tone": "CALM",
      "b_roll_semantic_prompt": "雪地里悬挂着系红绸带的鱼，旁有穿红衣女子，构图对称，色彩冷暖对比鲜明。",
      "camera_motion_effect": "静态",
      "editing_utility": "NARRATIVE_SUPPORT"
    },
    "transition_effect": { "type": "硬切", "duration_beats": 0.25 },
    "audio_sfx": { "trigger_sfx_type": "WHOOSH", "bgm_volume_behavior": "NORMAL" }
  }
]
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `belong_to_phase` | string | 所属叙事阶段（由 Python 按时间重叠确定性分配）|
| `absolute_trigger_ms` | int | 该镜头在原片中的触发时刻（毫秒），供参考理解 |
| `relative_beat_offset` | int | **弹性复用核心**：阶段起点后的第 N 个节拍处触发（见下方解析）|
| `shot_config.shot_type` | enum | 景别类型（见步骤3说明）|
| `shot_config.b_roll_semantic_prompt` | string | **直接用于素材库向量语义检索** |
| `shot_config.editing_utility` | enum | 该位置应选用何种类型素材 |
| `transition_effect.type` | string | 转场效果：硬切 / 叠化 / 淡入淡出 / 缩放推进 / 旋转切换 |
| `transition_effect.duration_beats` | float | 转场持续时长（以节拍为单位，确保与音乐速度同步）|
| `audio_sfx.trigger_sfx_type` | enum | 切镜头瞬间的音效：NONE / WHOOSH / POP / SWOOSH |
| `audio_sfx.bgm_volume_behavior` | enum | DUCKING（BGM 压低，为人声让路）/ NORMAL（正常响度）|

---

## `relative_beat_offset` 深度解析：弹性复用的核心

`relative_beat_offset` 存储的不是时间，而是**节拍序号**，这是模板实现跨 BPM 复用的关键机制。

**工作原理：**

```
原视频 BPM = 125，PHASE_STORY 起点 = 30336ms
镜头在原视频中触发于 40320ms
阶段起点到触发点之间有 22 个节拍
→ relative_beat_offset = 22

新视频 BPM = 150，新 PHASE_STORY 起点对应新 BGM 第一个 Drop
新第 22 个节拍 = Drop_time + 22 × (60000/150) = Drop_time + 8800ms
→ 该镜头在新视频中的触发时间自动对齐到第 22 拍，完美卡点
```

**下游使用方法：**

```python
# 给定新 BGM 的节拍时间戳列表和各阶段对应的新起始节拍索引
new_beats_ms = [0, 400, 800, 1200, ...]
phase_start_beat_idx = find_drop_beat_idx(new_beats_ms, new_bgm_drop_ms)

for entry in dynamic_pacing_blueprint:
    if entry["belong_to_phase"] == "PHASE_STORY":
        beat_idx = phase_start_beat_idx + entry["relative_beat_offset"]
        new_trigger_ms = new_beats_ms[beat_idx]
        # 在新视频 new_trigger_ms 处插入对应类型的素材
```

---

## CLI 参数说明

```
python pipeline.py <video.mp4> [选项]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mock` | False | 跳过所有模型推理，使用 Mock 数据，秒级完成（用于流程验证）|
| `--output-dir PATH` | outputs/pipeline/<stem> | 自定义输出目录 |
| `--max-shots N` | 30 | VL 分析的最大镜头数，超出时均匀采样 |
| `--analyze-all-shots` | False | 对所有检测到的镜头逐一分析，忽略 `--max-shots` 上限 |
| `--asr-backend` | qwen3-omni | ASR 后端：`qwen3-omni`（默认，与认知对齐合并加载）或 `qwen3-asr`（独立步骤）|
| `--language` | Chinese | ASR 语言提示（如 English / Japanese）|
| `--omni-use-video` | False | 认知对齐阶段同时将原始视频传入 Omni（需环境安装 ffmpeg）|
| `--forced-aligner-path PATH` | None | Qwen3-ForcedAligner 路径（仅 `qwen3-asr` 后端使用，用于句级时间戳）|

---

## 设计原则

### LLM 与 Python 的职责边界

| 职责 | 由谁负责 | 原因 |
|------|---------|------|
| 叙事阶段划分（时间边界） | LLM | 需要语义理解 |
| 风格标签、叙事目标 | LLM | 需要语义归纳 |
| 转场类型、音效建议 | LLM（兜底：规则推断） | 需要审美判断 |
| 镜头阶段归属（`belong_to_phase`）| Python（按时间重叠）| 确定性要求，LLM 索引易出现幻觉 |
| 节拍偏移量（`relative_beat_offset`）| Python（精确计数）| 数值计算，模型不可靠 |
| 时间比例（`start_ratio` 等）| Python（精确计算）| 数学运算 |
| 阶段边界规范化（首尾对齐）| Python（强制纠错）| LLM 的边界误差需硬性修正 |

### ASR 后端选择（实验验证结论）

| 方案 | 结果 | 推荐 |
|------|------|------|
| 视频模式 ASR（use_audio_in_video=True）| 需要系统级 ffmpeg，环境缺失时失败 | 不推荐（受环境限制）|
| Omni 分块 180 秒 | 输出 0 句（超长块导致 JSON 格式失稳）| 不推荐 |
| Omni 分块 60 秒 | 稳定输出句级时间戳（341s 视频得 60 句）| **推荐，当前默认** |

---

## 下游使用示例

最终只需将 `elastic_template.json` 提供给下游 LLM Agent：

```
以下是一个视频剪辑风格模板（elastic_template.json）。

请根据模板中的：
- style_metadata：了解视频品类和驱动模式
- storyline_structure：按叙事阶段结构组织新内容（相对时间比例可拉伸到任意时长）
- dynamic_pacing_blueprint[].b_roll_semantic_prompt：检索素材库，找到视觉语义匹配的新素材
- dynamic_pacing_blueprint[].relative_beat_offset：结合新 BGM 的节拍时间戳确定新的剪辑触发时间

结合以下新创作信息，生成 Remotion 时间线代码：
- 新脚本文案：...
- 新 BGM 节拍时间戳（ms）：[0, 400, 800, 1200, ...]
- 素材库检索结果：...

[粘贴 elastic_template.json 全文]
```

---

## 常见问题

**Q：`dynamic_pacing_blueprint` 中所有镜头都归属同一阶段？**  
A：这是旧版问题（LLM 用 shot_indices 指定镜头）。当前版本改为 LLM 输出时间边界，Python 按时间重叠确定性分配，已修复。

**Q：ASR 转录结果为空？**  
A：若视频以纯 BGM 为主无人声，空转录属正常。可通过 `--language English` 调整语言提示。若确认有人声但仍为空，检查分块大小（`_CHUNK_SEC = 60` in `text_processor.py`）。

**Q：Omni 推理 JSON 被截断怎么办？**  
A：流水线内置截断修复器（`_repair_truncated_json`）自动补全括号。若仍失败，可减少 `--max-shots`，缩短输入给 Omni 的镜头列表。

**Q：如何使用 `--omni-use-video`？**  
A：需要环境中安装了 `ffmpeg` 或 `avconv`（`qwen_omni_utils` 的视频音轨提取依赖）。若未安装，使用默认的分块音频 ASR 模式即可（效果相当）。

**Q：`--analyze-all-shots` 和 `--max-shots` 同时指定？**  
A：`--analyze-all-shots` 优先级更高，`--max-shots` 在全量分析模式下被忽略。

**Q：如何在没有 GPU 的环境验证流程？**  
A：使用 `--mock` 参数，跳过所有模型调用，返回结构完全一致的仿真数据，用于 CI/流程测试。
