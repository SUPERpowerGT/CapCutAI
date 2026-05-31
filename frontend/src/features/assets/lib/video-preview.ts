"use client";

type VideoPreview = {
  durationSeconds?: number;
  frameWidth?: number;
  frameHeight?: number;
  previewImageUrl?: string;
};

const previewTimeoutMs = 12000;

export async function readVideoPreview(sourceUrl: string): Promise<VideoPreview> {
  return new Promise((resolve) => {
    const video = document.createElement("video");
    video.preload = "auto";
    video.muted = true;
    video.playsInline = true;
    video.src = sourceUrl;

    let settled = false;
    let timeoutId = 0;
    let metadata: VideoPreview = {};

    const cleanup = () => {
      window.clearTimeout(timeoutId);
      video.pause();
      video.removeAttribute("src");
      video.load();
    };

    const finish = (value: VideoPreview) => {
      if (settled) {
        return;
      }

      settled = true;
      cleanup();
      resolve(value);
    };

    const snapshotFrame = () => {
      const width = video.videoWidth || metadata.frameWidth || 0;
      const height = video.videoHeight || metadata.frameHeight || 0;

      if (width <= 0 || height <= 0) {
        finish(metadata);
        return;
      }

      try {
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        if (!context) {
          finish(metadata);
          return;
        }

        context.drawImage(video, 0, 0, width, height);
        finish({
          ...metadata,
          previewImageUrl: canvas.toDataURL("image/jpeg", 0.82)
        });
      } catch {
        finish(metadata);
      }
    };

    video.onloadedmetadata = () => {
      metadata = {
        durationSeconds:
          Number.isFinite(video.duration) && video.duration > 0 ? video.duration : undefined,
        frameWidth: video.videoWidth || undefined,
        frameHeight: video.videoHeight || undefined
      };

      if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
        snapshotFrame();
      }
    };

    video.onloadeddata = snapshotFrame;
    video.onerror = () => finish(metadata);

    timeoutId = window.setTimeout(() => finish(metadata), previewTimeoutMs);
  });
}
