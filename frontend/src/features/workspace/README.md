# Workspace Feature

这里是前端最外层固定工作台壳子。

职责：

- 固定桌面客户端式布局
- 左 / 中 / 右 三大区域分栏
- 中间上 / 下 预览与时间轴分栏
- 拖拽调整 pane 尺寸
- 为后续 PC 客户端封装保留稳定外层结构

这里不负责具体业务数据实现：

- IM 对话逻辑在 `features/im`
- 资源逻辑在 `features/assets`
- 编辑器 / HyperFrames 接口在 `features/editor` 与 `features/hyperframes`
