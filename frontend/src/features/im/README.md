# IM Feature

这里是当前前端主线模块。

职责：

- 对话会话列表
- 消息流
- 输入框
- agent trace 展示
- 任务状态和 activity 展示
- 调用 `backend` 的 IM API

当前约定：

- `api/` 只放 IM 请求客户端
- `components/` 只放 IM 展示组件
- `hooks/` 只放 IM 页面状态编排
- `types/` 只放 IM 协议类型

当前 `im` 不再负责整个页面壳子，它只负责右侧 `Agent Panel` 区域内容。最外层固定工作台由 `features/workspace` 负责。

不要在这里直接实现：

- HyperFrames 编辑器集成
- 素材导入业务逻辑
- 与 IM 无关的通用工作台逻辑
