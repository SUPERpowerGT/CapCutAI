"""步骤2: 语音转文字，支持两种后端：

后端A  Qwen3-ASR-1.7B（默认）
  - 精准 ASR 专用模型，速度快，自动分 chunk 处理长音频
  - 文本截断修复：max_new_tokens=4096（官方默认 512 不够用）
  - 句级时间戳：需额外加载 Qwen3-ForcedAligner-0.6B；不可用时返回空列表

后端B  Qwen3-Omni（可选）
  - 将 WAV 切为 3 分钟 chunk，逐段请求 Omni 输出 JSON 句级时间戳
  - 自动合并并修正绝对时间偏移
  - 适合已加载 Omni 或无强制对齐模型的场景
"""

from __future__ import annotations

import gc
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any


# ---- 数据结构 ----

@dataclass
class SentenceTimestamp:
    text: str
    start_ms: int
    end_ms: int


@dataclass
class TranscriptResult:
    full_text: str
    sentences: list[SentenceTimestamp] = field(default_factory=list)


# ============================================================
# 后端A: Qwen3-ASR
# ============================================================

def run_asr(
    model_path: str,
    video_path: str | Path,
    language: str = "Chinese",
    wav_cache_path: str | Path | None = None,
    forced_aligner_path: str | None = None,
    attn_implementation: str = "flash_attention_2",
    max_new_tokens: int = 4096,
) -> TranscriptResult:
    """Qwen3-ASR 转录。

    参数说明：
    - max_new_tokens: 每个 chunk 的最大输出 token 数。官方默认 512 会对长音频截断，
      此处默认 4096（与官方 benchmark 设置一致）。
    - forced_aligner_path: 若提供 Qwen3-ForcedAligner-0.6B 的本地路径，则开启句级时间戳；
      否则 sentences 返回空列表。
    """
    import torch
    from qwen_asr import Qwen3ASRModel
    from framework.audio_utils import extract_audio_from_video

    video_path = Path(video_path)

    if wav_cache_path and Path(wav_cache_path).exists():
        wav_path = Path(wav_cache_path)
    else:
        wav_path = extract_audio_from_video(video_path, wav_cache_path)

    print(f"[ASR] 加载模型: {model_path}  (max_new_tokens={max_new_tokens})")

    use_timestamps = forced_aligner_path is not None
    model = Qwen3ASRModel.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        device_map="cuda:0",
        attn_implementation=attn_implementation,
        max_new_tokens=max_new_tokens,
        forced_aligner=forced_aligner_path if use_timestamps else None,
        forced_aligner_kwargs={"dtype": torch.bfloat16, "device_map": "cuda:0"} if use_timestamps else None,
    )

    if use_timestamps:
        print("[ASR] 使用 ForcedAligner 输出句级时间戳...")
        try:
            results = model.transcribe(audio=str(wav_path), language=language, return_time_stamps=True)
            result = results[0]
            sentences = _parse_forced_align_items(result)
            full_text = result.text or ""
        except Exception as e:
            print(f"[ASR] ForcedAligner 失败（{e}），退回纯文本模式")
            results = model.transcribe(audio=str(wav_path), language=language, return_time_stamps=False)
            result = results[0]
            full_text = result.text or ""
            sentences = []
    else:
        print("[ASR] 纯转录模式（无强制对齐模型，sentences 为空）")
        results = model.transcribe(audio=str(wav_path), language=language, return_time_stamps=False)
        result = results[0]
        full_text = result.text or ""
        sentences = []

    del model
    gc.collect()
    torch.cuda.empty_cache()

    return TranscriptResult(full_text=full_text, sentences=sentences)


