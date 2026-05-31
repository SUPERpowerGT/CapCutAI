# Assets Feature

这里是左侧 `Assets` 面板。

当前定位很简单：

```txt
桌面客户端里的主素材导入入口
```

不是给网页随便补一个素材入口。

## 这块负责什么

- 本地素材选择
- 当前素材显示
- 后续素材导入、删除、搜索、分类
- 当前 workspace 下的素材上下文

## 当前原则

1. 素材导入主入口在左侧
2. 右侧 `Agent` 不重复展示素材卡片
3. UI 主体保持一套
4. 本地 / 云端差异放在 gateway

## 当前已经有的抽象

- `AssetPickerGateway`
  - 负责选文件
- `AssetUploadGateway`
  - 负责登记 / 上传资产

当前本地实现：

- `browserAssetPickerGateway`
- `localAssetUploadGateway`

后面桌面版和云端版替换的应该是这层，不是重写整个左侧 UI。

## 当前工作方式

- 用户在左侧选视频
- 当前选中资产提升到工作台层
- 中间 `Preview` 读当前资产做本地预览
- 右侧 `Agent` 只负责发任务指令

## 继续看哪里

- 前端主文档：[`../../../README.md`](../../../README.md)
- 客户端路线：[`../../../../docs/desktop-client-plan/README.md`](../../../../docs/desktop-client-plan/README.md)
