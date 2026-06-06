"""Qwen3-ASR-1.7B Tester。

依赖官方 qwen-asr 包 (pip install qwen-asr)。
该包封装了 transformers / vLLM 两种后端, 此处使用 transformers 后端。
"""

from __future__ import annotations

import time
from typing import Any

import torch
from qwen_asr import Qwen3ASRModel

from framework.base import BaseTester, TaskResult


class Qwen3ASRTester(BaseTester):
    """Qwen3-ASR-1.7B 的封装。"""

    def __init__(
        self,
        model_path: str,
        name: str | None = None,
        dtype: torch.dtype = torch.bfloat16,
        device: str = "cuda:0",
        max_inference_batch_size: int = 8,
        max_new_tokens: int = 1024,
        attn_implementation: str | None = "flash_attention_2",
    ):
        super().__init__(model_path, name)
        self.dtype = dtype
        self.device = device
        self.max_inference_batch_size = max_inference_batch_size
        self.max_new_tokens = max_new_tokens
        self.attn_implementation = attn_implementation
        self.model: Qwen3ASRModel | None = None

    def _load_model(self) -> None:
        kwargs: dict[str, Any] = {
            "dtype": self.dtype,
            "device_map": self.device,
            "max_inference_batch_size": self.max_inference_batch_size,
            "max_new_tokens": self.max_new_tokens,
        }
        if self.attn_implementation:
            kwargs["attn_implementation"] = self.attn_implementation
        self.model = Qwen3ASRModel.from_pretrained(self.model_path, **kwargs)

    def _infer(self, media: str, prompt: str, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        """对单条音频做转录。

        prompt 在 ASR 场景下用于传递 language hint (例如 "Chinese" / "English") 或 None。
        如需让模型自动识别, 传入空字符串或 "auto"。
        """
        language = kwargs.get("language")
        if not language:
            language = prompt.strip() if prompt and prompt.strip().lower() != "auto" else None

        results = self.model.transcribe(
            audio=media,
            language=language,
            return_time_stamps=kwargs.get("return_time_stamps", False),
        )
        result = results[0]
        extra = {
            "language": getattr(result, "language", None),
            "return_time_stamps": kwargs.get("return_time_stamps", False),
        }
        # 如有 segment 时间戳, 一并保存
        if hasattr(result, "segments") and result.segments:
            extra["segments"] = [
                {
                    "start": getattr(seg, "start", None),
                    "end": getattr(seg, "end", None),
                    "text": getattr(seg, "text", None),
                }
                for seg in result.segments
            ]
        return result.text, extra

    # 覆盖 run_tasks: ASR 通常只有 1 个核心任务 (转录), 但保留多 prompt 形式以支持
    # "强制中文 / 强制英文 / 自动识别" 等多组对比, 复用基类即可。
