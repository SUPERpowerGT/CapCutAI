"""Qwen2.5-VL-7B-Instruct 视频理解能力 demo。

依赖:
    pip install "transformers>=4.49.0" accelerate qwen-vl-utils[decord] torch torchvision

运行:
    python qwen25vl_video_demo.py
"""

from __future__ import annotations

import time
from pathlib import Path

import torch
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

MODEL_NAME = "models/vlm/Qwen2.5-VL-7B-Instruct"

# 示例视频路径 —— 替换为你自己的视频
VIDEO_PATH = "data/3246165181.mp4"

# 帧采样参数 (Qwen2.5-VL 推荐控制总视觉 token 数, 详见官方 README)
FPS = 1.0                # 抽帧帧率
MIN_PIXELS = 4 * 28 * 28  # 单帧最小像素 (28*28 为 patch 基本单位)
MAX_PIXELS = 256 * 28 * 28  # 单帧最大像素, 控制显存
MAX_NEW_TOKENS = 512


def build_messages(video_path: str, prompt: str) -> list[dict]:
    """构造 Qwen2.5-VL 标准消息格式 (含视频)。"""
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "video",
                    "video": f"file://{Path(video_path).resolve()}",
                    "fps": FPS,
                    "min_pixels": MIN_PIXELS,
                    "max_pixels": MAX_PIXELS,
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]


def run_inference(
    model: Qwen2_5_VLForConditionalGeneration,
    processor: AutoProcessor,
    messages: list[dict],
) -> str:
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs, video_kwargs = process_vision_info(
        messages, return_video_kwargs=True
    )

    # transformers>=5.x 的 processor 要求 fps 为标量, 而 qwen-vl-utils 返回 list, 此处解包
    fps_val = video_kwargs.get("fps")
    if isinstance(fps_val, list) and len(fps_val) == 1:
        video_kwargs["fps"] = fps_val[0]

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
        **video_kwargs,
    ).to(model.device)

    with torch.inference_mode():
        generated_ids = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)

    trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    return processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]


def main() -> None:
    video_path = Path(VIDEO_PATH)
    if not video_path.exists():
        raise FileNotFoundError(
            f"未找到视频文件: {video_path}\n请将 VIDEO_PATH 替换为真实视频路径。"
        )

    print(f"[Loading] {MODEL_NAME} ...")
    t0 = time.time()
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",  # 无 flash-attn 时改 "sdpa"
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    print(f"[Loaded] in {time.time() - t0:.1f}s | device={model.device}")

    tasks = {
        "Task 1 - 视频整体描述": (
            "请用中文详细描述这段视频的整体内容，"
            "包括场景、出现的人物或物体、主要动作和事件的发展。"
        ),
        "Task 2 - 事件时间定位": (
            "请按时间顺序列出视频中发生的关键事件，"
            "并为每个事件标注大致的时间戳 (格式: [开始秒-结束秒] 事件描述)。"
            "若无法精确到秒，请给出相对位置 (如开头/中段/结尾)。"
        ),
    }

    for title, prompt in tasks.items():
        print(f"\n========== {title} ==========")
        print(f"[Prompt] {prompt}")
        t0 = time.time()
        answer = run_inference(model, processor, build_messages(str(video_path), prompt))
        print(f"[Latency] {time.time() - t0:.1f}s")
        print(f"[Answer]\n{answer}")


if __name__ == "__main__":
    main()
