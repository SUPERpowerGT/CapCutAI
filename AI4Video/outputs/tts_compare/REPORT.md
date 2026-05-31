# Qwen3-TTS 调研报告: CustomVoice vs VoiceDesign

> 测试日期: 2026-05-23
> 硬件: NVIDIA H20-3e (cuda:0), bf16 + flash-attention-2
> 模型权重根目录: `tts/`

---

## 1. 两类模型的能力定位

| 模型 | 控制方式 | 声音来源 | 适用场景 |
| --- | --- | --- | --- |
| `Qwen3-TTS-12Hz-1.7B-CustomVoice` | 选定**预置 speaker** + 可选自然语言 `instruct` 调节情绪/语气 | 9 种官方提供的高质量音色 (覆盖男女/年龄/方言/语种) | 角色固定、追求稳定性的产线场景 (有声书、配音、客服) |
| `Qwen3-TTS-12Hz-1.7B-VoiceDesign` | 完全由**自然语言 `instruct`** 描述目标音色 | 模型即时合成出符合描述的"虚拟人声" | 角色音定制、原型快速验证、避免侵权风险 |

两个模型同属 Qwen3-TTS 系列, 都基于 12Hz 离散多码本 LM 架构, 同样支持流式生成与 10 种语言。

代码加载/调用入口完全一致 (`Qwen3TTSModel.from_pretrained` → `generate_custom_voice` 或 `generate_voice_design`), 区别只在 **是否传 `speaker` 字段** 以及 **是否必须传 `instruct` 字段**。

---

## 2. 测试设计

### 2.1 CustomVoice — 同文本, 两个预置音色

- 文本: **"夜深了，我一个人坐在窗前，望着远处的灯火，心里突然涌起一股说不清的情绪。"**
- 选取的两个 speaker (官方表格里差异最大的中文男女组合):
  - **Vivian** — *Bright, slightly edgy young female voice* (年轻女性, 偏亮)
  - **Uncle_Fu** — *Seasoned male voice with a low, mellow timbre* (成熟男性, 低沉醇厚)
- 两次调用都不带 `instruct`, 仅靠 speaker 本身的音色差异。

### 2.2 VoiceDesign — 同文本, 两段自然语言描述

- 文本: **"听说，这次他真的回来了。已经整整十年了，谁也不曾忘记那个夏天发生的事。"**
- 两段差异极大的 `instruct`:
  - **elderly_male_narrator**: *"成熟稳重的中年男性嗓音，音色低沉浑厚，略带沙哑的颗粒感；语速偏慢，咬字清晰，带着沉思与追忆的气息，像是在讲述一段尘封的往事。"*
  - **lively_young_female**: *"活泼俏皮的少女声音，音调偏高，语速轻快灵动，句尾微微上扬，带着兴奋和八卦感，像是在和闺蜜分享一个惊人的消息。"*

### 2.3 评估方法 (客观可量化部分)

由于环境无法实际试听, 用以下两个 proxy 指标评估:

1. **文本保真度 (CER)** — 把生成的 wav 喂给 Whisper-large-v3-turbo 反向转录, 与原文做字符级 Levenshtein, 得到字符错误率 (CER, ↓)。CER 越低说明 TTS 念得越准。Whisper 缺标点本身会产生约 5-10% 的"伪 CER", 因此 ≤0.12 都可视为高保真。
2. **音色客观特征** — 用 `librosa.pyin` 估计基频 F0 (mean / std), 配合 RMS 能量与过零率 ZCR, 反映音高、能量与"亮度"差异。

---

## 3. 结果

### 3.1 CustomVoice 双角色

| 维度 | Vivian (年轻女声) | Uncle_Fu (成熟男声) |
| --- | ---: | ---: |
| 文本 | 夜深了，我一个人坐在窗前… (同) | 夜深了，我一个人坐在窗前… (同) |
| 时长 | 9.60 s | 9.44 s |
| 合成耗时 | 14.23 s | 13.54 s |
| Whisper 反转录 CER | **0.083** | **0.083** |
| F0 均值 | **294.0 Hz** (典型成年女声) | **197.6 Hz** (低沉男声) |
| F0 标准差 | 200.5 Hz (起伏丰富) | 175.6 Hz |
| 浊音占比 | 69.0% | 44.7% (更多气声/停顿) |
| RMS 能量 | 0.070 | 0.052 (更轻柔) |
| ZCR | 0.113 | 0.129 |

