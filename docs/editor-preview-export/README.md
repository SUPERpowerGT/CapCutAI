# Editor Preview And Export

这份文档记录当前剪辑器 MVP 的业务边界。

## 当前目标

剪辑器当前负责：

- 多 Source Video 素材预览
- 当前视频播放预览
- Source Video metadata 预览
- mock editing experience 摘要展示
- agent timeline draft 预览
- 导出 agent handoff package

当前不负责：

- 用户手动多轨剪辑
- 参考视频分析
- IM 对话
- HyperFrames 渲染执行

## 用户素材

用户可以上传多个 Source Video。

左侧 `Assets` 负责：

- 本地选择
- 本地登记
- 元数据读取
- 当前预览视频选择

中间 `Editor` 负责：

- 当前 Source Video 的 video preview
- 所有 Source Video 的数量和 metadata 摘要

## 经验数据

当前使用：

```txt
data/elastic_template.json
```

作为 mock editing experience。

后续后台接口接入后，Editor 不应该直接关心经验来自哪里，只需要消费归一化后的 `editingExperience`。

## `source_material.json`

后续进入真实闭环测试时，剪辑器和 agent 默认还需要一份外部输入：

```txt
source_material.json
```

它由 analyzer 产出，不由剪辑器负责生成。

当前这意味着：

- Editor 可以先继续做素材预览和 package 导出
- 当前已经可以接 mock `source_material.json`
- 真正的内容级自动剪辑仍要等 analyzer 链路正式接入

说明见：

- [`../source-material-handoff/README.md`](../source-material-handoff/README.md)

## 导出

当前 `Export Job` 导出的是 JSON package。

它不是最终 mp4。

package 包含：

- `sourceAssets`
- `sourceMaterials`
- `editingExperience`
- `timelinePlan`
- `editingJob`
- `renderResult`

后续 Codex / Cursor / agent 可以拿这份 package 测试 HyperFrames 工具链。

## 和 HyperFrames 的关系

HyperFrames 不外露给用户。

它属于 agent tool / render adapter：

```txt
editing package
  -> timeline plan
  -> HyperFrames composition
  -> final.mp4
```

## 相关文件

- [`../../frontend/src/features/editor/README.md`](../../frontend/src/features/editor/README.md)
- [`../agent-editing-tools/README.md`](../agent-editing-tools/README.md)
- [`../../shared/schemas/timeline-plan.schema.json`](../../shared/schemas/timeline-plan.schema.json)
- [`../../ai-service/output/README.md`](../../ai-service/output/README.md)
