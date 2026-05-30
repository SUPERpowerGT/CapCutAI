# Assets Feature

这里预留给资源模块同学。

当前默认心智不是“给 Web 页面补一个上传区”，而是：

```txt
给桌面客户端工作台实现左侧 Assets 面板
```

所以这里后续所有新增能力，都优先按客户端工作流设计；浏览器模式只保留开发调试价值。

后续职责：

- 素材上传
- 素材删除
- 素材分类与搜索
- 素材元数据展示
- 与后端资源模块的接口对接
- 左侧 `Assets Sidebar` 的真实实现

当前左侧边栏已经从 `im` 模块拆出来了，真正的资源业务不要继续写回 `im` 或 `workspace`。

当前已经先落了一层桌面友好的边界：

- 左侧 `Assets` 是主上传入口
- 当前浏览器开发模式下先通过本地文件选择器拿到参考视频和源视频
- 代码上已经有 `AssetPickerGateway` 抽象
- 当前也已经补上 `AssetUploadGateway` 抽象
- 本地模式下先走 `localAssetUploadGateway`

也就是说，后续如果切到桌面客户端，不应该重写左侧 UI，而是优先替换底层 picker 能力：

- 当前：`browserAssetPickerGateway`
- 未来：`desktopAssetPickerGateway`

而后续如果切到云端资产系统，不应该重写左侧 UI，而是优先替换 upload/register 能力：

- 当前：`localAssetUploadGateway`
- 未来：`cloudAssetUploadGateway`

另外当前已经明确一条协作原则：

- 左侧 `Assets` 负责文件选择和当前资产选择
- 当前选中的 `Reference / Source` 会提升到工作台层
- 当前工作上下文应该主要在左侧 `Assets` 里可见
- 右侧 `Agent Panel` 不再镜像展示这组资产卡片，只负责任务输入和结果反馈
