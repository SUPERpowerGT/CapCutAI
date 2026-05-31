# Workspace Agent Use Cases

这份文档回答一个最关键的问题：

```txt
CapCutAI 后面的 agent、context、memory、tool、subagent，到底是被哪些 use case 驱动出来的？
```

如果没有这份文档，后面很容易变成：

- 先设计一堆 context 字段
- 先做一堆 memory 分类
- 先接一堆 tool

但最后没人能回答：

```txt
这些东西到底是为哪个真实工作流服务的？
```

所以这份文档的目标不是讲实现，而是：

```txt
先定 use case，再反推 context / memory / tool / subagent 设计
```

---

## 1. One-line Decision

CapCutAI 当前最重要的 use case 只有 4 类：

1. 分析爆款参考视频
2. 基于参考风格剪用户视频
3. 对已生成结果继续修订
4. 在 workspace 里恢复和继续未完成工作

如果后面的设计不能服务这 4 类 use case，就说明做偏了。

---

## 2. Use Case Map

推荐固定成这条关系：

```txt
Workspace
  -> Reference Analysis
  -> Source Editing
  -> Revision
  -> Resume Work
```

进一步展开：

```txt
Use Case
  -> User Goal
  -> Required Inputs
  -> Runtime Context
  -> Required Memory
  -> Tools / Subagents
  -> Outputs / Artifacts
```

---

## 3. Use Case 1: Analyze Reference Video

### User Goal

用户上传一个爆款视频，希望系统理解它的风格，并沉淀成后面可复用的结构化结果。

典型输入：

- “分析这个参考视频的风格”
- “帮我拆一下这个爆款视频的节奏、字幕和音乐感觉”

### Required Inputs

最少需要：

- 当前 workspace
- 一个 `reference video`

### Runtime Context

这条 use case 最关心的 context：

- `workspaceId`
- `workspaceFolderPath`
- `referenceDirectoryPath`
- `referenceVideo`
- 当前 task mode = `analyze_reference`

### Required Memory

第一版最少需要：

- `workspace_memory`
  - 当前有没有 reference
- `artifact_memory`
  - 当前 reference 是否已经分析过
  - 是否有旧版 `style_profile`

### Tools / Subagents

第一版会逼出来的能力：

- metadata extractor
- material analyzer
- style summarizer
- style structurer
- local frame / audio / transcript preprocessors

后面更自然的抽象：

- `reference-analysis subagent`

### Outputs / Artifacts

最关键的输出：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

### Why It Matters

这条 use case 决定了：

- reference 资产怎么建模
- artifact memory 的最小结构
- style analysis 工具链怎么拆

---

## 4. Use Case 2: Create Styled Video from Source Videos

### User Goal

用户上传一个或多个 source videos，希望系统按参考风格生成成片。

典型输入：

- “帮我做成 One Last Kiss 风格”
- “用这个参考风格剪这几段用户视频”

### Required Inputs

最少需要：

- 当前 workspace
- 一个 `reference video`
- 至少一个 `source video`

### Runtime Context

这条 use case 最关心的 context：

- `workspaceId`
- `referenceVideo`
- `sourceVideos`
- `selectedSourceVideo`
- `referenceDirectoryPath`
- `sourceDirectoryPath`
- 当前 task mode = `create_styled_video`

### Required Memory

最少需要：

- `workspace_memory`
  - 当前 source 个数
  - 当前 selected source
- `artifact_memory`
  - latest `style_profile`
  - latest `editing_rules`
- 可选：
  - `preference_memory`

### Tools / Subagents

第一版会逼出来的能力：

- input normalizer
- source video analyzer
- style retriever
- director planner
- editing job generator
- render executor
- workspace-scoped local tool calls

后面更自然的抽象：

- `style-editing subagent`

### Outputs / Artifacts

最关键的输出：

- `timeline_plan.json`
- `editing_job.json`
- `final.mp4`

### Why It Matters

这条 use case 决定了：

- source assets 为什么必须支持多个
- selected source 为什么要进 context
- artifact retrieval 为什么不能只靠 conversation history

---

## 5. Use Case 3: Revise Existing Output

### User Goal

用户已经得到一个结果，希望继续微调，而不是从头再来。

典型输入：

- “把字幕改小一点”
- “节奏再快一点”
- “还是按刚才那个风格，但少一点贴图”

### Required Inputs

最少需要：

- 当前 workspace
- 已存在的 plan / render / analysis artifacts
- 当前 conversation

### Runtime Context

这条 use case 最关心的 context：

- `workspaceId`
- `conversationId`
- `selectedSourceVideo`
- 当前 task mode = `revise_video`
- 当前用户指令

### Required Memory

这是最依赖 memory 的 use case。

最少需要：

- `artifact_memory`
  - latest `style_profile`
  - latest `timeline_plan`
  - latest `render`
  - latest `revision_summary`
- `conversation_memory`
  - 最近一轮修订摘要
- 可选：
  - `preference_memory`

### Tools / Subagents

第一版会逼出来的能力：