**观察**:

- 两次合成对参考文本的字面还原都是 **8.3% CER**, 全部 "错误" 来自 Whisper 自身不输出 `，` `。` 而非 TTS 漏字 → 转录字符与原文几乎完全一致, 文本保真度合格。
- F0 均值差异接近 **100 Hz**, 与官方对两个 speaker 的描述 (Bright young female vs Seasoned male) 完全吻合, 性别 / 年龄轴上的可分性非常显著。
- Uncle_Fu 浊音占比明显更低 (44.7% vs 69.0%), 说明气声/停顿更多, 听感上会更"沉思"; 这是 mellow 男声音色的典型特征。

### 3.2 VoiceDesign 双描述

| 维度 | 老叙事男声 (instruct A) | 活泼少女声 (instruct B) |
| --- | ---: | ---: |
| 文本 | 听说，这次他真的回来了… (同) | 听说，这次他真的回来了… (同) |
| 时长 | 8.88 s | 7.28 s (语速明显更快) |
| 合成耗时 | 12.71 s | 9.98 s |
| Whisper 反转录 CER | 0.114 | 0.086 |
| F0 均值 | **82.2 Hz** (深沉成年男性) | **419.4 Hz** (高亢少女) |
| F0 标准差 | **9.4 Hz** (极平稳) | 79.5 Hz (起伏丰富) |
| 浊音占比 | 48.9% | 70.8% |
| RMS 能量 | 0.079 | **0.128** (更响亮) |
| ZCR | 0.159 | 0.207 (高频成分更多) |

**观察**:

- F0 均值差异高达 **337 Hz** (82 Hz vs 419 Hz), 完全对应两段 instruct 的描述 ("低沉浑厚" vs "音调偏高")。
- F0 标准差差异巨大 (9.4 Hz vs 79.5 Hz): 老叙事男声基本是平直陈述; 少女声则带句尾上扬, 与 "句尾微微上扬, 兴奋和八卦感" 的描述完全一致。
- 时长差异 (8.88 s vs 7.28 s) 直接验证了 instruct 中 "语速偏慢" / "语速轻快灵动" 的控制。
- 少女声 RMS 能量比老男声高 60%+, 听感上更"近、更亮"。
- 老男声 CER 略高 (0.114), 主要还是来自 Whisper 没输出标点; 字面文字本身没有漏字。

---

## 4. 横向对比与结论

| 维度 | CustomVoice | VoiceDesign |
| --- | --- | --- |
| 音色一致性 | ✅ 同一 speaker 多次调用音色稳定 (官方保证) | ⚠️ 同一 instruct 多次调用可能略有抖动, 适合做参考音 |
| 调用复杂度 | 极简: 选 speaker 即可 | 需要写好自然语言 prompt, prompt 工程量大 |
| 表达力上限 | 受预置音色约束, 极端风格需配 `instruct` | 可生成任何描述得出的虚构音色, 上限更高 |
| 商用风险 | 预置音色已授权 | 不依赖具体真人, 不易侵权 |
| 平均推理时长 (本测试, 9 秒输出) | ~13.9 s | ~11.3 s |
| 平均文本保真度 (CER) | 0.083 | 0.100 |
| 同一段中文 (~30 字) 的两次音色差异 | F0 差 96 Hz | F0 差 337 Hz |

**结论**:

1. **稳定生产首选 CustomVoice**: 9 种音色覆盖了常见的男女、年龄、方言组合, 文本保真高 (CER 8.3%) 且参数简单, 适合做固定角色配音、产品 TTS。
2. **风格定制首选 VoiceDesign**: 通过自然语言描述, 可实现极端音高 (本测试达到 82 Hz / 419 Hz 两端) 与极端语速差异, 自由度最大; 文本保真度仍然处于可接受水平 (CER ≤ 0.114), 适合做角色音原型、不愿与真人音色绑定的场景。
3. 两个模型 API 几乎可平替, 切换只需把 `generate_custom_voice(...)` 换成 `generate_voice_design(...)`, 并相应地把 `speaker` 替换为 `instruct`。
4. VoiceDesign 的 instruct 越具体, 控制越精准 (本测试两段 instruct 都明确写出了"音调/语速/语气", 因此 F0 / 时长 / 能量都能被精确驱动)。

