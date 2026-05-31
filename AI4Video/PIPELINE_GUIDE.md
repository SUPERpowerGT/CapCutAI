# 视频剪辑结构提取流水线使用指南

## 一、完整链路说明

### 流水线结构

```
输入视频 (.mp4)
      │
      ├──▶ 步骤1 音频处理 (Librosa)
      │         提取 WAV → 计算 BPM、节拍时间点、高潮爆发点
      │         输出: step1_audio.json
      │
      ├──▶ 步骤2 语音转录 (Qwen3-ASR-1.7B)
      │         识别人声 → 输出全文 + 句级时间戳
      │         输出: step2_transcript.json
      │
      ├──▶ 步骤3 视觉分析 (像素差检测 + Qwen3-VL-8B)
      │         检测镜头切换点 → 截取关键帧 → 逐镜语义分析
      │         输出: step3_visual.json + keyframes/*.jpg
      │
      ▼
步骤4 认知对齐 (Qwen3-Omni-30B)
      聚合三路数据 → LLM 输出语义字段（叙事阶段时间边界）
      → Python 确定性计算数值字段（镜头阶段分配、节拍偏移）
      → Schema 校验
      输出: elastic_template.json  ◀── 最终交付物
```

### 模型分工

| 模型 | 职责 | 输出什么 |
|------|------|----------|
| Librosa | 音频信号处理 | BPM、节拍时间戳、高潮点 |
| Qwen3-ASR-1.7B | 语音识别 | 口播文字 + 句级时间戳 |
| Qwen3-VL-8B | 视觉理解 | 每镜头景别、内容类型、情绪基调、语义描述 |
| Qwen3-Omni-30B | 多模态推理 | 叙事阶段时间边界、风格标签、字幕规则 |
| Python（确定性） | 数学换算 | 绝对时间 → 相对比例、镜头阶段分配、节拍偏移量 |

> **关键设计原则**：LLM 只负责语义判断（叙事阶段划分、风格描述），所有数值字段（时间比例、节拍偏移、镜头阶段归属）由 Python 精确计算，杜绝模型「臆造数字」。

---

## 二、输出文件详解

### `step1_audio.json` — 音频特征（步骤1 产出）

来自 **Librosa** 对视频音轨的分析，记录音乐的节奏骨架。

```json
{
  "bpm": 156.25,
  "beats_ms": [1600, 1984, 2368, ...],
  "drops_ms": [18272, 45152, 63776],
  "duration_ms": 118210
}
```

| 字段 | 类型 | 含义 |
|------|------|------|
| `bpm` | float | 每分钟节拍数（Beat Per Minute），反映音乐整体速度感 |
| `beats_ms` | int[] | 每个节拍的绝对时间戳（毫秒）。核心字段，用于最终「节拍偏移量」计算 |
| `drops_ms` | int[] | 音频能量爆发点时间戳（毫秒），即俗称的「高潮」。步骤4中用作叙事阶段自然分界参考 |
| `duration_ms` | int | 视频总时长（毫秒） |

---

### `step2_transcript.json` — 语音转录（步骤2 产出）

来自 **Qwen3-ASR** 对视频人声轨道的转录，记录口播内容与说话时间。

```json
{
  "full_text": "大家好，今天我要分享...",
  "sentences": [
    { "text": "大家好，今天我要分享一个非常实用的技巧。", "start_ms": 1200, "end_ms": 3400 }
  ]
}
```

| 字段 | 类型 | 含义 |
|------|------|------|
| `full_text` | string | 完整转录文本（所有句子拼接） |
| `sentences` | object[] | 句级时间戳列表 |
| `sentences[].text` | string | 该句话的文字内容 |
| `sentences[].start_ms` | int | 该句话的起始时间（毫秒） |
| `sentences[].end_ms` | int | 该句话的结束时间（毫秒） |

> 若视频以 BGM 为主无口播，`sentences` 为空列表属正常现象。

---

### `step3_visual.json` — 视觉分镜分析（步骤3 产出）

来自 **像素差镜头检测 + Qwen3-VL** 对每个镜头关键帧的理解，记录视频的视觉结构。

