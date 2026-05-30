# Desktop Client Plan

这里整理 CapCutAI 当前的桌面客户端落地方案。

## 结论

CapCutAI 的产品主形态现在已经定为：

```txt
Desktop-first
```

不是以 Web 版为最终交付的产品。

原因很直接：

- 本地视频 / 图片 / 音频上传
- 本地项目目录
- 本地输出目录
- 中间产物管理
- 左中右工作台
- 长时间作为真实工具使用

这些都更符合桌面客户端，而不是普通网页产品。

## 技术路线

推荐路线：

```txt
现有前端继续作为客户端界面层
Tauri 作为默认桌面壳
backend + ai-service 保留为本地/服务能力层
```

也就是说：

- `frontend` 继续负责界面
- `Tauri` 负责默认运行壳、本地窗口和文件系统入口
- `backend` / `ai-service` 继续负责消息、agent、流程和产物

这一套的核心原则是：

```txt
一套 frontend
Desktop 作为默认运行形态
Web 只保留开发 / 调试入口
```

当前推荐的真实落地方向不是：

```txt
只做纯本地玩具客户端
```

而是：

```txt
Local-first
Cloud-ready
```

也就是：

- 当前先保证本地可用
- 后续如果 backend / ai-service / database 上云，客户端可以平滑切换

## 多窗口心智

桌面客户端后续更合理的设计不是：

```txt
一个窗口 = 一个 chat session
```

而是：

```txt
一个窗口 = 一个 workspace / project 上下文
```

更具体一点：

```txt
Window
  -> Workspace / Project
    -> Assets
    -> Conversation
    -> Timeline / Output
```

这意味着：

- 窗口主绑定的是当前工作空间或项目
- conversation 只是这个项目里的一个子对象
- 左侧素材、右侧 agent、中间时间轴和输出结果，都应该围绕同一个上下文工作

因此当前界面上的 `New` 更合理的第一阶段语义应该是：

```txt
创建新的 workspace / project 上下文
```

而不是“继续堆新的聊天 session”。

当前继续往前推进后，默认入口不应该再是右侧按钮，而是：

```txt
Window -> New Window
```

也就是由桌面客户端窗口菜单新开一个全新的工作上下文窗口。

这样后面才更合理地支持：

- 多窗口并行处理不同视频项目
- 每个窗口有独立的参考视频 / 源视频 / 输出目录
- revision 指令始终绑定当前项目，而不是漂浮在全局 chat 里

所以当前开始预留的关系应该是：

- `project_id`
- `conversation_id`
- `asset_id`
- `timeline_id`
- `render_task_id`

其中：

- 窗口一级语义应当逐步落到 `project_id`
- `conversation_id` 跟着 `project_id` 走
- 后端虽然还保留 conversation 机制，但前端不应该把窗口语义继续理解成“多 session 聊天器”

## 为什么选 Tauri

推荐优先 `Tauri`，不优先 `Electron`。

原因：

- 更轻
- 更适合本地工具
- 对 macOS 支持明确
- 很适合“现有前端 + 本地桌面壳”的模式

官方文档明确：

- Tauri v2 支持 `macOS`
- Tauri 使用 Rust，开发前需要安装 Rust
- Next.js 集成推荐使用静态导出

Sources:
- https://v2.tauri.app/start/prerequisites/
- https://v2.tauri.app/start/frontend/nextjs/

## 当前现实状态

现在这套仓库已经补上了第一版 `Tauri` 桌面壳，并且已经成功打出：

- `CapCutAI.app`
- `CapCutAI_0.1.0_aarch64.dmg`

当前产物位置：

- [`../../frontend/src-tauri/target/release/bundle/macos/CapCutAI.app`](../../frontend/src-tauri/target/release/bundle/macos/CapCutAI.app)
- [`../../frontend/src-tauri/target/release/bundle/dmg/CapCutAI_0.1.0_aarch64.dmg`](../../frontend/src-tauri/target/release/bundle/dmg/CapCutAI_0.1.0_aarch64.dmg)

不过这不代表桌面化已经彻底做完，当前还存在几个重要现实点：

### 当前 frontend 仍然保留 Web 开发辅助能力

Tauri 官方对 Next.js 的建议是：

- 使用 `output: 'export'`
- 使用 `out/` 作为打包前端产物

但你们当前前端里还有：

- Next route handlers
  - `/api/im/conversations`
  - `/api/im/conversations/{conversationId}/messages`

当前对应实现文件就是：

