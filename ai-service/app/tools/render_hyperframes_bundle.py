import argparse
from pathlib import Path

from app.services.hyperframes_service import render_hyperframes_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a HyperFrames project bundle to a real MP4."
    )
    parser.add_argument(
        "--bundle-dir",
        dest="bundle_dir",
        required=True,
        help="Path to the HyperFrames bundle directory.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        required=False,
        help="Optional output MP4 path. Defaults to render-result.json / editing-job.json settings.",
    )
    parser.add_argument(
        "--quality",
        dest="quality",
        default="draft",
        choices=["draft", "standard", "high"],
        help="HyperFrames render quality.",
    )
    parser.add_argument(
        "--fps",
        dest="fps",
        type=int,
        required=False,
        help="Optional FPS override.",
    )
    parser.add_argument(
        "--docker",
        dest="use_docker",
        action="store_true",
        help="Render with HyperFrames Docker mode for a more stable local environment.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = render_hyperframes_bundle(
        bundle_dir=Path(args.bundle_dir).expanduser().resolve(),
        output_path=Path(args.output_path).expanduser().resolve() if args.output_path else None,
        quality=args.quality,
        fps=args.fps,
        use_docker=args.use_docker,
    )

    print("HyperFrames render completed")
    print(f"- output: {result['outputPath']}")
    if result.get("renderResultPath"):
        print(f"- render result: {result['renderResultPath']}")
    if result.get("stdout"):
        print(result["stdout"])
    if result.get("stderr"):
        print(result["stderr"])


if __name__ == "__main__":
    main()
