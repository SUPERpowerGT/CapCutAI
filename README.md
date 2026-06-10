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
- `ollama` / `AI4Video VL`：本地或托管模型入口

当前原则：

```txt
Desktop-first
Local-first
Cloud-ready
```

## 交付物总览

本仓库交付内容汇总如下：

- 项目说明：当前 README，包含项目定位、运行方式、演示链路、产物路径和文档索引。
- 代码：[`frontend`](./frontend/README.md)、[`backend`](./backend/README.md)、[`ai-service`](./ai-service/README.md)、[`AI4Video`](./AI4Video/README_API.md)、[`shared`](./shared/README.md)。
- 运行说明：见“最快启动”“日常怎么用”和 [`docs/90-getting-started/README.md`](./docs/90-getting-started/README.md)。
- 演示链路：右侧 IM 可触发“参考视频分析”和“按经验剪辑 source 素材”。
- 产出视频：默认落到 `~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/renders/`。
- 工具协议与安全边界：见 [`docs/03-architecture/02-client-backend-agent-tool-boundary/README.md`](./docs/03-architecture/02-client-backend-agent-tool-boundary/README.md) 和 [`docs/agent-editing-tools/README.md`](./docs/agent-editing-tools/README.md)。

系统定位：

```txt
Desktop Client
  + Local Agent Runtime
  + Local Tool Runtime
  + Local Workspace File System
  + Cloud / Local LLM
```

核心边界：

- 模型不直接调用客户端 UI
- 本地 Agent Runtime 通过受控工具能力调用 Local Tool Runtime
- `Client UI` 只负责交互、状态展示和结果预览

浏览器模式还保留，但只用于开发 / 调试，不再作为产品主形态。

## 项目边界

- 这是**一套前端代码**，不是网页版和客户端版两套独立 UI
- 当前推荐入口是 **Tauri 桌面开发版**
- 当前 `.app` 已可构建和打开
- 当前桌面客户端**仍依赖本地服务链**
- `Window -> New Window` 表示新建一个 `workspace` 并打开新的工作窗口，不等同于新建聊天 session。

## 运行环境

基础环境：

- Docker Desktop
- Docker Compose
- Node.js 22+
- npm 10+
- Python 3
- Ollama（如果走本地模型）
- Rust

视频剪辑 / 渲染工具链额外依赖：

- ffmpeg
- Google Chrome

说明：

- `make up` 依赖 Docker / Docker Compose
- `make smoke` 依赖本机 `python3`
- `npm run desktop:dev` / `npm run desktop:build` 依赖 Rust
- 当前 `.env.example` 默认 LLM provider 是本地 `Ollama`
- 当前 IM 视频工作流推荐可切到 `AI4Video VL`，token 放在 `AI4Video/pipeline_api/config.local.py` 或本地 `.env`
- native 主轨渲染依赖 `ffmpeg` / `ffprobe`
- HyperFrames render 依赖本机 Node.js 22+ 和 Chrome
- macOS 上可安装 `ffmpeg-full`；Docker 内会使用容器里的 `ffmpeg` / `ffprobe`

## 快速启动

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

上述命令会启动本地服务链，并打开桌面开发版客户端。

使用 AI4Video hosted-model 工作流时，需要额外配置私有 token：

```bash
cp AI4Video/pipeline_api/config.local.example.py AI4Video/pipeline_api/config.local.py
# 在 config.local.py 中填入 vl / omni token
# 将 .env 中 LLM_PROVIDER 设置为 ai4video_vl
docker compose up --build -d ai-service backend
```

`config.local.py` 已被 gitignore 忽略，真实 token 不应该提交。

仅验证剪辑工具链时，可在项目根目录执行：

```bash
scripts/render_editor_sample.sh
```

默认会使用 `data/test_case` 中的 mock analyzer 数据生成：

- `ai-service/output/plans/editor-sample.editing-package.json`
- `ai-service/output/renders/editor-sample.native.final.mp4`

说明：

- 这条命令走本机 ffmpeg native render
- 默认使用 `PROFILE=smoke`
- 用于验证“测试数据 -> 剪辑 package -> MP4”的闭环
- HyperFrames 仍作为复杂包装层 / overlay 能力保留，不作为默认主轨导出器

## 当前 IM 视频工作流

桌面端右侧 IM 现在支持两条主要视频链路：

```txt
参考/爆款视频
  -> AI4Video 分析
  -> workspace/assets/intermediate/
  -> workspace/assets/template/elastic_template.json

source 素材
  + elastic_template.json
  -> source 分析
  -> planner 生成 timeline_plan
  -> editing package
  -> native render
  -> workspace/artifacts/renders/*.native.final.mp4
```

固定产物约定：

