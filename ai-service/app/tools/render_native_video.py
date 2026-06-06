import argparse
from pathlib import Path

from app.services.native_render_service import render_native_video


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the main video track from an editor export package with ffmpeg."
    )
    parser.add_argument(
        "--package",
        dest="package_path",
        required=True,
        help="Path to the *.editing-package.json file.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        required=False,
        help="Optional output MP4 path. Defaults to editingJob.outputPath.",
    )
    parser.add_argument(
        "--max-long-side",
        dest="max_long_side",
        type=int,
        default=640,
        help="Largest output edge in pixels. Default is 640 for local draft renders.",
    )
    parser.add_argument(
        "--fps",
        dest="fps",
        type=int,
        required=False,
        help="Optional FPS override. Defaults to editingJob.renderHints.fps.",
    )
    parser.add_argument(
        "--max-clips",
        dest="max_clips",
        type=int,
        required=False,
        help="Optional cap for smoke tests.",
    )
    parser.add_argument(
        "--max-duration-ms",
        dest="max_duration_ms",
        type=int,
        required=False,
        help="Optional timeline duration cap for smoke tests.",
    )
    parser.add_argument(
        "--crf",
        dest="crf",
        type=int,
        default=28,
        help="x264 CRF. Lower is higher quality and slower.",
    )
    parser.add_argument(
        "--preset",
        dest="preset",
        default="veryfast",
        help="x264 preset. Use ultrafast for diagnostics or medium for better final quality.",
    )
    parser.add_argument(
        "--audio-mode",
        dest="audio_mode",
        choices=["mute", "source"],
        default="mute",
        help="Audio handling mode. Use source to preserve source clip audio.",
    )
    parser.add_argument(
        "--burn-subtitles",
        dest="burn_subtitles",
        action="store_true",
        help="Burn timeline subtitle clips into the rendered video.",
    )
    parser.add_argument(
        "--subtitle-font-size",
        dest="subtitle_font_size",
        type=int,
        default=24,
        help="ASS subtitle font size used when --burn-subtitles is enabled.",
    )
    parser.add_argument(
        "--subtitle-font-name",
        dest="subtitle_font_name",
        default="Heiti SC",
        help="ASS subtitle font family used when --burn-subtitles is enabled.",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        dest="ffmpeg_bin",
        required=False,
        help="Optional ffmpeg binary path. Use /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg for subtitle rendering on macOS.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = render_native_video(
        package_path=Path(args.package_path).expanduser().resolve(),
        output_path=Path(args.output_path).expanduser().resolve() if args.output_path else None,
        max_long_side=args.max_long_side,
        fps=args.fps,
        max_clips=args.max_clips,
        max_duration_ms=args.max_duration_ms,
        crf=args.crf,
        preset=args.preset,
        audio_mode=args.audio_mode,
        burn_subtitles=args.burn_subtitles,
        subtitle_font_size=args.subtitle_font_size,
        subtitle_font_name=args.subtitle_font_name,
        ffmpeg_bin=args.ffmpeg_bin,
    )

    print("Native ffmpeg render completed")
    print(f"- output: {result['outputPath']}")
    print(f"- render result: {result['renderResultPath']}")
    print(f"- clips: {result['clipCount']}")
    print(f"- size: {result['width']}x{result['height']} @ {result['fps']}fps")
    print(f"- audio: {result['audioMode']}")
    print(f"- subtitles: {result['subtitleCount']}")
    print(f"- duration: {result['durationSeconds']:.2f}s")


if __name__ == "__main__":
    main()
