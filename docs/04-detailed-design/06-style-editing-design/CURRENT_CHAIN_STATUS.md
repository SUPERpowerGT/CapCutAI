# Current Chain Status

这份文档记录当前两条视频链路的真实实现状态：

```txt
参考视频分析链
和
用户 source 素材剪辑链
```

## 当前总图

```txt
参考/爆款视频
  -> AI4Video pipeline_api
  -> step1_audio.json
  -> step2_transcript.json
  -> step3_visual.json
  -> elastic_template.json
  -> editingExperience

source 素材
  -> AI4Video pipeline_api
  -> sourceMaterials

editingExperience + sourceMaterials
  -> planner
  -> timelinePlan
  -> editing-package.json
  -> native ffmpeg render
  -> final.mp4
```

## 当前固定产物目录

用户可见 workspace 目录：

```txt
~/Documents/CapCutAI/Workspaces/<workspaceId>/
```

参考视频固定产物：

```txt
assets/intermediate/step1_audio.json
assets/intermediate/step2_transcript.json
assets/intermediate/step3_visual.json
assets/template/elastic_template.json
```

剪辑固定产物：

```txt
artifacts/plans/*.editing-package.json
artifacts/renders/*.native.final.mp4
artifacts/renders/*.native.final.render-result.json
```

内部调试缓存：

```txt
ai-service/output/im-runs/<workspaceId>/<conversationId_timestamp>/
```

注意：`im-runs` 不是用户最终交付目录。source 素材分析可以留在这里，最终 MP4 必须落回 workspace 的 `artifacts/renders/`。

## 已经闭环的能力

### 1. 参考视频 -> 风格经验

已经实现：

- 通过 IM 确认后启动 AI4Video 分析。
- 产出固定 `assets/template/elastic_template.json`。
- IM 状态查询优先检索固定产物，不从 source 缓存目录猜结果。

核心代码：

- [`../../../../AI4Video/pipeline_api.py`](../../../../AI4Video/pipeline_api.py)
- [`../../../../ai-service/app/services/reference_analysis_service.py`](../../../../ai-service/app/services/reference_analysis_service.py)
- [`../../../../ai-service/app/graph/conversation_graph.py`](../../../../ai-service/app/graph/conversation_graph.py)

### 2. 已有经验 + source 素材 -> demo 成片

已经实现：

- source 素材最多取 10 个。
- 每个 source 通过 AI4Video 生成结构化素材理解。
- planner 生成 `timelinePlan`。
- package builder 生成 `editing-package.json`。
- native ffmpeg renderer 生成 MP4。
- 最终成片落到 workspace `artifacts/renders/`。

核心代码：

- [`../../../../ai-service/app/services/styled_video_service.py`](../../../../ai-service/app/services/styled_video_service.py)
- [`../../../../ai-service/app/services/editing_planner_service.py`](../../../../ai-service/app/services/editing_planner_service.py)
- [`../../../../ai-service/app/tools/build_ai4video_package.py`](../../../../ai-service/app/tools/build_ai4video_package.py)
- [`../../../../ai-service/app/tools/render_native_video.py`](../../../../ai-service/app/tools/render_native_video.py)

### 3. IM 工具编排

已经实现：

- 用户上传参考视频和 source 后，IM 能识别“分析 / 剪辑 / 制作”意图。
- 重任务执行前会先确认。
- 已经存在 `elastic_template.json` 时，剪辑请求默认复用经验，不重复分析参考视频。
- 只有明确说“重新分析 / 重跑分析 / 再分析一次”才重跑参考分析。
- 分析或剪辑运行时，前端会锁定对应素材区，并显示动态状态。

核心代码：

- [`../../../../frontend/src/features/im/hooks/use-im-workspace.ts`](../../../../frontend/src/features/im/hooks/use-im-workspace.ts)
- [`../../../../frontend/src/features/workspace/components/WorkspaceShell.tsx`](../../../../frontend/src/features/workspace/components/WorkspaceShell.tsx)
- [`../../../../frontend/src/features/im/components/MessageFeed.tsx`](../../../../frontend/src/features/im/components/MessageFeed.tsx)

## 当前对象口径

### `editingExperience`

来源：

- `assets/template/elastic_template.json`

作用：

- 描述参考视频风格、节奏、叙事 phase、字幕/视觉偏好。

### `sourceMaterials`

来源：

- 对 source 素材运行 AI4Video pipeline。

作用：

- 描述每个 source 的音频节奏、转写、镜头和视觉语义。

### `timelinePlan`

来源：

- `editing_planner_service`。

作用：

- 决定哪些 source 片段被选中、何时出现、字幕和 overlay 怎么排。

### `editing-package.json`

来源：

- `build_ai4video_package.py`。

作用：

- 把素材、经验和计划打成 renderer 可执行包。

## 当前仍需增强的部分

### 1. Planner 质量

现在已经能出片，但 planner 仍偏最小闭环：

- LLM planner 失败时会 rule-based fallback。
- fallback 会更像“可渲染拼接”，不一定足够像参考风格。
- 需要继续增强 phase-aware 选片、卡点、字幕和情绪曲线。

### 2. 进度粒度

当前前端已经能显示分析/剪辑状态，但 source 分析、planner、package、render 的细粒度进度还可以继续拆。

### 3. 输出资产管理

最终 MP4 已落 workspace，但后续还需要：

- 在 workspace 中登记 render asset。
- 支持历史成片列表。
- 支持打开文件、复制路径、重新渲染。

## 当前建议下一步

优先级从高到低：

1. 增强 planner，让它真正利用 `editingExperience.storylinePhases` 和 source 视觉/音频特征。
2. 给剪辑工作流加更细粒度进度文件或事件。
3. 把最终 render 注册成 workspace asset。
4. 再考虑 HyperFrames 作为更复杂 overlay/动效 renderer。