```json
{
  "shots": [
    {
      "index": 0,
      "start_ms": 0,
      "end_ms": 10125,
      "keyframe_path": "outputs/pipeline/xxx/keyframes/shot_000_0ms.jpg",
      "shot_type": "A_ROLL_MEDIUM",
      "content_type": "PRESENTER",
      "emotional_tone": "HIGH_ENERGY",
      "b_roll_semantic_prompt": "主播面对镜头，背景整洁白色书房，神情自信",
      "camera_motion_effect": "静态",
      "editing_utility": "HOOK_OPENER"
    }
  ],
  "caption_info": {
    "font_family_type": "Sans-Serif-Bold",
    "css_style": "font-size: 36px; color: #FFFFFF; font-weight: bold;",
    "position_y_percentage": 78.0,
    "highlight_strategy": "核心关键词使用黄色高亮显示"
  }
}
```

#### `shots[]` 字段说明

| 字段 | 类型 | 含义 |
|------|------|------|
| `index` | int | 镜头序号（0开始） |
| `start_ms` | int | 镜头起始时间（毫秒） |
| `end_ms` | int | 镜头结束时间（毫秒） |
| `keyframe_path` | string | 该镜头代表帧截图的本地路径 |
| `shot_type` | enum | 景别类型：`A_ROLL_CLOSE_UP`（人物特写）/ `A_ROLL_MEDIUM`（人物中景）/ `B_ROLL_SEMANTIC`（场景/产品）|
| `content_type` | enum | 内容类型：`PRESENTER`（出镜讲解）/ `PRODUCT`（产品展示）/ `SCENE`（环境场景）/ `TEXT_GRAPHIC`（文字图形）|
| `emotional_tone` | enum | 情绪基调：`HIGH_ENERGY`（高能激昂）/ `NEUTRAL`（平稳叙述）/ `CALM`（舒缓情感）|
| `b_roll_semantic_prompt` | string | 画面视觉语义描述（50字以内），专为**素材库向量检索**设计，可直接用于相似素材检索 |
| `camera_motion_effect` | string | 运镜方式：静态 / 轻微放大 / 轻微缩小 / 左移 / 右移 / 震动 |
| `editing_utility` | enum | 剪辑用途：`HOOK_OPENER`（开头吸引）/ `NARRATIVE_SUPPORT`（叙事辅助）/ `EMPHASIS_HIGHLIGHT`（强调关键点）/ `TRANSITION_BRIDGE`（转场过渡）|

#### `caption_info` 字段说明

从各镜头字幕检测结果聚合的全局字幕样式（若视频无字幕则为 `null`）。

| 字段 | 类型 | 含义 |
|------|------|------|
| `font_family_type` | string | 字体大类（如 Sans-Serif-Bold） |
| `css_style` | string | 字幕 CSS 样式字符串，可直接应用于 Remotion/HyperFrames |
| `position_y_percentage` | float | 字幕纵向位置，0=顶部，100=底部（各镜头的中位数） |
| `highlight_strategy` | string | 关键词高亮规则描述 |

---

### `elastic_template.json` — 弹性剪辑模板（步骤4 最终产出）

来自 **Qwen3-Omni** 的语义聚合 + Python 确定性数学换算，是整个流水线的**核心交付物**，严格通过 JSON Schema 校验。

包含四大模块：`style_metadata` / `storyline_structure` / `visual_assets_rule` / `dynamic_pacing_blueprint`

---

#### 模块一：`style_metadata` — 风格元数据

```json
{
  "style_id": "knowledge-vlog-fast-paced",
  "category": "Knowledge_Vlog",
  "pacing_style": "HIGH_CONTRAST_FAST",
  "visual_theme": "Minimalist_White",
  "sample_video_total_duration_ms": 118210,
  "tags": ["口播", "知识分享", "极简风格"]
}
```

| 字段 | 类型 | 含义 |
|------|------|------|
| `style_id` | string | 风格唯一标识符（kebab-case），用于风格库检索和命名 |
| `category` | string | 视频品类（如 Knowledge_Vlog、Product_Showcase、Life_Record）|
| `pacing_style` | enum | 剪辑节奏风格：`HIGH_CONTRAST_FAST`（快切对比）/ `STEADY_NARRATIVE`（平稳叙述）/ `EMOTIONAL_SLOW`（情感慢节奏）|
| `visual_theme` | string | 视觉主题描述（如 Minimalist_White、Dark_Cinematic、Vibrant_Color）|
| `sample_video_total_duration_ms` | int | 原始样本视频总时长（毫秒），由 Python 填入，LLM 不参与 |
| `tags` | string[] | 内容标签列表，用于风格库分类检索 |

