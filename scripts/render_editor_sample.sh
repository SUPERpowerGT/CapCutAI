#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AI_SERVICE_DIR="$ROOT_DIR/ai-service"
OUTPUT_DIR="$AI_SERVICE_DIR/output"
PLAN_DIR="$OUTPUT_DIR/plans"
RENDER_DIR="$OUTPUT_DIR/renders"

PROFILE="${PROFILE:-smoke}"
MODE="${MODE:-test_case}"
WORKSPACE_ID="${WORKSPACE_ID:-workspace_editor_sample}"
PACKAGE_PATH="${PACKAGE_PATH:-$PLAN_DIR/editor-sample.editing-package.json}"
NATIVE_OUTPUT_PATH="${NATIVE_OUTPUT_PATH:-$RENDER_DIR/editor-sample.native.final.mp4}"
HYPERFRAMES_DIR="${HYPERFRAMES_DIR:-$PLAN_DIR/editor-sample.hyperframes}"
HYPERFRAMES_OUTPUT_PATH="${HYPERFRAMES_OUTPUT_PATH:-$RENDER_DIR/editor-sample.hyperframes.final.mp4}"
BUILD_HYPERFRAMES="${BUILD_HYPERFRAMES:-0}"
RENDER_HYPERFRAMES="${RENDER_HYPERFRAMES:-0}"
AUDIO_MODE="${AUDIO_MODE:-source}"
EXTERNAL_AUDIO_PATH="${EXTERNAL_AUDIO_PATH:-}"

CASES="${CASES:-7c8980565c6eb03ecfc916cef2c3671d dccaba4a4318a998f481ada83ac4f300 69ead07c5604ccf49e0ef54177553003 3c3541d128e859fd70eb789b98a1106a cd2ddb06976a5f7afad7e2626e41813b}"
EXPERIENCE_PATH="${EXPERIENCE_PATH:-}"
MATERIAL_DIRS="${MATERIAL_DIRS:-}"
SOURCE_VIDEOS="${SOURCE_VIDEOS:-}"
MAX_VIDEO_CLIPS_PER_MATERIAL="${MAX_VIDEO_CLIPS_PER_MATERIAL:-1}"

case "$PROFILE" in
  smoke)
    MAX_LONG_SIDE="${MAX_LONG_SIDE:-640}"
    MAX_DURATION_MS="${MAX_DURATION_MS:-12000}"
    PRESET="${PRESET:-ultrafast}"
    CRF="${CRF:-30}"
    SUBTITLE_FONT_SIZE="${SUBTITLE_FONT_SIZE:-24}"
    ;;
  draft)
    MAX_LONG_SIDE="${MAX_LONG_SIDE:-1280}"
    MAX_DURATION_MS="${MAX_DURATION_MS:-}"
    PRESET="${PRESET:-veryfast}"
    CRF="${CRF:-26}"
    SUBTITLE_FONT_SIZE="${SUBTITLE_FONT_SIZE:-32}"
    ;;
  1080p)
    MAX_LONG_SIDE="${MAX_LONG_SIDE:-1920}"
    MAX_DURATION_MS="${MAX_DURATION_MS:-}"
    PRESET="${PRESET:-veryfast}"
    CRF="${CRF:-23}"
    SUBTITLE_FONT_SIZE="${SUBTITLE_FONT_SIZE:-42}"
    ;;
  *)
    echo "Unknown PROFILE: $PROFILE" >&2
    echo "Use PROFILE=smoke, PROFILE=draft, or PROFILE=1080p." >&2
    exit 1
    ;;
esac

mkdir -p "$PLAN_DIR" "$RENDER_DIR"

cd "$AI_SERVICE_DIR"

