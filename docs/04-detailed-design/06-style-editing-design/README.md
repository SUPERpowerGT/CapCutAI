# Style Editing Design

这份文档说明当前“根据参考视频经验，剪辑用户 source 素材”的产品链路。

它关注的是：

```txt
已有风格经验 + 用户素材
  -> 剪辑计划
  -> 可渲染 package
  -> final.mp4
```

参考视频本身的分析细节见：

- [`../05-style-analysis-design/README.md`](../05-style-analysis-design/README.md)
- [`CURRENT_CHAIN_STATUS.md`](./CURRENT_CHAIN_STATUS.md)

## 当前目标

输入：

- 一个参考/爆款视频，或已有 `elastic_template.json`
- 1 到 10 个 source 视频
- 用户在 IM 中的自然语言指令

输出：

- `timeline_plan.json`
- `editing-package.json`
- `*.native.final.mp4`

目标不是给文字建议，而是直接产出可预览的 demo 成片。

## 当前总流程

```txt
Reference Video
  -> AI4Video pipeline_api
  -> assets/template/elastic_template.json
  -> editingExperience

Source Videos
  -> AI4Video pipeline_api
  -> sourceMaterials

editingExperience + sourceMaterials + user prompt
  -> planner
  -> timelinePlan
  -> editing-package.json
  -> native ffmpeg render
  -> final.mp4
```

## Workspace 目录约定

当前用户可见产物全部按 workspace 归档：

```txt
~/Documents/CapCutAI/Workspaces/<workspaceId>/
  assets/
    reference/current/       参考/爆款视频
    source/                  用户 source 素材
    intermediate/            参考视频分析中间文件
    template/elastic_template.json
  artifacts/
    plans/                   timeline plan / editing package
    renders/                 final MP4 / render result
```

内部调试缓存：

```txt
ai-service/output/im-runs/
```

注意：

- `assets/template/elastic_template.json` 是固定参考经验位置。
- `artifacts/renders/*.native.final.mp4` 是最终成片交付位置。
- `ai-service/output/im-runs` 不作为用户最终成片路径。

## IM 产品行为

当前 IM agent 的行为约定：

- 用户说“分析爆款/参考视频”时，先确认，再运行 AI4Video 分析。
- 用户说“剪辑/制作/出一版 demo”时，如果已有 `elastic_template.json`，默认直接复用经验剪 source。
- 只有用户明确说“重新分析 / 重跑分析 / 再分析一次”，才重跑参考视频分析。
- 用户问“产物 / 结果 / 分析好了没”时，优先检索 workspace 固定产物。
- 长任务运行时，前端会锁定对应素材区，并显示动态状态。

## 核心对象

### `editingExperience`

来源：

- `assets/template/elastic_template.json`

作用：

- 描述参考视频的风格、节奏、叙事 phase、视觉和字幕偏好。

### `sourceMaterials`

来源：

- 对 source 视频运行 AI4Video pipeline。

作用：

- 描述用户素材中的音频节奏、转写、镜头和视觉语义。

### `timelinePlan`

来源：

- `editing_planner_service`。

作用：

- 决定素材片段选择、顺序、时长、字幕和 overlay。

### `editing-package.json`

来源：

- `build_ai4video_package.py`。

作用：

- renderer 可执行的完整导出包。

### `renderResult`

来源：

- `render_native_video.py` / `native_render_service.py`。

作用：

- 记录最终 MP4 路径、尺寸、音频模式、字幕数量、渲染命令和错误信息。

## 当前代码入口

IM 编排：

- [`../../../../ai-service/app/graph/conversation_graph.py`](../../../../ai-service/app/graph/conversation_graph.py)
- [`../../../../frontend/src/features/im/hooks/use-im-workspace.ts`](../../../../frontend/src/features/im/hooks/use-im-workspace.ts)

参考分析：

- [`../../../../ai-service/app/services/reference_analysis_service.py`](../../../../ai-service/app/services/reference_analysis_service.py)
- [`../../../../AI4Video/pipeline_api.py`](../../../../AI4Video/pipeline_api.py)

剪辑成片：

- [`../../../../ai-service/app/services/styled_video_service.py`](../../../../ai-service/app/services/styled_video_service.py)
- [`../../../../ai-service/app/services/editing_planner_service.py`](../../../../ai-service/app/services/editing_planner_service.py)
- [`../../../../ai-service/app/tools/build_ai4video_package.py`](../../../../ai-service/app/tools/build_ai4video_package.py)
- [`../../../../ai-service/app/tools/render_native_video.py`](../../../../ai-service/app/tools/render_native_video.py)

## 当前状态

已经完成：

- 参考视频分析到 `elastic_template.json`。
- source 素材分析。
- planner 生成 `timelinePlan`，并支持 fallback。
- package builder。
- native ffmpeg render。
- IM 触发、确认、状态展示和素材锁定。
- 最终成片输出到 workspace `artifacts/renders/`。

仍需增强：

- planner 质量，让成片更像参考视频，而不只是可渲染。
- source 分析和 render 的细粒度进度。
- 最终成片登记成 workspace asset。
- 横竖屏混剪和目标比例策略。
- 更复杂的 overlay / 动效 renderer。

## 继续阅读

- [`CURRENT_CHAIN_STATUS.md`](./CURRENT_CHAIN_STATUS.md)
- [`AI4VIDEO_CLOSURE_CHECKLIST.md`](./AI4VIDEO_CLOSURE_CHECKLIST.md)
