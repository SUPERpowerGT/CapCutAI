# Docs

这里是 CapCutAI 的文档中心。

当前统一口径：

```txt
Desktop-first
Local-first
Cloud-ready
```

说明：

- 桌面客户端是默认产品形态。
- 浏览器模式保留开发 / 调试价值。
- Agent Runtime 优先在本地运行。
- Tool Runtime 通过受控工具能力暴露。
- 原始视频、分析产物和最终成片优先保存在本地 workspace。

## 推荐阅读顺序

首次阅读建议顺序：

1. 仓库入口：[`../README.md`](../README.md)
2. Getting Started：[`90-getting-started/README.md`](./90-getting-started/README.md)
3. 项目概览：[`01-overview/README.md`](./01-overview/README.md)
4. Workspace Agent Use Cases：[`02-use-cases/01-workspace-agent-use-cases/README.md`](./02-use-cases/01-workspace-agent-use-cases/README.md)
5. System Architecture：[`03-architecture/03-system-architecture/README.md`](./03-architecture/03-system-architecture/README.md)
6. 当前视频链路状态：[`04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md`](./04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md)

## 文档治理

- 文档治理规则：[`00-document-governance/README.md`](./00-document-governance/README.md)

## 项目说明与用例

- 项目概览：[`01-overview/README.md`](./01-overview/README.md)
- Use Cases 总览：[`02-use-cases/README.md`](./02-use-cases/README.md)
- Workspace Agent Use Cases：[`02-use-cases/01-workspace-agent-use-cases/README.md`](./02-use-cases/01-workspace-agent-use-cases/README.md)
- Getting Started：[`90-getting-started/README.md`](./90-getting-started/README.md)

## 整体 AI 架构与安全边界

- Architecture 总览：[`03-architecture/README.md`](./03-architecture/README.md)
- Workspace Agent Runtime：[`03-architecture/01-workspace-agent-runtime-model/README.md`](./03-architecture/01-workspace-agent-runtime-model/README.md)
- Client / Backend / Agent / Tool 边界：[`03-architecture/02-client-backend-agent-tool-boundary/README.md`](./03-architecture/02-client-backend-agent-tool-boundary/README.md)
- System Architecture：[`03-architecture/03-system-architecture/README.md`](./03-architecture/03-system-architecture/README.md)
- Tool 协议：[`agent-editing-tools/README.md`](./agent-editing-tools/README.md)
- Codex video editing skill：[`agent-editing-tools/codex-video-editing-skill.md`](./agent-editing-tools/codex-video-editing-skill.md)
- Codex skill draft：[`agent-editing-tools/codex-skill-draft.md`](./agent-editing-tools/codex-skill-draft.md)

## 运行时、模型与服务

- Detailed Design 总览：[`04-detailed-design/README.md`](./04-detailed-design/README.md)
- AI Service 视频架构：[`04-detailed-design/01-ai-service-video-architecture/README.md`](./04-detailed-design/01-ai-service-video-architecture/README.md)
- LangGraph 工程规范：[`04-detailed-design/02-langgraph-engineering-guideline/README.md`](./04-detailed-design/02-langgraph-engineering-guideline/README.md)
- MVP 视频管线：[`04-detailed-design/03-mvp-video-pipeline/README.md`](./04-detailed-design/03-mvp-video-pipeline/README.md)
- Agent LLM 配置：[`04-detailed-design/09-agent-llm-setup/README.md`](./04-detailed-design/09-agent-llm-setup/README.md)
- Agent Runtime 调用接口：[`04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md`](./04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md)
- Agent Runtime 韧性与检索策略：[`04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md`](./04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md)

## 视频分析、剪辑与渲染

- 风格分析设计：[`04-detailed-design/05-style-analysis-design/README.md`](./04-detailed-design/05-style-analysis-design/README.md)
- 风格剪辑设计：[`04-detailed-design/06-style-editing-design/README.md`](./04-detailed-design/06-style-editing-design/README.md)
- 当前链路状态：[`04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md`](./04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md)
- AI4Video 闭环清单：[`04-detailed-design/06-style-editing-design/AI4VIDEO_CLOSURE_CHECKLIST.md`](./04-detailed-design/06-style-editing-design/AI4VIDEO_CLOSURE_CHECKLIST.md)
- Source Material Handoff：[`source-material-handoff/README.md`](./source-material-handoff/README.md)
- 当前剪辑入口：[`current-editing-entrypoints/README.md`](./current-editing-entrypoints/README.md)
- Editor Preview Export：[`editor-preview-export/README.md`](./editor-preview-export/README.md)
- HyperFrames Draft Builder：[`hyperframes-draft-builder/README.md`](./hyperframes-draft-builder/README.md)
- Render Pipeline Restructure：[`render-pipeline-restructure/README.md`](./render-pipeline-restructure/README.md)
- Editor MVP Change Summary：[`editor-mvp-change-summary/README.md`](./editor-mvp-change-summary/README.md)
- MVP Film Editing PRD：[`mvp-filmediting-plan/mvp-prd.md`](./mvp-filmediting-plan/mvp-prd.md)

## 客户端、IM 与存储

- Desktop Client Design：[`04-detailed-design/07-desktop-client-design/README.md`](./04-detailed-design/07-desktop-client-design/README.md)
- Agent Panel IM Design：[`04-detailed-design/08-agent-panel-im-design/README.md`](./04-detailed-design/08-agent-panel-im-design/README.md)
- Database / Storage Design：[`04-detailed-design/04-database-storage-design/README.md`](./04-detailed-design/04-database-storage-design/README.md)
- Workspace Storage / Target Schema：[`04-detailed-design/12-workspace-storage-and-target-schema/README.md`](./04-detailed-design/12-workspace-storage-and-target-schema/README.md)
- Frontend README：[`../frontend/README.md`](../frontend/README.md)
- Backend README：[`../backend/README.md`](../backend/README.md)
- AI Service README：[`../ai-service/README.md`](../ai-service/README.md)
- Shared README：[`../shared/README.md`](../shared/README.md)
- Scripts README：[`../scripts/README.md`](../scripts/README.md)

## 交付物溯源

- 项目说明：[`../README.md`](../README.md)
- 运行说明：[`90-getting-started/README.md`](./90-getting-started/README.md)
- 整体 AI 架构：[`03-architecture/03-system-architecture/README.md`](./03-architecture/03-system-architecture/README.md)
- 工具协议与安全边界：[`03-architecture/02-client-backend-agent-tool-boundary/README.md`](./03-architecture/02-client-backend-agent-tool-boundary/README.md)
- 当前视频闭环：[`04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md`](./04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md)
- 输出视频目录：`~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/renders/`