- 参考分析中间文件：`~/Documents/CapCutAI/Workspaces/<workspaceId>/assets/intermediate/`
- 参考风格模板：`~/Documents/CapCutAI/Workspaces/<workspaceId>/assets/template/elastic_template.json`
- 剪辑 package：`~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/plans/`
- 最终成片：`~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/renders/`
- 内部调试缓存：`ai-service/output/im-runs/`

IM 行为约定：

- 用户要求分析参考视频时，先确认，再跑 AI4Video 分析。
- 用户要求剪辑/制作视频时，如果当前 workspace 已有 `elastic_template.json`，默认复用现有经验，不重复分析参考视频。
- 只有用户明确说“重新分析 / 重跑分析 / 再分析一次”时，才会重跑参考视频分析。
- 长任务运行时，参考/素材上传和删除会被锁定，IM 显示动态状态。

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

仅调试前端页面时，可以在 `frontend/` 目录执行：

```bash
npm run dev
```

浏览器开发地址：

- `http://127.0.0.1:3000`

该模式仅用于前端开发调试，不作为默认产品入口。

## 当前桌面版是什么状态

现在的桌面客户端已经可以：

- 打开工作台界面
- 创建 / 恢复本地 `workspace`
- `Window -> New Window` 创建新的 workspace 窗口
- 导入本地视频到当前 workspace
- 在中间 `Preview` 立即显示本地视频预览
- 跑右侧 `Agent` 对话链路
- 通过 IM 分析参考视频并沉淀 `elastic_template.json`
- 通过 IM 复用参考经验剪辑 source 素材并输出 MP4

当前桌面客户端仍依赖本地服务链，需要先启动：

```bash
ollama serve
make up
```

当前状态：

- 客户端界面已经是桌面版
- 服务链目前仍是本地依赖

## 常用命令

项目根目录：

