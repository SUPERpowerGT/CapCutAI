"""VLM 视频理解测试入口。

同一视频依次过 Qwen2.5-VL-7B-Instruct 和 Qwen3-VL-8B-Instruct, 跑 3 个任务:
  1. 整体内容描述
  2. 事件时间戳定位 (重点考察)
  3. 视频内声音识别探针 (验证 VLM 能否听到声音)

结果以 JSON 形式落盘到 outputs/, 便于人工对比。
"""

from __future__ import annotations

from pathlib import Path

from framework.tasks import VLM_TASKS
from framework.vlm import QwenVLTester

# ============= 配置区 (按需修改) =============
VIDEO_PATH = "AI4Video/data/3246165181.mp4"

VLM_MODELS: list[dict] = [
    {
        "name": "Qwen2.5-VL-7B",
        "path": "Qwen2.5-VL-7B-Instruct",
    },
    {
        "name": "Qwen3-VL-8B",
        "path": "Qwen3-VL-8B-Instruct",
    },
]

OUTPUT_DIR = Path("AI4Video/outputs")
# =============================================


def main() -> None:
    video_path = Path(VIDEO_PATH)
    if not video_path.exists():
        raise FileNotFoundError(f"未找到视频: {video_path}")

    for cfg in VLM_MODELS:
        print(f"\n############ {cfg['name']} ############")
        tester = QwenVLTester(
            model_path=cfg["path"],
            name=cfg["name"],
            fps=1.0,
            max_new_tokens=1024,
        )
        results = tester.run_tasks(str(video_path), VLM_TASKS)
        out_file = OUTPUT_DIR / f"vlm_{cfg['name']}.json"
        tester.save_results(results, out_file)

        # 释放显存, 避免连续加载 OOM
        del tester
        import gc, torch
        gc.collect()
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
