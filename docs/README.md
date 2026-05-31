# Docs

这里是 CapCutAI 的文档中心。

当前文档口径已经统一成：

```txt
Desktop-first
Local-first
Cloud-ready
```

也就是说：

- 桌面客户端是默认产品形态
- 浏览器模式只保留开发 / 调试价值
- 一套前端代码，不维护两套 UI
- Agent Runtime 优先在本地运行
- Tool Runtime 优先以本地受控能力暴露
- 原始视频与产物优先保存在本地 workspace

## 文档层次

当前推荐按 4 层理解所有设计文档：

```txt
1. Overview
2. Use Cases
3. Architecture
4. Detailed Design
```

如果要看这套分层为什么这样定，以及哪些文档该归哪一层，先看：

- [`00-document-governance/README.md`](./00-document-governance/README.md)

## 1. Overview

入口页：

1. [`01-overview/README.md`](./01-overview/README.md)

推荐先看：

1. [`../README.md`](../README.md)
2. [`01-overview/README.md`](./01-overview/README.md)

补充：

- 启动与环境：[`90-getting-started/README.md`](./90-getting-started/README.md)

## 2. Use Cases

这一层只回答：

- 用户到底拿系统做什么
- 哪几条 use case 最重要
- 哪些能力是被 use case 逼出来的

入口页：

1. [`02-use-cases/README.md`](./02-use-cases/README.md)

主文档：

1. [`02-use-cases/01-workspace-agent-use-cases/README.md`](./02-use-cases/01-workspace-agent-use-cases/README.md)

## 3. Architecture

这一层只回答：

- 系统怎么分层
- runtime 核心概念是什么
- 各层怎么交互
- 数据和控制流怎么走

入口页：

1. [`03-architecture/README.md`](./03-architecture/README.md)

推荐按这个顺序看：

1. [`03-architecture/01-workspace-agent-runtime-model/README.md`](./03-architecture/01-workspace-agent-runtime-model/README.md)
2. [`03-architecture/02-client-backend-agent-tool-boundary/README.md`](./03-architecture/02-client-backend-agent-tool-boundary/README.md)
3. [`03-architecture/03-system-architecture/README.md`](./03-architecture/03-system-architecture/README.md)

它们分别负责：

- `workspace-agent-runtime-model`
  - runtime 核心概念：workspace、context、memory、AgentState
- `client-backend-agent-tool-boundary`
  - Client / Backend / Agent Runtime / Tool Runtime 的边界
- `system-architecture`
  - 总体拓扑、存储归属、目标表类别、高层时序图

## 4. Detailed Design

入口页：

1. [`04-detailed-design/README.md`](./04-detailed-design/README.md)

这一层才进入具体落地。

### 运行时与执行链

1. [`04-detailed-design/01-ai-service-video-architecture/README.md`](./04-detailed-design/01-ai-service-video-architecture/README.md)
2. [`04-detailed-design/02-langgraph-engineering-guideline/README.md`](./04-detailed-design/02-langgraph-engineering-guideline/README.md)
3. [`04-detailed-design/03-mvp-video-pipeline/README.md`](./04-detailed-design/03-mvp-video-pipeline/README.md)

### 存储与数据库

1. [`04-detailed-design/04-database-storage-design/README.md`](./04-detailed-design/04-database-storage-design/README.md)
2. [`../shared/README.md`](../shared/README.md)

### 视频专项设计

1. [`04-detailed-design/05-style-analysis-design/README.md`](./04-detailed-design/05-style-analysis-design/README.md)
2. [`04-detailed-design/06-style-editing-design/README.md`](./04-detailed-design/06-style-editing-design/README.md)

### 客户端专项设计

1. [`04-detailed-design/07-desktop-client-design/README.md`](./04-detailed-design/07-desktop-client-design/README.md)
2. [`04-detailed-design/08-agent-panel-im-design/README.md`](./04-detailed-design/08-agent-panel-im-design/README.md)
3. [`../frontend/README.md`](../frontend/README.md)

### 模型与 provider 配置

1. [`04-detailed-design/09-agent-llm-setup/README.md`](./04-detailed-design/09-agent-llm-setup/README.md)
2. [`../ai-service/README.md`](../ai-service/README.md)

## 推荐阅读顺序

如果你是第一次进入设计讨论，永远先按这条顺序：

1. [`../README.md`](../README.md)
2. [`02-use-cases/01-workspace-agent-use-cases/README.md`](./02-use-cases/01-workspace-agent-use-cases/README.md)
3. [`03-architecture/01-workspace-agent-runtime-model/README.md`](./03-architecture/01-workspace-agent-runtime-model/README.md)
4. [`03-architecture/02-client-backend-agent-tool-boundary/README.md`](./03-architecture/02-client-backend-agent-tool-boundary/README.md)
5. [`03-architecture/03-system-architecture/README.md`](./03-architecture/03-system-architecture/README.md)
6. 再进入任一细节设计文档

## 一句话原则

```txt
Use Cases 先于 Architecture
Architecture 先于 Detailed Design
不要跳过上层直接钻细节
```
