# Workspace Agent Runtime & Context Engineering Model

这份文档是 CapCutAI 的 agent runtime 基线。

它只解决 6 个问题：

1. 系统的主语是什么
2. `context`、`memory`、`runtime state` 分别是什么
3. 一次 agent run 是怎么被驱动起来的
4. 这些信息在 frontend / backend / ai-service / orchestrator / tools 之间怎么流动
5. 哪些 schema / 接口应该先定死
6. 失败时怎么降级

先给最终拍板：

```txt
Workspace 是主语
context 是当前 run 的事实输入快照
memory 是可跨 run 复用的沉淀
agent state 是 graph 执行时承载这些信息的可变状态
context engineering 是构造、选择、压缩、检索、注入、更新这些信息的工程过程
```

再补两句工程上最重要的边界：

```txt
Agent Runtime 负责思考、编排和工具调度
Local Tool Runtime 负责真实媒体执行
```

---

## 1. System Model

CapCutAI 不是聊天产品，核心主语不是 session，而是 workspace。

推荐固定成这条关系：

```txt
Window
  -> Workspace
    -> Assets
    -> Task
    -> Conversation
    -> Artifacts
```

如果按运行时视角展开，推荐理解成：

```txt
Desktop Client
  -> Local Agent Runtime
    -> Memory / Context Builder
    -> Graph Orchestrator
    -> Local Tool Runtime
  -> Workspace File System
  -> Cloud / Local LLM
```

其中：

- `Workspace`
  - 一个桌面窗口对应一个 workspace
  - 持有本地目录、资产、任务、产物
- `Assets`
  - 当前最关键的是：
    - `reference video`
    - `source videos`
- `Task`
  - 当前这轮到底在做什么：
    - `chat`
    - `analyze_reference`
    - `create_styled_video`
    - `revise_video`
- `Conversation`
  - 只是交互记录，不是产品主心智
- `Artifacts`
  - 中间产物和最终产物
  - 例如：
    - `style_profile.json`
    - `timeline_plan.json`
    - `final.mp4`

---

## 2. Core Definitions

先定 4 句最重要的定义：

```txt
context = 每次 run 重新组装的事实输入快照
memory = 运行后沉淀、下次按需检索的可复用记忆
runtime state = graph 执行过程中持续变化的状态容器
context engineering = 构造、选择、压缩、检索、注入、更新这些信息的工程过程
```

再补一个硬边界：

```txt
context 是 AgentState 的输入字段之一
但 AgentState 不等于 context
```

因为 `AgentState` 里还会继续长出：

- intent inference
- tool calls
- partial artifacts
- response draft
- error / warning / retry info

---

## 3. Layer Boundary

这一章只讲分层，不讲流程。

### 3.1 Context

`context` 是当前这一次 run 开始前，系统能明确知道的事实。

来源只能是：

- frontend 当前窗口
- workspace 当前目录
- assets 当前状态
- conversation 当前请求
- task 当前入口

`context` 的特点：

- 每次请求都可以重新构造
- 在一次 run 内应尽量只读
- 不能被当成长期状态来源

一句话：

```txt
context 负责“这轮开始时手上有什么”
```

### 3.2 Memory

`memory` 是 run 之后沉淀下来、未来还能读回复用的信息。

来源可以是：

- conversation history 的整理结果
- workspace facts 的沉淀
- tool outputs
- artifact metadata
- user preference summary

一句话：

```txt
memory 负责“以前做过什么、以后还能继续用什么”
```

### 3.3 Runtime State

`runtime state` 是 graph 执行过程中的状态容器。

它会随着节点执行而变化。

例如：

- `intent`
- `tool_calls`
- `response`
- `status`
- `error`

一句话：

```txt
context 是输入
runtime state 是运行中的承载体
memory 是运行后的沉淀
```

### 3.4 Control Plane vs Data Plane

推荐再加一个统一视角：

- 控制面
  - 用户意图
  - AgentState
  - tool selection
  - plan / revision
