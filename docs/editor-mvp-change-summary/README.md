# Editor MVP Change Summary

记录时间：

```txt
2026-05-31 17:05:00 CST
```

## 背景

本次修改围绕剪辑器 MVP。

目标是先让剪辑器承担业务上最稳定的一段：

```txt
多 Source Video 预览
+ mock editing experience
+ agent timeline draft
+ HyperFrames handoff package
```

当前仍然遵循项目主口径：

- `Desktop Client`
- 一套 `frontend`
- `Tauri` 是默认运行壳
- Web 只用于开发 / 调试
- `Local-first, Cloud-ready`

## 影响范围

### Frontend

影响模块：

- `frontend/src/features/assets`
- `frontend/src/features/editor`
- `frontend/src/features/workspace`
- `frontend/src/features/hyperframes`

主要变化：

- Source Video 支持一次选择多个文件
- 左侧 Assets 展示多个 Source Video
- Editor 预览当前选中的 Source Video
- Editor 展示素材 metadata、多份 mock `sourceMaterial` 摘要和 mock editing experience
- Timeline 区展示基于 3-4 份 `sourceMaterial` 串联生成的 agent timeline draft，不提供用户手动剪辑交互
- 新增 `Export Job`，导出 JSON handoff package
- 新增 `ai-service` 本地 HyperFrames draft builder，可把导出 package 转成 composition draft 目录

### Shared

新增共享 schema：

- `shared/schemas/editing-experience.schema.json`
- `shared/schemas/timeline-plan.schema.json`
- `shared/schemas/editing-job.schema.json`
- `shared/schemas/render-result.schema.json`
- `shared/schemas/hyperframes-composition-draft.schema.json`

### AI Service Output

新增输出目录说明：

- `ai-service/output/README.md`
- `ai-service/output/materials/README.md`
- `ai-service/output/plans/README.md`
- `ai-service/output/renders/README.md`

### Docs

新增：

- `docs/editor-preview-export/README.md`
- `docs/agent-editing-tools/README.md`
- `docs/agent-editing-tools/codex-skill-draft.md`
- `docs/hyperframes-draft-builder/README.md`
- `docs/editor-mvp-change-summary/README.md`

## 当前导出说明

当前导出的是 agent handoff package。

它包含：

- `sourceAssets`
- `sourceMaterials`
- `editingExperience`
- `timelinePlan`
- `editingJob`
- `renderResult`

它不是最终 mp4。

最终 mp4 后续由 Codex / agent / HyperFrames adapter 根据 package 渲染得到。

## 当前未做

当前未做：

- 用户手动时间轴剪辑
- HyperFrames runtime 接入
- 前端直接渲染 mp4
- 后端持久化 render job
- IM 自动触发编辑工具

## 后续建议

下一步建议：

1. 用 Codex 根据导出的 package 手工生成一版 HyperFrames composition
2. 先用本地 draft builder 生成 composition draft 目录
3. 验证 `timeline_plan` 是否足够表达经验数据
4. 再接真实 HyperFrames render
5. 最后把 render job 持久化到 backend

## 2026-06-06 渲染链路重构记录

记录时间：

```txt
2026-06-06 17:26:26 CST
```

本次继续推进导出链路，主要目标是解决 HyperFrames 直接承担完整主视频轨时速度慢、稳定性不足的问题。

新增：

- `docs/render-pipeline-restructure/README.md`
- `ai-service/app/services/native_render_service.py`
- `ai-service/app/tools/render_native_video.py`

新的推荐闭环：

```txt
data/test_case
  -> editing-package.json
  -> ffmpeg native main-track render
  -> draft mp4
```

HyperFrames 仍然保留，但职责调整为后续字幕、标题、贴纸、包装层等 agent composition，不再作为第一阶段主视频轨的唯一导出器。

本次 smoke 验证：

- 输入：3 个 `data/test_case` case
- package：`ai-service/output/plans/native-smoke.editing-package.json`
- 输出：`ai-service/output/renders/native-smoke.final.mp4`
- 验证输出：12s、640x360、30fps、H.264
- 二次验证输出：`ai-service/output/renders/native-smoke-verify.final.mp4`
- 二次验证输出：6s、640x360、30fps、单 video stream

2026-06-06 18:20 CST 继续补充：

- `render_native_video` 新增 `--audio-mode source`
- `render_native_video` 新增 `--burn-subtitles`
- `render_native_video` 新增 `--subtitle-font-size`
- `render_native_video` 新增 `--subtitle-font-name`
- `render_native_video` 新增 `--ffmpeg-bin`
- macOS 上会自动优先使用 `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`
- 默认字幕字体改为 `Heiti SC`
- 已验证 `ffmpeg-full` 可以输出带原声和 ASS 字幕烧录的 MP4

验证输出：

- `ai-service/output/renders/native-smoke-full-ffmpeg-heiti.final.mp4`
- 6s、640x360、30fps、H.264 video、AAC stereo audio

当前限制：

- 暂时不混入外部 BGM
- 暂时不做转场和 overlay

后续建议：

1. 增加 proxy media cache
2. 增加音频轨混合
3. 增加字幕烧录或 HyperFrames overlay 合成
4. 增加 smoke / draft / final render profile

## 2026-06-06 Agent 样片和 1080p 链路记录

记录时间：

```txt
2026-06-06 19:17:36 CST
```

本次继续以 agent 角色验证多源 source video 自动剪辑链路。

已完成：

- 使用 `data/test_case` 中 5 个 mock analyzer case 组织样片 timeline
- 生成 `ai-service/output/plans/agent-sample.editing-package.json`
- 使用 native ffmpeg render 导出 1080p base video
- 输出 `ai-service/output/renders/agent-sample-1080-base.mp4`
- 生成 `ai-service/output/plans/agent-sample-1080-hyperframes`
- HyperFrames bundle lint 通过，结果为 `0 errors, 0 warnings`
- 本机环境检查通过，Node / ffmpeg / Chrome / Docker daemon 均可用

1080p base video 验证结果：

```txt
duration: 32.333333s
video: H.264 1920x1080
audio: AAC 48000Hz stereo
size: 24,013,602 bytes
```

今天明确下来的边界：

- 真实视频主轨剪辑和导出优先使用 ffmpeg native render
- HyperFrames 不暴露给用户 UI
- HyperFrames 作为 agent 内部生成式视觉层能力保留
- 没有真实视频的 HyperFrames composition 此前已经可用
- 带真实 source video 的 1080p HyperFrames 本机 render 仍需后续排查

遇到的问题：

- 本机 HyperFrames render / snapshot 在真实视频 composition 上曾报 `Cannot access 'he' before initialization`
- Docker render 没有进入实际渲染，镜像构建阶段因 Debian apt 源连接超时失败

当前可交付闭环：

```txt
mock analyzer data
  -> agent timeline
  -> editing-package
  -> ffmpeg native render
  -> 1080p mp4
```

后续建议：

1. 继续把 agent 的剪辑判断沉淀到 skill 文档
2. 用 ffmpeg 补齐 BGM、ducking、基础转场
3. 让 HyperFrames 专注包装层和复杂视觉层
4. 后续单独处理 HyperFrames Docker renderer image 或云端 render 环境
