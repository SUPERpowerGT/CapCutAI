# Desktop Client Plan

这份文档只回答一件事：

```txt
CapCutAI 为什么默认按桌面客户端做，以及现在怎么落
```

## 结论

CapCutAI 当前主形态是：

```txt
Desktop-first
```

不是把 Web 版当最终产品。

原因很直接：

- 本地视频 / 图片 / 音频
- 本地 workspace / 项目目录
- 本地输出目录
- 左中右工作台
- 长时间作为真实工具使用

这些都更符合桌面客户端。

## 技术路线

当前路线：

```txt
frontend 继续做界面层
Tauri 作为默认桌面壳
backend + ai-service 保留服务能力
Local Tool Runtime 承接本地媒体能力
```

一句话：

```txt
一套 frontend
Desktop 是默认运行形态
Web 只用于开发 / 调试
```

再严格一点，当前推荐的桌面架构是：

```txt
Desktop Client
  -> Local Agent Runtime
  -> Local Tool Runtime
  -> Local Workspace File System
  -> Cloud / Local LLM
```

## 当前窗口心智

现在已经明确：

```txt
一个窗口 = 一个 workspace
不是一个窗口 = 一个 chat session
```

更完整一点：

```txt
Window
  -> Workspace
    -> Assets
    -> Conversation
    -> Timeline / Output
```

所以：

- `Window -> New Window` = 新建一个新的 workspace 窗口
- conversation 只是 workspace 里的子对象

## Workspace 生命周期

当前推荐体验：

1. 第一次打开 App
   - 自动创建默认 workspace
2. 再次打开 App
   - 恢复上次 workspace
3. `Window -> New Window`
   - 创建新的 workspace 并打开新窗口
4. `File -> Open Workspace...`
   - 作为高级入口，打开已有 workspace

## Workspace 目录结构

推荐第一版：

```txt
<workspace-folder>/
  workspace.json
  assets/
    reference/
    source/
    images/
    audio/
  artifacts/
    materials/
    plans/
    renders/
  cache/
  logs/
```

当前语义：

- workspace 本地生命周期归客户端
- conversation / message 归 backend
- 智能编排归本地 Agent Runtime
- 媒体分析、渲染、导出归本地 Tool Runtime

## 当前已经完成到哪

当前已经有：

- Tauri 桌面壳
- `desktop:dev`
- `desktop:build`
- `.app` 产物
- workspace 基础恢复逻辑
- `Window -> New Window` 新 workspace 逻辑

当前还没有完全做完的：

- `File -> Open Workspace...`
- 最近 workspace 列表
- 全量桌面文件系统接入
- 完整的项目目录管理

## 当前策略

当前推荐一直按这个原则推进：

```txt
Local-first
Cloud-ready
```

也就是：

- 当前先保证本地可用
- 后续 backend / ai-service / database 上云时，客户端平滑切换
- 但默认不把完整原始视频上传到云端做主流程处理
