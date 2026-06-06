# Codex Skill Draft: Video Editing Orchestrator

这是一份后续迁移成 Codex skill 的草案。

当前先放在 `docs/`，用于人工调试和 agent 自检。

## Trigger

当用户要求：

- 基于 `source_material` 和经验数据自动剪辑视频
- 生成 `timeline_plan`
- 根据已有 `editing-package.json` 导出 MP4
- 修改剪辑节奏、字幕、音频、包装层

使用本草案。

## Principle

不要把剪辑判断写死在脚本里。

agent 负责：

- 阅读 `source_material`
- 阅读 editing experience
- 选择素材片段
- 规划节奏
- 生成或修改 `timelinePlan`
- 决定调用 ffmpeg 还是 HyperFrames

脚本负责：

- 校验环境
- 把明确的 timeline 执行为视频
- 生成中间产物
- 写回 render result

## Current Agent Editing Scope

当前 agent 可以先承担以下剪辑能力：

- 读取 `source_material` / `editing-package.json`
- 从多个 source video 中选择片段
- 生成多段硬切 timeline
- 保留源视频原声
- 烧录基础字幕
- 输出 smoke / draft / 1080p MP4
- 生成 HyperFrames composition bundle，交给后续包装层或复杂视觉层使用

当前不要求 agent 完成：

- 用户手动时间轴交互
- 视频内容 analyzer
- 生产级 BGM 自动匹配
- 复杂转场自动选择
- HyperFrames 暴露给前端用户

## Tool Responsibility Split

### Use ffmpeg for deterministic media operations

优先交给 ffmpeg：

- 视频片段截取
- 多源视频拼接
- 硬切
- 等比缩放、pad、crop
- 输出分辨率和 fps 控制
- 原声保留或静音
- 基础音频混合
- BGM 混入
- 人声 / BGM 音量调整
- 基础 fade in / fade out
- 基础转场，例如 `xfade`
- 基础字幕烧录，例如 ASS subtitles
- proxy / draft / final render profile
- 最终 MP4 编码

原因：

- 这些是媒体处理基础能力
- 可预测、可复现
- 本地性能更接近剪辑软件
- 不依赖浏览器逐帧采集

### Use HyperFrames for generated visual composition

交给 HyperFrames：

- 复杂字幕动效
- 标题卡
- 贴纸、标签、强调框
- 信息图层
- 品牌包装层
- 复杂 HTML/CSS/JS composition
- agent 生成的视觉模板
- 需要可编程布局的 overlay

原因：

- HTML/CSS 更适合动态视觉设计
- agent 更容易生成和修改
- 不应该暴露给用户 UI

当前策略：

- 无视频或轻量包装层的 HyperFrames composition 已经可以作为 agent 视觉生成链路使用
- 带真实 source video 的长主轨，不作为第一阶段 HyperFrames 的优先渲染对象
- 如果需要 HyperFrames 参与真实视频成片，优先让 ffmpeg 先产出主轨 base video，再由 HyperFrames 生成包装层或 overlay
- 如果 HyperFrames 本机 render 遇到浏览器采帧 runtime 问题，先检查 timeline contract，再用 ffmpeg native render 保障闭环

### Avoid HyperFrames for primary video assembly

不要让 HyperFrames 承担：

- 大量原视频主轨拼接
- 长视频完整导出
- 频繁 smoke test
- 纯硬切剪辑

这会让浏览器采帧承担过重工作，速度和稳定性都不理想。

## Workflow

### 1. Inspect environment

先确认本机能力：

```bash
cd ai-service
python3 -m app.tools.inspect_render_environment
```

期望：

```json
{
  "ffmpeg": {
    "available": true,
    "hasSubtitles": true,
    "hasDrawtext": true,
    "hasOverlay": true,
    "hasXfade": true
  }
}
```

macOS 上推荐安装 `ffmpeg-full`。工具会自动优先使用：

```txt
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
```

### 2. Read inputs

优先读取：

```txt
*.editing-package.json
```

如果没有 package，则读取：

```txt
data/test_case/<case_id>/step1_audio.json
data/test_case/<case_id>/step2_transcript.json
data/test_case/<case_id>/step3_visual.json
data/elastic_template.json
```

如果用户已经提供 analyzer 产物，应直接读取 analyzer 后的 `source_material` 子集，不要重新实现 analyzer。

### 3. Build or revise timeline

agent 根据 `source_material` 和经验数据决定：

- 哪些 source video 进入成片
- 每个 phase 使用哪些 shot
- 每个 clip 的 `sourceStartMs` 和 `durationMs`
- subtitle track 使用哪些 sentence
- audio track 是否保留原声、静音、后续混 BGM
- overlay track 是否需要交给 HyperFrames

### 4. Render ffmpeg draft

先生成可播放 MP4：

