# Agent Editing Tools

这份文档定义剪辑器 MVP 阶段，agent / Codex / Cursor 如何基于经验数据和 Source Video 生成剪辑任务。

当前目标不是让用户手动剪辑，而是先跑通：

```txt
Source Videos
  -> source_material.json
  -> Editing Experience
  -> Timeline Plan
  -> HyperFrames Composition
  -> Editing Job
  -> final.mp4
```

## 当前输入

### 1. Source Videos

用户可以上传多个 Source Video。

这些视频由左侧 `Assets` 管理，当前是本地 object url 和 metadata：

- `assetId`
- `workspaceId`
- `name`
- `mimeType`
- `durationSeconds`
- `frameWidth`
- `frameHeight`
- `objectUrl`

### 2. Editing Experience

经验数据来自爆款视频分析沉淀。

当前先使用：

```txt
data/elastic_template.json
```

这个文件包含：

- `style_metadata`
- `storyline_structure`
- `visual_assets_rule`
- `dynamic_pacing_blueprint`

后续如果增加 ASR 人声台词，可以继续并入 editing experience，供 planner 选择台词、字幕和节奏点。

### 3. Source Material

当前后续开发应当假定 analyzer 已经把 Source Video 转成：

```txt
source_material.json
```

它不是剪辑器负责生成的，而是作为外部前置输入交给 planner。

这份输入至少应该表达：

- 视频基础信息
- 粗镜头切分
- 片段视觉语义
- 人声 / 台词块
- 候选叙事角色
- 音乐节奏点 / drops

详细说明见：

- [`../source-material-handoff/README.md`](../source-material-handoff/README.md)

当前 `data/test_case/<case_id>/` 的 mock 数据已经基本可以映射成：

- `step1_audio.json`
- `step2_transcript.json`
- `step3_visual.json`

其中 `elastic_template.json` 更适合作为可选调试上下文，而不是 `sourceMaterial` 主输入。

### 4. Editor Export Package

前端 Editor 的 `Export Job` 会下载一份 JSON package。

这份 package 包含：

- `sourceAssets`
- `sourceMaterials`
- `editingExperience`
- `timelinePlan`
- `editingJob`
- `renderResult`

## Tool 草案

### `inspect_render_environment`

输入：

```json
{}
```

输出：

```json
{
  "ffmpeg": {
    "available": true,
    "hasSubtitles": true,
    "hasDrawtext": true,
    "hasOverlay": true,
    "hasXfade": true
  },
  "hyperframes": {
    "availableViaNpx": true
  }
}
```

职责：

- 让 agent 在剪辑前确认本机 render 能力
- 判断是否可以使用 ASS 字幕、overlay、xfade 等 ffmpeg 能力
- 判断 HyperFrames CLI 是否可作为后续 composition 工具

当前 repo 内入口：

```bash
cd ai-service
python3 -m app.tools.inspect_render_environment
```

### `load_editing_experience`

输入：

```json
{
  "experiencePath": "data/elastic_template.json"
}
```

输出：

```json
{
  "editingExperience": {}
}
```

职责：

- 读取经验 JSON
- 归一化为 `editing-experience.schema.json`
- 后续兼容多个经验文件

### `create_timeline_plan`

输入：

```json
{
  "sourceMaterials": [],
  "editingExperience": {}
}
```

输出：

```json
{
  "timelinePlan": {}
}
```

职责：

- 基于 `sourceMaterials[].visualShots` 选择视频片段
- 基于 `sourceMaterials[].transcript.sentences` 生成字幕计划
- 基于 `sourceMaterials[].beatsMs / dropsMs` 决定节奏点
- 基于多个 `source_material.json` 在多个 Source Video 中选片
- 生成 subtitle / overlay / audio track 占位

### `create_hyperframes_composition`

输入：

```json
{
  "timelinePlan": {},
  "editingExperience": {},
  "outputDir": "ai-service/output/plans/example.hyperframes/"
}
```

输出：

```json
{
  "compositionPath": "ai-service/output/plans/example.hyperframes/"
}
```

职责：

- 把 timeline plan 转成 HyperFrames 可以渲染的 composition
- 生成 HTML / CSS / JS 或后续 HyperFrames adapter 需要的文件
- 不把 HyperFrames 细节暴露给用户 UI

当前 repo 内已经有一个最小 draft builder：

```bash
cd ai-service
python -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```

它会生成：

- `composition.draft.json`
- `index.html`
- `composition-data.js`
- `composition.js`

这一步先解决：

- package -> composition draft
- timeline -> scene mapping
- 给 Codex / Cursor 一个可继续改造成真实 render composition 的起点

它还没有解决：

- 稳定本地视频文件路径
- 真正的 HyperFrames mp4 render

### `render_with_native_ffmpeg`

输入：

```json
{
  "packagePath": "ai-service/output/plans/example.editing-package.json",
  "outputPath": "ai-service/output/renders/example.native.final.mp4",
  "maxLongSide": 640,
  "audioMode": "source",
  "burnSubtitles": true
}
```

输出：

```json
{
  "renderResult": {
    "renderer": "ffmpeg-native",
    "outputPath": "ai-service/output/renders/example.native.final.mp4"
  }
}
```

职责：

- 读取 editor export package
- 根据 `timelinePlan.video` 截取并拼接源视频
- 根据 `timelinePlan.subtitle` 生成 ASS 字幕并烧录
- 支持源视频原声或静音
- 输出可直接播放的 MP4

当前 repo 内入口：

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

macOS 上如果安装了 `ffmpeg-full`，工具会自动优先使用：

```txt
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
```

也可以显式传入：

```bash
--ffmpeg-bin /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
```

### `render_with_hyperframes`

输入：

```json
{
  "compositionPath": "ai-service/output/plans/example.hyperframes/",
  "outputPath": "ai-service/output/renders/example.final.mp4"
}
```

输出：

```json
{
  "renderResult": {}
}
```

职责：

- 调用 HyperFrames 渲染 mp4
- 输出 `final.mp4`
- 输出 `render_result.json`

当前建议：

- 主视频轨、基础字幕、原声优先使用 `render_with_native_ffmpeg`
- 复杂字幕动效、标题、贴纸、包装层再交给 HyperFrames composition

## 输出目录

输出目录说明见：

- [`../../ai-service/output/README.md`](../../ai-service/output/README.md)
- [`../../ai-service/output/plans/README.md`](../../ai-service/output/plans/README.md)
- [`../../ai-service/output/renders/README.md`](../../ai-service/output/renders/README.md)

## 共享协议

- [`../../shared/schemas/editing-experience.schema.json`](../../shared/schemas/editing-experience.schema.json)
- [`../../shared/schemas/timeline-plan.schema.json`](../../shared/schemas/timeline-plan.schema.json)
- [`../../shared/schemas/editing-job.schema.json`](../../shared/schemas/editing-job.schema.json)
- [`../../shared/schemas/render-result.schema.json`](../../shared/schemas/render-result.schema.json)
- [`../../shared/schemas/hyperframes-composition-draft.schema.json`](../../shared/schemas/hyperframes-composition-draft.schema.json)

## Codex Skill Draft

- [`./codex-video-editing-skill.md`](./codex-video-editing-skill.md)
- [`./codex-skill-draft.md`](./codex-skill-draft.md)

## 当前不做

当前不做：

- 用户手动时间轴剪辑
- 在 UI 里展示 HyperFrames 配置
- 在前端浏览器里直接渲染 mp4
- 后端持久化 render job

这些都应该等 agent / HyperFrames 链路跑通后继续接。