- 数据面
  - 原始视频
  - 抽帧
  - 音频特征
  - artifacts
  - final.mp4

一句话：

```txt
模型和 Agent Runtime 主要工作在控制面
workspace 和 Tool Runtime 主要承载数据面
```

---

## 4. Runtime State vs Long-term Memory

这里要强制区分：

```txt
context = run 启动前输入进来的事实快照
runtime state = graph 执行过程中持续变化的状态容器
memory = 跨 run 复用的持久化沉淀
```

例子：

- `context.workspaceId`
  - 输入事实
- `state.intent`
  - 运行中推理出的结果
- `state.tool_calls`
  - 运行中产生
- `state.response`
  - 运行结束生成
- `memory.artifact_memory`
  - 下次还可复用

建议固定理解成：

```txt
context is immutable within one run as much as possible
runtime state is mutable during graph execution
```

---

## 5. Context Engineering

在 CapCutAI 中，`Context Engineering` 指的是：

```txt
在每一次 agent run 之前和之中，
动态构造一份足够准确、足够紧凑、足够可执行的上下文输入，
并把相关 memory 以正确形式注入 graph / prompt / tools / subagents。
```

它不是单纯写 prompt，而是完整的信息调度过程。

### 5.1 Steps

```txt
Context Collection
-> Context Normalization
-> Context Selection
-> Context Compression
-> Memory Retrieval
-> Context Injection
-> Context Update
```

### 5.2 Prompt Engineering vs Context Engineering

```txt
Prompt Engineering 关注：怎么写提示词
Context Engineering 关注：这次 run 应该看到哪些信息，这些信息从哪里来、如何组织、如何更新
```

对 CapCutAI 来说：

```txt
Context Engineering 比 Prompt Engineering 更重要
```

因为这个系统不是一次性问答，而是 workspace-based runtime：

- 有 reference video
- 有多个 source videos
- 有 timeline plan
- 有 style profile
- 有 render output
- 有 revision history
- 有用户偏好

关键不是“提示词漂不漂亮”，而是：

```txt
每一次 agent run，系统能不能把正确的信息塞到正确的位置
```

---

## 6. Context Model

### 6.1 Recommended Context Schema

```txt
context
  workspace
  assets
  conversation
  task
```

对于视频工作流，后面还会自然长出：

```txt
context.media_manifest
context.task_checkpoint
```

### 6.2 Example

```json
{
  "workspace": {
    "workspaceId": "workspace_123",
    "workspaceTitle": "Workspace 123",
    "workspaceFolderPath": "/Users/zee/Documents/CapCutAI/Workspaces/workspace_123"
  },
  "assets": {
    "referenceDirectoryPath": "assets/reference/current",
    "sourceDirectoryPath": "assets/source",
    "referenceVideo": {
      "assetId": "asset_ref_1",
      "name": "one-last-kiss.mp4",
      "workspaceRelativePath": "assets/reference/current/one-last-kiss.mp4"
    },
    "sourceVideos": [
      {
        "assetId": "asset_src_1",
        "name": "clip-01.mp4",
        "workspaceRelativePath": "assets/source/asset_src_1__clip-01.mp4"
      }
    ],
    "selectedSourceVideo": {
      "assetId": "asset_src_1",
      "name": "clip-01.mp4",
      "workspaceRelativePath": "assets/source/asset_src_1__clip-01.mp4"
    }
  },
  "conversation": {
    "conversationId": "conv_123",
    "latestUserMessage": "按上次那个风格继续改"
  },
  "task": {
    "entry": "chat",
    "mode": "revise_video"
  }
}
```

### 6.3 Rules

- frontend 只传当前事实
- context 每次 run 可重建
- context 不负责长期持久化
- 某个信息如果需要跨轮次稳定存在，不能只靠 context，必须进入 memory 或 artifact

---

## 7. Memory Model

### 7.1 Recommended Memory Schema

```txt
memory
  conversation_memory
  workspace_memory
  artifact_memory
  preference_memory
```

再往工程上讲，建议拆成两类：

```txt
retrievable_memory
executable_artifact_refs
```

