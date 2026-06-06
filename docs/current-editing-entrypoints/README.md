# Current Editing Entrypoints

记录时间：

```txt
2026-05-31 22:05:00 CST
```

这份文档不是最终 README 改稿。

它的目的只有一个：

```txt
把当前我们已经做出来的剪辑器 / agent handoff / HyperFrames 相关入口
和对应的启动方式整理清楚
```

你确认口径没问题之后，再决定怎么合到仓库正式 README。

## 当前项目主口径

这份文档沿用仓库当前主口径：

```txt
Desktop-first
Local-first
Cloud-ready
```

也就是说：

- 产品主形态是桌面客户端
- `frontend` 只有一套代码
- `Tauri` 是默认运行壳
- 浏览器模式只保留开发 / 调试价值

## 这次改动主要加了什么

当前和剪辑器、多源测试、HyperFrames handoff 直接相关的改动，主要分成 4 块。

### 1. 前端 Editor 多源预览与导出

现在前端支持：

- 上传多个 `Source Video`
- 在中间 `Preview` 预览当前选中的视频
- 在 `Timeline` 区显示 agent draft timeline 摘要
- 点击 `Export Job` 导出 `*.editing-package.json`

相关入口：

- [`../../frontend/src/features/assets/components/AssetsSidebar.tsx`](../../frontend/src/features/assets/components/AssetsSidebar.tsx)
- [`../../frontend/src/features/editor/components/EditorSurface.tsx`](../../frontend/src/features/editor/components/EditorSurface.tsx)
- [`../../frontend/src/features/editor/components/PreviewViewport.tsx`](../../frontend/src/features/editor/components/PreviewViewport.tsx)
- [`../../frontend/src/features/editor/components/TimelinePanel.tsx`](../../frontend/src/features/editor/components/TimelinePanel.tsx)

### 2. 多源 mock `sourceMaterial` 测试池

现在前端和后续测试工具都默认可以消费：

```txt
data/test_case/<case_id>/
```

每个 case 里当前至少可以用到：

- `step1_audio.json`
- `step2_transcript.json`
- `step3_visual.json`
- `elastic_template.json`
- 原视频 `MP4`
- `keyframes/`

前端 mock 数据入口：

- [`../../frontend/src/features/editor/data/mock-source-material.ts`](../../frontend/src/features/editor/data/mock-source-material.ts)
- [`../../frontend/src/features/editor/data/mock-editing-experience.ts`](../../frontend/src/features/editor/data/mock-editing-experience.ts)

### 3. Editor export package -> HyperFrames draft bundle

现在 `ai-service` 里已经有一个本地工具，可以把前端导出的 package 转成 HyperFrames draft bundle。

入口：

- [`../../ai-service/app/tools/build_hyperframes_draft.py`](../../ai-service/app/tools/build_hyperframes_draft.py)
- [`../../ai-service/app/services/hyperframes_service.py`](../../ai-service/app/services/hyperframes_service.py)

生成目录里当前会包含：

- `composition.draft.json`
- `timeline-plan.json`
- `editing-job.json`
- `render-result.json`
- `preview.html`
- `index.html`
- `assets/`

### 4. `data/test_case` -> package 的测试工具

为了不必每次都先去前端上传视频、再手动点导出，现在还补了一个测试工具：

- [`../../ai-service/app/tools/build_test_case_package.py`](../../ai-service/app/tools/build_test_case_package.py)

它可以直接从：

```txt
data/test_case/<case_id>/
```

生成一份标准的：

```txt
*.editing-package.json
```

## 当前几个“业务入口”

如果从“业务链路”而不是“技术栈目录”看，当前最重要的入口有 6 个。

### 入口 1：桌面客户端工作台

作用：

- 上传 `Source Video`
- 看 Preview
- 看 Timeline draft
- 导出 `editing-package.json`

启动方式：

```bash
cd frontend
source "$HOME/.cargo/env"
npm run desktop:dev
```

桌面开发模式地址：

- `http://127.0.0.1:3001`

说明：

- 这是当前推荐入口
- 适合看工作台交互、上传素材、导出 package
- 当前不适合拿它直接验证最终渲染 mp4

### 入口 2：浏览器调试版前端

作用：

- 只调页面
- 不走桌面壳

启动方式：

```bash
cd frontend
npm run dev
```

地址：

- `http://127.0.0.1:3000`

说明：

- 只建议前端开发 / 调试时使用
- 不是产品主入口

### 入口 3：从 `data/test_case` 直接生成 package

作用：

- 跳过前端上传
- 直接拿 mock 测试数据构建 agent handoff package

命令示例：

