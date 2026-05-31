# Client / Backend / AI Service Boundary

这份文档只回答一个问题：

```txt
CapCutAI 里，哪些事情属于客户端，哪些属于 backend，哪些属于 ai-service？
```

如果这个边界不先定清楚，后面设计 agent context 时一定会反复打架：

- 这个字段前端传？
- backend 查？
- ai-service 推理出来？
- tool 再去读文件？

这份文档的目标就是把这些边界先拍板。

---

## 1. One-line Decision

先给最重要的结论：

```txt
Client UI 负责提供当前事实和本地工作区入口
Backend 负责业务记录、任务入口和持久化边界
AI Service / Local Agent Runtime 负责 context engineering、memory retrieval、graph orchestration 和 tool dispatch
Local Tool Runtime 负责真实媒体分析、渲染与导出执行
```

再换一种更工程的说法：

```txt
Client UI = 事实采集与展示层
Backend = 业务与持久化边界层
AI Service / Agent Runtime = 智能编排层
Local Tool Runtime = 媒体执行层
```

再补一个关键边界：

```txt
UI Client != Tool Runtime
模型不直接操作 UI
Agent Runtime 调的是本地受控工具能力
```

---

## 2. Layer Model

当前推荐固定成这条链：

```txt
User Action
  -> Client UI
  -> Backend
  -> AI Service / Agent Runtime
  -> Local Tool Runtime / Artifacts / Memory
  -> Backend
  -> Client UI
```

其中：

- `Client`
  - 桌面窗口
  - workspace 本地目录
  - assets 面板
  - preview / timeline / agent panel
- `Local Tool Runtime`
  - FFmpeg
  - scene split
  - frame extraction
  - audio feature extraction
  - render / transcode
- `Backend`
  - conversation / task / persistence / API entry
  - 业务级记录和状态
- `AI Service`
  - context normalization
  - memory retrieval
  - graph orchestration
  - prompt / tool / subagent 调度

---

## 3. Responsibility Matrix

### 3.1 Client

客户端负责：

- 管理当前桌面窗口
- 打开 / 创建 / 恢复 workspace
- 管理本地 workspace 文件夹
- 管理当前选中的 reference/source assets
- 采集当前用户消息
- 提供 UI-level task hint
- 展示 agent response / activity / artifacts summary
- 展示 preview / timeline / upload state
- 预览本地 `final.mp4`

客户端不负责：

- 构造长期 memory
- 读取 artifact 全文给模型
- 判断长期偏好
- 决定最终用哪个 subagent
- 保存主业务语义状态作为唯一真相
- 直接执行复杂媒体分析 / 渲染
- 把任意 UI 操作暴露成模型可自由调用的动作

一句话：

```txt
Client 负责采集“当前事实”，不负责生成“长期工作记忆”
```

### 3.2 Backend

backend 负责：

- API 入口
- conversation record
- task record
- workspace / conversation 关系
- 持久化边界
- 调用 ai-service
- 存储业务级状态和索引
- future cloud-ready 的服务边界
- 记录任务状态和结果摘要

backend 不负责：

- prompt 组织
- graph routing
- tool orchestration
- memory selection 逻辑本身

一句话：

```txt
Backend 是业务与持久化边界，不是智能编排器
```

### 3.3 AI Service

ai-service 负责：

- build normalized context
- retrieve relevant memory
- construct AgentState
- run graph
- intent routing
- tool / subagent orchestration
- final response generation
- update memory
- write artifact metadata
- 把语义层 plan 编译成可执行工具调用

ai-service 不负责：

- 管理桌面窗口
- 直接决定本地 UI 状态
- 直接拥有 workspace 文件夹生命周期
- 替代 backend 成为业务 API 边界
- 直接替代 Local Tool Runtime 执行底层媒体处理

一句话：

```txt
AI Service 是智能编排层，不是桌面客户端，也不是主业务网关
```

### 3.4 Tool Layer

tool layer 负责：

- video analysis
- audio analysis
- timeline generation
- render execution
- artifact creation

tool layer 不负责：

- 主流程决策
- memory 检索决策
- conversation 语义判断

一句话：

```txt
Tool 做能力，AI Service 做调度
```

再严格一点：

```txt
Tool Runtime 提供白名单、结构化、可审计的本地能力
不是让模型直接操作客户端组件
```

---

## 4. Context Source of Truth

这是最关键的一章。

后面设计 `context schema` 时，必须先知道每个字段的来源是谁。

### 4.1 Workspace Context

典型字段：

