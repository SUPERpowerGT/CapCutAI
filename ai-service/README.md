# AI Service

这里是 CapCutAI 当前阶段的 agent 服务。

当前主线：

```txt
internal health
-> internal agent respond
-> langgraph conversation graph
-> configured llm provider
```

## 这层负责什么

- 提供 `/internal/health`
- 提供 `/internal/agent/respond`
- 接收 backend 传来的 conversation / messages
- 用 LangGraph 编排最小 respond 流程
- 调当前配置的 provider
- 返回 reply 和 trace

当前 `ai-service` 不负责：

- 本地 workspace 文件夹创建
- conversation 持久化
- 本地素材目录生命周期

## 怎么启动

推荐在项目根目录：

```bash
make up
```

或只起它自己：

```bash
docker compose up --build -d ai-service
```

健康检查：

- `http://127.0.0.1:38000/internal/health`

## 当前默认模型入口

当前默认：

```txt
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

也就是说：

- 本地默认走 Ollama
- 后续要切别的 provider，只改 `.env`
- 上云时也沿用同一套 env key

## 当前目录

```txt
app/api/         FastAPI 路由
app/graph/       LangGraph state 与流程
app/services/    graph 入口编排
app/schemas/     Pydantic schema
app/assets/      固定风格文件入口
input/           本地输入视频
output/          分析 / 规划 / 导出产物
```

## 当前与 workspace 的关系

桌面客户端当前按：

```txt
一个窗口 = 一个 workspace
```

对 `ai-service` 来说：

- workspace 本地生命周期归客户端
- `ai-service` 消费 workspace 上下文
- 后续 `materials / plans / renders` 应按 workspace 归档

一句话：

```txt
workspace 的本地结构归客户端
workspace 下的智能分析与产物生成归 ai-service
```

## 当前标准写法

当前 `respond` 主链是后面继续扩图最该参考的模板：

- API
  - [`internal_agent_api.py`](./app/api/internal_agent_api.py)
- Service
  - [`agent_service.py`](./app/services/agent_service.py)
- Graph
  - [`conversation_graph.py`](./app/graph/conversation_graph.py)
  - [`state.py`](./app/graph/state.py)
- Schema
  - [`message.py`](./app/schemas/message.py)
  - [`respond_request.py`](./app/schemas/respond_request.py)
  - [`respond_response.py`](./app/schemas/respond_response.py)

## 后面视频链看哪里

如果你接下来做视频能力，优先看：

- [`../docs/mvp-video-pipeline/README.md`](../docs/mvp-video-pipeline/README.md)
- [`../docs/ai-service-video-architecture/README.md`](../docs/ai-service-video-architecture/README.md)
- [`../docs/langgraph-guideline/README.md`](../docs/langgraph-guideline/README.md)
- [`../docs/style-analysis-design/README.md`](../docs/style-analysis-design/README.md)
- [`../docs/style-editing-design/README.md`](../docs/style-editing-design/README.md)

## 当前可直接用的本地工具

如果你已经拿到了 Editor 导出的 `*.editing-package.json`，现在可以先在本地生成一版 HyperFrames draft composition：

```bash
cd ai-service
python -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```

默认会把产物写到 package 里的 `editingJob.compositionPath`。