def _parse_forced_align_items(result) -> list[SentenceTimestamp]:
    """从 ForcedAlignResult 的字符/词级 items 聚合为句级时间戳。

    ASRTranscription.time_stamps 是 ForcedAlignResult，
    其 .items 是 List[ForcedAlignItem]，每项含 text/start_time/end_time（秒）。
    按中文标点或时间间隔（>0.8s）聚合为句子。
    """
    time_stamps = getattr(result, "time_stamps", None)
    if time_stamps is None:
        return []

    items = getattr(time_stamps, "items", None)
    if not items:
        return []

    sentences: list[SentenceTimestamp] = []
    buf_text = ""
    buf_start: float | None = None
    buf_end: float = 0.0
    PAUSE_THRESHOLD = 0.8  # 静音超过此值则强制断句（秒）

    for item in items:
        text = (item.text or "").strip()
        start = float(item.start_time)
        end = float(item.end_time)

        if not text:
            continue

        # 若有明显静音间隔，先提交当前句
        if buf_start is not None and (start - buf_end) > PAUSE_THRESHOLD:
            if buf_text.strip():
                sentences.append(SentenceTimestamp(
                    text=buf_text.strip(),
                    start_ms=int(buf_start * 1000),
                    end_ms=int(buf_end * 1000),
                ))
            buf_text = ""
            buf_start = None

        if buf_start is None:
            buf_start = start
        buf_text += text
        buf_end = end

        # 遇到句末标点则断句
        if text in ("。", "！", "？", ".", "!", "?", "…", "……"):
            sentences.append(SentenceTimestamp(
                text=buf_text.strip(),
                start_ms=int(buf_start * 1000),
                end_ms=int(buf_end * 1000),
            ))
            buf_text = ""
            buf_start = None

    # 尾部残余
    if buf_text.strip() and buf_start is not None:
        sentences.append(SentenceTimestamp(
            text=buf_text.strip(),
            start_ms=int(buf_start * 1000),
            end_ms=int(buf_end * 1000),
        ))

    return sentences


# ============================================================
# 后端B: Qwen3-Omni ASR
# ============================================================

_CHUNK_SEC = 60         # 每段最大时长（秒）；60s 是 Omni ASR JSON 输出稳定的上限
_OMNI_SAMPLE_RATE = 16000

_ASR_OMNI_PROMPT = """请对以上音频内容进行语音识别，以 JSON 格式输出句子级别的转录结果。

严格按以下格式输出，不要添加任何额外文字：
{"sentences": [{"text": "句子文本", "start_sec": 0.0, "end_sec": 2.5}]}

要求：
1. 按自然语句断句（句号、问号、感叹号等）
2. start_sec 和 end_sec 是该句相对于本段音频起始的秒数（浮点数，精度 0.1s）
3. 若音频无人声或完全静音，返回 {"sentences": []}
4. 不要识别背景音乐，只识别人声口播"""