其中：

- `retrievable_memory`
  - summary
  - preference
  - workspace facts
  - revision summary
- `executable_artifact_refs`
  - 指向真实 artifact 的 metadata / path / version / reusable 标记

### 7.2 Conversation History vs Conversation Memory

- 原始 `messages`
  - 是 `conversation history`
  - 不是已经整理好的 memory
- 由 messages 提炼出的摘要
  - 才更像 `conversation_memory`

一句话：

```txt
raw history 不是 memory
history summary 才更像 memory
```

### 7.3 Artifact vs Artifact Memory

- `style_profile.json`
  - 是 artifact 本体
- `artifact_memory`
  - 不应存 artifact 全文
  - 应存：
    - metadata
    - path
    - version
    - summary
    - reusable 标记

示例：

```json
{
  "artifactId": "artifact_style_001",
  "type": "style_profile",
  "path": "artifacts/materials/style_profile.json",
  "summary": "One Last Kiss style profile extracted from reference video",
  "version": 3,
  "createdByTaskId": "task_123",
  "reusable": true
}
```

一句话：

```txt
artifact 本体不是 memory
artifact 的 metadata / path / version / summary 更适合作为 artifact_memory
```

### 7.4 Where Memory Lives

#### Runtime Memory

放在 graph state 里，临时可变。

#### Workspace-local Memory

放在 workspace 文件夹里，例如：

```txt
<workspace>/
  memory/
    workspace_memory.json
    artifact_memory.json
    conversation_summary.json
```

这里推荐再补一个任务持久化目录：

```txt
<workspace>/
  tasks/
    task_123.json
```

至少记录：

- `taskId`
- 当前阶段
- 计划版本
- tool 调用历史
- 错误信息
- 产物路径

#### Backend / DB Memory

放 conversation records、task records、未来云端同步状态。

#### Artifact Files

真实 artifact 本体继续放：

- `style_profile.json`
- `timeline_plan.json`
- `final.mp4`

---

## 8. Memory Read / Write Path

### 8.1 Write Path

```txt
user request
  -> build context
  -> run graph / tools / subagents
  -> produce results / artifacts
  -> summarize / normalize
  -> write memory
```

这条路径决定：

- 沉淀什么
- 沉淀成什么结构
- 写到哪里

### 8.2 Read Path

```txt
user request
  -> build context
  -> retrieve relevant memory
  -> inject selected memory into graph state
  -> agent planning
  -> tool execution
```

这条路径决定：

- 本轮到底读哪些 memory
- 哪些给模型看
- 哪些只给 tool / planner 用

一句话：

```txt
memory 不应该每次全量塞给模型
而应该按任务检索、按需注入
```

---

## 9. AgentState Schema

推荐先定成：

```txt
meta
context
memory
intent
tool_calls
artifacts
response
status
error
```

其中 `status` 推荐优先支持：

- `queued`
- `running`
- `waiting_for_input`
- `failed`
- `cancelled`
- `completed`

### Example

```json
{
  "meta": {
    "runId": "run_123",
    "taskId": "task_123",
    "workspaceId": "workspace_123",
    "conversationId": "conv_123",
    "createdAt": "2026-05-31T12:00:00Z"
  },
  "context": {
    "workspace": {
      "workspaceId": "workspace_123",
      "workspaceFolderPath": "/Workspaces/workspace_123"
    },
    "assets": {
      "referenceVideo": {
        "assetId": "asset_ref_1",
        "path": "assets/reference/current/ref.mp4"
      },
      "sourceVideos": []
    },
    "conversation": {
      "conversationId": "conv_123",
      "latestUserMessage": "按上次那个风格继续改"
    },
    "task": {
      "entry": "chat",
      "mode": "revise_video"
    }
  },
  "memory": {
    "conversationMemory": {
      "summary": "User is revising a previously generated result."
    },
    "workspaceMemory": {
      "hasReferenceVideo": true,
      "hasSourceVideo": true
    },
    "artifactMemory": [
      {
        "artifactId": "artifact_style_001",
        "type": "style_profile",
        "path": "artifacts/materials/style_profile.json",
        "version": 3,
        "reusable": true
      }
    ],
    "preferenceMemory": {
      "subtitleStyle": "clean_minimal"
    }
  },
  "intent": {
    "type": "revise_video",
    "confidence": 0.91,
    "missingFields": []
  },
  "toolCalls": [],
  "artifacts": [],
  "response": null,
  "status": "running",
  "error": null
}
```

