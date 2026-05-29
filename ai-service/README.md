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
6. 如果要做视频能力，再看：
   - [`../docs/mvp-video-pipeline/README.md`](../docs/mvp-video-pipeline/README.md)
   - [`../docs/ai-service-video-architecture/README.md`](../docs/ai-service-video-architecture/README.md)
   - [`../docs/langgraph-guideline/README.md`](../docs/langgraph-guideline/README.md)

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
- `input`
- `output`

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

### `app/assets`

后续放固定风格文件、模板素材和结构化 style assets。

当前先只保留目录边界，不往里面塞业务逻辑。

### `input`

放本地输入视频素材。

当前建议继续按这两个入口分：

- `input/uservideo/`
- `input/stylizationvideo/`

含义：

- `uservideo`：用户自己的待处理视频
- `stylizationvideo`：参考风格视频 / 爆款视频

### `output`

放 agent 和后续编辑执行层产出的中间结果与最终结果。

当前建议先按这三类分：

- `output/materials/`
- `output/plans/`
- `output/renders/`

含义：

- `materials`：`materials.json` 这类分析产物
- `plans`：`timeline_plan.json`、`editing_job.json` 这类规划产物
- `renders`：`final.mp4` 这类最终导出视频

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
│   ├── assets/
│   │   └── styles/
│   └── main.py
├── input/
│   ├── stylizationvideo/
│   └── uservideo/
├── output/
│   ├── materials/
│   ├── plans/
│   └── renders/
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
- `assets/styles` 看后续固定风格文件入口
- `input` 看本地视频输入
- `output` 看分析、规划和导出产物

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

## 视频输入输出约定

当前如果开始做视频能力，先按这个约定：

- 参考风格视频放：
  - `ai-service/input/stylizationvideo/`
- 用户视频放：
  - `ai-service/input/uservideo/`
- 分析产物放：
  - `ai-service/output/materials/`
- 规划产物放：
  - `ai-service/output/plans/`
- 最终视频放：
  - `ai-service/output/renders/`

这样后面无论是：

- Material Analyzer
- Style Retriever
- Director Planner
- Editing Skills

大家都会知道输入输出应该落在哪。

## 视频能力如何长出来

当前 `ai-service` 已经有一条最小 IM 对话链，但后面视频能力不会继续硬塞进现在的 `conversation_graph`。

后续建议按三条 graph 长出来：

- `conversation_graph`
- `style_analysis_graph`
- `style_editing_graph`
- `revision_graph`

详细设计见：

- [`../docs/mvp-video-pipeline/README.md`](../docs/mvp-video-pipeline/README.md)
- [`../docs/ai-service-video-architecture/README.md`](../docs/ai-service-video-architecture/README.md)

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
