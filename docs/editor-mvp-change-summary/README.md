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
