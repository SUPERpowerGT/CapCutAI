"""视频剪辑结构提取流水线（API 版）—— CLI 入口。

与本地版 pipeline.py 的区别：
  - 步骤2（ASR）、步骤3（视觉分析）、步骤4（认知对齐）均通过 302.ai API 调用
  - 步骤1（音频特征提取）保留本地执行（Librosa，无需 GPU）
  - 镜头边界检测 + 关键帧提取保留本地执行（PyAV，无需 GPU）
  - 无需加载任何本地模型权重

用法:
    python pipeline_api.py <video.mp4>                      # 完整 API 运行
    python pipeline_api.py <video.mp4> --output-dir /tmp    # 自定义输出目录
    python pipeline_api.py <video.mp4> --analyze-all-shots  # 分析所有镜头
    python pipeline_api.py <video.mp4> --language English   # 英文 ASR

运行前先在 pipeline_api/config.py 中填写 API_KEYS。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path


OUTPUT_BASE = Path("outputs/pipeline_api")


def _print_step(n: int, title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  步骤{n}: {title}")
    print(f"{'='*60}")


def _fmt(seconds: float) -> str:
    """将秒数格式化为可读字符串，如 '1m 23.4s' 或 '45.2s'。"""
    if seconds >= 60:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"


def run_pipeline_api(
    video_path: Path,
    output_dir: Path,
    max_shots: int = 30,
    analyze_all: bool = False,
    language: str = "Chinese",
    diff_threshold: float = 0.25,
) -> dict:
    """执行完整 API 流水线并返回最终 JSON。

    步骤1: 音频特征提取 (Librosa，本地，无需 GPU)
    步骤2: 语音识别 ASR (Qwen3-Omni API)
    步骤3: 视觉分析 (镜头检测本地 + Qwen3-VL API)
    步骤4: 认知对齐与弹性映射 (Qwen3-Omni API + Python 数学换算)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_cache = output_dir / f"{video_path.stem}.wav"
    keyframes_dir = output_dir / "keyframes"

    t_pipeline_start = time.perf_counter()
    step_times: dict[str, float] = {}

    # ================================================================
    # 步骤1: 音频特征提取（本地，无需 GPU）
    # ================================================================
    _print_step(1, "音频特征提取 (Librosa，本地)")
    t0 = time.perf_counter()
    from pipeline.audio_processor import extract_audio_features
    audio = extract_audio_features(video_path, wav_cache_path=wav_cache)
    step_times["步骤1 音频特征提取"] = time.perf_counter() - t0
    print(f"[Audio] BPM={audio.bpm:.1f}, 节拍数={len(audio.beats_ms)}, 高潮点={audio.drops_ms}")
    print(f"[步骤1] 耗时: {_fmt(step_times['步骤1 音频特征提取'])}")

    step1_path = output_dir / "step1_audio.json"
    step1_path.write_text(json.dumps(asdict(audio), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[步骤1] 已保存: {step1_path}")

    # ================================================================
    # 步骤2: 语音识别 ASR（Qwen3-Omni API）
    # ================================================================
    _print_step(2, "语音识别 ASR (Qwen3-Omni API)")
    t0 = time.perf_counter()
    from pipeline_api.asr_processor import run_asr_api
    transcript = run_asr_api(wav_cache, language=language)
    step_times["步骤2 语音识别 ASR"] = time.perf_counter() - t0
    print(f"[ASR-API] 转录完成: {len(transcript.sentences)} 句，全文={transcript.full_text[:80]}...")
    print(f"[步骤2] 耗时: {_fmt(step_times['步骤2 语音识别 ASR'])}")

    step2_path = output_dir / "step2_transcript.json"
    step2_path.write_text(json.dumps(asdict(transcript), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[步骤2] 已保存: {step2_path}")

    # ================================================================
    # 步骤3: 视觉分析（镜头检测本地 + Qwen3-VL API）
    # ================================================================
    _print_step(3, "视觉分析 (镜头检测本地 + Qwen3-VL API)")
    t0 = time.perf_counter()
    from pipeline_api.vl_processor import run_visual_analysis_api
    visual = run_visual_analysis_api(
        video_path=video_path,
        keyframes_dir=keyframes_dir,
        max_shots=max_shots,
        analyze_all=analyze_all,
        diff_threshold=diff_threshold,
    )
    step_times["步骤3 视觉分析"] = time.perf_counter() - t0
    print(f"[VL-API] 视觉分析完成: {len(visual.shots)} 个镜头")
    print(f"[步骤3] 耗时: {_fmt(step_times['步骤3 视觉分析'])}")

    step3_path = output_dir / "step3_visual.json"
    step3_path.write_text(
        json.dumps(
            {"shots": [asdict(s) for s in visual.shots], "caption_info": visual.caption_info},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[步骤3] 已保存: {step3_path}")

    # ================================================================
    # 步骤4: 认知对齐与弹性映射（Qwen3-Omni API）
    # ================================================================
    _print_step(4, "认知对齐与弹性映射 (Qwen3-Omni API)")
    t0 = time.perf_counter()
    from pipeline_api.orchestrator import run_orchestration_api
    final_json = run_orchestration_api(audio=audio, transcript=transcript, visual=visual)
    step_times["步骤4 认知对齐"] = time.perf_counter() - t0
    print("[Orchestrator-API] JSON 组装与 Schema 校验完成")
    print(f"[步骤4] 耗时: {_fmt(step_times['步骤4 认知对齐'])}")

    total_sec = time.perf_counter() - t_pipeline_start
    step_times["总计"] = total_sec

    # 耗时汇总
    print(f"\n{'='*60}")
    print("  耗时汇总")
    print(f"{'='*60}")
    for label, sec in step_times.items():
        bar = "─" * 4 if label != "总计" else "═" * 4
        print(f"  {bar} {label:<18} {_fmt(sec):>10}")
    print(f"{'='*60}")

    return final_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="视频剪辑结构提取流水线（API 版）—— 通过 302.ai API 调用 Qwen 多模态模型"
    )
    parser.add_argument("video", help="输入视频路径（.mp4）")
    parser.add_argument(
        "--output-dir", default=None,
        help="输出目录（默认: outputs/pipeline_api/<video_stem>）",
    )
    parser.add_argument(
        "--max-shots", type=int, default=30,
        help="VL API 分析的最大镜头数，超出时均匀采样（默认: 30）；--analyze-all-shots 时忽略",
    )
    parser.add_argument(
        "--analyze-all-shots", action="store_true",
        help="对所有检测到的镜头逐一调用 VL API（无采样上限）",
    )
    parser.add_argument(
        "--language", default="Chinese",
        help="ASR 语言提示（默认: Chinese）",
    )
    parser.add_argument(
        "--diff-threshold", type=float, default=0.25,
        help="镜头边界像素差检测阈值（0~1，默认: 0.25）",
    )
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"[Error] 视频文件不存在: {video_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_BASE / video_path.stem
    output_json = output_dir / "elastic_template.json"

    print(f"\n[Pipeline-API] 视频: {video_path}")
    print(f"[Pipeline-API] 输出目录: {output_dir}")
    print(f"[Pipeline-API] 全量镜头分析: {args.analyze_all_shots}")
    print(f"[Pipeline-API] ASR 语言: {args.language}")

    try:
        final_json = run_pipeline_api(
            video_path=video_path,
            output_dir=output_dir,
            max_shots=args.max_shots,
            analyze_all=args.analyze_all_shots,
            language=args.language,
            diff_threshold=args.diff_threshold,
        )
    except Exception as e:
        print(f"\n[Error] API 流水线执行失败: {e}", file=sys.stderr)
        raise

    output_json.write_text(json.dumps(final_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  [完成] 弹性模板已保存: {output_json}")
    print(f"  视频时长: {final_json['style_metadata']['sample_video_total_duration_ms']}ms")
    print(f"  叙事阶段: {len(final_json['storyline_structure'])} 个")
    print(f"  剪辑卡点: {len(final_json['dynamic_pacing_blueprint'])} 个")
    print(f"  风格ID: {final_json['style_metadata']['style_id']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
