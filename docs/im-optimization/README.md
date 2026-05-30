# IM Optimization

这里整理 CapCutAI 当前 `IM` 工作台的优化路线。

目标不是一次把聊天区做成最终态，而是先把最影响真实使用感的部分收顺，再为后续视频分析、自动剪辑、对话修订预留结构。

## 当前定位

当前 `IM` 不是普通聊天窗口，而是未来的视频编辑控制台。

当前前端原则：

- 后端保留 conversation 机制
- 前端不强调 `session` 概念
- 默认只展示一个当前工作会话
- `New` 代表开始新一轮，不代表让用户管理一排 session

当前产品形态原则：

- 当前阶段按桌面工作台风格的 Web App 推进
- 后续目标是封装为 PC 客户端
- 所以右侧 `IM` 不是网页聊天框，而是工作台里的 `Agent Panel`
- 上传、素材、任务、输出都要按桌面工作流来理解

后续它会承担三类入口：

- 生成视频
- 修改已经剪辑好的视频
- 查看 agent 当前正在执行的阶段

所以优化方向要围绕：

- 对话体验自然
- 状态感明确
- 会话管理顺手
- 后续能承载视频上下文

## 和整体工作台的职责边界

当前推荐边界是：

- 左侧 `Assets`
  - 作为主上传入口
  - 管参考视频、用户视频、图片、音频等素材
- 中间 `Editor`
  - 管预览和时间轴
  - 后续接 HyperFrames 或其他编辑能力
- 右侧 `Agent Panel`
  - 只负责意图输入、任务状态、结果反馈、后续 revision 指令

这里有一个明确原则：

```txt
上传主入口放左侧 Assets，不放在右侧输入框里。
```

原因是：

- 上传属于素材管理，不属于对话行为
- 右侧输入框应该专注表达意图
- 未来 PC 客户端里，左侧素材区会越来越重，右侧则应该保持轻量控制台语义

这也意味着一条具体 UI 原则：

```txt
Reference / Source 的可见上下文放在左侧 Assets
右侧 Agent 不重复镜像这组资产卡片
```

## 当前已经具备

- 会话创建
- 用户消息即时插入
- assistant 回复展示
- 输入框 `Enter` 发送、`Shift + Enter` 换行
- backend + ai-service 全链路打通

## 优先级

### P0 必做

这些会直接影响当前 demo 和真实使用感。

1. assistant 流式回复
- 不要等整段返回后一次出现
- 先有占位，再逐步补全

2. agent 状态显示
- 至少支持：
  - `idle`
  - `thinking`
  - `planning`
  - `editing`
  - `failed`

3. 隐式会话体验
- 不让 session 管理抢右侧空间
- 用户只感知当前工作对话
- 后端继续保留 conversation 以支撑状态与历史

4. 消息错误定位
- 失败时不只在顶部显示错误
- 要能明确反馈到当前消息发送动作

5. Activity Item 结构
- 对话流里的状态反馈不要只靠布尔值硬编码
- 当前处理、tool 调用、subagent 步骤、system event 都应该统一走 `activity item`
- 这样后面接工具和子代理时，不需要重新设计一套渲染逻辑

### P1 应做

这些不一定第一时间做，但会很快影响后续开发体验。

1. 当前上下文头部
- 后面优先显示当前视频 / 当前版本 / 当前任务
- 不优先显示 session 标题

2. 输入框自动增高
- 短消息不占太高
- 长消息自然扩展

3. 更明确的空态
- 空会话时提示当前可以做什么
- 比如上传视频、描述风格、要求修改

4. 消息类型扩展
- 不只保留纯文本消息
- 预留：
  - `system_event`
  - `upload_event`
  - `plan_summary`
  - `render_result`
  - `revision_result`

### P2 后做

这些更接近后续正式产品形态。

1. 当前上下文头部
- 当前视频
- 当前 style profile
- 当前 timeline version

2. revision 历史感知
- 对话不只是聊天记录
- 还要和某次剪辑版本绑定

3. 可引用产物
- 消息里引用：
  - `materials.json`
  - `timeline_plan.json`
  - `final.mp4`

## 推荐实现顺序

1. 先做 assistant 流式回复
2. 再做 agent 状态显示
3. 再做当前任务上下文头部
4. 再做输入框自动增高
5. 再为消息类型扩展补 schema
6. 最后接上下文头部

## 前端落点建议

### `features/im/components`

适合放：

- `ConversationList`
- `MessageFeed`
- `ChatComposer`
- `ChatStatusBar`
- `ConversationRenameInput`

### `features/im/hooks`

适合放：

- 会话切换逻辑
- optimistic message
- 删除会话后的自动跳转
- 流式回复编排
- 错误恢复

### `features/im/types`

适合放：

- `Conversation`
- `Message`
- `MessageRole`
- `MessageType`
- `AgentStatus`
- `AgentActivityItem`

### `features/im/api`

适合放：

- conversation CRUD
- message send / list
- 后续 streaming 或 SSE 接口

### Activity 渲染原则

对话流里未来会出现的不只是 assistant 文本，还会有：

- 当前处理中
- tool 调用中
- subagent 执行中
- system event
- revision 执行结果

所以代码上应该保持：

```txt
message = 用户 / assistant 的正文内容
activity item = 状态、工具、子代理、系统事件
```

这两类对象不要混成一个 `Message`。

## 和后续视频能力的关系

IM 优化不能只站在“聊天 UI”的角度做。

后续它需要自然承接：

- 用户上传自己的视频后说：
  - “帮我做成 One Last Kiss 风格”
- 用户看完成片后继续说：
  - “前半段节奏快一点”
  - “字幕改成更细的字体”
  - “封面加一张图片”

所以现在的优化应该尽量避免把 `IM` 写死成普通问答窗口。

更准确地说：

```txt
右侧 = Agent Console / Agent Panel
不是 Chat App
```

## 当前建议

如果只做一项最值钱的优化：

先做：

```txt
流式回复 + agent 状态显示
```

因为这两项最能让当前 `IM` 从“能用”变成“像一个真的 AI 工作台”。