- `workspaceId`
- `workspaceTitle`
- `workspaceFolderPath`
- `referenceDirectoryPath`
- `sourceDirectoryPath`

来源：

- **Client**

为什么：

- 这些字段来自当前桌面窗口和本地 workspace 目录
- 客户端最先知道，也最贴近真实本地状态

backend / ai-service 的角色：

- backend 透传 / 记录
- ai-service 归一化后进入 `context.workspace`

### 4.2 Asset Context

典型字段：

- `referenceVideo`
- `sourceVideos`
- `selectedSourceVideo`
- asset `workspaceRelativePath`
- asset metadata（name / mime / duration / resolution）

来源：

- **Client**

为什么：

- 左侧 `Assets` 是当前工作区资产的实时入口
- 当前 selected source 这种“窗口级事实”只有客户端知道得最及时

backend / ai-service 的角色：

- backend 透传 / 可选记录
- ai-service 归一化为 `context.assets`

### 4.3 Conversation Context

典型字段：

- `conversationId`
- `latestUserMessage`
- raw `messages`

来源：

- `latestUserMessage`：**Client**
- `conversationId`：**Client + Backend**
- `messages`：**Backend**

为什么：

- 当前用户刚输入的那句，客户端最先知道
- conversation 历史记录的持久化真相在 backend

### 4.4 Task Context

典型字段：

- `entry`
- `mode`
- 当前是否是 analyze / create / revise

来源：

- **Client 初始 hint**
- **AI Service 最终解释**

为什么：

- 用户点击入口时，客户端能提供“入口意图”
- 但最终任务类型不应该完全相信前端，ai-service 仍需要结合消息和 memory 做判断

一句话：

```txt
task hint 可以来自 client
task intent 的最终解释权在 ai-service
```

### 4.5 Memory Context

这里要明确：

```txt
memory 不是 client 传来的
```

来源应该是：

- workspace-local memory
- backend / DB memory
- artifact metadata
- previous run summaries

这些读取和选择都属于：

- **AI Service**

backend 的角色：

- 提供可持久化的记录与查询边界

client 的角色：

- 不生成 memory
- 不决定 memory 检索

---

## 5. Boundary Principles

更细的 `context source of truth`、request / response contract、以及跨层禁止项已经拆到：

- [`../../04-detailed-design/13-request-context-and-boundary-contracts/README.md`](../../04-detailed-design/13-request-context-and-boundary-contracts/README.md)

---

## 6. Runtime Chain

当前推荐链路：

```txt
user action
  -> client UI collects raw facts
  -> backend enriches with persisted conversation/task facts
  -> ai-service / agent runtime normalizes context
  -> ai-service / agent runtime retrieves memory
  -> ai-service / agent runtime constructs AgentState
  -> graph routes intent / tools / subagents
  -> local tool runtime produces results / artifacts
  -> ai-service / agent runtime updates memory + response payload
  -> backend records result
  -> client UI renders result
```

这里一定要看清楚：

- `context` 的主要构造起点是 client + backend
- `memory` 的构造和检索起点是 ai-service
- `response payload` 的编排终点是 ai-service

---

## 7. Final Decision

如果只保留最硬的一版，就保留这几句：

```txt
Client 提供当前事实
Backend 提供业务记录与持久化边界
AI Service / Local Agent Runtime 负责 context engineering、memory retrieval 和 runtime orchestration
Local Tool Runtime 负责真实媒体执行
task hint 可以来自 client
task intent 的最终解释权在 ai-service
memory 不来自 client
artifact 全文不应该跨边界乱传
模型不直接调用 UI
```

---

## Related Docs

- Workspace Agent Runtime：[`../01-workspace-agent-runtime-model/README.md`](../01-workspace-agent-runtime-model/README.md)
- Request / Context Contracts：[`../../04-detailed-design/13-request-context-and-boundary-contracts/README.md`](../../04-detailed-design/13-request-context-and-boundary-contracts/README.md)
- LangGraph 规范：[`../../04-detailed-design/02-langgraph-engineering-guideline/README.md`](../../04-detailed-design/02-langgraph-engineering-guideline/README.md)
- AI Service 视频架构：[`../../04-detailed-design/01-ai-service-video-architecture/README.md`](../../04-detailed-design/01-ai-service-video-architecture/README.md)
- 前端主文档：[`../../frontend/README.md`](../../frontend/README.md)
- 后端主文档：[`../../backend/README.md`](../../backend/README.md)
- AI Service 主文档：[`../../ai-service/README.md`](../../ai-service/README.md)
