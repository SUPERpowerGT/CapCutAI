"""视频剪辑结构提取流水线 —— CLI 入口。

用法:
    python pipeline.py <video.mp4>                    # 完整运行（需模型权重）
    python pipeline.py <video.mp4> --mock             # Mock 模式（无需权重，用于测试）
    python pipeline.py <video.mp4> --output-dir /tmp  # 自定义输出目录
    python pipeline.py <video.mp4> --omni-use-video   # Omni 同时接收原始视频

流程（与 TASK.md 四步骤对应）:
  步骤1  音频处理   (Librosa) -> BPM、节拍点、高潮点
  步骤2  语音转录   (Qwen3-ASR) -> 全文 + 句级时间戳
  步骤3  视觉分析   (Qwen3-VL) -> 镜头切分 + 逐镜语义
  步骤4  认知对齐   (Qwen3-Omni) -> 弹性 JSON Schema 组装
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from dataclasses import asdict
from pathlib import Path

import torch

# ============= 模型路径配置（按需修改）=============
ASR_MODEL_PATH  = "Qwen3-ASR-1.7B"
VLM_MODEL_PATH  = "Qwen3-VL-8B-Instruct"
OMNI_MODEL_PATH = "Qwen3-Omni-30B-A3B-Instruct"
OUTPUT_BASE     = Path("outputs/pipeline")
# ==================================================


def _model_available(path: str) -> bool:
    return Path(path).exists()


def _get_video_duration_ms(video_path: Path) -> int:
    """获取视频时长（毫秒）。优先使用 PyAV，降级到 ffprobe，最后返回默认值。"""
    try:
        from framework.frame_extractor import VideoFrameExtractor
        with VideoFrameExtractor(video_path) as ext:
            return int(ext.duration_sec * 1000)
    except ImportError:
        pass
    try:
        import subprocess, json as _json
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(video_path)],
            capture_output=True, text=True, timeout=10,
        )
        info = _json.loads(result.stdout)
        return int(float(info["format"]["duration"]) * 1000)
    except Exception:
        return 60_000  # 默认 60 秒


def _print_step(n: int, title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  步骤{n}: {title}")
    print(f"{'='*60}")


def run_pipeline(
    video_path: Path,
    output_dir: Path,
    mock: bool = False,
    omni_use_video: bool = False,
    max_shots: int = 30,
    analyze_all: bool = False,
    language: str = "Chinese",
    asr_backend: str = "qwen3-omni",
    forced_aligner_path: str | None = None,
) -> dict:
    """执行完整流水线并返回最终 JSON。

    当 asr_backend == "qwen3-omni"（默认）时：
      - 步骤1: 音频特征提取 (Librosa)
      - 步骤2: 视觉分析 (Qwen3-VL)
      - 步骤3: ASR + 认知对齐 (Qwen3-Omni 单次加载，两阶段推理)
    当 asr_backend == "qwen3-asr" 时保持原有四步骤。
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_cache = output_dir / f"{video_path.stem}.wav"
    keyframes_dir = output_dir / "keyframes"

    combined_omni_mode = (asr_backend == "qwen3-omni") and not mock

    # ================================================================
    # 步骤1: 音频特征提取
    # ================================================================
    _print_step(1, "音频特征提取 (Librosa)")

    if mock:
        from pipeline.mock import mock_audio_features
        duration_ms = _get_video_duration_ms(video_path)
        audio = mock_audio_features(duration_ms)
        print(f"[Mock] AudioFeatures: BPM={audio.bpm:.1f}, 节拍数={len(audio.beats_ms)}, 时长={audio.duration_ms}ms")
    else:
        from pipeline.audio_processor import extract_audio_features
        audio = extract_audio_features(video_path, wav_cache_path=wav_cache)
        print(f"[Audio] BPM={audio.bpm:.1f}, 节拍数={len(audio.beats_ms)}, 高潮点={audio.drops_ms}")

    step1_path = output_dir / "step1_audio.json"
    step1_path.write_text(json.dumps(asdict(audio), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[步骤1] 中间结果已保存: {step1_path}")

    # ================================================================
    # 步骤2: 语音转录（仅非合并模式）
    # ================================================================
    transcript = None

    if mock:
        _print_step(2, "语音转录 (Mock)")
        from pipeline.mock import mock_transcript
        transcript = mock_transcript(audio.duration_ms)
        print(f"[Mock] TranscriptResult: {len(transcript.sentences)} 句，全文长度={len(transcript.full_text)}")
        step2_path = output_dir / "step2_transcript.json"
        step2_path.write_text(json.dumps(asdict(transcript), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[步骤2] 中间结果已保存: {step2_path}")

    elif not combined_omni_mode:
        # 传统 ASR 独立步骤（qwen3-asr 后端）
        _print_step(2, "语音转录 (Qwen3-ASR)")
        if not _model_available(ASR_MODEL_PATH):
            print(f"[Warning] ASR 模型不存在: {ASR_MODEL_PATH}，使用 Mock 数据")
            from pipeline.mock import mock_transcript
            transcript = mock_transcript(audio.duration_ms)
        else:
            from pipeline.text_processor import run_asr
            transcript = run_asr(
                ASR_MODEL_PATH, video_path,
                language=language,
                wav_cache_path=wav_cache,
                forced_aligner_path=forced_aligner_path,
            )
            print(f"[ASR] 转录完成: {len(transcript.sentences)} 句，全文={transcript.full_text[:80]}...")
        step2_path = output_dir / "step2_transcript.json"
        step2_path.write_text(json.dumps(asdict(transcript), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[步骤2] 中间结果已保存: {step2_path}")

    else:
        print("\n[步骤2] ASR 合并至步骤3（Qwen3-Omni 共享实例），跳过独立 ASR 步骤")

    # ================================================================
    # 步骤3: 视觉分析
    # ================================================================
    step_num = 3 if not combined_omni_mode or mock else 2
    _print_step(step_num, "视觉分析 (镜头检测 + Qwen3-VL)")

    if mock or not _model_available(VLM_MODEL_PATH):
        if not mock:
            print(f"[Warning] VLM 模型不存在: {VLM_MODEL_PATH}，使用 Mock 数据")
        from pipeline.mock import mock_visual_analysis
        visual = mock_visual_analysis(audio.duration_ms, keyframes_dir=keyframes_dir)
        print(f"[Mock] VisualAnalysis: {len(visual.shots)} 个镜头")
    else:
        from pipeline.visual_processor import run_visual_analysis
        visual = run_visual_analysis(
            model_path=VLM_MODEL_PATH,
            video_path=video_path,
            keyframes_dir=keyframes_dir,
            max_shots=max_shots,
            analyze_all=analyze_all,
        )
        print(f"[Visual] 分析完成: {len(visual.shots)} 个镜头")

    step3_path = output_dir / "step3_visual.json"
    step3_path.write_text(
        json.dumps(
            {"shots": [asdict(s) for s in visual.shots], "caption_info": visual.caption_info},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[步骤3] 中间结果已保存: {step3_path}")

    # ================================================================
    # 步骤4: 认知对齐与弹性映射（合并模式下同时包含 ASR）
    # ================================================================
    step_label = "ASR + 认知对齐 (Qwen3-Omni 单次加载)" if combined_omni_mode else "认知对齐 (Qwen3-Omni + 确定性数学换算)"
    _print_step(4, step_label)

    if mock or not _model_available(OMNI_MODEL_PATH):
        if not mock:
            print(f"[Warning] Omni 模型不存在: {OMNI_MODEL_PATH}，使用 Mock 数据")
        from pipeline.mock import mock_final_json
        final_json = mock_final_json(audio.duration_ms)
        print("[Mock] 已生成完整 Schema JSON（Mock 模式）")
    else:
        from pipeline.orchestrator import run_orchestration
        final_json, asr_transcript = run_orchestration(
            model_path=OMNI_MODEL_PATH,
            video_path=video_path,
            audio=audio,
            transcript=transcript,          # None → 触发合并 ASR
            visual=visual,
            use_video=omni_use_video,
            wav_path=wav_cache if combined_omni_mode else None,
        )
        print("[Orchestrator] JSON 组装与 Schema 校验完成")

        # 合并模式下保存 ASR 结果（step2_transcript.json）
        if asr_transcript is not None:
            step2_path = output_dir / "step2_transcript.json"
            step2_path.write_text(
                json.dumps(asdict(asr_transcript), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[步骤4] ASR 结果已保存: {step2_path}")

    return final_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="视频剪辑结构提取流水线 —— 输出弹性 JSON 模板"
    )
    parser.add_argument("video", help="输入视频路径（.mp4）")
    parser.add_argument(
        "--output-dir", default=None,
        help="输出目录（默认: outputs/pipeline/<video_stem>）",
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="跳过所有模型推理，使用 Mock 数据（快速测试流程）",
    )
    parser.add_argument(
        "--omni-use-video", action="store_true",
        help="认知对齐阶段同时将原始视频传入 Omni（感知更全面，显存占用更大）",
    )
    parser.add_argument(
        "--max-shots", type=int, default=30,
        help="VL 分析的最大镜头数，超出时均匀采样（默认: 30）；--analyze-all-shots 时此参数忽略",
    )
    parser.add_argument(
        "--analyze-all-shots", action="store_true",
        help="对所有检测到的镜头逐一分析（无采样上限，适合精细分析）",
    )
    parser.add_argument(
        "--language", default="Chinese",
        help="ASR 语言提示（默认: Chinese）",
    )
    parser.add_argument(
        "--asr-backend", default="qwen3-omni", choices=["qwen3-asr", "qwen3-omni"],
        help=(
            "ASR 后端（默认: qwen3-omni）。"
            "qwen3-omni: 与认知对齐合并为一次模型加载，自动输出句级时间戳；"
            "qwen3-asr: 独立 ASR 步骤，需配合 --forced-aligner-path 获取时间戳。"
        ),
    )
    parser.add_argument(
        "--forced-aligner-path", default=None,
        help="Qwen3-ForcedAligner 本地路径（仅 qwen3-asr 后端使用，用于句级时间戳）",
    )
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"[Error] 视频文件不存在: {video_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_BASE / video_path.stem
    output_json = output_dir / "elastic_template.json"

    print(f"\n[Pipeline] 视频: {video_path}")
    print(f"[Pipeline] 输出目录: {output_dir}")
    print(f"[Pipeline] Mock 模式: {args.mock}")
    print(f"[Pipeline] 全量镜头分析: {args.analyze_all_shots}")
    print(f"[Pipeline] ASR 后端: {args.asr_backend}")

    try:
        final_json = run_pipeline(
            video_path=video_path,
            output_dir=output_dir,
            mock=args.mock,
            omni_use_video=args.omni_use_video,
            max_shots=args.max_shots,
            analyze_all=args.analyze_all_shots,
            language=args.language,
            asr_backend=args.asr_backend,
            forced_aligner_path=args.forced_aligner_path,
        )
    except Exception as e:
        print(f"\n[Error] 流水线执行失败: {e}", file=sys.stderr)
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
