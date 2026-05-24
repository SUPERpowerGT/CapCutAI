# AI Service

这里是 CapCutAI 当前阶段的 agent 服务。

这份 `README.md` 是 `ai-service` 当前唯一主文档。后续所有人都应该按这份文档继续开发，不要另外维护一份独立的 agent 架构说明。

## 先看这里

如果你第一次进入 `ai-service/`，按这个顺序看：

1. 看“当前主线”
2. 看“当前目录规则”
3. 看“当前 agent 标准写法”
4. 看“LLM Provider 配置”
5. 看“验证要求”

## 当前主线

当前 `ai-service` 只保留已经接上真实链路的部分：

```txt
internal health
  -> internal agent respond
  -> langgraph conversation graph
  -> configured llm provider
  -> explicit unavailable reply on provider failure
```

当前真正跑在链路里的能力只有：

- 提供 `/internal/health`
- 提供 `/internal/agent/respond`
- 接收 backend 传来的 conversation / messages
- 通过 LangGraph 执行最小 respond 流程
- 优先调用当前配置的 provider
- provider 不可用时返回明确错误信息
- 返回 trace

## 启动方式

推荐在项目根目录启动：

```bash
docker compose up --build -d ai-service
```

或者如果你已经启动了整套依赖：

```bash
make up
```

默认地址：

- API: `http://127.0.0.1:38000`
- Health: `GET /internal/health`
- Respond: `POST /internal/agent/respond`

## 配置原则

当前配置已经按“本地不惊喜、上云可复用”来设计：

- 默认 `LLM_PROVIDER=ollama`
- 复制 `.env.example` 后，项目默认按本地 Ollama 运行
- 没有启动 Ollama 时，会返回明确的 unavailable 信息
- 想切真实 provider，只改根目录 `.env`
- 上云时也沿用同一套 env key，直接挂到容器环境即可

## 当前目录规则

当前 `ai-service` 只按这几层继续开发：

- `app/api`
- `app/graph`
- `app/services`
- `app/schemas`
- `app/utils`

### `app/api`

负责：

- FastAPI 路由入口
- 内部服务接口暴露

当前只保留：

- `health_api.py`
- `internal_agent_api.py`

### `app/graph`

负责：

- LangGraph state
- LangGraph 节点与流程定义

当前只保留：

- `state.py`
- `conversation_graph.py`

### `app/services`

负责：

- graph 调用入口
- 上层编排

当前只保留：

- `agent_service.py`

### `app/schemas`

负责：

- Pydantic schema
- backend 与 ai-service 当前协议的 Python 表达

当前只保留：

- `message.py`
- `respond_request.py`
- `respond_response.py`

### `app/utils`

当前先空着，不要为了“看起来完整”往里面塞工具函数。

## 当前 ai-service 目录结构

```txt
ai-service/
├── app/
│   ├── api/
│   │   ├── health_api.py
│   │   └── internal_agent_api.py
│   ├── graph/
│   │   ├── conversation_graph.py
│   │   └── state.py
│   ├── schemas/
│   │   ├── message.py
│   │   ├── respond_request.py
│   │   └── respond_response.py
│   ├── services/
│   │   └── agent_service.py
│   └── main.py
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

理解方式：

- `api` 看 HTTP 入口
- `graph` 看 LangGraph 流程
- `services` 看服务入口
- `schemas` 看协议模型

## 当前 agent 标准写法

当前 `respond` 主链是 `ai-service` 的标准模板，后面新增 graph 能力优先照着它扩。

当前结构：

- FastAPI 入口
  - [`internal_agent_api.py`](./app/api/internal_agent_api.py)

- service 入口
  - [`agent_service.py`](./app/services/agent_service.py)

- graph 定义
  - [`conversation_graph.py`](./app/graph/conversation_graph.py)
  - [`state.py`](./app/graph/state.py)

- schema
  - [`respond_request.py`](./app/schemas/respond_request.py)
  - [`respond_response.py`](./app/schemas/respond_response.py)
  - [`message.py`](./app/schemas/message.py)

## LLM Provider 配置

当前 `ai-service` 已经改成统一 provider 配置方式。

只需要改根目录 `.env` 里的这组变量：

```txt
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
```

支持的 provider：

- `ollama`
- `gemini`
- `openrouter`
- `groq`

默认策略：

```txt
按 LLM_PROVIDER 选择 provider -> 调用失败时返回明确错误信息
```

推荐理解：

- `LLM_PROVIDER` 是唯一入口
- provider 专属 key/model 只是对应实现的配置值
- 团队不要依赖“本机 shell 里刚好有某个 key”这种隐式行为

### Gemini

```txt
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
```

### OpenRouter

```txt
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openrouter/auto
```

### Groq

```txt
LLM_PROVIDER=groq
GROQ_API_KEY=...
GROQ_MODEL=llama-3.1-8b-instant
```

### Ollama

```txt
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
```

## 本地与云上如何用

### 本地

1. 复制 `.env.example` 为 `.env`
2. 安装并启动 Ollama
3. 拉取本地模型，例如：

```bash
ollama pull qwen2.5:7b
ollama serve
```

4. 默认先用 `LLM_PROVIDER=ollama`
5. 需要其他 provider 时，再显式改成 `gemini / openrouter / groq`

### 云上

推荐原则：

- 不上传 `.env`
- 由云平台 Secret / Environment Variables 注入
- 只改 `LLM_PROVIDER` 和对应 provider 的 key/model
- 应用代码不需要改

也就是说，本地和云上使用的是同一套配置名，只是来源不同：

- 本地：`.env`
- 云上：Secret Manager / 容器环境变量 / Helm values / CI 注入

更完整的接入说明见：

- [`../docs/agent-llm/README.md`](../docs/agent-llm/README.md)

## 当前明确不写的东西

在真实链路没接上之前，不要把这些内容重新加回来：

- 多工具编排
- 复杂 memory
- 多 agent 协作
- project / asset / editing artifacts
- 独立任务队列

原因很简单：

- backend 现在没接
- 前端现在没接
- 数据库存储也没接
- 先写只会制造假复杂度

## 验证要求

任何 `ai-service` 结构调整后，至少要过：

```bash
docker compose up --build -d ai-service
make smoke
```

## 参考文档

- [`../README.md`](../README.md)
- [`../backend/README.md`](../backend/README.md)
- [`../docs/agent-llm/README.md`](../docs/agent-llm/README.md)
