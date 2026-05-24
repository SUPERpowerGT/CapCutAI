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

## 启动前需要什么

本地先准备好这些环境：

- Docker Desktop
- Docker Compose
- Node.js 20+
- npm 10+
- Python 3
- Ollama

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

### 7. 启动前端

```bash
cd frontend
npm run dev
```

然后打开：

```txt
http://127.0.0.1:3000
```

## 日常启动

如果你之前已经跑通过一次，后面日常开发通常只需要：

```bash
cd /Users/zee/xuziyi/projects/CapCutAI
ollama serve
make up
cd frontend
npm run dev
```

如果你想顺手验证链路没坏，再跑：

```bash
make smoke
```

## 常用地址

- Frontend: `http://127.0.0.1:3000`
- Backend health: `http://127.0.0.1:38080/api/health`
- AI health: `http://127.0.0.1:38000/internal/health`

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
