# Document Structure

这份文档不讨论产品功能，也不讨论实现细节。

它只回答一个问题：

```txt
CapCutAI 的设计文档体系应该怎么分层，哪些文档该放在哪一层，各自只回答什么问题？
```

先给最终结论：

```txt
第一层：概述
第二层：Use Cases
第三层：Architecture
第四层：Detailed Design
```

这个顺序不能反。

因为：

- 没有概述，大家不知道系统整体在说什么
- 没有 use case，架构会飘
- 没有架构，细节会散
- 细节文档应该服务上三层，不应该反过来主导它们

---

## 1. Layer Model

### Layer 1: Overview

这一层回答：

- 这是什么产品
- 当前主形态是什么
- 核心心智是什么
- 整体边界大概是什么
- 去哪里继续看

这一层不回答：

- 每条 use case 的输入输出细节
- 分层契约细节
- 数据库存储细节
- graph / schema / table 设计

### Layer 2: Use Cases

这一层回答：

- 用户到底会拿系统做什么
- 哪几条 use case 最重要
- 每条 use case 的输入、输出、成功条件是什么
- 哪些能力是被 use case 逼出来的

这一层不回答：

- Client / Backend / Agent Runtime 怎么拆
- 表结构和存储位置怎么定
- graph / tool / schema 怎么写

### Layer 3: Architecture

这一层回答：

- 为了支撑 use case，系统怎么分层
- 每个运行时模块负责什么
- 数据和控制流如何穿过系统
- 本地文件、数据库、Agent Runtime、Tool Runtime 如何协作

这一层不回答：

- 某个 graph 的节点细节
- 某个 JSON schema 的字段全集
- 某张表的完整 SQL

### Layer 4: Detailed Design

这一层回答：

- 某个子系统具体怎么实现
- 某条业务链具体怎么跑
- 某类 graph / schema / artifact / table 怎么设计
- 某类工具或执行器怎么组织

这一层不应该再重新定义：

- 产品主语
- use case 主线
- 顶层架构边界

---

## 2. Recommended Doc Tree

推荐固定成这棵树：

```txt
1. Overview
   - README.md
   - docs/README.md

2. Use Cases
   - docs/02-use-cases/01-workspace-agent-use-cases/README.md

3. Architecture
   - docs/03-architecture/01-workspace-agent-runtime-model/README.md
   - docs/03-architecture/02-client-backend-agent-tool-boundary/README.md
   - docs/03-architecture/03-system-architecture/README.md

4. Detailed Design
   - docs/04-detailed-design/04-database-storage-design/README.md
   - docs/04-detailed-design/01-ai-service-video-architecture/README.md
   - docs/04-detailed-design/02-langgraph-engineering-guideline/README.md
   - docs/04-detailed-design/05-style-analysis-design/README.md
   - docs/04-detailed-design/06-style-editing-design/README.md
   - docs/04-detailed-design/07-desktop-client-design/README.md
   - docs/04-detailed-design/08-agent-panel-im-design/README.md
   - docs/04-detailed-design/09-agent-llm-setup/README.md
   - docs/04-detailed-design/03-mvp-video-pipeline/README.md
   - docs/04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md
   - docs/04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md
   - docs/04-detailed-design/12-workspace-storage-and-target-schema/README.md
   - docs/04-detailed-design/13-request-context-and-boundary-contracts/README.md
```

---

## 3. Current Docs Mapping

下面这张表只做一件事：

```txt
把现有文档映射到正确层级
```

| Doc | Layer | Keep | Reason |
| --- | --- | --- | --- |
| `README.md` | Overview | yes | 仓库总入口 |
| `docs/README.md` | Overview | yes | 文档中心入口 |
| `docs/02-use-cases/01-workspace-agent-use-cases/README.md` | Use Cases | yes | use case 主文档 |
| `docs/03-architecture/01-workspace-agent-runtime-model/README.md` | Architecture | yes | runtime 核心概念 |
| `docs/03-architecture/02-client-backend-agent-tool-boundary/README.md` | Architecture | yes | 分层边界 |
| `docs/03-architecture/03-system-architecture/README.md` | Architecture | yes | 总体拓扑、存储、时序 |
| `docs/04-detailed-design/04-database-storage-design/README.md` | Detailed Design | yes | 数据库存储细节 |
| `docs/04-detailed-design/01-ai-service-video-architecture/README.md` | Detailed Design | yes | ai-service 落地设计 |
| `docs/04-detailed-design/02-langgraph-engineering-guideline/README.md` | Detailed Design | yes | graph 工程约定 |
| `docs/04-detailed-design/05-style-analysis-design/README.md` | Detailed Design | yes | reference analysis 细节链 |
| `docs/04-detailed-design/06-style-editing-design/README.md` | Detailed Design | yes | style editing 细节链 |
| `docs/04-detailed-design/03-mvp-video-pipeline/README.md` | Detailed Design | keep for now | 当前主链摘要，但和 use case / architecture 有重叠 |
| `docs/04-detailed-design/07-desktop-client-design/README.md` | Detailed Design | yes | desktop 客户端专项设计 |
| `docs/04-detailed-design/08-agent-panel-im-design/README.md` | Detailed Design | yes | agent panel 专项设计 |
| `docs/04-detailed-design/09-agent-llm-setup/README.md` | Detailed Design | yes | provider / 配置细节 |
| `docs/04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md` | Detailed Design | yes | runtime invocation / interface 细节 |
| `docs/04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md` | Detailed Design | yes | failure / retrieval / priority 细节 |
| `docs/04-detailed-design/12-workspace-storage-and-target-schema/README.md` | Detailed Design | yes | 目标存储布局和目标表设计 |
| `docs/04-detailed-design/13-request-context-and-boundary-contracts/README.md` | Detailed Design | yes | request / context contract 细节 |
| `docs/90-getting-started/README.md` | not design | yes | 启动文档，不算设计层 |

