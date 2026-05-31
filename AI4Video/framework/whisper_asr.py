"""Whisper-large-v3-turbo Tester。

使用 HuggingFace transformers 的 `pipeline("automatic-speech-recognition", ...)`
封装, 支持 chunked long-form 转录与可选时间戳输出。
"""

from __future__ import annotations

from typing import Any

import torch
from transformers import (
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    pipeline,
)

from framework.audio_utils import load_wav_as_array
from framework.base import BaseTester


class WhisperASRTester(BaseTester):
    """Whisper-large-v3-turbo 的封装 (transformers 后端)。"""

    def __init__(
        self,
        model_path: str,
        name: str | None = None,
        dtype: torch.dtype = torch.float16,
        device: str = "cuda:0",
        chunk_length_s: int = 30,
        batch_size: int = 8,
        max_new_tokens: int = 440,
    ):
        super().__init__(model_path, name)
        self.dtype = dtype
        self.device = device
        self.chunk_length_s = chunk_length_s
        self.batch_size = batch_size
        self.max_new_tokens = max_new_tokens
        self.pipe = None

    def _load_model(self) -> None:
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_path,
            dtype=self.dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to(self.device)
        processor = AutoProcessor.from_pretrained(self.model_path)
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=self.dtype,
            device=self.device,
            chunk_length_s=self.chunk_length_s,
            batch_size=self.batch_size,
        )

    def _infer(self, media: str, prompt: str, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        # 把音频读成 numpy 数组, 避免依赖额外的 ffmpeg 二进制
        audio, sr = load_wav_as_array(media)
        assert sr == 16000, f"Whisper 期望 16kHz, 当前为 {sr}"

        generate_kwargs: dict[str, Any] = {"task": "transcribe"}
        language = (kwargs.get("language") or prompt or "").strip().lower()
        if language and language not in {"auto", "none"}:
            generate_kwargs["language"] = language

        return_timestamps = kwargs.get("return_time_stamps", False)

        result = self.pipe(
            {"raw": audio, "sampling_rate": sr},
            generate_kwargs=generate_kwargs,
            return_timestamps=return_timestamps,
        )

        extra: dict[str, Any] = {
            "language": generate_kwargs.get("language", "auto"),
            "return_time_stamps": return_timestamps,
        }
        if return_timestamps and isinstance(result, dict) and result.get("chunks"):
            extra["segments"] = [
                {
                    "start": ch.get("timestamp", (None, None))[0],
                    "end": ch.get("timestamp", (None, None))[1],
                    "text": ch.get("text", ""),
                }
                for ch in result["chunks"]
            ]
        return result["text"].strip(), extra
