# Agent Runtime Invocation And Interfaces

这份文档专门回答：

- Agent Runtime 一次 invocation 是怎么被驱动起来的
- invocation 的输入输出应该长什么样
- runtime 侧建议先定哪些接口

它不重新定义：

- workspace 是什么
- context / memory / AgentState 的概念
- Client / Backend / Agent Runtime / Tool Runtime 的总边界

这些上层概念请先看：

- [`../../03-architecture/01-workspace-agent-runtime-model/README.md`](../../03-architecture/01-workspace-agent-runtime-model/README.md)
- [`../../03-architecture/02-client-backend-agent-tool-boundary/README.md`](../../03-architecture/02-client-backend-agent-tool-boundary/README.md)

## 1. Suggested Interfaces

```ts
interface MemoryRetriever {
  retrieve(input: {
    workspaceId: string
    conversationId: string
    intentType?: string
    assetIds?: string[]
    query: string
  }): Promise<SelectedMemory>
}

interface MemoryReader {
  readCandidates(input: {
    workspaceId: string
    conversationId?: string
  }): Promise<CandidateMemorySet>
}

interface MemorySelector {
  select(input: {
    intentType?: string
    assetIds?: string[]
    query: string
    candidates: CandidateMemorySet
  }): Promise<SelectedMemory>
}

interface MemoryCompressor {
  compress(input: {
    history?: string
    artifactSummaries?: string[]
    revisionTrail?: string[]
  }): Promise<CompressedMemoryPayload>
}

interface MemoryWriter {
  write(input: {
    workspaceId: string
    conversationId?: string
    runId: string
    memory: PersistedMemoryPatch
  }): Promise<void>
}
```

## 2. Agent Invocation Drive Chain

当前推荐的驱动链：

```txt
user action
  -> frontend collects raw context
  -> backend receives request
  -> ai-service builds normalized context
  -> memory retriever selects relevant memory
  -> orchestrator builds AgentState
  -> graph decides intent / tools / subagents
  -> tools execute / artifacts update
  -> memory update
  -> final response back to UI
```

### Start

起点可以是：

- 用户发送消息
- 用户点击某个明确动作
- 某个任务结束后自动推进下一阶段

### Middle

真正的“智能驱动”发生在：

- context normalization
- memory retrieval
- agent state construction
- graph routing

不是发生在前端。

### End

一次 invocation 的输出不只是一句 reply，还应该包括：

- assistant text
- activity items
- task status update
- artifact metadata update
- memory update

## 3. Related Docs

- Runtime Model：[`../../03-architecture/01-workspace-agent-runtime-model/README.md`](../../03-architecture/01-workspace-agent-runtime-model/README.md)
- LangGraph Guideline：[`../../02-langgraph-engineering-guideline/README.md`](../../02-langgraph-engineering-guideline/README.md)
- AI Service Video Architecture：[`../../01-ai-service-video-architecture/README.md`](../../01-ai-service-video-architecture/README.md)