---

## 4. Responsibility of Each Core Design Doc

这一章最重要。

因为现在乱，核心不是“文档太多”，而是“每份文档都在讲太多层的问题”。

### 4.1 `workspace-agent-use-cases`

只负责回答：

- 核心 use case 是什么
- 每条 use case 的目标、输入、输出、成功条件
- 为什么这些 use case 会逼出 context / memory / tool / artifact

不应该展开：

- 详细模块拓扑
- 详细数据库表
- 完整时序图实现细节

### 4.2 `workspace-agent-model`

只负责回答：

- workspace 是什么
- context / memory / AgentState 是什么
- runtime 的核心概念和数据模型是什么

不应该展开：

- Client / Backend / Tool Runtime 边界细节
- 所有数据库表
- 每条 use case 的完整时序图

### 4.3 `client-backend-ai-boundary`

只负责回答：

- Client UI / Backend / Agent Runtime / Tool Runtime 分别做什么
- 输入输出 contract 的边界归属
- 哪些信息不能跨层乱传

不应该展开：

- memory schema 全细节
- task / artifact 表设计
- 每条业务链的完整流程设计

### 4.4 `system-architecture`

只负责回答：

- 系统总体拓扑
- 运行时总链路
- 文件系统和数据库的职责边界
- 关键 use case 的高层时序图

它可以概括提到：

- 目标表
- 存储位置
- 模块关系

但不应该替代：

- `database-storage`
- `ai-service-video-architecture`
- `style-*`

### 4.5 Detailed Design Docs

每份只负责自己那一块：

- `database-storage`
  - 表、索引、存储介质
- `ai-service-video-architecture`
  - ai-service 内部 graph / service / schema 演进
- `langgraph-guideline`
  - graph 约定、tool / skill / trace 约定
- `style-analysis-design`
  - 参考视频分析链
- `style-editing-design`
  - 套风格编辑链
- `desktop-client-plan`
  - 桌面端专项设计
- `im-optimization`
  - 右侧 Agent Panel 专项设计
- `agent-runtime-invocation-and-interfaces`
  - invocation 和接口细节
- `agent-runtime-resilience-and-retrieval-policy`
  - 失败策略、检索策略、实现优先级
- `workspace-storage-and-target-schema`
  - workspace 文件布局、目标表、use case 存储映射
- `request-context-and-boundary-contracts`
  - context 来源和 request / response contract 细节

---

## 5. Current Overlaps

现在最主要的重叠有这些：

### Overlap 1

`workspace-agent-model` 和 `system-architecture`

重叠点：

- control plane / data plane
- tasks / memory / artifact 的存储位置

处理原则：

- 概念定义留在 `workspace-agent-model`
- 总拓扑和全局落点留在 `system-architecture`

### Overlap 2

`client-backend-ai-boundary` 和 `system-architecture`

重叠点：

- Client / Backend / Agent Runtime / Tool Runtime 关系

处理原则：

- 边界责任留在 `client-backend-ai-boundary`
- 系统全链路视角留在 `system-architecture`

### Overlap 3

`workspace-agent-use-cases` 和 `mvp-video-pipeline`

重叠点：

- 分析 / 生成 / 修订三条链

处理原则：

- 用户任务视角留在 `workspace-agent-use-cases`
- 当前 MVP 执行主线留在 `mvp-video-pipeline`

如果后面继续重构文档，`mvp-video-pipeline` 可以收缩成：

- 当前版本范围
- 当前不做什么
- 当前闭环顺序

### Overlap 4

`system-architecture` 和 `database-storage`

重叠点：

- 表设计
- 存储位置

处理原则：

- 总体归属和表类别留在 `system-architecture`
- 字段和落库细节留在 `database-storage`

---

## 6. Recommended Reading Order

以后讨论设计，推荐永远按这条顺序：

1. Overview
2. Use Cases
3. Architecture
4. Detailed Design

具体到当前仓库：

1. [`../README.md`](../../README.md)
2. [`../README.md`](../README.md)
3. [`../02-use-cases/01-workspace-agent-use-cases/README.md`](../02-use-cases/01-workspace-agent-use-cases/README.md)
4. [`../03-architecture/01-workspace-agent-runtime-model/README.md`](../03-architecture/01-workspace-agent-runtime-model/README.md)
5. [`../03-architecture/02-client-backend-agent-tool-boundary/README.md`](../03-architecture/02-client-backend-agent-tool-boundary/README.md)
6. [`../03-architecture/03-system-architecture/README.md`](../03-architecture/03-system-architecture/README.md)
7. 再进入各个细节文档

---

## 7. What To Do Next

文档层次定完之后，下一步不是继续铺新文档，而是做这 3 件事：

1. 收紧每份核心文档的职责边界
2. 把重复内容从 Architecture 层移回 Detailed Design 层
3. 让 `docs/README.md` 完全按这 4 层来组织

---

## 8. Final Decision

如果只保留最硬的一版，就保留这几句：

```txt
CapCutAI 的设计文档必须按四层组织：概述、Use Cases、Architecture、Detailed Design
Use Cases 先于 Architecture
Architecture 先于 Detailed Design
每份文档只回答自己这一层的问题，不要跨层乱写
文档中心必须反映这套层次，而不是按零散主题堆文档
```