echo "Building editing package..."
case "$MODE" in
  test_case)
    PACKAGE_CMD=(
      python3 -m app.tools.build_test_case_package
      --cases
    )
    for case_id in $CASES; do
      PACKAGE_CMD+=("$case_id")
    done
    PACKAGE_CMD+=(
      --workspace-id "$WORKSPACE_ID"
      --output "$PACKAGE_PATH"
      --max-video-clips-per-case 1
    )
    if [[ -n "$MAX_DURATION_MS" ]]; then
      PACKAGE_CMD+=(--smoke-duration-ms "$MAX_DURATION_MS")
    fi
    ;;
  ai4video)
    if [[ -z "$EXPERIENCE_PATH" || -z "$MATERIAL_DIRS" || -z "$SOURCE_VIDEOS" ]]; then
      echo "MODE=ai4video requires EXPERIENCE_PATH, MATERIAL_DIRS, and SOURCE_VIDEOS." >&2
      exit 1
    fi

    PACKAGE_CMD=(
      python3 -m app.tools.build_ai4video_package
      --materials
    )
    for material_dir in $MATERIAL_DIRS; do
      PACKAGE_CMD+=("$material_dir")
    done
    PACKAGE_CMD+=(
      --videos
    )
    for video_path in $SOURCE_VIDEOS; do
      PACKAGE_CMD+=("$video_path")
    done
    PACKAGE_CMD+=(
      --experience "$EXPERIENCE_PATH"
      --workspace-id "$WORKSPACE_ID"
      --output "$PACKAGE_PATH"
      --max-video-clips-per-material "$MAX_VIDEO_CLIPS_PER_MATERIAL"
    )
    if [[ -n "$MAX_DURATION_MS" ]]; then
      PACKAGE_CMD+=(--max-duration-ms "$MAX_DURATION_MS")
    fi
    ;;
  *)
    echo "Unknown MODE: $MODE" >&2
    echo "Use MODE=test_case or MODE=ai4video." >&2
    exit 1
    ;;
esac

"${PACKAGE_CMD[@]}"

echo "Rendering native ffmpeg MP4..."
NATIVE_CMD=(
  python3 -m app.tools.render_native_video
  --package "$PACKAGE_PATH"
  --output "$NATIVE_OUTPUT_PATH"
  --max-long-side "$MAX_LONG_SIDE"
  --audio-mode "$AUDIO_MODE"
  --burn-subtitles
  --subtitle-font-size "$SUBTITLE_FONT_SIZE"
  --subtitle-font-name "Heiti SC"
  --preset "$PRESET"
  --crf "$CRF"
)
if [[ "$AUDIO_MODE" == "external" ]]; then
  if [[ -z "$EXTERNAL_AUDIO_PATH" ]]; then
    echo "AUDIO_MODE=external requires EXTERNAL_AUDIO_PATH." >&2
    exit 1
  fi
  NATIVE_CMD+=(--external-audio-path "$EXTERNAL_AUDIO_PATH")
fi
if [[ -n "$MAX_DURATION_MS" ]]; then
  NATIVE_CMD+=(--max-duration-ms "$MAX_DURATION_MS")
fi
"${NATIVE_CMD[@]}"

if [[ "$BUILD_HYPERFRAMES" == "1" || "$RENDER_HYPERFRAMES" == "1" ]]; then
  echo "Building HyperFrames bundle..."
  python3 -m app.tools.build_hyperframes_draft \
    --package "$PACKAGE_PATH" \
    --output-dir "$HYPERFRAMES_DIR"
fi

if [[ "$RENDER_HYPERFRAMES" == "1" ]]; then
  echo "Rendering HyperFrames MP4..."
  python3 -m app.tools.render_hyperframes_bundle \
    --bundle-dir "$HYPERFRAMES_DIR" \
    --output "$HYPERFRAMES_OUTPUT_PATH" \
    --quality draft
fi

echo
echo "Done."
echo "- package: $PACKAGE_PATH"
echo "- native mp4: $NATIVE_OUTPUT_PATH"
if [[ "$BUILD_HYPERFRAMES" == "1" || "$RENDER_HYPERFRAMES" == "1" ]]; then
  echo "- hyperframes bundle: $HYPERFRAMES_DIR"
fi
if [[ "$RENDER_HYPERFRAMES" == "1" ]]; then
  echo "- hyperframes mp4: $HYPERFRAMES_OUTPUT_PATH"
fi
