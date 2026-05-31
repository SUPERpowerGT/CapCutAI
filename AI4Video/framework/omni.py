"""Qwen3-Omni-30B-A3B-Instruct Tester。

与 VLM 不同之处:
    - 使用 qwen_omni_utils.process_mm_info, 同时返回 audios / images / videos
    - 通过 use_audio_in_video 控制是否将视频中的音轨作为额外模态送入模型
    - generate 输出需要 thinker_return_dict_in_generate=True 后从 sequences 切片
    - 模型类: Qwen3OmniMoeForConditionalGeneration
"""

from __future__ import annotations

from typing import Any

import torch
from qwen_omni_utils import process_mm_info
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor

from framework.base import BaseTester


class Qwen3OmniTester(BaseTester):
    """Qwen3-Omni 视频/音视频理解 Tester。"""

    def __init__(
        self,
        model_path: str,
        name: str | None = None,
        fps: float = 1.0,
        max_new_tokens: int = 1024,
        use_audio_in_video: bool = True,
        attn_implementation: str = "flash_attention_2",
        dtype: torch.dtype | str = "auto",
    ):
        super().__init__(model_path, name)
        self.fps = fps
        self.max_new_tokens = max_new_tokens
        self.use_audio_in_video = use_audio_in_video
        self.attn_implementation = attn_implementation
        self.dtype = dtype
        self.model = None
        self.processor = None

    def _load_model(self) -> None:
        self.model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
            self.model_path,
            dtype=self.dtype,
            device_map="auto",
            attn_implementation=self.attn_implementation,
        )
        self.processor = Qwen3OmniMoeProcessor.from_pretrained(self.model_path)

    def _build_messages(self, video_path: str, prompt: str) -> list[dict]:
        return [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": (
                        "You are Qwen, a virtual human capable of perceiving auditory and visual inputs."
                    )}
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "video", "video": video_path, "fps": self.fps},
                    {"type": "text", "text": prompt},
                ],
            },
        ]

    def _infer(self, media: str, prompt: str, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        use_audio = kwargs.get("use_audio_in_video", self.use_audio_in_video)
        messages = self._build_messages(media, prompt)

        text = self.processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        audios, images, videos = process_mm_info(messages, use_audio_in_video=use_audio)

        inputs = self.processor(
            text=text,
            audio=audios,
            images=images,
            videos=videos,
            return_tensors="pt",
            padding=True,
            use_audio_in_video=use_audio,
        )
        inputs = inputs.to(self.model.device).to(self.model.dtype)

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_new_tokens", self.max_new_tokens),
                thinker_return_dict_in_generate=True,
                use_audio_in_video=use_audio,
                # 不输出语音, 仅文本 (省时省显存)
                return_audio=False,
            )

        # outputs 可能是 (text_ids, audio) 或仅 text_ids; 当 return_audio=False 时取 text_ids
        text_ids = outputs[0] if isinstance(outputs, tuple) else outputs
        sequences = text_ids.sequences if hasattr(text_ids, "sequences") else text_ids

        in_len = inputs["input_ids"].shape[1]
        answer = self.processor.batch_decode(
            sequences[:, in_len:], skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        extra = {
            "use_audio_in_video": use_audio,
            "sampled_fps": self.fps,
        }
        return answer, extra
