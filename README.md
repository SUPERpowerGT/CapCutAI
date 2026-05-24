# CapCutAI

CapCutAI 当前已经收敛成：

```txt
先把 IM + agent 的最小全链路脚手架跑通
```

当前最重要的链路：

```txt
Frontend / IM
    ↓
Spring Boot Backend
    ↓
FastAPI AI Service
    ↓
PostgreSQL
```

复杂编辑器能力目前不是主路径，先不放进当前启动主链。

## 当前仓库状态

当前仓库已经具备一套可启动的基础脚手架：

- `postgres` 通过 Docker 运行
- `backend` 通过 Docker 运行
- `ai-service` 通过 Docker 运行
- backend 已有 `conversation / message / agent respond` 基础骨架
- ai-service 已接上 `LangGraph + provider router`
- 默认本地 provider 是 `Ollama`

当前默认目标不是做完整产品，而是保证：

```txt
任何人拉到本地后，按文档可以直接把脚手架跑起来
```

## 运行环境要求

第一次拉项目前，至少准备好这些环境：

- Docker Desktop
- Docker Compose
- Node.js 20+
- npm 10+
- Python 3
- Ollama

说明：

- `make up` 依赖 Docker / Docker Compose
- `make smoke` 依赖本机 `python3`
- `frontend` 本地开发依赖 `node` 和 `npm`
- 当前默认 LLM provider 是本地 `Ollama`

## 首次配置前提

当前默认 `.env.example` 已经按本地 Ollama 写好，所以第一次运行前只需要确认：

1. 本机已安装 Ollama
2. 默认模型已拉取
3. Ollama 服务已启动

推荐先执行：

```bash
ollama pull qwen2.5:7b
ollama serve
```

如果你后续要切远程 provider，再改根目录 `.env`：

- `LLM_PROVIDER=gemini`
- `LLM_PROVIDER=openrouter`
- `LLM_PROVIDER=groq`

## 一键启动

推荐步骤：

1. 复制环境变量

```bash
cp .env.example .env
```

2. 本地先启动 Ollama

```bash
ollama pull qwen2.5:7b
ollama serve
```

如果是第一次使用，还需要先确认默认模型已经拉好。

3. 启动核心服务

```bash
make up
```

说明：

- 复制 `.env.example` 后，默认 `LLM_PROVIDER=ollama`
- 本地需要先启动 Ollama 并拉取模型
- 需要切远程模型时，再显式在 `.env` 里切到 `gemini / openrouter / groq`

等价命令：

```bash
docker compose up --build -d postgres ai-service backend
```

4. 查看服务状态

```bash
make ps
```

5. 运行最小 smoke test

```bash
make smoke
```

6. 启动前端页面

```bash
cd frontend
npm run dev
```

## 快速排障

### 1. `make up` 很慢

最常见原因不是代码问题，而是：

- Docker 正在重新 build 镜像
- Gradle / Python 依赖需要重新下载
- Docker Hub 网络慢

先看服务是不是其实已经起来了：

```bash
make ps
```

### 2. `make smoke` 失败

先确认这三件事：

1. `postgres / backend / ai-service` 都是 `Up`
2. 本地 `ollama serve` 已经启动
3. 默认模型已经拉好

```bash
ollama pull qwen2.5:7b
ollama serve
make up
make smoke
```

### 3. agent 回复不对，或者像没接上模型

先看 AI health：

```txt
http://127.0.0.1:38000/internal/health
```

重点看返回里的：

- `provider`
- `model`
- `mode`
- `configured`

如果你看到的不是 `ollama`，说明 `.env` 配置和你预期不一致。

### 4. 前端能打开，但发不出消息

先检查：

- backend health: `http://127.0.0.1:38080/api/health`
- ai health: `http://127.0.0.1:38000/internal/health`

然后重新：

```bash
make smoke
cd frontend
npm run dev
```

## 默认端口

为了减少和本机其他项目冲突，当前默认端口是：

- PostgreSQL: `55432`
- Backend: `38080`
- AI Service: `38000`

健康检查：

- Backend health: `http://127.0.0.1:38080/api/health`
- AI health: `http://127.0.0.1:38000/internal/health`
- Frontend local page: `http://127.0.0.1:3000`

## 目录说明

- [`docs/`](./docs/README.md): 当前项目文档中心
- [`frontend/`](./frontend/README.md): 前端工程，后续收敛为 IM UI
- [`backend/`](./backend/README.md): Spring Boot 主控服务。当前 backend 唯一主文档也在这里，包含架构规则、启动方式、配置、DTO 约定和新增功能开发方式
- [`ai-service/`](./ai-service/README.md): FastAPI agent 服务
- [`shared/`](./shared/README.md): 共享协议和 schema
- [`scripts/`](./scripts/README.md): 仓库级辅助脚本与 smoke test

## 推荐阅读顺序

如果你是第一次拉这个项目，建议按这个顺序看：

1. 先看这份 [`README.md`](./README.md)
2. 再看 [`frontend/README.md`](./frontend/README.md)
3. 再看 [`backend/README.md`](./backend/README.md)
4. 再看 [`ai-service/README.md`](./ai-service/README.md)
5. 如果要查 LLM 配置，再看 [`docs/agent-llm/README.md`](./docs/agent-llm/README.md)
6. 如果要查数据库落库，再看 [`docs/database-storage/README.md`](./docs/database-storage/README.md)
7. 如果要看跨服务协议，再看 [`shared/README.md`](./shared/README.md)

## 当前建议推进顺序

1. 稳定 `backend + ai-service + postgres`
2. 稳定 `conversation / message / agent respond` 协议
3. 前端收敛成 IM 页面
4. 再考虑流式响应、trace、工具调用

## 主要文档

- [`backend/README.md`](./backend/README.md)
- [`frontend/README.md`](./frontend/README.md)
- [`ai-service/README.md`](./ai-service/README.md)
- [`docs/agent-llm/README.md`](./docs/agent-llm/README.md)
- [`docs/database-storage/README.md`](./docs/database-storage/README.md)
- [`shared/README.md`](./shared/README.md)
