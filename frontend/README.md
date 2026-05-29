# Frontend

这里是 CapCutAI 的前端工程。

当前前端不是“所有东西都堆在一个页面里”，而是按未来桌面客户端工作台来设计：

- `workspace`
- `im`
- `assets`
- `editor`
- `hyperframes`

当前 `workspace` 是最外层固定壳子，`im` 是真实主线，另外两块先保留边界，不在这里乱写假逻辑。

当前产品形态原则：

- 当前阶段先做桌面工作台风格的 Web App
- 后续目标是封装成 PC 客户端
- 所以前端现在就要按桌面软件边界来组织
- 不是按普通网页聊天工具的思路来设计右侧 `IM`

## 当前主线

frontend 当前首页是一个固定工作台：

- 左边 `Assets`
- 中间 `Editor`
- 中间上 `Preview`
- 中间下 `Timeline`
- 右边 `Chat`

这些区域都内嵌在固定 shell 里，后续会向 PC 客户端形态演进，并支持像 VS Code 一样拖动分栏。

当前真正接了后端链路的只有 `Chat / IM` 部分。

当前推荐职责边界：

- 左侧 `Assets`
  - 主上传入口
  - 管参考视频、用户视频、图片、音频等素材
- 中间 `Editor`
  - 管预览和时间轴
  - 后续接 HyperFrames 或其他编辑能力
- 右侧 `Agent`
  - 管意图输入
  - 管任务状态
  - 管分析 / 生成 / revision 指令

明确原则：

```txt
上传主入口在左侧 Assets，不在右侧输入框。
```

## 目录结构

```txt
src/
  app/
    api/im/...                Next route handlers，代理到 backend
    layout.tsx
    page.tsx                  页面入口，只组装主工作台
  features/
    workspace/                最外层固定工作台壳子
    im/                       当前真实主线
      api/                    IM 请求客户端
      components/             IM 展示组件
      hooks/                  IM 状态编排
      lib/                    IM 内部格式化和小工具
      types/                  IM 协议类型
    assets/                   资源模块预留边界
    editor/                   中间剪辑区域边界
    hyperframes/              HyperFrames 集成预留边界
  server/
    backend-proxy.ts          服务端代理工具
```

工程目录里只应该有一个当前有效的 `.next/` 构建缓存。

- `.next/` 是 Next 当前运行或构建产物
- `.next_stale_*` 属于旧缓存，应该直接清掉
- `node_modules/`、`.next/` 都不是源码结构的一部分

## 团队分工约定

### `workspace`

最外层固定桌面工作台。

职责：

- 固定 `assets / editor / chat` 三栏
- 固定中间 `preview / timeline` 上下两块
- 管拖拽分栏
- 以后适配 PC 客户端壳子

这里不要写：

- IM 请求逻辑
- 资源上传逻辑
- HyperFrames 具体编辑逻辑

### `im`

由你负责，当前已经落地。

职责：

- agent panel
- message feed
- input box
- 与 backend 的 IM 接口对接

注意：

- 后端继续保留 conversation 机制
- 前端不强调 `session` 概念
- 右侧默认只展示“当前工作对话”

不要在 `im` 里继续塞：

- HyperFrames 编辑器逻辑
- 资源上传 / 删除 / 搜索逻辑

### `assets`

由资源模块同学负责。

职责：

- 素材上传
- 素材删除
- 素材分类 / 搜索 / 元数据
- 对接 backend 资源接口

### `hyperframes`

由 HyperFrames 同学负责。

职责：

- 接入 HyperFrames 前端编辑能力
- 管理 HyperFrames 相关状态
- 和 IM / assets 通过清晰接口协作

## 当前开发规则

### 页面入口

[`src/app/page.tsx`](./src/app/page.tsx) 只做页面装配，不写业务细节。

### Feature 模块规则

- `features/workspace` 只负责外层布局与分栏
- `features/editor` 只负责中间编辑区域壳子

- `features/im/api` 只放请求函数
- `features/im/components` 只放展示组件
- `features/im/hooks` 只放状态和交互编排
- `features/im/types` 只放协议类型

### Next 代理规则

前端不要直接从浏览器跨域打 backend，统一先走：

- `/api/im/conversations`
- `/api/im/conversations/{conversationId}/messages`

服务端代理逻辑统一放在：

- [`src/server/backend-proxy.ts`](./src/server/backend-proxy.ts)

## 本地运行

先确保 backend / ai-service / postgres 已经启动：

```bash
make up
make smoke
```

然后在 `frontend/` 里：

```bash
npm run dev
```

前端默认本地地址：

```txt
http://127.0.0.1:3000
```

默认 backend 地址来自：

```txt
NEXT_PUBLIC_BACKEND_BASE_URL
```

当前默认值：

```txt
http://127.0.0.1:38080
```

## 最小自检

页面起来后，至少确认这几件事：

1. 左侧能看到 `Assets` 占位面板
2. 右侧能看到干净的 `Agent` 面板
3. 点击 `New` 能开始新一轮对话
4. 发消息后，用户消息会立刻出现
5. 随后出现 assistant 回复

## 如何新增前端功能

### 新增 IM 功能

按现有 `im` 结构继续扩展：

1. `types/` 先补协议类型
2. `api/` 再补请求函数
3. `hooks/` 编排状态
4. `components/` 只负责展示

### 新增资源功能

直接落在 `features/assets/`，不要回写 `features/im/`。

### 新增编辑器功能

中间预览、时间轴、HyperFrames 接入相关能力，优先落在 `features/editor/` 或 `features/hyperframes/`，不要写进 `workspace`。

### 新增 HyperFrames 功能

直接落在 `features/hyperframes/`，不要把编辑器逻辑塞进 IM 页面组件。

## 当前明确不做

- 不在 frontend 里重写一套自研时间轴
- 不把资源模块硬塞进 IM hook
- 不把 HyperFrames 状态直接写进对话组件
- 不把外层工作台拖拽状态和具体业务状态混在一起

## 参考文档

- [`../README.md`](../README.md)
- [`../backend/README.md`](../backend/README.md)
- [`../ai-service/README.md`](../ai-service/README.md)
- [`../docs/im-optimization/README.md`](../docs/im-optimization/README.md)