---

#### 模块二：`storyline_structure` — 叙事骨架

视频的「章节目录」，框定整个视频的宏观叙事结构。由 LLM 判断阶段边界，Python 计算所有时间数值。

```json
[
  {
    "phase_id": "PHASE_HOOK",
    "narrative_goal": "通过主播直视镜头快速建立信任，3秒内抓住观众注意力",
    "bgm_alignment_rule": "ALIGN_TO_BGM_START",
    "absolute_time_range": {
      "start_ms": 0,
      "end_ms": 18000,
      "duration_ms": 18000
    },
    "relative_time_range": {
      "start_ratio": 0.0,
      "end_ratio": 0.1524,
      "duration_ratio": 0.1524
    }
  }
]
```

**阶段 `phase_id` 说明：**

| 值 | 叙事阶段 | 典型内容 | 建议时长占比 |
|----|---------|---------|------------|
| `PHASE_HOOK` | 钩子吸引 | 开门见山的核心卖点、反常识结论、强烈视觉冲击 | 0%~15% |
| `PHASE_PROBLEM` | 痛点铺垫 | 描述用户痛点、建立共鸣、呈现问题背景 | 15%~40% |
| `PHASE_SOLUTION` | 解决方案 | 展示产品/方法/技巧，配合 B-roll 强化信任 | 40%~80% |
| `PHASE_CTA` | 行动引导 | 购买/关注/收藏号召，品牌露出，收尾 | 80%~100% |

**各字段说明：**

| 字段 | 类型 | 含义 |
|------|------|------|
| `phase_id` | enum | 叙事阶段标识符（见上表）|
| `narrative_goal` | string | 该阶段的导演意图与情绪设计（中文），指导素材选取和剪辑风格 |
| `bgm_alignment_rule` | enum | BGM 对齐规则：`ALIGN_TO_BGM_START`（从头对齐）/ `ALIGN_TO_FIRST_DROP`（第一高潮对齐）等，用于复用时 BGM 卡点适配 |
| `absolute_time_range.start_ms` | int | 该阶段在原片中的起始时间（毫秒）|
| `absolute_time_range.end_ms` | int | 该阶段在原片中的结束时间（毫秒）|
| `absolute_time_range.duration_ms` | int | 该阶段持续时长（毫秒）|
| `relative_time_range.start_ratio` | float | 起始时间占总时长的比例（0.0~1.0），用于等比例映射到任意时长的新视频 |
| `relative_time_range.end_ratio` | float | 结束时间比例 |
| `relative_time_range.duration_ratio` | float | 时长比例 |

---

#### 模块三：`visual_assets_rule` — 视觉资产规则

字幕排版规格与全局覆盖层定义，可直接映射为 CSS/Remotion 样式代码。

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

| 字段 | 类型 | 含义 |
|------|------|------|
| `main_caption.font_family_type` | string | 字体大类（如 Sans-Serif-Bold / Serif-Elegant）|
| `main_caption.css_style` | string | 完整 CSS 样式字符串，可直接用于 Remotion `<Sequence>` 的 style 属性 |
| `main_caption.position_y_percentage` | float | 字幕纵向位置（0=顶部，100=底部）|
| `main_caption.highlight_strategy` | string | 关键词高亮规则（供下游 LLM 生成字幕时使用）|
| `global_overlays` | object[] | 全局覆盖层列表（进度条、水印、边框等）；通常为空数组 |

---

#### 模块四：`dynamic_pacing_blueprint` — 微观剪辑蓝图

每个镜头的原子剪辑动作，是 `storyline_structure` 大纲之下的具体执行指令。每条记录对应一个被分析的镜头。

```json
[
  {
    "belong_to_phase": "PHASE_HOOK",
    "absolute_trigger_ms": 0,
    "relative_beat_offset": 0,
    "shot_config": {
      "shot_type": "A_ROLL_MEDIUM",
      "content_type": "PRESENTER",
      "emotional_tone": "HIGH_ENERGY",
      "b_roll_semantic_prompt": "主播面对镜头，背景整洁白色书房，神情自信",
      "camera_motion_effect": "静态",
      "editing_utility": "HOOK_OPENER"
    },
    "transition_effect": {
      "type": "硬切",
      "duration_beats": 0.5
    },
    "audio_sfx": {
      "trigger_sfx_type": "NONE",
      "bgm_volume_behavior": "NORMAL"
    }
  }
]
```

