# Getting Started

这份文档只回答一件事：

```txt
别人第一次拿到 CapCutAI，应该怎么启动
```

当前项目默认主线是：

```txt
frontend
  -> backend
  -> ai-service
  -> postgres
```

当前默认 LLM provider 是：

```txt
Ollama
```

当前除了浏览器开发入口，也已经有第一版桌面客户端壳：

```txt
Tauri Desktop Client
```

## 启动前需要什么

本地先准备好这些环境：

- Docker Desktop
- Docker Compose
- Node.js 20+
- npm 10+
- Python 3
- Ollama
- Rust

说明：

- 只跑 `make up + make smoke + npm run dev` 时，Rust 不是必须
- 跑 `npm run desktop:dev` 或 `npm run desktop:build` 时，需要先装好 Rust / Tauri 前置

## 第一次启动

### 1. 进入项目根目录

```bash
cd /Users/zee/xuziyi/projects/CapCutAI
```

### 2. 复制环境变量

```bash
cp .env.example .env
```

默认 `.env.example` 已经配置成：

- `LLM_PROVIDER=ollama`
- `OLLAMA_MODEL=qwen2.5:7b`

## 3. 拉取 Ollama 模型

```bash
ollama pull qwen2.5:7b
```

如果你已经拉过这个模型，这一步可以跳过。

### 4. 启动 Ollama

```bash
ollama serve
```

这一步通常需要保持运行。

### 5. 启动后端链路

```bash
make up
```

这会启动：

- `postgres`
- `backend`
- `ai-service`

### 6. 跑一遍 smoke test

```bash
make smoke
```

如果成功，你会看到：

- backend health 正常
- conversation 创建成功
- message 发送成功
- assistant reply 成功返回

### 7. 启动桌面开发版

```bash
cd frontend
npm run desktop:dev
```

这是当前推荐入口。

说明：

- 这属于开发模式
- 会占用一个终端进程
- 改代码后会重新编译
- 相当于桌面客户端版本的热更新开发

### 8. 启动浏览器开发版（可选）

如果你只想在浏览器里调试前端，也可以执行：

```bash
cd frontend
npm run dev
```

## 日常启动

如果你之前已经跑通过一次，后面日常客户端开发通常只需要：

```bash
cd /Users/zee/xuziyi/projects/CapCutAI
ollama serve
make up
cd frontend
npm run desktop:dev
```

如果你只是在浏览器里调试，再把最后一步换成：

```bash
npm run dev
```

如果你想顺手验证链路没坏，再跑：

```bash
make smoke
```

如果你想直接打出桌面客户端：

```bash
cd frontend
npm run desktop:build
```

这一步会生成：

- `CapCutAI.app`
- `CapCutAI_0.1.0_aarch64.dmg`

这属于打包模式，不是开发热更新模式。

## 现在打开 `.app` 能不能直接用

可以打开界面，但当前仍然需要先启动本地服务链。

也就是说，在当前版本里，直接打开 `.app` 之前，仍然要先保证这些东西已经起来：

```bash
ollama serve
make up
```

所以当前最准确的理解是：

- 桌面客户端界面已经落地
- 但 `backend / ai-service / postgres / ollama` 仍然是本地依赖
- 现在还不是“完全自带所有服务”的单体桌面应用

## 每次跑 `desktop:dev` 会不会多装一个 App

不会。

- `npm run desktop:dev` 只是启动开发版桌面窗口
- `npm run desktop:build` 只是重新生成最新版产物
- 不会每跑一次就多安装一个新的应用

## 常用地址

- Frontend: `http://127.0.0.1:3000`
- Backend health: `http://127.0.0.1:38080/api/health`
- AI health: `http://127.0.0.1:38000/internal/health`

## 桌面客户端产物

当前桌面构建会输出：

- `frontend/src-tauri/target/release/bundle/macos/CapCutAI.app`
- `frontend/src-tauri/target/release/bundle/dmg/CapCutAI_0.1.0_aarch64.dmg`

## 常用命令

查看服务状态：

```bash
make ps
```

停止容器：

```bash
make down
```

查看日志：

```bash
make logs
```

## 常见问题

### `make up` 很慢

最常见原因不是代码坏了，而是：

- Docker 正在重新 build
- 依赖正在重新下载
- Docker Hub 网络慢

先看服务是不是其实已经起来了：

```bash
make ps
```

### `make smoke` 失败

先确认：

1. `ollama serve` 已启动
2. `qwen2.5:7b` 已拉好
3. `postgres / backend / ai-service` 都是 `Up`

### agent 没走 Ollama

打开：

```txt
http://127.0.0.1:38000/internal/health
```

重点看：

- `provider`
- `model`
- `mode`
- `configured`

如果不是 `ollama`，说明 `.env` 配置和你预期不一致。

## 相关文档

- [`../../README.md`](../../README.md)
- [`../../frontend/README.md`](../../frontend/README.md)
- [`../../backend/README.md`](../../backend/README.md)
- [`../../ai-service/README.md`](../../ai-service/README.md)
- [`../agent-llm/README.md`](../agent-llm/README.md)