```bash
cd ai-service
python3 -m app.tools.build_test_case_package \
  --cases 7c8980565c6eb03ecfc916cef2c3671d 27daab568829a31941b9eb1a0ce6502d 3b5ffa605eee8e7e5ace9365a48386d7 \
  --workspace-id workspace_test_case \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/plans/test-case.editing-package.json
```

如果只做 smoke test，可以再加：

```bash
--max-video-clips-per-case 1
--smoke-duration-ms 6000
```

说明：

- 这是当前验证 agent / tool / planner 输入最直接的入口
- 不依赖前端手动导出

### 入口 4：从 package 生成 HyperFrames draft bundle

作用：

- 把 `editing-package.json` 转成 HyperFrames composition draft 目录

命令示例：

```bash
cd ai-service
python3 -m app.tools.build_hyperframes_draft \
  --package /Users/chengjinshi/CapCutAI/ai-service/output/plans/test-case.editing-package.json \
  --output-dir /Users/chengjinshi/CapCutAI/ai-service/output/plans/test-case-render.hyperframes
```

说明：

- 这是当前把 agent handoff package 接到 HyperFrames 的中间入口
- 适合确认：
  - timeline 是否生成了 scene
  - 是否吃到了真实源视频
  - render 尺寸是否按源比例缩放

### 入口 5：渲染 HyperFrames bundle

作用：

- 让 HyperFrames 真正尝试输出 mp4

命令示例：

本地模式：

```bash
cd ai-service
python3 -m app.tools.render_hyperframes_bundle \
  --bundle-dir /Users/chengjinshi/CapCutAI/ai-service/output/plans/test-case-render.hyperframes \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/renders/test-case-render.final.mp4 \
  --quality draft
```

Docker 模式：

```bash
cd ai-service
python3 -m app.tools.render_hyperframes_bundle \
  --bundle-dir /Users/chengjinshi/CapCutAI/ai-service/output/plans/test-case-render.hyperframes \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/renders/test-case-render.final.mp4 \
  --quality draft \
  --docker
```

说明：

- 当前本地模式已经能真正调用 HyperFrames CLI 并输出 MP4
- HyperFrames composition 必须注册合法 timeline contract，不能用 `{}` 占位
- Docker 模式入口保留，但不是当前默认推荐路径
- Docker 更适合作为后续预构建 renderer image / CI runner，而不是每次本地临时 build

### 入口 6：Native 主轨渲染

作用：

- 直接读取 `editing-package.json`
- 使用 ffmpeg 渲染 video 主轨、原声和基础字幕
- 输出用于闭环验证的 draft mp4

命令示例：

```bash
cd ai-service
python3 -m app.tools.render_native_video \
  --package /Users/chengjinshi/CapCutAI/ai-service/output/plans/test-case.editing-package.json \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/renders/test-case-native.final.mp4 \
  --max-long-side 640 \
  --max-duration-ms 12000 \
  --audio-mode source \
  --burn-subtitles \
  --preset veryfast \
  --crf 28
```

说明：

- 这是当前更推荐的闭环测试出口
- 当前支持 video 主轨、源视频原声和 ASS 字幕烧录
- macOS 上安装 `ffmpeg-full` 后会自动优先使用 `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`
- HyperFrames 仍然保留给后续复杂字幕动效、包装、overlay composition

## 当前启动 / 部署逻辑

### A. 启动完整本地服务链

在项目根目录：

```bash
ollama serve
make up
```

可选自检：

```bash
make smoke
```

作用：

- 起 backend
- 起 ai-service
- 起 postgres
- 起其它本地依赖

适合：

- 开桌面客户端
- 跑完整工作台
- 联调 IM / backend / ai-service

### B. 只跑前端桌面工作台

在 `frontend/`：

```bash
source "$HOME/.cargo/env"
npm run desktop:dev
```

适合：

- 素材上传预览
- Timeline draft UI 调整
- 导出 package

### C. 只跑 ai-service 工具链

如果这次只是验证：

```txt
data/test_case -> editing-package -> hyperframes bundle -> render
```

那么不需要先起完整桌面工作台。

直接在 `ai-service/` 跑这几个脚本就行：

1. `build_test_case_package`
2. `build_hyperframes_draft`
3. `render_hyperframes_bundle`

这条路径更适合纯工具链测试。

### D. 一条命令验证剪辑工具链

如果只想验证：

```txt
data/test_case -> editing-package -> native render -> mp4
```

在项目根目录：

```bash
scripts/render_editor_sample.sh
```

默认输出：

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

如果要额外生成 HyperFrames bundle：

```bash
BUILD_HYPERFRAMES=1 scripts/render_editor_sample.sh
```

如果要继续尝试 HyperFrames render：