- revision intent parser
- artifact loader
- plan patcher
- re-render executor
- checkpoint-aware task resumer

后面更自然的抽象：

- `revision subagent`

### Outputs / Artifacts

最关键的输出：

- patched `timeline_plan.json`
- new `editing_job.json`
- new `final.mp4`
- revision summary

### Why It Matters

这条 use case 决定了：

- 为什么 `artifact_memory` 优先级比 `conversation_memory` 更高
- 为什么 memory read path 必须是按任务检索
- 为什么 IM 不能只是聊天，而要变成 workspace agent console

---

## 6. Use Case 4: Resume Workspace and Continue Work

### User Goal

用户关闭 app 或切换窗口后，再次回来时，希望继续上次工作，而不是重新开始。

典型输入：

- 打开 app
- 打开某个 workspace
- `Window -> New Window`

### Required Inputs

最少需要：

- 当前 workspace 文件夹
- 当前 workspace 下已有 assets
- 当前 workspace 下已有 memory / artifacts

### Runtime Context

这条 use case 最关心的 context：

- `workspaceId`
- `workspaceFolderPath`
- `referenceDirectoryPath`
- `sourceDirectoryPath`

### Required Memory

最少需要：

- `workspace_memory`
- `artifact_memory`
- `conversation_summary`

### Tools / Subagents

第一版未必需要新 subagent，但会逼出来这些能力：

- workspace asset scanner
- workspace memory loader
- artifact metadata loader
- task checkpoint loader

### Outputs / Artifacts

最关键的恢复结果：

- 左侧资产列表恢复
- 右侧 conversation 恢复
- 可继续 revision / generate

### Why It Matters

这条 use case 决定了：

- 为什么 workspace 才是主语
- 为什么 session 不是主心智
- 为什么 memory 必须是可持久化、可恢复的

---

## 7. What These Use Cases Force Us to Design

如果把上面 4 个 use case 放在一起看，后面一定会逼出这些设计：

### Context

至少要能表达：

- workspace
- assets
- conversation
- task

### Memory

至少要有：

- `workspace_memory`
- `artifact_memory`
- `conversation_memory`

其中当前最关键的是：

- `workspace_memory`
- `artifact_memory`

### Tools

至少会需要：

- reference analysis tools
- source analysis tools
- plan generation tools
- render tools
- artifact loading / patching tools

这些工具默认都应该优先理解成：

```txt
由 Local Tool Runtime 暴露给 Agent Runtime 的受控本地能力
```

### Subagents

最自然的 3 个方向：

- `reference-analysis subagent`
- `style-editing subagent`
- `revision subagent`

---

## 8. Priority Order

按 use case 驱动，当前推荐优先级是：

### P0

- Use Case 1: Analyze Reference Video
- Use Case 2: Create Styled Video from Source Videos

因为这两条决定 MVP 能不能闭环。

### P1

- Use Case 3: Revise Existing Output

因为它决定 IM 的真正价值，但前提是前两条先能产出 artifacts。

### P2

- Use Case 4: Resume Workspace and Continue Work

它很重要，但更多是把产品从“能跑通”升级成“真的能长期用”。

---

## 9. How to Use This Doc

后面团队每设计一层东西时，都先回来看这份文档：

### 设计 context schema 前

先问：

```txt
这个字段是被哪个 use case 需要的？
```

### 设计 memory schema 前

先问：

```txt
这是为了哪条 use case 的“下次继续做”服务的？
```

### 设计 tool 前

先问：

```txt
它是为分析、生成、修订、恢复中的哪一步服务？
```

### 设计 subagent 前

先问：

```txt
它是不是对应一个稳定、独立、会长期存在的 use case？
```

---

## 10. Final Decision

如果只保留最硬的一版，就保留这几句：

```txt
CapCutAI 的设计应由 use case 驱动，不是由 prompt 或 graph 反推
当前最关键的 use case 是：分析 reference、生成 styled video、修订 output、恢复 workspace
artifact_memory 是视频工作流里最重要的 memory 之一
Workspace 是主语，Conversation 只是交互记录
IM 最终应该服务 revision 和 orchestration，而不是单纯聊天
模型负责理解和计划，本地工具负责执行
```

---

## Related Docs

- Workspace Agent Runtime：[`../../03-architecture/01-workspace-agent-runtime-model/README.md`](../../03-architecture/01-workspace-agent-runtime-model/README.md)
- Client / Backend / AI 边界：[`../../03-architecture/02-client-backend-agent-tool-boundary/README.md`](../../03-architecture/02-client-backend-agent-tool-boundary/README.md)
- 视频 MVP 主线：[`../../04-detailed-design/03-mvp-video-pipeline/README.md`](../../04-detailed-design/03-mvp-video-pipeline/README.md)
- 风格分析设计：[`../../04-detailed-design/05-style-analysis-design/README.md`](../../04-detailed-design/05-style-analysis-design/README.md)
- 风格套用设计：[`../../04-detailed-design/06-style-editing-design/README.md`](../../04-detailed-design/06-style-editing-design/README.md)
