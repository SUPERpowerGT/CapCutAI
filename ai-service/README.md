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

当前剪辑 / 渲染工具额外依赖：

- `ffmpeg`
- `ffprobe`
- Google Chrome
- Node.js 22+（仅 HyperFrames render 需要）

本机 macOS 推荐：

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
- Docker 服务镜像内也安装了 `ffmpeg`，IM 工作流在容器中渲染时会使用容器内的 `ffmpeg` / `ffprobe`
- HyperFrames Docker render 可以作为后续稳定 renderer image 方向，但临时 build 容易受 apt / 网络影响

## 当前默认模型入口

`.env.example` 默认：

```txt
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

也就是说：

- 本地默认走 Ollama
- 当前 IM 视频工作流推荐可切到 `AI4Video VL`
- 后续要切别的 provider，只改 `.env`
- 上云时也沿用同一套 env key

AI4Video hosted-model 配置：

```bash
cp AI4Video/pipeline_api/config.local.example.py AI4Video/pipeline_api/config.local.py
# 填入 vl / omni token
# .env 中设置：
LLM_PROVIDER=ai4video_vl
```

读取优先级：

```txt
AI4VIDEO_VL_API_KEY / AI4VIDEO_OMNI_API_KEY
  -> LLM_API_KEY（仅 IM LLM fallback）
  -> AI4Video/pipeline_api/config.local.py
```

注意：

- `config.local.py` 已被 gitignore 忽略。
- 禁止将真实 token 写入 `config.py` 或提交到仓库。
- `vl` 用于 IM/planner/VL 视觉理解。
- `omni` 用于 ASR 和认知对齐。

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
output/          内部调试运行缓存
```

## 当前与 workspace 的关系

桌面客户端当前按：

```txt
一个窗口 = 一个 workspace
```

对 `ai-service` 来说：

- workspace 本地生命周期归客户端
- `ai-service` 消费 workspace 上下文
- 固定参考分析产物和最终成片按 workspace 归档

一句话：

```txt
workspace 的本地结构归客户端 / 本地工作区
workspace 下的智能编排归 ai-service / Agent Runtime
workspace 下的媒体执行归 Local Tool Runtime
```

当前固定目录约定：

```txt
~/Documents/CapCutAI/Workspaces/<workspaceId>/
  assets/
    reference/current/       当前参考/爆款视频
    source/                  用户待剪 source 素材
    intermediate/            参考视频分析中间文件
    template/elastic_template.json
  artifacts/
    plans/                   editing-package.json / timeline plan
    renders/                 最终 *.native.final.mp4 与 render-result.json
```

内部调试缓存：

```txt
ai-service/output/im-runs/<workspaceId>/<conversationId_timestamp>/
```

缓存目录主要用于 source 分析和排障，不作为用户最终交付路径。

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

该层用于承载后续模型、tool、skill 扩展，避免将工作流逻辑继续堆叠到 graph 文件中。

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

## 视频链路参考文档

视频能力相关文档：

- [`../docs/04-detailed-design/03-mvp-video-pipeline/README.md`](../docs/04-detailed-design/03-mvp-video-pipeline/README.md)
- [`../docs/04-detailed-design/01-ai-service-video-architecture/README.md`](../docs/04-detailed-design/01-ai-service-video-architecture/README.md)
- [`../docs/03-architecture/01-workspace-agent-runtime-model/README.md`](../docs/03-architecture/01-workspace-agent-runtime-model/README.md)
- [`../docs/03-architecture/02-client-backend-agent-tool-boundary/README.md`](../docs/03-architecture/02-client-backend-agent-tool-boundary/README.md)
- [`../docs/02-use-cases/01-workspace-agent-use-cases/README.md`](../docs/02-use-cases/01-workspace-agent-use-cases/README.md)
- [`../docs/04-detailed-design/02-langgraph-engineering-guideline/README.md`](../docs/04-detailed-design/02-langgraph-engineering-guideline/README.md)
- [`../docs/04-detailed-design/05-style-analysis-design/README.md`](../docs/04-detailed-design/05-style-analysis-design/README.md)
- [`../docs/04-detailed-design/06-style-editing-design/README.md`](../docs/04-detailed-design/06-style-editing-design/README.md)

## 当前 IM 视频工作流

当前 graph 已接入三类工作流：

- `ANALYZE_REFERENCE`：分析参考/爆款视频，产出 `elastic_template.json`。
- `CREATE_STYLED_VIDEO`：复用已有参考经验，分析 source 素材并渲染 demo。
- `ANALYZE_AND_CREATE_STYLED_VIDEO`：在没有现成经验或用户明确要求重跑时，先分析参考视频再剪 source。

行为约定：

- workspace 已有 `assets/template/elastic_template.json` 时，剪辑/制作请求默认走 `CREATE_STYLED_VIDEO`，不会重复分析参考视频。
- 只有用户明确说“重新分析 / 重跑分析 / 再分析一次”，才会重跑参考视频分析。
- 状态查询会优先检查 workspace 固定产物，不从 source 分析缓存里猜结果。
- 长任务异常会被摘要成用户可读问题，不直接把底层 traceback 打进 IM。

## 当前可直接用的本地工具

容器服务健康检查：

```bash
docker compose exec ai-service /bin/sh -lc 'python - <<PY
from urllib.request import urlopen
print(urlopen("http://127.0.0.1:8000/internal/health", timeout=5).read().decode())
PY'
```

mock 剪辑闭环验证：

```bash
scripts/render_editor_sample.sh
```

默认使用 `PROFILE=smoke`，输出到脚本 smoke 目录：

```txt
ai-service/output/plans/editor-sample.editing-package.json
ai-service/output/renders/editor-sample.native.final.mp4
```

IM 产品链路的最终输出不走上述 smoke 目录，而是：

```txt
~/Documents/CapCutAI/Workspaces/<workspaceId>/artifacts/renders/
```

常用 profile：

```bash
PROFILE=smoke scripts/render_editor_sample.sh
PROFILE=draft scripts/render_editor_sample.sh
PROFILE=1080p scripts/render_editor_sample.sh
```

已有 Editor 导出的 `*.editing-package.json` 时，可直接运行 native render：

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

如果需要生成 HyperFrames bundle：

```bash
BUILD_HYPERFRAMES=1 scripts/render_editor_sample.sh
```

如果需要继续尝试 HyperFrames render：

```bash
RENDER_HYPERFRAMES=1 PROFILE=1080p scripts/render_editor_sample.sh
```

HyperFrames 主要用于：

- 标题卡
- 复杂字幕动效
- 贴纸 / callout
- 品牌包装层
- agent 生成式 HTML/CSS 视觉层

## 常见排障

- `API key 无效`：先分别检查 `AI4VIDEO_VL_API_KEY`、`AI4VIDEO_OMNI_API_KEY` 或 `config.local.py`。
- `ffprobe 不可用`：检查容器或本机是否有 `ffmpeg` / `ffprobe`。
- “已经分析完成但找不到产物”：检查当前 workspace 的 `assets/template/elastic_template.json`；source 缓存目录不能作为完成依据。
- “成片路径在 ai-service/output/im-runs”：这是内部缓存路径，最终交付应在 workspace `artifacts/renders/`。
