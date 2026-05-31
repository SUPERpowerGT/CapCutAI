# Agent LLM Setup

这里记录 CapCutAI 当前 `ai-service` 的大模型接入方式。

当前状态：

```txt
LangGraph graph 已接上
通过统一 provider 配置选择 LLM
没有可用 provider 时返回明确错误信息
```

核心原则：

- 默认 `LLM_PROVIDER=ollama`
- 只有显式切到其他 provider，才会改用远程 API
- 这样别人拉项目下来不会因为本机环境变量残留而得到“看起来随机”的行为

## 当前实现

当前 `ai-service` 的 respond 流程是：

```txt
FastAPI /internal/agent/respond
  -> agent_service.py
  -> LangGraph conversation_graph.py
  -> configured provider or explicit unavailable reply
```

关键文件：

- [`../../ai-service/app/api/internal_agent_api.py`](../../ai-service/app/api/internal_agent_api.py)
- [`../../ai-service/app/services/agent_service.py`](../../ai-service/app/services/agent_service.py)
- [`../../ai-service/app/graph/conversation_graph.py`](../../ai-service/app/graph/conversation_graph.py)
- [`../../ai-service/app/graph/state.py`](../../ai-service/app/graph/state.py)

## 当前配置方式

当前只需要改一组配置就能切 provider：

```txt
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
```

支持：

- `ollama`
- `gemini`
- `openrouter`
- `groq`

推荐做法：

- 本地开发默认 `ollama`
- 需要远程模型时显式切 provider
- 上云沿用相同 env key，由云平台注入 secret

## 本地如何配置

先复制环境变量：

```bash
cp .env.example .env
```

然后在根目录 `.env` 里确认：

```txt
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
```

本地需要先安装并启动 Ollama，例如：

```bash
ollama pull qwen2.5:7b
ollama serve
```

或者切 OpenRouter：

```txt
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=你的_key
OPENROUTER_MODEL=openrouter/auto
```

或者切 Groq：

```txt
LLM_PROVIDER=groq
GROQ_API_KEY=你的_key
GROQ_MODEL=llama-3.1-8b-instant
```

## Docker 如何透传

当前 [`docker-compose.yml`](../../docker-compose.yml) 会把 `LLM_PROVIDER` 和各 provider 所需 key/model 一起透传给 `ai-service`。

## 健康检查如何看配置是否生效

现在 `GET /internal/health` 会直接返回：

- `provider`
- `model`
- `mode`
- `configured`

所以别人拿到项目后，不用猜当前到底是不是 live 模式。

## 如何重建服务

改完配置后重建：

```bash
docker compose up --build -d ai-service backend
```

或者直接：

```bash
make up
```

然后跑一次：

```bash
make smoke
```

## 如何判断现在走的是哪个 provider

优先看 `GET /internal/health`，其次再看消息返回里的 trace / artifacts。

如果走了 Gemini，trace 里会出现：

```txt
graph.generate_reply.gemini
```

如果走了 OpenRouter：

```txt
graph.generate_reply.openrouter
```

如果走了 Groq：

```txt
graph.generate_reply.groq
```

如果 provider 没配置好，会出现类似：

```txt
graph.provider_not_configured.ollama
```

或者：

```txt
graph.provider_error.openrouter.*
```

## 当前取舍

- 现在已经是真正的 LangGraph + provider router 接法
- 但 graph 还是最小 skeleton，不是复杂多节点 agent
- 这样做的目的是先让 `IM + agent` 全链路跑真模型
- 后续再继续拆 `intent / context / tools / response` 节点

## 参考

- [`../README.md`](../README.md)
- [`../../ai-service/README.md`](../../ai-service/README.md)
