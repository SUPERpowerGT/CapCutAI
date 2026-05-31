# Getting Started

这份文档只回答一件事：

```txt
第一次拉下 CapCutAI，怎么最快跑起来
```

当前推荐入口：

```txt
Desktop Client Dev
```

## 先准备什么

- Docker Desktop
- Docker Compose
- Node.js 20+
- npm 10+
- Python 3
- Ollama
- Rust

说明：

- 只跑服务链和浏览器调试时，Rust 不是必须
- 跑 `desktop:dev` / `desktop:build` 时，需要 Rust

## 3 分钟启动卡

在项目根目录：

```bash
cp .env.example .env
ollama pull qwen2.5:7b
ollama serve
make up
make smoke
```

然后在 `frontend/`：

```bash
cd frontend
source "$HOME/.cargo/env"
npm install
npm run desktop:dev
```

这就是当前推荐启动方式。

## 你实际会启动什么

本地服务链：

- `postgres`
- `backend`
- `ai-service`
- `ollama`

桌面客户端：

- `frontend + Tauri`

## 常用入口

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

说明：

- `desktop:dev`
  - 桌面开发版
  - 当前主入口
  - 使用 `http://127.0.0.1:3001`
- `desktop:build`
  - 打包桌面客户端
- `dev`
  - 浏览器调试入口
  - 使用 `http://127.0.0.1:3000`

## 打包后能不能直接用

可以直接打开 `.app` 界面，但当前仍然需要先启动本地服务链：

```bash
ollama serve
make up
```

也就是说，现在是：

- 客户端界面已经落地
- 服务链当前还是本地依赖

## 常用地址

- Backend health：`http://127.0.0.1:38080/api/health`
- AI health：`http://127.0.0.1:38000/internal/health`
- Frontend dev（browser）：`http://127.0.0.1:3000`
- Frontend dev（desktop）：`http://127.0.0.1:3001`

## 常见坑

### `npm run desktop:dev` 找不到 `cargo`

执行：

```bash
source "$HOME/.cargo/env"
```

然后重新运行：

```bash
cd frontend
npm run desktop:dev
```

### `npm run desktop:dev` 在哪里执行

必须在：

```bash
frontend/
```

目录里执行，不是在仓库根目录。

### 为什么重新打开 App 还能看到旧对话

当前桌面端默认会恢复上次 `workspace`。

所以你看到的是：

- 旧 `workspace`
- 这个 `workspace` 下的 conversation

这属于当前本地工作区恢复逻辑。

## 下一步看什么

- 总入口：[`../../README.md`](../../README.md)
- 前端：[`../../frontend/README.md`](../../frontend/README.md)
- 后端：[`../../backend/README.md`](../../backend/README.md)
- AI：[`../../ai-service/README.md`](../../ai-service/README.md)
- 桌面客户端路线：[`../04-detailed-design/07-desktop-client-design/README.md`](../04-detailed-design/07-desktop-client-design/README.md)
