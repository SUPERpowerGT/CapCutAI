"""剪辑专项对比实验入口。

流程:
  1. 顺序加载 Qwen2.5-VL-7B / Qwen3-VL-8B / Qwen3-Omni-30B-A3B
  2. 每个模型在 5 个剪辑任务上各跑一次 (Omni 默认启用 audio_in_video)
  3. 解析模型输出中的时间戳, 在视频中截取对应帧 (取每个区间中点)
  4. 生成 markdown 报告 outputs/EDITING_REPORT.md
"""

from __future__ import annotations

import gc
import json
from dataclasses import asdict
from pathlib import Path

import torch

from framework.base import TaskResult
from framework.frame_extractor import VideoFrameExtractor, extract_frames_for_timestamps
from framework.omni import Qwen3OmniTester
from framework.report import ModelTaskRun, build_report
from framework.tasks import VLM_EDITING_TASKS
from framework.timestamp_parser import parse_timestamps
from framework.vlm import QwenVLTester

# ============= 配置区 =============
VIDEO_PATH = "data/3246165181.mp4"

MODELS: list[dict] = [
    {
        "name": "Qwen2.5-VL-7B",
        "path": "Qwen2.5-VL-7B-Instruct",
        "kind": "vlm",
    },
    {
        "name": "Qwen3-VL-8B",
        "path": "Qwen3-VL-8B-Instruct",
        "kind": "vlm",
    },
    {
        "name": "Qwen3-Omni-30B-A3B",
        "path": "Qwen3-Omni-30B-A3B-Instruct",
        "kind": "omni",
        "use_audio_in_video": True,
    },
]

TASK_DISPLAY = {
    "hook_identification": "Hook 识别",
    "shot_segmentation":   "分镜结构",
    "scene_typing":        "专场识别",
    "rhythm_cutpoints":    "节奏卡点",
    "three_act_structure": "三段式结构",
}

OUTPUT_DIR = Path("AI4Video/outputs/editing")
RAW_JSON_DIR = OUTPUT_DIR / "raw"
FRAMES_DIR = OUTPUT_DIR / "frames"
REPORT_PATH = OUTPUT_DIR / "EDITING_REPORT.md"
# =================================


def _build_tester(cfg: dict):
    if cfg["kind"] == "vlm":
        return QwenVLTester(model_path=cfg["path"], name=cfg["name"], max_new_tokens=1024)
    if cfg["kind"] == "omni":
        return Qwen3OmniTester(
            model_path=cfg["path"],
            name=cfg["name"],
            max_new_tokens=1024,
            use_audio_in_video=cfg.get("use_audio_in_video", True),
        )
    raise ValueError(f"未知模型类型: {cfg['kind']}")


def _free_model(tester) -> None:
    """释放上一个模型占用的显存。"""
    if hasattr(tester, "model") and tester.model is not None:
        del tester.model
    if hasattr(tester, "processor") and tester.processor is not None:
        del tester.processor
    del tester
    gc.collect()
    torch.cuda.empty_cache()


def main() -> None:
    video_path = Path(VIDEO_PATH)
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_JSON_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    # 用一个 extractor 探到视频时长, 供 report 显示
    with VideoFrameExtractor(video_path) as ext:
        duration_sec = ext.duration_sec

    all_runs: list[ModelTaskRun] = []

    for cfg in MODELS:
        print(f"\n############ {cfg['name']} ############")
        raw_path = RAW_JSON_DIR / f"{cfg['name']}.json"
        tester = None

        if raw_path.exists():
            print(f"[skip] 复用已有结果: {raw_path}")
            payload = json.loads(raw_path.read_text(encoding="utf-8"))
            results = [TaskResult(**item) for item in payload]
        else:
            tester = _build_tester(cfg)
            results = tester.run_tasks(str(video_path), VLM_EDITING_TASKS)
            tester.save_results(results, raw_path)

        # 解析时间戳并截帧
        for r in results:
            timestamps = parse_timestamps(r.answer)
            seconds = [t.midpoint_sec for t in timestamps]
            descriptions = [t.line for t in timestamps]

            frame_subdir = FRAMES_DIR / cfg["name"] / r.task_name
            frame_paths: list[Path] = []
            if seconds:
                frame_paths = extract_frames_for_timestamps(
                    video_path, seconds, frame_subdir, name_prefix=r.task_name
                )

            # 相对路径 (相对于 markdown 文件目录), 便于 md 渲染
            rel_paths = [p.relative_to(OUTPUT_DIR).as_posix() for p in frame_paths]
            ts_rows = list(zip(descriptions, seconds, rel_paths))

            all_runs.append(ModelTaskRun(
                model_name=cfg["name"],
                task_name=r.task_name,
                prompt=r.prompt,
                answer=r.answer,
                latency_sec=r.latency_sec,
                extra=r.extra,
                timestamp_rows=ts_rows,
            ))

        if tester is not None:
            _free_model(tester)

    # 落盘 runs 元信息 (便于复跑报告时无需重新推理)
    (OUTPUT_DIR / "runs.json").write_text(
        json.dumps([asdict(r) for r in all_runs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    notes = (
        "> **说明**: \n"
        "> - 所有截图取自每条时间戳「区间中点」, 用作人工核验代表帧。\n"
        "> - Qwen3-Omni 默认开启 `use_audio_in_video=True`, 同时感知视觉与音轨;"
        " 两个 VLM 模型仅吃视觉帧 (此前实验已验证)。\n"
        "> - 三个模型 prompt 与采样 fps (1.0) 完全一致, 仅模型本身不同。"
    )
    report = build_report(
        title="Qwen-VL / Qwen-Omni 视频剪辑理解能力对比",
        video_path=video_path,
        video_duration_sec=duration_sec,
        task_titles=TASK_DISPLAY,
        runs=all_runs,
        output_md_path=REPORT_PATH,
        extra_notes=notes,
    )
    print(f"\n[Report] {report}")


if __name__ == "__main__":
    main()