```bash
RENDER_HYPERFRAMES=1 PROFILE=1080p scripts/render_editor_sample.sh
```

说明：

- 这条脚本默认不依赖 Docker
- 默认走本机 ffmpeg native render
- 默认使用 `PROFILE=smoke`
- HyperFrames render 需要 Node.js 22+ 和 Chrome

## 当前推荐验证顺序

如果你现在要复现我们这次改动，推荐顺序是：

1. 先看桌面端能否正常上传多个 `Source Video`
2. 先确认 `Export Job` 能正常导出 package
3. 再用 `build_test_case_package` 直接生成一份标准测试 package
4. 再用 `build_hyperframes_draft` 生成 bundle
5. 最后再尝试 `render_hyperframes_bundle`

这样更容易快速分辨问题是在：

- 前端上传
- package 导出
- draft 生成
- 还是最终 render

## 当前已经确认通了什么

目前已经明确打通的部分：

- 多 `Source Video` 上传与预览
- Timeline draft 摘要展示
- `Export Job` 导出 `editing-package.json`
- `data/test_case` -> `editing-package.json`
- `editing-package.json` -> HyperFrames draft bundle
- draft bundle 中优先使用真实 `MP4` 作为主画面素材
- render 尺寸默认跟随源视频比例，而不是固定 `9:16`

## 当前还没完全稳定的部分

### 1. HyperFrames render 性能

此前遇到的错误：

```txt
t.capturedTimeline.pause is not a function
Cannot access 'he' before initialization
```

已经定位为 composition 注册了非法 timeline：

```js
window.__timelines["main"] = {};
```

修复为最小 paused timeline contract 后，HyperFrames 本地 render 已经可以输出真实视频 MP4。

当前剩余问题不是“跑不通”，而是：

- 1080p 真实视频全量主轨逐帧 render 明显慢于 ffmpeg
- 32s / 1080p 样片 HyperFrames render 耗时约 4m
- 因此 HyperFrames 仍建议用于复杂包装层、字幕动效、短时 overlay，而不是默认主轨导出器

### 2. HyperFrames Docker render

当前 `--docker` 入口已经接好，但它内部仍会触发自己的 `docker build`。

这一步目前可能碰到：

- Docker Hub 元数据鉴权
- Debian apt 源连接超时
- build 阶段下载依赖慢

也就是说，Docker 路径更适合作为后续固定 renderer image，而不是当前默认快速启动路径。

## 当前 smoke test 入口

当前最轻量的 smoke test 逻辑是：

- `1 case`
- `1 video clip`
- `6s`
- `360p`
- 保持源视频比例

对应命令：

```bash
cd ai-service
python3 -m app.tools.build_test_case_package \
  --cases 7c8980565c6eb03ecfc916cef2c3671d \
  --workspace-id workspace_smoke \
  --max-video-clips-per-case 1 \
  --smoke-duration-ms 6000 \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/plans/smoke-test.editing-package.json

python3 -m app.tools.build_hyperframes_draft \
  --package /Users/chengjinshi/CapCutAI/ai-service/output/plans/smoke-test.editing-package.json \
  --output-dir /Users/chengjinshi/CapCutAI/ai-service/output/plans/smoke-test.hyperframes
```

然后再尝试：

```bash
python3 -m app.tools.render_hyperframes_bundle \
  --bundle-dir /Users/chengjinshi/CapCutAI/ai-service/output/plans/smoke-test.hyperframes \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/renders/smoke-test.final.mp4
```

或：

```bash
python3 -m app.tools.render_hyperframes_bundle \
  --bundle-dir /Users/chengjinshi/CapCutAI/ai-service/output/plans/smoke-test.hyperframes \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/renders/smoke-test-docker.final.mp4 \
  --docker
```

## 你可以考虑并入正式 README 的内容

如果后面要把这份文档里的内容合进主 README，我建议优先合这几块：

1. 当前新增的 3 个 `ai-service` 工具入口
2. `data/test_case` 的测试链路入口
3. HyperFrames 当前状态说明
4. smoke test 推荐命令

不建议一口气把所有细节都塞进主 README。

更适合的做法是：

- 主 README 只放高层入口和最短命令
- 细节保留在这份文档或视频工作流文档里

## 相关文档

- [`../editor-preview-export/README.md`](../editor-preview-export/README.md)
- [`../agent-editing-tools/README.md`](../agent-editing-tools/README.md)
- [`../hyperframes-draft-builder/README.md`](../hyperframes-draft-builder/README.md)
- [`../source-material-handoff/README.md`](../source-material-handoff/README.md)
- [`../editor-mvp-change-summary/README.md`](../editor-mvp-change-summary/README.md)