**顶层字段：**

| 字段 | 类型 | 含义 |
|------|------|------|
| `belong_to_phase` | enum | 该镜头所属的叙事阶段（对应 `storyline_structure` 中的 `phase_id`）。由 Python 按时间重叠确定性分配，不依赖 LLM |
| `absolute_trigger_ms` | int | 该镜头在原片中的触发时刻（毫秒）。即原片该镜头开始的绝对时间 |
| `relative_beat_offset` | int | **弹性核心字段**。该镜头触发点相对于所在阶段起点，经过了多少个节拍（整数计数）。复用时替换为新 BGM 的第 N 个节拍时间，剪辑点自动适配新音乐速度 |

**`shot_config` 字段（来自步骤3 VL 分析）：**

| 字段 | 类型 | 含义 |
|------|------|------|
| `shot_type` | enum | 景别：`A_ROLL_CLOSE_UP` / `A_ROLL_MEDIUM` / `B_ROLL_SEMANTIC` |
| `content_type` | enum | 内容类型：`PRESENTER` / `PRODUCT` / `SCENE` / `TEXT_GRAPHIC` |
| `emotional_tone` | enum | 情绪基调：`HIGH_ENERGY` / `NEUTRAL` / `CALM` |
| `b_roll_semantic_prompt` | string | 画面视觉语义描述，**可直接用于素材库向量检索**，寻找风格相似的新素材 |
| `camera_motion_effect` | string | 运镜方式（静态 / 轻微放大 / 左移 / 右移 / 震动等）|
| `editing_utility` | enum | 剪辑用途标签，指导新视频中对应位置应选用何种类型素材 |

**`transition_effect` 字段：**

| 字段 | 类型 | 含义 |
|------|------|------|
| `type` | string | 转场效果（硬切 / 淡入淡出 / 叠化 / 滑动等）|
| `duration_beats` | float | 转场持续时长（以节拍为单位，如 0.5 = 半拍，1.0 = 一拍）|

**`audio_sfx` 字段：**

| 字段 | 类型 | 含义 |
|------|------|------|
| `trigger_sfx_type` | enum | 该剪辑点触发的音效类型：`WHOOSH`（飞过音）/ `POP`（弹出音）/ `NONE`（无音效）|
| `bgm_volume_behavior` | enum | BGM 音量处理：`DUCKING`（背景音压低，突出口播）/ `NORMAL`（正常音量）|

---

## 三、关键字段深度解析

### `relative_beat_offset` — 弹性复用的核心

这是整个弹性模板最重要的设计。它记录的**不是时间，而是节拍序号**。

**工作原理：**

```
原视频 BGM BPM = 120，阶段起点 = 第0拍（0ms）
镜头A 触发时间 = 第4拍（2000ms）→ relative_beat_offset = 4

新视频 BGM BPM = 150，阶段起点 = 第0拍（0ms）
新第4拍时间 = 4 × (60000/150) = 1600ms
→ 镜头A 在新视频中应在 1600ms 触发，完美卡点
```

**下游使用方法：**

```python
# 给定新 BGM 的节拍时间戳列表
new_beats_ms = [0, 400, 800, 1200, 1600, ...]
phase_start_beat_index = 0  # 该阶段从第0拍开始

for blueprint_entry in phase_entries:
    beat_idx = phase_start_beat_index + blueprint_entry["relative_beat_offset"]
    new_trigger_ms = new_beats_ms[beat_idx]  # 新剪辑点时间
```

### `b_roll_semantic_prompt` — 向量检索接口

专为语义检索设计的文本描述，可直接输入 embedding 模型，在素材库中寻找视觉风格相似的替换素材：

```python
# 示例：使用 b_roll_semantic_prompt 检索素材库
query_vector = embed_model.encode(shot["b_roll_semantic_prompt"])
similar_assets = vector_db.search(query_vector, top_k=5)
```

---

## 四、AI 剪辑方案制定

### 应提供哪个文件？

**提供 `elastic_template.json`，这是唯一需要给下游 LLM 的文件。**

