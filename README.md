# CapCutAI

CapCutAI 当前主形态已经明确为：

```txt
Desktop Client
```

现在的实现方式是：

- 一套 `frontend` 代码
- `Tauri` 作为默认桌面壳
- 浏览器模式只保留开发 / 调试价值
- 当前策略是 `Local-first, Cloud-ready`

当前最重要的服务链路：

```txt
Frontend / Desktop UI
    ↓
Spring Boot Backend
    ↓
FastAPI AI Service
    ↓
PostgreSQL
```

## 运行环境

第一次拉项目，至少准备：

- Docker Desktop
- Docker Compose
- Node.js 20+
- npm 10+
- Python 3
- Ollama
- Rust

说明：

- `make up` 依赖 Docker / Docker Compose
- `make smoke` 依赖本机 `python3`
- `npm run desktop:dev` / `desktop:build` 依赖 `Rust + Tauri`
- 当前默认 LLM provider 是本地 `Ollama`

## 最快启动

在项目根目录执行：

```bash
cp .env.example .env
ollama pull qwen2.5:7b
ollama serve
make up
make smoke
cd frontend
npm run desktop:dev
```

如果你只想在浏览器里调试前端，把最后一步换成：

```bash
npm run dev
```

## 常用入口

- 桌面开发版：`cd frontend && npm run desktop:dev`
- 桌面打包版：`cd frontend && npm run desktop:build`
- 浏览器调试版：`cd frontend && npm run dev`
- 服务状态：`make ps`
- 全链路自检：`make smoke`

## 三种运行方式

### 1. 开发模式

```bash
cd frontend
npm run desktop:dev
```

说明：

- 这是桌面客户端开发模式
- 会占用一个终端进程
- 改代码后会重新编译
- 适合日常开发

### 2. 打包模式

```bash
cd frontend
npm run desktop:build
```

说明：

- 这会生成可直接打开的桌面客户端产物
- 当前 macOS 产物是 `.app` 和 `.dmg`
- 适合给自己或组员直接打开使用

### 3. 当前可用但仍依赖本地服务的使用模式

当前即使已经有 `.app`，也不是“完全脱离本地服务”的纯单文件客户端。

现在仍然需要先启动：

```bash
ollama serve
make up
```

也就是说：

- `CapCutAI.app` 已经可以像正常应用一样打开界面
- 但当前 `backend / ai-service / postgres / ollama` 仍然要先在本机运行
- 现在是“客户端界面已落地，服务链仍是本地依赖”的状态

### 4. 会不会每次都多装一个 App

不会。

- `npm run desktop:dev` 不会安装新的 App，只是启动一个开发版窗口
- `npm run desktop:build` 会重新生成最新产物，但不会自动在系统里装出很多份不同应用

默认端口：

- Backend health: `http://127.0.0.1:38080/api/health`
- AI health: `http://127.0.0.1:38000/internal/health`
- Frontend dev: `http://127.0.0.1:3000`

## 先看哪些文档

第一次拉项目，建议按这个顺序看：

1. [`docs/getting-started/README.md`](./docs/getting-started/README.md)
2. [`frontend/README.md`](./frontend/README.md)
3. [`backend/README.md`](./backend/README.md)
4. [`ai-service/README.md`](./ai-service/README.md)
5. [`docs/desktop-client-plan/README.md`](./docs/desktop-client-plan/README.md)

按主题继续看：

- LLM 配置：[`docs/agent-llm/README.md`](./docs/agent-llm/README.md)
- 数据库存储：[`docs/database-storage/README.md`](./docs/database-storage/README.md)
- 文档中心：[`docs/README.md`](./docs/README.md)
- 共享协议：[`shared/README.md`](./shared/README.md)
- 仓库脚本：[`scripts/README.md`](./scripts/README.md)

## 目录入口

- [`frontend/`](./frontend/README.md): 客户端界面层与桌面工作台主文档
- [`backend/`](./backend/README.md): Spring Boot 主控服务
- [`ai-service/`](./ai-service/README.md): FastAPI agent 服务
- [`docs/`](./docs/README.md): 文档中心
- [`shared/`](./shared/README.md): 共享协议和 schema
- [`scripts/`](./scripts/README.md): 仓库级辅助脚本与 smoke test