- [`../../frontend/src/server/backend-proxy.ts`](../../frontend/src/server/backend-proxy.ts)
- [`../../frontend/src/app/api/im/conversations/route.ts`](../../frontend/src/app/api/im/conversations/route.ts)
- [`../../frontend/src/app/api/im/conversations/[conversationId]/route.ts`](../../frontend/src/app/api/im/conversations/[conversationId]/route.ts)
- [`../../frontend/src/app/api/im/conversations/[conversationId]/messages/route.ts`](../../frontend/src/app/api/im/conversations/[conversationId]/messages/route.ts)

这意味着当前前端仍然保留 Next 的服务端能力，浏览器开发模式下仍可使用代理链。

所以当前桌面构建不是“完全不做适配就直接打包”，而是：

- 桌面构建时临时禁用 `app/api`
- 强制走 `NEXT_PUBLIC_IM_TRANSPORT=direct`
- 导出 `out/`
- 再由 `Tauri` 打包

也就是说，当前已经能出客户端，但后续仍然应该继续把：

- Next 代理层
- 纯 UI 层
- 桌面文件能力

拆得更干净。

### 现在不是两套前端

当前不是：

```txt
一套 Web UI + 一套 Desktop UI
```

而是：

```txt
一套 frontend
  -> npm run dev           浏览器开发入口
  -> npm run desktop:dev   客户端开发入口
  -> npm run desktop:build 客户端打包入口
```

所以后续默认做法应该是：

- 新功能先按客户端心智设计
- 浏览器模式只用于开发调试
- 不再把“网页版完整体验”当独立目标维护

## Local-first / Cloud-ready 原则

当前应该明确采用下面这条原则：

```txt
本地先跑通，云端预备役先留好切换点
```

这意味着当前不追求：

- 立刻把服务端全部云化
- 立刻补完整登录系统
- 立刻补生产级对象存储

但必须从现在开始预留：

1. 客户端不要写死只能连本地服务
2. 文件选择能力和文件上传能力要分开
3. `backend / ai-service / db` 以后可以整体迁到云上
4. 前端 transport 要能在本地直连和云端直连之间切换

## 后续上云时最核心的切换点

如果后续要变成：

```txt
用户下载桌面客户端
客户端直接连云端 backend / ai-service / db
```

当前最重要的预留点就是这几个：

### 1. IM transport

当前已经有：

- `proxy`
- `direct`

后续上云时，客户端应该继续走：

```txt
direct
```

只是把：

```txt
NEXT_PUBLIC_BACKEND_BASE_URL
```

从本地地址切到云端地址。

### 2. Assets picker 和 upload 分层

当前已经有：

- `AssetPickerGateway`
- `AssetUploadGateway`

它们分别负责：

- `AssetPickerGateway`
  - 选文件
- `AssetUploadGateway`
  - 登记 / 上传资产

后续真正上云时，应该新增的是：

- `cloudAssetUploadGateway`

它负责“把本地选中的文件上传到云端资产系统”。

这样就不会把：

- 选文件
- 上传文件
- 保存 asset id

三件事混死在一个 UI 组件里。

### 3. provider 配置

当前本地默认：

- `OLLAMA`

后续上云时：

- 客户端不应该再依赖用户本机 `ollama`
- `ai-service` 应该在云端接模型 provider

也就是说：

```txt
本地阶段：client -> local backend/ai-service -> local/provider
云端阶段：client -> cloud backend/ai-service -> cloud/provider
```

客户端 UI 不应该因为这个切换而重写。

### 4. 项目 / 产物目录

当前本地阶段：

- 可以有本地项目目录
- 可以有本地输出目录

后续上云阶段：

- 最终结果和中间产物可能会进入对象存储
- 但客户端依然可以保留“本地工作目录”体验

所以从现在开始就要避免把：

- 本地目录路径
- 云端文件 URL

混成同一种字段。

## 正确的迁移策略

不是立刻重写，而是按下面顺序推进。

### Phase 1. 正式确立 Desktop-first

先统一共识：

- 产品交付形态是桌面客户端
- Web 只保留开发调试价值
- 以后前端所有交互都按桌面工作台心智来设计

这个阶段现在已经完成：

- `Assets / Editor / Agent` 三块边界
- 右侧 `Agent Panel`
- 左侧 `Assets` 作为主上传入口
- `Tauri` 桌面壳与 `.app/.dmg` 打包

### Phase 2. 为 Tauri 做前端准备

目标不是立刻打包，而是让当前前端更适合被 Tauri 包。

这一步建议做：

1. 把前端里的服务端代理能力和纯 UI 分开
2. 明确哪些接口：
   - 继续走 backend
   - 哪些以后会走桌面文件能力
3. 把文件选择、输出目录这些能力抽象出来

这一步现在已经开始落地：