```bash
cd ai-service
python3 -m app.tools.render_native_video \
  --package ../path/to/example.editing-package.json \
  --output ./output/renders/example.native.final.mp4 \
  --max-long-side 640 \
  --audio-mode source \
  --burn-subtitles \
  --preset veryfast \
  --crf 28
```

常用 profile：

```txt
smoke: --max-long-side 640 --max-duration-ms 6000 --preset ultrafast --crf 30
draft: --max-long-side 1280 --preset veryfast --crf 26
final: --max-long-side 1920 --preset medium --crf 20
```

1080p draft 建议：

```bash
cd ai-service
python3 -m app.tools.render_native_video \
  --package ./output/plans/agent-sample.editing-package.json \
  --output ./output/renders/agent-sample-1080-base.mp4 \
  --max-long-side 1920 \
  --audio-mode source \
  --burn-subtitles \
  --subtitle-font-size 42 \
  --subtitle-font-name "Heiti SC" \
  --preset veryfast \
  --crf 23
```

### 5. Add HyperFrames only when needed

当 timeline 里出现复杂包装层需求时，再生成 HyperFrames draft：

```bash
cd ai-service
python3 -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```

HyperFrames 输出应该作为 overlay / packaging stage 的输入，而不是主视频轨的第一选择。

### 6. Validate package before render

如果生成了 HyperFrames bundle，先做结构校验：

```bash
npx --yes hyperframes lint ./output/plans/<bundle-dir>
```

当前已验证过的模式：

- `editing-package.json` 到 ffmpeg native MP4 可闭环
- 1080p base video 可由 ffmpeg native render 生成
- HyperFrames bundle 可生成并通过 lint
- 纯视觉 / 无真实 source video 的 HyperFrames composition 此前已可用
- 带真实 source video 的 HyperFrames 1080p render 已可走通

当前观察到的限制：

- 带真实 source video 的 1080p HyperFrames 本机 render 曾在 browser capture 阶段报 `Cannot access 'he' before initialization`
- 实际根因是 composition 注册了 `window.__timelines["main"] = {}`，空对象没有 `pause()` 等 timeline 控制方法
- Docker render 曾在镜像构建阶段因 `deb.debian.org` apt 连接超时失败
- 修复为空 timeline contract 后，HyperFrames render 可以完成，但 1080p 全量主轨耗时约 4m
- 这些问题不影响 ffmpeg native render 闭环，也不代表 HyperFrames bundle schema 不可用

### 7. HyperFrames timeline contract

不要写：

```js
window.__timelines["main"] = {};
```

如果 composition 没有 GSAP 动效，也必须注册一个可被 HyperFrames 控制的 paused timeline contract：

```js
window.__timelines = window.__timelines || {};
window.__timelines["main"] = {
  _time: 0,
  _duration: 32.333,
  pause() { return this; },
  play() { return this; },
  seek(value) { this._time = Number(value) || 0; return this; },
  totalTime(value) {
    if (typeof value === "number") this._time = value;
    return this._time;
  },
  time() { return this._time; },
  duration() { return this._duration; },
  timeScale() { return this; },
  kill() { return this; }
};
```

如果有真实动效，则优先使用 GSAP：

```js
const tl = gsap.timeline({ paused: true });
window.__timelines["main"] = tl;
```

registry key 必须等于 root element 的 `data-composition-id`。

## Decision Table

| Editing need | Primary tool | Notes |
| --- | --- | --- |
| Cut a segment | ffmpeg | Use `sourceStartMs` / `durationMs` |
| Concatenate clips | ffmpeg | Main timeline path |
| Preserve source audio | ffmpeg | `--audio-mode source` |
| Mute | ffmpeg | `--audio-mode mute` |
| Burn simple subtitles | ffmpeg | ASS subtitles |
| Subtitle animation | HyperFrames | Use only when visual style matters |
| Title card | HyperFrames | HTML/CSS composition |
| Sticker / callout | HyperFrames | Later overlay stage |
| BGM mix | ffmpeg | Future native audio stage |
| Audio ducking | ffmpeg | Future native audio stage |
| Fade / xfade | ffmpeg | Future native transition stage |
| Final MP4 encoding | ffmpeg | Stable export path |

## Output Contract

每次 render 完成后输出：

```json
{
  "renderId": "render_xxx",
  "jobId": "editing_job_xxx",
  "status": "completed",
  "renderer": "ffmpeg-native",
  "outputPath": "ai-service/output/renders/example.native.final.mp4"
}
```

失败时必须保留：

```json
{
  "status": "failed",
  "errorMessage": "..."
}
```

## User-facing Rule

不要在用户界面中暴露 ffmpeg 或 HyperFrames。

用户只需要看到：

- 正在生成
- 生成完成
- 预览视频
- 导出视频

具体工具是 agent 内部执行细节。