def run_asr_with_omni(
    model_path: str,
    video_path: str | Path,
    wav_cache_path: str | Path | None = None,
    language: str = "Chinese",
    max_new_tokens: int = 2048,
    attn_implementation: str = "flash_attention_2",
) -> TranscriptResult:
    """使用 Qwen3-Omni 进行语音识别，输出含句级时间戳的转录结果。

    将长音频切为 3 分钟 chunk，每段独立请求 Omni 输出 JSON，
    再按时间偏移合并为完整转录。
    """
    import numpy as np
    import soundfile as sf
    import torch
    from framework.audio_utils import extract_audio_from_video
    from qwen_omni_utils import process_mm_info
    from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor

    video_path = Path(video_path)

    # 提取/复用 WAV
    if wav_cache_path and Path(wav_cache_path).exists():
        wav_path = Path(wav_cache_path)
    else:
        wav_path = extract_audio_from_video(video_path, wav_cache_path)

    # 读取 WAV 为 numpy 数组（16kHz mono float32）
    audio_array, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
    if sr != _OMNI_SAMPLE_RATE:
        import librosa
        audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=_OMNI_SAMPLE_RATE)
    if audio_array.ndim > 1:
        audio_array = audio_array.mean(axis=1)

    total_sec = len(audio_array) / _OMNI_SAMPLE_RATE
    print(f"[Omni-ASR] 音频总时长: {total_sec:.1f}s，切分为 {int(total_sec / _CHUNK_SEC) + 1} 段")

    # 加载 Omni 模型
    print(f"[Omni-ASR] 加载 Omni 模型: {model_path}")
    model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
        model_path,
        dtype="auto",
        device_map="auto",
        attn_implementation=attn_implementation,
    )
    processor = Qwen3OmniMoeProcessor.from_pretrained(model_path)

    all_sentences: list[SentenceTimestamp] = []
    chunk_start_sec = 0.0
    chunk_idx = 0

    while chunk_start_sec < total_sec:
        chunk_end_sec = min(chunk_start_sec + _CHUNK_SEC, total_sec)
        chunk_arr = audio_array[
            int(chunk_start_sec * _OMNI_SAMPLE_RATE): int(chunk_end_sec * _OMNI_SAMPLE_RATE)
        ]
        chunk_idx += 1
        print(f"[Omni-ASR] 处理片段 {chunk_idx}: {chunk_start_sec:.1f}s ~ {chunk_end_sec:.1f}s")

        lang_hint = f"请以{language}语言识别。" if language else ""
        prompt = lang_hint + _ASR_OMNI_PROMPT

        # 构建消息（audio-only，不传视频）
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "你是专业语音识别助手，擅长准确转录口播内容并输出时间戳。"}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio": chunk_arr},
                    {"type": "text", "text": prompt},
                ],
            },
        ]

        text_input = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(messages, use_audio_in_video=False)

        inputs = processor(
            text=text_input,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True,
            use_audio_in_video=False,
        ).to(model.device).to(model.dtype)

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                thinker_return_dict_in_generate=True,
                use_audio_in_video=False,
                return_audio=False,
            )

        text_ids = outputs[0] if isinstance(outputs, tuple) else outputs
        sequences = text_ids.sequences if hasattr(text_ids, "sequences") else text_ids
        in_len = inputs["input_ids"].shape[1]
        response = processor.batch_decode(sequences[:, in_len:], skip_special_tokens=True)[0]

        chunk_sentences = _parse_omni_asr_response(response, offset_sec=chunk_start_sec)
        all_sentences.extend(chunk_sentences)
        print(f"[Omni-ASR] 片段 {chunk_idx} 识别 {len(chunk_sentences)} 句")

        chunk_start_sec = chunk_end_sec

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()

    full_text = "".join(s.text for s in all_sentences)
    return TranscriptResult(full_text=full_text, sentences=all_sentences)


