# Render Pipeline Restructure

记录时间：

```txt
2026-06-06 17:26:26 CST
```

这份文档记录当前视频导出链路的重构方案和已经落地的第一步实现。

当前目标不是一次性做出生产级剪辑引擎，而是先让 `data/test_case` 的 mock 多源输入可以走一条更稳定、更接近剪辑软件的本地导出链路。

## 背景

之前链路是：

```txt
editing-package.json
  -> HyperFrames draft bundle
  -> HyperFrames render
  -> final.mp4
```

这条链路可以表达 agent 生成式 composition，但它把完整主视频轨也交给浏览器逐帧采集，实际运行会比较慢，也在本地环境里出现过稳定性问题。

剪映、必剪这类工具虽然也是本地导出，但它们通常使用原生媒体管线：

```txt
source video
  -> decoder / cache / proxy
  -> native timeline compositor
  -> hardware/software encoder
  -> final.mp4
```

所以当前重构方向是：

```txt
主视频剪辑 / 拼接 / 硬切 / 原声 / 基础字幕
  -> ffmpeg native render

复杂字幕样式 / 标题 / 贴纸 / 包装 / agent composition
  -> HyperFrames overlay render
```

## 新链路

第一阶段采用 hybrid render：

```txt
data/test_case
  -> editing-package.json
  -> native main-track render
  -> draft mp4
```

后续再扩展成：

```txt
data/test_case
  -> editing-package.json
  -> native main-track render
  -> HyperFrames overlay render
  -> final mp4
```

## 职责划分

### Native main-track render

负责：

- 多源视频片段截取
- 主视频轨拼接
- 硬切
- 等比缩放
- 原声保留或静音
- ASS 字幕烧录
- draft / smoke 输出

当前实现入口：

- [`../../ai-service/app/tools/render_native_video.py`](../../ai-service/app/tools/render_native_video.py)
- [`../../ai-service/app/services/native_render_service.py`](../../ai-service/app/services/native_render_service.py)

当前第一版已经支持视频主轨、源视频原声和基础字幕烧录。

### HyperFrames composition

负责：

- agent 生成的包装层
- 更复杂的字幕样式
- 标题 / 贴纸 / overlay
- 后续更复杂的 HTML/CSS/JS composition

当前保留入口：

- [`../../ai-service/app/tools/build_hyperframes_draft.py`](../../ai-service/app/tools/build_hyperframes_draft.py)
- [`../../ai-service/app/tools/render_hyperframes_bundle.py`](../../ai-service/app/tools/render_hyperframes_bundle.py)
- [`../../ai-service/app/services/hyperframes_service.py`](../../ai-service/app/services/hyperframes_service.py)

## 当前可运行入口

### 1. 生成测试 package

```bash
cd /Users/chengjinshi/CapCutAI/ai-service
python3 -m app.tools.build_test_case_package \
  --cases 7c8980565c6eb03ecfc916cef2c3671d 27daab568829a31941b9eb1a0ce6502d 3b5ffa605eee8e7e5ace9365a48386d7 \
  --workspace-id workspace_native_smoke \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/plans/native-smoke.editing-package.json \
  --max-video-clips-per-case 1 \
  --smoke-duration-ms 6000
```

### 2. 走 native 主轨渲染

```bash
cd /Users/chengjinshi/CapCutAI/ai-service
python3 -m app.tools.render_native_video \
  --package /Users/chengjinshi/CapCutAI/ai-service/output/plans/native-smoke.editing-package.json \
  --output /Users/chengjinshi/CapCutAI/ai-service/output/renders/native-smoke.final.mp4 \
  --max-long-side 640 \
  --max-duration-ms 12000 \
  --audio-mode source \
  --burn-subtitles \
  --preset veryfast \
  --crf 28
```

输出：

```txt
ai-service/output/renders/native-smoke.final.mp4
ai-service/output/renders/native-smoke.final.render-result.json
```

macOS 上如果安装了 `ffmpeg-full`，工具会自动优先使用：

```txt
/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
```

也可以显式指定：

```bash
--ffmpeg-bin /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
```

## 为什么这条链路更可行

### 1. 主视频轨回到媒体工具

主轨剪辑本质上是视频解码、截取、拼接、编码。ffmpeg 比浏览器 DOM 采帧更适合这件事。

### 2. HyperFrames 不再承担最重的部分

HyperFrames 更适合 agent 生成的可视化包装层，不适合第一阶段直接承担很多原视频片段的主轨拼接。

### 3. 保留现有 package contract

新的 native render 直接读取现有 `*.editing-package.json`，不要求前端和 planner 重新换协议。

### 4. 先 smoke，再扩展

第一版支持 `--max-clips`、`--max-duration-ms`、`--max-long-side`，方便先跑短视频闭环，再逐步放大测试规模。

## 当前能力

- 渲染 video 主轨
- 支持源视频原声或静音
- 支持把 subtitle track 生成 ASS 并烧录到视频
- 支持按源视频比例等比缩放
- 支持 smoke duration / clip count 限制

## 当前限制

- 暂时不混入外部 BGM
- 暂时不做转场
- 多素材会按 timeline 顺序硬切拼接
- 输出尺寸默认根据第一个源视频等比缩放

这些限制是有意保守的。我们先保证“真实视频进入、真实视频出来、速度可接受”，再把字幕、音频、包装层逐步加回去。

## 后续迭代建议

1. 增加 proxy media cache
   - `source video -> low-res proxy`
   - draft render 只吃 proxy
   - final render 回源视频

2. 增加音频轨
   - 第一版可直接保留源视频原声
   - 后续再支持 BGM、ducking、人声优先

3. 增强字幕系统
   - 当前基础字幕使用 ffmpeg `subtitles` / ASS
   - 复杂字幕动效再交给 HyperFrames overlay

