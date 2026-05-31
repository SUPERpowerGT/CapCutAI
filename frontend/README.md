# Frontend

这里是 CapCutAI 的客户端界面层。

当前口径：

```txt
Desktop-first
一套 frontend
Tauri 是默认运行壳
Web 只用于开发 / 调试
```

前端这层要特别区分：

```txt
Client UI != Local Tool Runtime
```

也就是说：

- 前端负责 workspace 交互、状态展示、结果预览
- 前端不直接承载复杂剪辑逻辑
- 本地剪辑能力应该通过稳定接口接到本地 Agent / Tool Runtime

## 这层负责什么

- 左侧 `Assets`
- 中间 `Editor`
  - `Preview`
  - `Timeline`
- 右侧 `Agent Panel`
- 整个桌面工作台布局
- 收集当前窗口级 workspace facts
- 展示任务进度、artifact 摘要、最终视频预览

前端现在不是聊天网页，而是桌面工作台。

## 现在怎么跑

推荐桌面开发版：

```bash
cd frontend
source "$HOME/.cargo/env"
npm run desktop:dev
```

浏览器调试版：

```bash
cd frontend
npm run dev
```

打包桌面客户端：

```bash
cd frontend
source "$HOME/.cargo/env"
npm run desktop:build
```

如果 `npm run desktop:dev` 报：

```txt
listen EPERM: operation not permitted 127.0.0.1:3001
```

通常是当前终端环境不允许本地监听端口。先在普通本地终端里单独执行：

```bash
npm run desktop:web-dev
```

确认能看到 `Local: http://127.0.0.1:3001`，再回到 `npm run desktop:dev`。

## 当前心智

```txt
一个窗口 = 一个 workspace
不是一个窗口 = 一个 chat session
```

也就是说：

- 左侧素材
- 中间预览 / 时间轴
- 右侧 agent 对话

都应该围绕同一个 `workspace` 工作。

`Window -> New Window` 的语义是：

- 新建一个新的 workspace
- 打开一个新的工作窗口

## 当前目录

```txt
src/
  app/                  页面入口与 Next 代理路由
  features/
    workspace/          工作台壳子、分栏、workspace 上下文
    assets/             左侧素材面板
    editor/             中间预览与时间轴
    im/                 右侧 Agent Panel
    hyperframes/        后续编辑能力预留
  server/               当前开发代理工具
  shared/               前端共享设计 token / 通用类型
```

## 模块边界

### `workspace`

负责：

- 固定三栏布局
- 左右 / 上下分栏
- workspace 上下文
- 桌面窗口级行为接入

不要放：

- 具体上传逻辑
- IM 请求逻辑
- HyperFrames 业务逻辑

### `assets`

负责：

- 主素材导入入口
- 当前素材选择
- 素材元数据展示
- 后续目录 / 上传 / 搜索 / 删除

### `editor`

负责：

- 本地视频预览
- 时间轴区域
- 后续 HyperFrames 接入点

### `im`

负责：

- Agent 对话流
- 输入框
- activity / 状态反馈
- 与 backend IM 接口对接

## 当前几个关键原则

1. 素材导入主入口在左侧 `Assets`
2. 右侧是 `Agent Panel`，不是聊天软件
3. 前端弱化 `session UI`，强化 `workspace`
4. 新功能默认按桌面客户端能力设计
5. UI 不直接做剪辑决策，UI 展示的是 Agent Runtime 和 Tool Runtime 的执行结果

## 当前适配层

为了后面本地 / 云端切换更顺，现在已经有几层抽象：

- `AssetPickerGateway`
- `AssetUploadGateway`
- `IM transport`
  - `proxy`
  - `direct`

这意味着：

- UI 主体只维护一套
- 差异尽量落在底层 adapter / gateway
- 后面可以把本地素材导入、本地工具调用、云端同步分别挂到独立适配层

## 继续看哪里

- 总入口：[`../README.md`](../README.md)
- 启动：[`../docs/90-getting-started/README.md`](../docs/90-getting-started/README.md)
- 桌面路线：[`../docs/04-detailed-design/07-desktop-client-design/README.md`](../docs/04-detailed-design/07-desktop-client-design/README.md)
- Assets：[`./src/features/assets/README.md`](./src/features/assets/README.md)
- IM：[`../docs/04-detailed-design/08-agent-panel-im-design/README.md`](../docs/04-detailed-design/08-agent-panel-im-design/README.md)