def transcribe_with_loaded_omni(
    model: Any,
    processor: Any,
    audio_array: "np.ndarray",
    language: str = "Chinese",
    max_new_tokens: int = 2048,
) -> TranscriptResult:
    """使用已加载的 Omni 模型对音频进行分块转录，返回含句级时间戳的转录结果。

    不加载/卸载模型，供 orchestrator 在共享同一个 Omni 实例时调用，
    从而避免重复的模型初始化开销。
    """
    import numpy as np
    from qwen_omni_utils import process_mm_info
    import torch

    total_sec = len(audio_array) / _OMNI_SAMPLE_RATE
    all_sentences: list[SentenceTimestamp] = []
    chunk_start_sec = 0.0
    chunk_idx = 0

    while chunk_start_sec < total_sec:
        chunk_end_sec = min(chunk_start_sec + _CHUNK_SEC, total_sec)
        chunk_arr = audio_array[
            int(chunk_start_sec * _OMNI_SAMPLE_RATE): int(chunk_end_sec * _OMNI_SAMPLE_RATE)
        ]
        chunk_idx += 1
        print(f"[Omni-ASR] 处理片段 {chunk_idx}: {chunk_start_sec:.1f}s ~ {chunk_end_sec:.1f}s")

        lang_hint = f"请以{language}语言识别。" if language else ""
        prompt = lang_hint + _ASR_OMNI_PROMPT

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "你是专业语音识别助手，擅长准确转录口播内容并输出时间戳。"}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio": chunk_arr},
                    {"type": "text", "text": prompt},
                ],
            },
        ]

        text_input = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(messages, use_audio_in_video=False)

        inputs = processor(
            text=text_input,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True,
            use_audio_in_video=False,
        ).to(model.device).to(model.dtype)

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                thinker_return_dict_in_generate=True,
                use_audio_in_video=False,
                return_audio=False,
            )

        text_ids = outputs[0] if isinstance(outputs, tuple) else outputs
        sequences = text_ids.sequences if hasattr(text_ids, "sequences") else text_ids
        in_len = inputs["input_ids"].shape[1]
        response = processor.batch_decode(sequences[:, in_len:], skip_special_tokens=True)[0]

        chunk_sentences = _parse_omni_asr_response(response, offset_sec=chunk_start_sec)
        all_sentences.extend(chunk_sentences)
        print(f"[Omni-ASR] 片段 {chunk_idx} 识别 {len(chunk_sentences)} 句")

        chunk_start_sec = chunk_end_sec

    full_text = "".join(s.text for s in all_sentences)
    return TranscriptResult(full_text=full_text, sentences=all_sentences)


def _parse_omni_asr_response(response: str, offset_sec: float = 0.0) -> list[SentenceTimestamp]:
    """解析 Omni ASR 输出的 JSON，提取句级时间戳并加上 chunk 时间偏移。"""
    try:
        m = re.search(r"\{[\s\S]*\}", response)
        if not m:
            return []
        data = json.loads(m.group())
        raw_sentences = data.get("sentences", [])
        result = []
        for s in raw_sentences:
            text = (s.get("text") or "").strip()
            if not text:
                continue
            start_sec = float(s.get("start_sec", 0.0)) + offset_sec
            end_sec = float(s.get("end_sec", start_sec + 1.0)) + offset_sec
            result.append(SentenceTimestamp(
                text=text,
                start_ms=int(start_sec * 1000),
                end_ms=int(end_sec * 1000),
            ))
        return result
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


# ============================================================
# ASR-VL 时间戳对齐
# ============================================================

def align_transcript_to_shots(
    transcript: TranscriptResult,
    shots: list,          # list[ShotAnalysis]（避免循环导入，用 Any 类型）
    overlap_threshold: float = 0.2,
) -> dict[int, dict]:
    """将 ASR 转录结果按时间戳重叠对齐到 VL 镜头分析结果。

    算法：
      对每个镜头 [shot.start_ms, shot.end_ms]，遍历所有句子，
      计算重叠时长占句子时长的比例；超过 overlap_threshold 则归属该镜头。
      同一句话可同时归属多个镜头（跨镜句子）。

    参数：
      overlap_threshold: 句子时长中至少有多大比例落在镜头内才被纳入（默认 0.2）。
        设为 0.2 是因为 Omni 时间戳精度约 ±1~3s，需容忍一定误差。

    返回：
      dict，key=shot.index，value={"aligned_text": str, "sentence_count": int}
    """
    result: dict[int, dict] = {}

    for shot in shots:
        shot_start = shot.start_ms
        shot_end = shot.end_ms
        aligned: list[str] = []

        for sent in transcript.sentences:
            sent_dur = sent.end_ms - sent.start_ms
            if sent_dur <= 0:
                continue

            overlap_start = max(sent.start_ms, shot_start)
            overlap_end = min(sent.end_ms, shot_end)
            overlap_ms = max(0, overlap_end - overlap_start)

            if overlap_ms / sent_dur >= overlap_threshold:
                aligned.append(sent.text)

        result[shot.index] = {
            "aligned_text": "".join(aligned),
            "sentence_count": len(aligned),
        }

    return result
