# AI Service

这里是 CapCutAI 当前阶段的 agent 服务。

当前主线：

```txt
internal health
-> internal agent respond
-> langgraph conversation graph
-> configured llm provider
```

这层现在的定位，推荐统一理解成：

```txt
Local-first Agent Runtime
```

更准确地说：

- 模型负责理解用户意图、分析风格、生成和修订计划
- `ai-service` / Agent Runtime 负责 context engineering、memory retrieval、graph orchestration、tool dispatch
- 真正的视频分析、渲染、转码应该由本地 Tool Runtime 执行

## 这层负责什么

- 提供 `/internal/health`
- 提供 `/internal/agent/respond`
- 接收 backend 传来的 conversation / messages
- 用 LangGraph 编排最小 respond 流程
- 调当前配置的 provider
- 返回 reply 和 trace
- 按 workspace 组织 context / memory / artifact refs
- 作为本地工具能力的受控调度层

当前 `ai-service` 不负责：

- 本地 workspace 文件夹创建
- conversation 持久化
- 本地素材目录生命周期
- 直接让模型操作客户端 UI
- 把任意 OS 能力暴露给模型

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

## 本地视频工具链环境

如果只跑 agent respond，`make up` 就够了。

如果要跑当前剪辑 / 渲染工具，还需要本机准备：

- `ffmpeg`
- `ffprobe`
- Google Chrome
- Node.js 22+（仅 HyperFrames render 需要）

macOS 推荐：

```bash
brew install ffmpeg
```

如果需要 ASS 字幕、更多滤镜或你已经安装 `ffmpeg-full`，工具会自动优先使用：

```txt
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
```

环境检查：

```bash
cd ai-service
python3 -m app.tools.inspect_render_environment
```

说明：

- native 主轨渲染走本机 ffmpeg
- HyperFrames render 走本机 Node.js + Chrome
- Docker 仍推荐用于服务链，不作为当前视频工具链的默认渲染入口
- HyperFrames Docker render 可以作为后续稳定 renderer image 方向，但临时 build 容易受 apt / 网络影响

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
app/memory/      conversation / workspace memory 组装
app/tools/       可被 graph 调用的基础只读工具
app/prompts/     graph / node prompt 组织
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
workspace 的本地结构归客户端 / 本地工作区
workspace 下的智能编排归 ai-service / Agent Runtime
workspace 下的媒体执行归 Local Tool Runtime
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
- Memory
  - [`workspace_memory.py`](./app/memory/workspace_memory.py)
- Tools
  - [`workspace_tools.py`](./app/tools/workspace_tools.py)
- Prompts
  - [`conversation_prompt.py`](./app/prompts/conversation_prompt.py)
- Schema
  - [`message.py`](./app/schemas/message.py)
  - [`respond_request.py`](./app/schemas/respond_request.py)
  - [`respond_response.py`](./app/schemas/respond_response.py)

## 当前 agent 底层分层

当前 `conversation_graph` 已经不是“直接拼 prompt 然后回一句”了，而是先走：

```txt
messages
-> conversation memory
-> workspace memory
-> intent classify
-> base tools
-> prompt build
-> llm reply
```

后面视频工作流推荐统一按这条链理解：

```txt
user intent
-> context build
-> memory retrieval
-> structured plan
-> local tool calls
-> artifacts
-> response / trace / task status
```

当前第一批基础工具只做只读和校验：

- `describe_workspace_state`
- `list_source_videos`
- `validate_workspace_inputs`

这层先搭稳，后面接更多模型、tool、skill 才不会把工作流逻辑继续塞回 graph 文件里。

## Tool Boundary

后面工具层建议坚持两个原则：

1. 只暴露白名单能力
2. 工具输入输出必须结构化、可校验、可审计

更理想的调用语义是：

- `video.probe(assetId)`
- `video.extractScenes(assetId, config)`
- `audio.detectBeats(assetId)`
- `timeline.render(planId)`

而不是把任意 shell / 任意文件操作直接交给模型。

## 后面视频链看哪里

如果你接下来做视频能力，优先看：

- [`../docs/04-detailed-design/03-mvp-video-pipeline/README.md`](../docs/04-detailed-design/03-mvp-video-pipeline/README.md)
- [`../docs/04-detailed-design/01-ai-service-video-architecture/README.md`](../docs/04-detailed-design/01-ai-service-video-architecture/README.md)
- [`../docs/03-architecture/01-workspace-agent-runtime-model/README.md`](../docs/03-architecture/01-workspace-agent-runtime-model/README.md)
- [`../docs/03-architecture/02-client-backend-agent-tool-boundary/README.md`](../docs/03-architecture/02-client-backend-agent-tool-boundary/README.md)
- [`../docs/02-use-cases/01-workspace-agent-use-cases/README.md`](../docs/02-use-cases/01-workspace-agent-use-cases/README.md)
- [`../docs/04-detailed-design/02-langgraph-engineering-guideline/README.md`](../docs/04-detailed-design/02-langgraph-engineering-guideline/README.md)
- [`../docs/04-detailed-design/05-style-analysis-design/README.md`](../docs/04-detailed-design/05-style-analysis-design/README.md)
- [`../docs/04-detailed-design/06-style-editing-design/README.md`](../docs/04-detailed-design/06-style-editing-design/README.md)

## 当前可直接用的本地工具

如果只想快速验证当前剪辑闭环，推荐在项目根目录跑：

```bash
scripts/render_editor_sample.sh
```

默认使用 `PROFILE=smoke`，会完成：

```txt
data/test_case
  -> editing-package.json
  -> ffmpeg native render
  -> mp4
```

输出：

```txt
ai-service/output/plans/editor-sample.editing-package.json
ai-service/output/renders/editor-sample.native.final.mp4
```

常用 profile：

```bash
PROFILE=smoke scripts/render_editor_sample.sh
PROFILE=draft scripts/render_editor_sample.sh
PROFILE=1080p scripts/render_editor_sample.sh
```

如果需要同时生成 HyperFrames bundle：

```bash
BUILD_HYPERFRAMES=1 scripts/render_editor_sample.sh
```

如果需要继续尝试 HyperFrames render：

```bash
RENDER_HYPERFRAMES=1 PROFILE=1080p scripts/render_editor_sample.sh
```

如果你已经拿到了 Editor 导出的 `*.editing-package.json`，也可以先在本地生成一版 HyperFrames draft composition：

```bash
cd ai-service
python -m app.tools.build_hyperframes_draft \
  --package ../path/to/example.editing-package.json
```

默认会把产物写到 package 里的 `editingJob.compositionPath`。

当前更推荐的真实视频闭环出口是 native render：

```bash
cd ai-service
python3 -m app.tools.render_native_video \
  --package ./output/plans/editor-sample.editing-package.json \
  --output ./output/renders/editor-sample.native.final.mp4 \
  --max-long-side 1280 \
  --audio-mode source \
  --burn-subtitles \
  --preset veryfast \
  --crf 26
```

HyperFrames 主要用于：

- 标题卡
- 复杂字幕动效
- 贴纸 / callout
- 品牌包装层
- agent 生成式 HTML/CSS 视觉层