---

## 5. 核心调用代码

### 5.1 加载模型 (两个模型完全一致)

```python
import torch
from qwen_tts import Qwen3TTSModel

model = Qwen3TTSModel.from_pretrained(
    "<本地权重目录, 例如 .../Qwen3-TTS-12Hz-1.7B-CustomVoice>",
    device_map="cuda:0",
    dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",  # 需提前 pip install flash-attn
)
```

### 5.2 CustomVoice: 选预置 speaker

```python
# 单条
wavs, sr = model.generate_custom_voice(
    text="夜深了，我一个人坐在窗前，望着远处的灯火，心里突然涌起一股说不清的情绪。",
    language="Chinese",      # 也支持 "Auto"
    speaker="Vivian",        # 9 种之一: Vivian / Serena / Uncle_Fu / Dylan / Eric / Ryan / Aiden / Ono_Anna / Sohee
    instruct=None,           # 可选, 例如 "用特别愤怒的语气说"
)
sf.write("vivian.wav", wavs[0], sr)

# 批量 (节省 prefill 开销)
wavs, sr = model.generate_custom_voice(
    text=["...句 1...", "...句 2..."],
    language=["Chinese", "English"],
    speaker=["Vivian", "Ryan"],
    instruct=["", "Very happy."],
)
```

可用 speaker / language 在运行时查询:

```python
model.get_supported_speakers()   # ['aiden', 'dylan', 'eric', 'ono_anna', 'ryan', 'serena', 'sohee', 'uncle_fu', 'vivian']
model.get_supported_languages()  # ['auto', 'chinese', 'english', 'french', ..., 'korean']
```

### 5.3 VoiceDesign: 用自然语言描述声音

```python
# 单条
wavs, sr = model.generate_voice_design(
    text="听说，这次他真的回来了。已经整整十年了，谁也不曾忘记那个夏天发生的事。",
    language="Chinese",
    instruct="成熟稳重的中年男性嗓音，音色低沉浑厚，略带沙哑的颗粒感；语速偏慢，咬字清晰，带着沉思与追忆的气息。",
)
sf.write("design_male.wav", wavs[0], sr)

# 批量
wavs, sr = model.generate_voice_design(
    text=["...A...", "...B..."],
    language=["Chinese", "English"],
    instruct=[
        "低沉浑厚的中年男性...",
        "Speak in an incredulous tone, but with a hint of panic..."
    ],
)
```

### 5.4 复用部分参数

`generate_custom_voice` / `generate_voice_design` 都接收 HuggingFace `model.generate` 的 kwargs (`top_p`, `max_new_tokens` 等), 可以按需调节采样行为。

---

## 6. 产物清单

```
outputs/tts_compare/
├── custom_vivian_chinese.wav          # CustomVoice / Vivian (女)
├── custom_uncle_fu_chinese.wav        # CustomVoice / Uncle_Fu (男)
├── design_elderly_male_narrator.wav   # VoiceDesign / 老叙事男声
├── design_lively_young_female.wav     # VoiceDesign / 活泼少女声
├── metadata.json                      # 每条音频的合成参数 + 时长 + 延迟
├── analysis.json                      # Whisper 反转录 + CER + 声学统计
└── REPORT.md                          # 本报告
```

复现入口:

```bash
cd AI4Video
python run_tts_compare.py        # 4 段 wav + metadata.json
python analyze_tts_outputs.py    # CER + 声学统计 -> analysis.json
```

---

## 7. 环境关键事项

- `pip install -U qwen-tts` 会拉取 `torchaudio` 作为依赖, 但 NGC PyTorch 2.9.0a0 + CUDA 13 与 PyPI 上 `torchaudio` 的 cu12 / cu13 ABI 不严格匹配; 解决办法: `pip install --no-deps "torchaudio==2.9.*" --index-url https://download.pytorch.org/whl/cpu` (CPU build 不做 CUDA 版本检查, qwen-tts 实际只用到 torchaudio 的 IO/重采样)。
- `flash-attention-2` 已存在 (`flash_attn 2.7.4.post1`), 推理时显式传 `attn_implementation="flash_attention_2"` 即可启用。
- 推理峰值显存 ~12 GB 单卡, H20 单卡完全够用; 模型本体 ~3.8 GB safetensors。