```bash
make up
make smoke
make ps
make down
scripts/render_editor_sample.sh
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
- Workspace final renders：`~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/renders/`
- Workspace editing packages：`~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/plans/`
- AI service debug runs：`ai-service/output/im-runs/`

## 文档导航

文档中心总入口：

- [`docs/README.md`](./docs/README.md)

推荐阅读顺序：

1. [`docs/90-getting-started/README.md`](./docs/90-getting-started/README.md)
2. [`docs/01-overview/README.md`](./docs/01-overview/README.md)
3. [`docs/02-use-cases/01-workspace-agent-use-cases/README.md`](./docs/02-use-cases/01-workspace-agent-use-cases/README.md)
4. [`docs/03-architecture/03-system-architecture/README.md`](./docs/03-architecture/03-system-architecture/README.md)
5. [`docs/04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md`](./docs/04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md)

### 代码入口

- 前端 / 桌面端：[`frontend/README.md`](./frontend/README.md)
- 后端主控服务：[`backend/README.md`](./backend/README.md)
- AI Agent 服务：[`ai-service/README.md`](./ai-service/README.md)
- AI4Video 分析链：[`AI4Video/README_API.md`](./AI4Video/README_API.md)
- 共享协议：[`shared/README.md`](./shared/README.md)
- 仓库脚本：[`scripts/README.md`](./scripts/README.md)

### 项目说明与用例

- 文档治理：[`docs/00-document-governance/README.md`](./docs/00-document-governance/README.md)
- 项目概览：[`docs/01-overview/README.md`](./docs/01-overview/README.md)
- Use Cases 总览：[`docs/02-use-cases/README.md`](./docs/02-use-cases/README.md)
- Workspace Agent Use Cases：[`docs/02-use-cases/01-workspace-agent-use-cases/README.md`](./docs/02-use-cases/01-workspace-agent-use-cases/README.md)
- Getting Started：[`docs/90-getting-started/README.md`](./docs/90-getting-started/README.md)

### 整体 AI 架构与安全边界

- Architecture 总览：[`docs/03-architecture/README.md`](./docs/03-architecture/README.md)
- Workspace Agent Runtime：[`docs/03-architecture/01-workspace-agent-runtime-model/README.md`](./docs/03-architecture/01-workspace-agent-runtime-model/README.md)
- Client / Backend / Agent / Tool 边界：[`docs/03-architecture/02-client-backend-agent-tool-boundary/README.md`](./docs/03-architecture/02-client-backend-agent-tool-boundary/README.md)
- System Architecture：[`docs/03-architecture/03-system-architecture/README.md`](./docs/03-architecture/03-system-architecture/README.md)
- Tool 协议草案：[`docs/agent-editing-tools/README.md`](./docs/agent-editing-tools/README.md)
- Codex video editing skill：[`docs/agent-editing-tools/codex-video-editing-skill.md`](./docs/agent-editing-tools/codex-video-editing-skill.md)
- Codex skill draft：[`docs/agent-editing-tools/codex-skill-draft.md`](./docs/agent-editing-tools/codex-skill-draft.md)

### 运行时、模型与服务

- Detailed Design 总览：[`docs/04-detailed-design/README.md`](./docs/04-detailed-design/README.md)
- AI Service 视频架构：[`docs/04-detailed-design/01-ai-service-video-architecture/README.md`](./docs/04-detailed-design/01-ai-service-video-architecture/README.md)
- LangGraph 工程规范：[`docs/04-detailed-design/02-langgraph-engineering-guideline/README.md`](./docs/04-detailed-design/02-langgraph-engineering-guideline/README.md)
- MVP 视频管线：[`docs/04-detailed-design/03-mvp-video-pipeline/README.md`](./docs/04-detailed-design/03-mvp-video-pipeline/README.md)
- Agent LLM 配置：[`docs/04-detailed-design/09-agent-llm-setup/README.md`](./docs/04-detailed-design/09-agent-llm-setup/README.md)
- Agent Runtime 调用接口：[`docs/04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md`](./docs/04-detailed-design/10-agent-runtime-invocation-and-interfaces/README.md)
- Agent Runtime 韧性与检索策略：[`docs/04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md`](./docs/04-detailed-design/11-agent-runtime-resilience-and-retrieval-policy/README.md)

### 视频分析、剪辑与渲染

- 风格分析设计：[`docs/04-detailed-design/05-style-analysis-design/README.md`](./docs/04-detailed-design/05-style-analysis-design/README.md)
- 风格剪辑设计：[`docs/04-detailed-design/06-style-editing-design/README.md`](./docs/04-detailed-design/06-style-editing-design/README.md)
- 当前链路状态：[`docs/04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md`](./docs/04-detailed-design/06-style-editing-design/CURRENT_CHAIN_STATUS.md)
- AI4Video 闭环清单：[`docs/04-detailed-design/06-style-editing-design/AI4VIDEO_CLOSURE_CHECKLIST.md`](./docs/04-detailed-design/06-style-editing-design/AI4VIDEO_CLOSURE_CHECKLIST.md)
- Source Material Handoff：[`docs/source-material-handoff/README.md`](./docs/source-material-handoff/README.md)
- 当前剪辑入口：[`docs/current-editing-entrypoints/README.md`](./docs/current-editing-entrypoints/README.md)
- Editor Preview Export：[`docs/editor-preview-export/README.md`](./docs/editor-preview-export/README.md)
- HyperFrames Draft Builder：[`docs/hyperframes-draft-builder/README.md`](./docs/hyperframes-draft-builder/README.md)
- Render Pipeline Restructure：[`docs/render-pipeline-restructure/README.md`](./docs/render-pipeline-restructure/README.md)
- Editor MVP Change Summary：[`docs/editor-mvp-change-summary/README.md`](./docs/editor-mvp-change-summary/README.md)
- MVP Film Editing PRD：[`docs/mvp-filmediting-plan/mvp-prd.md`](./docs/mvp-filmediting-plan/mvp-prd.md)

### 客户端、存储与 IM

- Desktop Client Design：[`docs/04-detailed-design/07-desktop-client-design/README.md`](./docs/04-detailed-design/07-desktop-client-design/README.md)
- Agent Panel IM Design：[`docs/04-detailed-design/08-agent-panel-im-design/README.md`](./docs/04-detailed-design/08-agent-panel-im-design/README.md)
- Database / Storage Design：[`docs/04-detailed-design/04-database-storage-design/README.md`](./docs/04-detailed-design/04-database-storage-design/README.md)
- Workspace Storage / Target Schema：[`docs/04-detailed-design/12-workspace-storage-and-target-schema/README.md`](./docs/04-detailed-design/12-workspace-storage-and-target-schema/README.md)

## 当前开发约定

- 新功能默认按 **Desktop-first** 设计
- 浏览器模式只作为调试入口保留
- `workspace` 比 `session` 更重要
- 一个窗口 = 一个 `workspace`
- conversation 目前跟着 `workspace` 走
- 原始视频、抽帧、中间产物、最终产物优先保存在本地 workspace
- 模型负责理解、规划、修订；真正的视频分析、渲染、转码由本地工具执行
- 当前主轨粗剪、字幕烧录、音频保留优先使用 ffmpeg
- HyperFrames 主要用于复杂字幕动效、标题卡、贴纸、包装层和 agent 生成式视觉层

## 排障说明

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

### `npm run desktop:dev` 提示 `listen EPERM: operation not permitted 127.0.0.1:3001`

这通常不是 Tauri 本身异常，而是当前终端环境不允许本地监听端口。

先确认你是在普通本地终端里运行，而不是受限沙箱 / 受限远程环境里运行。

然后在：

```bash
cd frontend
npm run desktop:web-dev
```

单独验证前端 dev server 能不能起来。

如能正常看到：

```txt
Local: http://127.0.0.1:3001
```

再回到：

```bash
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