前三步的中间文件是原始感知数据，信息冗余；`elastic_template.json` 已完成聚合、归一化与数学换算，专为下游 Agent 设计。

### 典型 Prompt 示例

```
以下是一个视频剪辑风格模板（elastic_template.json），请根据这份模板的
storyline_structure 叙事骨架（相当于章节目录）和
dynamic_pacing_blueprint 微观剪辑蓝图（相当于每章的具体动作），
结合新脚本文案和新 BGM 的节拍时间戳列表，
生成新视频的 Remotion 时间线代码。

[粘贴 elastic_template.json 内容]

新脚本文案：...
新 BGM 节拍时间戳（ms）：[0, 480, 960, 1440, ...]
```

---

## 五、使用方法

### 基本命令

```bash
# 完整运行（需要所有模型权重）
python pipeline.py data/your_video.mp4

# Mock 模式（无需模型，快速测试流程）
python pipeline.py data/your_video.mp4 --mock

# 指定输出目录
python pipeline.py data/your_video.mp4 --output-dir /path/to/output

# 全量镜头分析（分析所有检测到的镜头，无采样上限）
python pipeline.py data/your_video.mp4 --analyze-all-shots

# Omni 同时感知原始视频（更强但更慢）
python pipeline.py data/your_video.mp4 --omni-use-video

# 调整最大分析镜头数（默认30；--analyze-all-shots 时此参数忽略）
python pipeline.py data/your_video.mp4 --max-shots 40

# 指定 ASR 语言
python pipeline.py data/your_video.mp4 --language English

# 查看所有参数
python pipeline.py --help
```

### 输出目录结构

```
outputs/pipeline/<video_stem>/
├── elastic_template.json   # ★ 最终弹性模板（提供给下游 LLM）
├── step1_audio.json        # 中间产物：音频特征（可用于验证 BPM 和节拍检测）
├── step2_transcript.json   # 中间产物：语音转录（可用于验证 ASR 质量）
├── step3_visual.json       # 中间产物：视觉分镜（可用于验证镜头检测和 VL 分析）
├── <video_stem>.wav        # 提取的音频缓存（可复用，避免重复提取）
└── keyframes/              # 各镜头关键帧截图
    ├── shot_000_0ms.jpg
    ├── shot_001_10125ms.jpg
    └── ...
```

### 模型路径配置

编辑 `pipeline.py` 顶部的配置区：

```python
ASR_MODEL_PATH  = "/path/to/Qwen3-ASR-1.7B"
VLM_MODEL_PATH  = "/path/to/Qwen3-VL-8B-Instruct"
OMNI_MODEL_PATH = "/path/to/Qwen3-Omni-30B-A3B-Instruct"
```

### 分步调试

每一步结束后均有中间 JSON 文件持久化到磁盘，可用于独立验证每步的输出质量。若某一步失败，可从任意步骤续跑，无需重新运行前面的步骤。

---

## 六、常见问题

**Q: 叙事覆盖率不到 100% 怎么办？**
A: 使用 `--analyze-all-shots` 参数，对所有检测到的镜头进行分析，消除因采样导致的尾部覆盖空白。

**Q: dynamic_pacing_blueprint 中各镜头都被分配到 PHASE_HOOK 怎么办？**
A: 这是旧版本的问题（LLM 用 shot_indices 指定镜头）。当前版本改为 LLM 输出时间边界（start_ms/end_ms），Python 按时间重叠确定性分配，不再依赖 LLM 的镜头索引判断，已修复。

**Q: ASR 转录结果为空或不准？**
A: 通过 `--language` 参数指定语言（如 `--language English`）。若视频无人声，空转录属正常。

**Q: Omni 推理 JSON 被截断怎么办？**
A: 流水线内置截断修复器会自动处理。若仍失败，可适当减少 `--max-shots`，缩短输入给 Omni 的镜头列表长度。

**Q: 如何只重跑某一个步骤？**
A: 直接修改对应的 `pipeline/step*.py` 文件后，用 Python 脚本手动调用对应函数并覆盖中间文件即可。中间 JSON 文件的保存使得每步可独立调试和重运行。

**Q: `--analyze-all-shots` 和 `--max-shots` 同时指定会怎样？**
A: `--analyze-all-shots` 优先级更高，`--max-shots` 在全量分析模式下被忽略。