- `IM` 请求层支持 `proxy / direct` 双 transport
- 当前浏览器开发默认还是 `proxy`
- 后续桌面迁移时，可以先切到 `direct`
- 左侧 `Assets` 已经开始通过 `AssetPickerGateway` 抽象本地文件选择能力
- 当前浏览器模式使用 `browserAssetPickerGateway`
- 后续桌面模式可以直接替换为 `desktopAssetPickerGateway`

最先要拆的就是当前这条代理链：

```txt
im-client -> Next route handlers -> backend-proxy -> backend
```

后续桌面客户端里更合理的方向是：

```txt
im-client -> backend
assets file actions -> desktop shell file APIs
```

对应的前端配置入口会是：

```txt
NEXT_PUBLIC_IM_TRANSPORT=direct
NEXT_PUBLIC_BACKEND_BASE_URL=http://127.0.0.1:38080
```

### Phase 3. 补桌面前置环境

需要准备：

1. 安装 Rust
2. 确认 macOS 开发依赖
3. 决定是否本地安装 `tauri` CLI

这一步现在已经完成：

- Rust 已安装
- `@tauri-apps/cli` 已安装
- `src-tauri/` 已生成

### Phase 4. 搭最小 Tauri 壳

第一版桌面壳只做：

- 能在 macOS 上打开当前工作台
- 能加载现有前端界面
- 不急着马上接完全部本地文件系统能力

这一步现在也已经完成。

当前相关文件：

- [`../../frontend/src-tauri/tauri.conf.json`](../../frontend/src-tauri/tauri.conf.json)
- [`../../frontend/src-tauri/src/main.rs`](../../frontend/src-tauri/src/main.rs)
- [`../../frontend/src-tauri/src/lib.rs`](../../frontend/src-tauri/src/lib.rs)
- [`../../frontend/scripts/build-desktop.mjs`](../../frontend/scripts/build-desktop.mjs)

### Phase 5. 接本地能力

这一步才开始真正体现客户端价值：

- 选择本地素材文件
- 选择项目目录
- 设置输出目录
- 打开本地导出结果

### Phase 6. 为上云保留平滑切换能力

这一步现在不用全做完，但必须从今天开始按这个原则设计：

1. 客户端只依赖配置，不依赖“必须是 localhost”
2. backend / ai-service 地址随环境切换
3. picker 和 upload 分层
4. 本地 provider 和云端 provider 分层
5. 本地目录语义和云端资产语义分层

## 对当前前端的直接影响

当前前端已经在往正确方向走，但后面需要继续坚持这些原则：

### 1. `Assets` 是主上传入口

不要把上传主流程塞回右侧输入框。

客户端里：

- 左侧 `Assets`
  - 上传文件
  - 管本地素材
- 右侧 `Agent`
  - 只管意图和任务控制

### 2. `Agent Panel` 不等于聊天工具

客户端里右侧应该更像：

- 任务控制台
- 工作流输出流
- revision 指令入口

而不是普通聊天软件。

### 3. 文件系统能力要和 UI 解耦

后面一定会出现两类能力：

- 浏览器开发模式下的文件选择
- 客户端模式下的本地路径和目录选择

所以现在就不要把文件上传逻辑写死成浏览器-only。

## 对当前 backend / ai-service 的直接影响

桌面客户端不会推翻现在的 backend / ai-service。

反而更合理的关系是：

- `frontend desktop shell`
  - 本地 UI
  - 本地文件能力
- `backend`
  - conversation / message / orchestration
- `ai-service`
  - LangGraph / agent / video pipeline

也就是说：

```txt
客户端负责人机交互和本地文件
backend + ai-service 负责业务和智能链路
```

## 当前最值得做的下一步

按价值排序，我建议：

1. 保持当前前端继续往桌面工作台方向收口
2. 明确前端哪些能力未来要切到桌面文件系统
3. 把 picker / upload / project directory 的职责彻底拆开
4. 保持客户端默认可本地运行
5. 同时为云端地址、云端上传、云端 provider 保留切换点

## 当前不建议做的事

- 现在就推倒现有前端
- 现在就为了 Tauri 把 backend / ai-service 改乱
- 现在就追求完整安装器或分发流程
- 现在就把所有上传逻辑从 Web 直接迁成桌面 API

## 一句话总结

CapCutAI 应该是：

```txt
桌面客户端产品
Web 技术栈界面
Tauri 桌面壳
backend + ai-service 业务与 agent 链路
```

当前最稳的做法不是“立刻重写成客户端”，而是：

```txt
先把前端继续按桌面工作台收好
再补 Rust / Tauri 壳
再接本地文件能力
```