4. 增加 overlay 合成层
   - 先 native main-track render
   - 再 HyperFrames 生成透明 overlay 或完整包装层
   - 最后用 ffmpeg 合成

5. 增加 render profile
   - `smoke`: 360p / veryfast / short duration
   - `draft`: 720p / veryfast / proxy
   - `final`: source ratio / higher quality / full timeline

## 当前结论

短期内，可行闭环应该是：

```txt
source_material + editing_experience
  -> timeline_plan
  -> editing-package
  -> ffmpeg native render
  -> draft mp4
```

HyperFrames 继续保留，但职责调整为 agent composition 和包装层，而不是第一阶段的完整主视频导出器。

## 2026-06-06 Agent 样片验证记录

记录时间：

```txt
2026-06-06 19:17:36 CST
```

本次以 agent 视角使用 `data/test_case` 中的多源 mock analyzer 数据，生成了一版样片 package 和 native render 输出。

### 输入

选取 5 个 source video case：

```txt
7c8980565c6eb03ecfc916cef2c3671d
dccaba4a4318a998f481ada83ac4f300
69ead07c5604ccf49e0ef54177553003
3c3541d128e859fd70eb789b98a1106a
cd2ddb06976a5f7afad7e2626e41813b
```

agent 根据经验文档和 analyzer mock 数据组织为：

```txt
PHASE_HOOK
PHASE_PROBLEM
PHASE_SOLUTION
PHASE_CTA
```

### 产物

生成 package：

```txt
ai-service/output/plans/agent-sample.editing-package.json
```

生成 native 1080p base video：

```txt
ai-service/output/renders/agent-sample-1080-base.mp4
```

验证信息：

```txt
duration: 32.333333s
video: H.264 1920x1080
audio: AAC 48000Hz stereo
size: 24,013,602 bytes
```

同时生成 HyperFrames bundle：

```txt
ai-service/output/plans/agent-sample-1080-hyperframes
```

HyperFrames bundle 已通过：

```bash
npx --yes hyperframes lint ai-service/output/plans/agent-sample-1080-hyperframes
```

结果：

```txt
0 errors, 0 warnings
```

### HyperFrames 渲染观察

此前观察到的问题已经进一步定位。

此前无真实视频素材的 HyperFrames composition 已经可用。今天尝试的是“包含真实 source video 的 1080p composition render”，这个场景在本机 Chrome capture 阶段出现过：

```txt
Cannot access 'he' before initialization
t.capturedTimeline.pause is not a function
```

根因不是本机 Mac、Chrome、ffmpeg 或视频素材不可用，而是生成的 composition 为了通过 timeline registry 校验写了：

```js
window.__timelines["main"] = {};
```

HyperFrames 要求 `window.__timelines[compositionId]` 是一个可被 runtime 控制的 paused timeline，至少需要提供 `pause / play / seek / totalTime / time / duration` 等方法。空对象可以让部分静态校验通过，但 render 阶段调用 `pause()` 时会失败。

已经排除的点：

- Node 已切到 `v22.22.3`
- HyperFrames CLI 为 `0.6.76`
- `hyperframes doctor` 全部通过
- ffmpeg / ffprobe 为 `8.1`
- Chrome 可被 HyperFrames 识别
- Docker daemon 可用
- bundle lint 为 0 error / 0 warning
- base video 已重新编码为 30fps / keyframe interval 30

修复方式：

```txt
ai-service/app/services/hyperframes_service.py
```

新增 `_build_empty_timeline_script()`，在没有 GSAP 动效的 composition 中注册一个最小 paused timeline contract，而不是注册空对象。

修复后验证：

```txt
lint: 0 errors, 0 warnings
snapshot: 5 frames captured
render: completed
```

HyperFrames 成功输出：

```txt
ai-service/output/renders/agent-sample-1080-hyperframes-fixed.final.mp4
ai-service/output/renders/agent-sample-1080-hyperframes-fixed.render-result.json
```

输出信息：

```txt
duration: 32.354362s
video: H.264 1920x1080 30fps
audio: AAC 48000Hz stereo
size: 25,635,024 bytes
render time: 4m 4.7s
```

Docker render 尝试没有进入实际渲染阶段，失败在镜像构建时无法连接 Debian apt 源：

```txt
Could not connect to deb.debian.org:80
Docker image build failed
```

因此当前结论是：

- agent 到 package 的剪辑决策链路可走通
- ffmpeg native 1080p MP4 导出可走通
- HyperFrames bundle 生成和 lint 可走通
- 带真实 source video 的 HyperFrames 本机 render 已可走通，但 1080p 全量主轨逐帧渲染耗时明显高于 ffmpeg native render
- HyperFrames 不适合作为第一阶段主视频轨的默认导出器，更适合作为包装层、复杂视觉层或短时 overlay renderer

### 下一步建议

短期交付仍以 ffmpeg native render 作为真实视频闭环。

HyperFrames 继续用于：

- 标题卡
- 复杂字幕样式
- 包装层
- 贴纸和强调层
- agent 生成的 HTML/CSS visual composition

当需要再次验证 HyperFrames 真实视频 render 时，建议先准备可复现环境：

- Node 22+
- HyperFrames 固定版本
- 可访问 Debian apt 源的 Docker build 环境
- 或预构建好的 HyperFrames renderer image

本机环境推荐：

```txt
macOS Apple Silicon
Node.js 22+
HyperFrames 0.6.76
Google Chrome 148+
ffmpeg / ffprobe 8.1
16GB+ memory
```

如果追求更稳定的 HyperFrames render 环境，建议使用预构建 Docker renderer image 或 CI runner，避免每次临时构建镜像时受 Debian apt 源网络影响。
