# IM Optimization

这里记录右侧 `Agent Panel` 的优化方向。

当前前提已经固定：

```txt
右侧不是聊天软件
右侧是 Agent 工作面板
```

## 当前原则

- 后端可以继续保留 conversation
- 前端不强调 `session` UI
- 当前窗口只围绕一个 workspace 工作
- 素材导入主入口在左侧 `Assets`
- 右侧只负责：
  - 意图输入
  - 状态反馈
  - 结果展示
  - 后续 revision 指令

## 当前已经完成

- 用户消息即时插入
- assistant 流式出现
- 中文输入法组合输入不再误发送
- activity item 结构已接入
- session UI 已弱化
- `Window -> New Window` 开始承接新工作上下文

## 后面优先级

### P0

- 继续优化流式反馈视觉
- 明确 tool / subagent / system event 的 activity 展示
- 让错误反馈更自然

### P1

- 当前任务上下文提示
- revision 指令心智
- 更完整的消息类型扩展

### P2

- 与时间轴 / 渲染产物更深地绑定
- 对具体计划、版本、产物做引用

## 一句话方向

右侧最终应该更像：

```txt
Agent Console
```

而不是：

```txt
IM Chat App
```
