# Editor Feature

这里是中间剪辑区域的前端边界。

当前职责：

- 上方 `Preview`
- 下方 `Timeline`
- Source Video 本地预览
- Source Video metadata / 素材信息预览
- mock editing experience 摘要展示
- agent timeline / HyperFrames job 草案预览
- 导出 agent handoff package

当前阶段不要在这里实现 IM 会话逻辑，也不要把资源管理逻辑混进来。

## 当前不做

当前不做用户手动多轨剪辑交互。

也就是说，第一版先不实现：

- split
- trim
- drag
- ripple edit
- track item editing

这些后面等 agent 生成和 HyperFrames 渲染链路跑通后再补。

## 当前导出

当前 `Export Job` 导出的是 JSON package，不是最终 mp4。

这份 package 包含：

- source assets
- source materials
- editing experience
- timeline plan
- editing job
- render result

后续由 agent / Codex / Cursor 根据 package 生成 HyperFrames composition 并渲染 mp4。
