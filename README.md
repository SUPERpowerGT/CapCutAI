# CapCutAI

CapCutAI 当前主形态是：

```txt
Desktop Client
```

现在的实现方式是：

- `frontend`：桌面客户端界面层
- `Tauri`：默认桌面壳
- `backend`：Spring Boot 主控服务
- `ai-service`：FastAPI + LangGraph agent 服务
- `postgres`：本地数据库
- `ollama`：当前默认本地模型入口

当前原则：

```txt
Desktop-first
Local-first
Cloud-ready
```

浏览器模式还保留，但只用于开发 / 调试，不再作为产品主形态。

## 先知道这几件事

- 这是**一套前端代码**，不是网页版和客户端版两套 UI
- 当前推荐入口是 **Tauri 桌面开发版**
- 当前 `.app` 已可构建和打开
- 当前桌面客户端**仍依赖本地服务链**
- `Window -> New Window` 的语义是：
  - 新建一个新的 `workspace`
  - 打开一个新的工作窗口
  - 不是“新建聊天 session”

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
- `npm run desktop:dev` / `npm run desktop:build` 依赖 Rust
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
source "$HOME/.cargo/env"
npm install
npm run desktop:dev
```

当前推荐就这样启动。

## 日常怎么用

### 1. 启动本地服务链

在项目根目录：

```bash
ollama serve
make up
```

可选自检：

```bash
make smoke
```

### 2. 启动桌面客户端开发版

在 `frontend/` 目录：

```bash
source "$HOME/.cargo/env"
npm run desktop:dev
```

说明：

- 这是当前推荐开发入口
- 会占一个终端进程
- 改代码会重新编译
- 桌面开发模式使用 `http://127.0.0.1:3001`

### 3. 打包桌面客户端

在 `frontend/` 目录：

```bash
source "$HOME/.cargo/env"
npm run desktop:build
```

当前会产出：

- `frontend/src-tauri/target/release/bundle/macos/CapCutAI.app`
- `frontend/src-tauri/target/release/bundle/dmg/CapCutAI_0.1.0_aarch64.dmg`

说明：

- `.app` 当前可用
- `.dmg` bundling 仍有已知问题，后续再修

### 4. 浏览器模式

如果你只是调前端页面，也可以在 `frontend/` 里跑：

```bash
npm run dev
```

浏览器开发地址：

- `http://127.0.0.1:3000`

但当前这不是推荐产品入口。

## 当前桌面版是什么状态

现在的桌面客户端已经可以：

- 打开工作台界面
- 创建 / 恢复本地 `workspace`
- `Window -> New Window` 创建新的 workspace 窗口
- 本地上传视频
- 在中间 `Preview` 立即显示本地视频预览
- 跑右侧 `Agent` 对话链路

但当前它还不是“单文件全内置桌面应用”，因为这些服务仍要本机先起来：

```bash
ollama serve
make up
```

也就是说：

- 客户端界面已经是桌面版
- 服务链目前仍是本地依赖

## 常用命令

项目根目录：

```bash
make up
make smoke
make ps
make down
```

`frontend/` 目录：

```bash
npm run desktop:dev
npm run desktop:build
npm run dev
```

## 常用地址

- Backend health：`http://127.0.0.1:38080/api/health`
- AI health：`http://127.0.0.1:38000/internal/health`
- Frontend dev（browser）：`http://127.0.0.1:3000`
- Frontend dev（desktop）：`http://127.0.0.1:3001`

## 目录入口

- [`frontend/README.md`](./frontend/README.md)
  - 客户端界面层、桌面工作台、分栏和功能模块
- [`backend/README.md`](./backend/README.md)
  - Spring Boot 主控服务
- [`ai-service/README.md`](./ai-service/README.md)
  - LangGraph / LLM / agent 服务
- [`docs/README.md`](./docs/README.md)
  - 文档中心
- [`shared/README.md`](./shared/README.md)
  - 共享协议和 schema
- [`scripts/README.md`](./scripts/README.md)
  - 仓库级脚本和 smoke test

## 建议先看哪些文档

第一次拉项目，建议按这个顺序看：

1. [`docs/getting-started/README.md`](./docs/getting-started/README.md)
2. [`frontend/README.md`](./frontend/README.md)
3. [`backend/README.md`](./backend/README.md)
4. [`ai-service/README.md`](./ai-service/README.md)
5. [`docs/desktop-client-plan/README.md`](./docs/desktop-client-plan/README.md)

按主题继续看：

- LLM 配置：[`docs/agent-llm/README.md`](./docs/agent-llm/README.md)
- 桌面客户端路线：[`docs/desktop-client-plan/README.md`](./docs/desktop-client-plan/README.md)
- 数据库存储：[`docs/database-storage/README.md`](./docs/database-storage/README.md)
- 文档中心：[`docs/README.md`](./docs/README.md)

## 当前开发约定

- 新功能默认按 **Desktop-first** 设计
- 浏览器模式只作为调试入口保留
- `workspace` 比 `session` 更重要
- 一个窗口 = 一个 `workspace`
- conversation 目前跟着 `workspace` 走

## 常见坑

### `npm run desktop:dev` 提示找不到 `cargo`

先执行：

```bash
source "$HOME/.cargo/env"
```

然后再运行：

```bash
cd frontend
npm run desktop:dev
```

### `npm run desktop:dev` 要在哪跑

必须在：

```bash
frontend/
```

目录里执行，不是在仓库根目录。

### 为什么重新打开 App 还能看到旧对话

当前桌面端默认会恢复上次 `workspace`。

所以你看到的是：

- 旧 `workspace`
- 对应 `workspace` 下的 conversation

这属于当前本地工作区恢复逻辑，不是 bug。
