# HyperFrames Feature

这里预留给 HyperFrames 集成同学。

后续职责：

- 接入 HyperFrames 前端编辑能力
- 管理 HyperFrames 相关状态
- 对接 timeline / preview / editing 协议
- 与 IM 模块通过清晰接口协作，而不是直接互相写死

当前版本不要把 HyperFrames 逻辑塞进 `im` 模块。

## 当前产品边界

HyperFrames 不应该外露为用户界面能力。

用户只应该看到：

- Source Video 预览
- agent timeline / job 状态
- 最终视频结果

HyperFrames 是 agent / tool 执行层：

```txt
editing package
  -> timeline_plan
  -> HyperFrames composition
  -> editing_job
  -> final.mp4
```

## 当前输入

第一版输入来自 Editor 导出的 JSON package。

这个 package 包含：

- `sourceAssets`
- `sourceMaterials`
- `editingExperience`
- `timelinePlan`
- `editingJob`
- `renderResult`

当前 `ai-service` 已经有一个最小 draft builder 可以把这份 package 转成 composition 目录：

```bash
cd ai-service
python -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```

这一步生成的是 HyperFrames composition draft，不是最终 mp4。

共享协议见：

- [`../../../shared/schemas/editing-experience.schema.json`](../../../shared/schemas/editing-experience.schema.json)
- [`../../../shared/schemas/timeline-plan.schema.json`](../../../shared/schemas/timeline-plan.schema.json)
- [`../../../shared/schemas/editing-job.schema.json`](../../../shared/schemas/editing-job.schema.json)
- [`../../../shared/schemas/render-result.schema.json`](../../../shared/schemas/render-result.schema.json)
- [`../../../shared/schemas/hyperframes-composition-draft.schema.json`](../../../shared/schemas/hyperframes-composition-draft.schema.json)
