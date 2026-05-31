# Codex Skill Draft: HyperFrames Editing

这是一份后续迁移成 Codex skill 的草案。

当前先放在 `docs/`，用于人工调试。

## Trigger

当用户要求：

- 根据 Source Video 和经验数据生成剪辑计划
- 根据 `timeline_plan.json` 生成 HyperFrames composition
- 渲染或导出视频

使用本草案。

## Inputs

优先读取 Editor 导出的 package：

```txt
*.editing-package.json
```

如果没有 package，则读取：

- `data/elastic_template.json`
- Source Video metadata

## Workflow

1. 读取 editing package
2. 校验字段：
   - `sourceAssets`
   - `editingExperience`
   - `timelinePlan`
   - `editingJob`
3. 在 `ai-service/output/plans/` 下创建 composition 目录
4. 优先调用本地 draft builder：
   - `cd ai-service`
   - `python -m app.tools.build_hyperframes_draft --package ../path/to/example.editing-package.json`
5. 根据 draft 输出继续细化真实 HyperFrames composition
6. 在 `ai-service/output/renders/` 写入：
   - `final.mp4`
   - `render_result.json`

## HyperFrames Command Draft

后续真实接入时，可以按 HyperFrames 官方 CLI 或 Node producer 选择实现方式。

CLI 形态草案：

```bash
npx hyperframes render --output ai-service/output/renders/example.final.mp4
```

Node producer 形态草案：

```txt
timeline_plan
  -> composition draft files
  -> refined composition files
  -> producer render
  -> final.mp4
```

## Output Contract

渲染完成后必须输出：

```json
{
  "renderId": "render_xxx",
  "jobId": "editing_job_xxx",
  "status": "completed",
  "outputPath": "ai-service/output/renders/example.final.mp4"
}
```

## User-facing Rule

不要在用户界面中暴露 HyperFrames。

用户只需要看到：

- 正在生成
- 生成完成
- 最终视频

HyperFrames 是 agent 内部工具。

## Current Limitation

如果导出 package 里的素材还是浏览器 `blob:` object URL，draft builder 可以继续产出 composition 目录，但还不能直接稳定渲染最终 mp4。

真实 render 前需要把素材替换成稳定的本地文件路径或 workspace-managed asset path。
