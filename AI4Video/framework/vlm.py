"""Qwen 系列 VLM (Qwen2.5-VL / Qwen3-VL) 视频理解 Tester。

两个模型同属 Qwen-VL 家族, 推理调用方式高度一致:
    - chat template -> processor -> model.generate
    - 视频通过 qwen_vl_utils.process_vision_info 预处理

通过 AutoModelForImageTextToText 统一加载, 自动适配两种 architecture。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from qwen_vl_utils import process_vision_info
from transformers import AutoModelForImageTextToText, AutoProcessor

from framework.base import BaseTester


class QwenVLTester(BaseTester):
    """Qwen2.5-VL / Qwen3-VL 通用视频理解 Tester。"""

    def __init__(
        self,
        model_path: str,
        name: str | None = None,
        fps: float = 1.0,
        min_pixels: int = 4 * 28 * 28,
        max_pixels: int = 256 * 28 * 28,
        max_new_tokens: int = 1024,
        attn_implementation: str = "flash_attention_2",
        dtype: torch.dtype = torch.bfloat16,
    ):
        super().__init__(model_path, name)
        self.fps = fps
        self.min_pixels = min_pixels
        self.max_pixels = max_pixels
        self.max_new_tokens = max_new_tokens
        self.attn_implementation = attn_implementation
        self.dtype = dtype
        self.model = None
        self.processor = None

    def _load_model(self) -> None:
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_path,
            dtype=self.dtype,
            attn_implementation=self.attn_implementation,
            device_map="auto",
        )
        self.processor = AutoProcessor.from_pretrained(self.model_path)

    def _build_messages(self, video_path: str, prompt: str) -> list[dict]:
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video",
                        "video": f"file://{Path(video_path).resolve()}",
                        "fps": self.fps,
                        "min_pixels": self.min_pixels,
                        "max_pixels": self.max_pixels,
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

    def _infer(self, media: str, prompt: str, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        messages = self._build_messages(media, prompt)
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        # return_video_metadata=True 时, video_inputs[i] 是 (tensor, metadata_dict) 元组,
        # metadata 包含原始 fps 与抽帧索引, 是 Qwen3-VL 计算时间戳所必需的。
        image_inputs, video_inputs, video_kwargs = process_vision_info(
            messages, return_video_kwargs=True, return_video_metadata=True
        )

        # 拆元组: 视频张量列表 + 元数据列表 (Qwen2.5-VL 会忽略 video_metadata, 安全)
        video_tensors, video_metadata = None, None
        if video_inputs is not None and len(video_inputs) > 0:
            if isinstance(video_inputs[0], tuple) and len(video_inputs[0]) == 2:
                video_tensors = [v[0] for v in video_inputs]
                video_metadata = [v[1] for v in video_inputs]
            else:
                video_tensors = video_inputs

        # transformers>=5.x processor 要求 fps 为标量, 此处兼容 qwen-vl-utils 返回 list
        fps_val = video_kwargs.get("fps")
        if isinstance(fps_val, list) and len(fps_val) == 1:
            video_kwargs["fps"] = fps_val[0]

        processor_kwargs: dict[str, Any] = dict(video_kwargs)
        if video_metadata is not None:
            processor_kwargs["video_metadata"] = video_metadata

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_tensors,
            padding=True,
            return_tensors="pt",
            **processor_kwargs,
        ).to(self.model.device)

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_new_tokens", self.max_new_tokens),
                repetition_penalty=kwargs.get("repetition_penalty", 1.05),
            )

        trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        answer = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        # 仅保留可 JSON 序列化的字段
        meta_summary = None
        if video_metadata:
            m = video_metadata[0]
            meta_summary = {
                "original_fps": m.get("fps") if isinstance(m, dict) else None,
                "num_sampled_frames": (
                    int(m["frames_indices"].numel())
                    if isinstance(m, dict) and "frames_indices" in m
                    else None
                ),
            }
        extra = {
            "num_video_frames": (
                video_tensors[0].shape[0] if video_tensors is not None and len(video_tensors) > 0 else 0
            ),
            "sampled_fps": video_kwargs.get("fps"),
            "video_metadata": meta_summary,
        }
        return answer, extra
