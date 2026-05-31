import argparse
from pathlib import Path

from app.services.hyperframes_service import (
    build_hyperframes_composition_draft,
    load_editor_export_package,
    write_hyperframes_draft_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a HyperFrames composition draft bundle from an editor export package."
    )
    parser.add_argument(
        "--package",
        dest="package_path",
        required=True,
        help="Path to the *.editing-package.json exported from the editor.",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        required=False,
        help="Directory for generated HyperFrames draft files. Defaults to editingJob.compositionPath.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package_path = Path(args.package_path).expanduser().resolve()
    export_package = load_editor_export_package(package_path)
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else Path(export_package.editing_job.composition_path).expanduser().resolve()
    )

    draft = build_hyperframes_composition_draft(export_package)
    written_files = write_hyperframes_draft_bundle(export_package, draft, output_dir)

    print(f"Built HyperFrames draft for timeline: {export_package['timelinePlan']['timelineId']}")
    print(f"Output directory: {output_dir}")
    for label, file_path in written_files.items():
        print(f"- {label}: {file_path}")


if __name__ == "__main__":
    main()
