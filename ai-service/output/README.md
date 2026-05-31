# AI Service Output

这里放视频链路的本地输出产物。

当前策略仍然是：

```txt
Local-first
Cloud-ready
```

也就是说，第一版可以先把 agent / Codex / Cursor 调试出来的产物落在本地目录里，后续再替换成后端持久化或云端对象存储。

## 目录说明

```txt
output/
├── materials/
├── plans/
└── renders/
```

### `materials/`

放参考视频分析链输出的结构化经验材料。

典型文件：

- `*.materials.json`
- `*.style_profile.json`
- `*.editing_rules.json`
- `*.editing_experience.json`

### `plans/`

放用户视频自动剪辑链输出的计划与执行任务。

典型文件：

- `*.timeline_plan.json`
- `*.editing_job.json`
- `*.hyperframes/`

其中 `*.hyperframes/` 后续可以放 agent 生成的 HyperFrames composition 文件。

### `renders/`

放最终渲染产物和渲染结果描述。

典型文件：

- `*.final.mp4`
- `*.render_result.json`

## 当前约定

当前前端 Editor 的 `Export Job` 会先导出一份 JSON package，里面包括：

- `sourceAssets`
- `editingExperience`
- `timelinePlan`
- `editingJob`
- `renderResult`

这份 package 用来给 agent / Codex / Cursor 调试 HyperFrames 工具链。

当前也支持从这份 package 进一步生成 HyperFrames draft composition 目录：

```bash
cd ai-service
python -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```
