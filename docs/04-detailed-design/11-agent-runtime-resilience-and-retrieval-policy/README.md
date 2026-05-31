# Agent Runtime Resilience And Retrieval Policy

这份文档专门回答：

- Agent Runtime 遇到失败时怎么降级
- P0 阶段 retrieval 应该优先遵循什么策略
- 实现优先级怎么排

它不重新定义：

- context / memory / AgentState 的基础概念
- 系统总体架构边界

## 1. Failure And Fallback Policy

文档不能只有 happy path，至少先定这些失败策略。

### Context 缺失关键字段

例如：

- 没有 reference video
- 没有 source video
- 缺 workspaceId

处理：

- 不进入 tool execution
- 返回缺失信息提示
- `status = waiting_for_input`

### Memory Retrieval 失败

例如：

- workspace memory 读取失败
- artifact metadata store 不可用

处理：

- 不阻塞主流程
- 降级为 `context-only run`
- 记录 warning trace / log

### Artifact Path 不存在

例如：

- `style_profile.json` 被删掉
- `timeline_plan.json` 路径失效

处理：

- 标记 `artifact_memory` 为 stale
- 不信任旧 artifact
- 要求重新生成或重新选择输入

### Tool 执行失败

例如：

- 视频分析失败
- timeline 生成失败
- render 超时

处理：

- 写入 task error
- 保留 partial artifacts
- 返回可恢复建议

### Memory Write 失败

例如：

- 本地 memory 文件写失败
- DB 写失败

处理：

- 不影响主响应
- 记录 warning / retry task
- 后续异步重试

### 并发写同一 workspace

例如：

- 两个窗口并发修改同一 workspace memory

处理：

- append-only 或 versioned writes
- 不做 silent overwrite
- 必要时标记冲突并要求 refresh

## 2. Deterministic Retrieval First

这里要提前拍板：

```txt
memory retrieval 不一定等于向量检索
```

CapCutAI 的 P0 更适合结构化检索。

优先使用：

- `workspaceId`
- `artifactType`
- `latestVersion`
- `taskType`
- `selectedAssetIds`

例如：

### `revise_video`

优先查：

- latest `timeline_plan`
- latest `render`
- latest `revision_summary`

### `create_styled_video`

优先查：

- latest `style_profile`
- selected source assets
- user preference if exists

一句话：

```txt
P0 阶段优先 deterministic retrieval
不是 semantic vector retrieval
```

## 3. Implementation Priority

### P0

先做稳：

- normalized `context`
- `AgentState` schema
- `workspace_memory`
- `artifact_memory` metadata
- basic `memory read path`

### P1

再补：

- `conversation_memory` summary
- `task_context`
- `memory builder / writer`
- `failure / fallback policy`

### P2

最后再补：

- `preference_memory`
- advanced retrieval memory
- advanced compression / reranking

## 4. Related Docs

- Runtime Model：[`../../03-architecture/01-workspace-agent-runtime-model/README.md`](../../03-architecture/01-workspace-agent-runtime-model/README.md)
- Database Storage：[`../../04-database-storage-design/README.md`](../../04-database-storage-design/README.md)
- AI Service Video Architecture：[`../../01-ai-service-video-architecture/README.md`](../../01-ai-service-video-architecture/README.md)