---

## 10. Module Responsibility

这部分提前定死，不然后面最容易吵：

```txt
这个字段前端传？
后端查？
agent 自己生成？
tool 里处理？
```

### Frontend

负责提供：

- `workspaceId`
- `conversationId`
- 当前 workspace 基本事实
- 当前选中的 reference / source 资产
- 当前用户消息
- UI-level task hint

不负责：

- 生成 memory
- 判断长期偏好
- 读取 artifact 全文
- 决定最终 subagent

一句话：

```txt
frontend 只负责提供当前事实
```

### Backend / AI Service

负责：

- build context
- retrieve memory
- construct AgentState
- run graph
- update memory
- write artifact metadata

其中：

- backend
  - 更偏 conversation / task / persistence / business entry
- ai-service
  - 更偏 graph / orchestration / prompt / tool / subagent dispatch

一句话：

```txt
backend / ai-service 负责把原始事实变成 agent 可运行状态
```

### LangGraph / Orchestrator

负责：

- intent routing
- subagent dispatch
- tool orchestration
- state transition
- final response generation

不负责：

- 直接管理 UI
- 直接维护本地窗口状态
- 直接实现底层视频算法

一句话：

```txt
orchestrator 决定下一步该由谁做什么
```

### Tool Layer

负责：

- video analysis
- audio analysis
- timeline generation
- render execution
- artifact creation

不负责：

- 主流程决策
- memory 注入决策
- conversation 语义判断

一句话：

```txt
tool 做能力，orchestrator 做决策
```

### Memory Layer

建议明确拆成 4 个工程模块：

#### MemoryReader

从 workspace-local memory / DB / artifact metadata 中读取候选 memory。

#### MemorySelector

根据：

- `workspaceId`
- `conversationId`
- `intentType`
- `artifactType`
- `recency`
- `selected asset ids`

选择相关 memory。

#### MemoryCompressor

压缩：

- 长 history
- 长 artifact summary
- 长 revision 记录

#### MemoryWriter

在 run 结束后写入：

- `conversation_memory`
- `workspace_memory`
- `artifact_memory`
- `preference_memory`

更细的 invocation、接口、失败策略和检索策略已经拆到详细设计层：

- [`../../04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md`](../../04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md)
- [`../../04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md`](../../04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md)

---

## 11. Final Decision

如果只保留最硬的版本，就保留这几句：

```txt
Workspace 是主语
context = 每次 run 重新组装的事实输入快照
memory = 运行后沉淀、下次按需检索的可复用记忆
context 在一次 run 内应尽量只读
runtime state 是 graph 执行过程中的可变状态
raw history 不是 memory
history summary 才更像 memory
artifact 本体不是 memory
artifact 的 metadata / path / version / summary 更适合作为 artifact_memory
P0 优先 deterministic retrieval，不优先 vector retrieval
```

---

## Related Docs

- LangGraph 规范：[`../../04-detailed-design/02-langgraph-engineering-guideline/README.md`](../../04-detailed-design/02-langgraph-engineering-guideline/README.md)
- AI Service 视频架构：[`../../04-detailed-design/01-ai-service-video-architecture/README.md`](../../04-detailed-design/01-ai-service-video-architecture/README.md)
- Agent Runtime Invocation：[`../../04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md`](../../04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md)
- Runtime Resilience / Retrieval：[`../../04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md`](../../04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md)
- 前端主文档：[`../../frontend/README.md`](../../frontend/README.md)
- AI Service 主文档：[`../../ai-service/README.md`](../../ai-service/README.md)
