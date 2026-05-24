# Docs

这里是 CapCutAI 的文档中心。

当前文档已经收敛成一条主线：

```txt
IM + agent 最小闭环
```

## 当前最重要的文档

- [`getting-started/README.md`](./getting-started/README.md)
  第一次拉项目后的启动说明。直接讲清楚需要什么环境、怎么起 Ollama、怎么 `make up`、怎么跑前端。

- [`../README.md`](../README.md)
  仓库总入口。第一次拉项目先看这个，先把 `Ollama + Docker` 跑起来。

- [`../frontend/README.md`](../frontend/README.md)
  前端当前唯一主文档。讲清楚工作台分层、IM 主线、以及后续 `assets / hyperframes` 的协作边界。

- [`../backend/README.md`](../backend/README.md)
  backend 当前唯一主文档。讲清楚目录规则、DTO 分层、启动、配置和如何新增功能。

- [`../ai-service/README.md`](../ai-service/README.md)
  ai-service 当前唯一主文档。讲清楚 LangGraph、provider 路由、Ollama 默认配置和验证方式。

- [`database-storage/README.md`](./database-storage/README.md)
  当前数据库存储说明。讲清楚消息最终存在哪里，以及本地如何进入 PostgreSQL 查看。

- [`agent-llm/README.md`](./agent-llm/README.md)
  当前 agent 大模型接入说明。讲清楚默认 Ollama 怎么配置，以及如何丝滑切到 Gemini / OpenRouter / Groq。

## 当前建议阅读顺序

如果你现在刚拉项目：

1. 先看根目录 [`README.md`](../README.md)
2. 再看 [`getting-started/README.md`](./getting-started/README.md)
3. 再看 [`frontend/README.md`](../frontend/README.md)、[`backend/README.md`](../backend/README.md)、[`ai-service/README.md`](../ai-service/README.md)
4. 如果要查 LLM 配置，再看 [`agent-llm/README.md`](./agent-llm/README.md)
5. 如果要查消息落库，再看 [`database-storage/README.md`](./database-storage/README.md)
