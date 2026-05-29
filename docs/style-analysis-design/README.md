# Style Analysis Design

这份文档只讲一件事：

```txt
参考视频分析链到底怎么设计
```

它不负责用户视频自动剪辑，也不负责 IM 修订。

## 目标

输入一个参考风格视频，例如：

- `ai-service/input/stylizationvideo/onelastkiss.mp4`

输出一套后面可以复用的结构化风格资产：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

也就是说，这条链的目的不是只给一句“这个视频很唯美”的总结，而是：

```txt
把爆款视频拆成后面 planner 和 editing skills 真能用的结构
```

## 这条链要回答什么问题

1. 这个风格到底由哪些维度构成
2. 哪些维度是后面自动剪辑必须依赖的
3. 哪些分析结果只是展示价值，不能进入自动流程

## 推荐流程

```txt
Reference Video
  -> Metadata Extractor
  -> Material Analyzer
  -> Style Summarizer
  -> Style Structurer
  -> outputs/materials.json
  -> outputs/style_profile.json
  -> outputs/editing_rules.json
```

## 节点设计

### 1. Metadata Extractor

负责先抽最基础的视频客观信息：

- 时长
- 分辨率
- fps
- 是否有音轨
- 编码信息

输出建议字段：

```json
{
  "durationSec": 0,
  "width": 0,
  "height": 0,
  "fps": 0,
  "hasAudio": true
}
```

### 2. Material Analyzer

负责分析“素材层面”的结构：

- 粗粒度镜头段落
- 是否出现字幕
- 是否有贴图 / 图片 / 装饰元素
- 是否有明显标题帧 / 结尾帧
- 音乐与音效使用方式

输出建议文件：

- `materials.json`

### 3. Style Summarizer

负责生成高层风格总结：

- 节奏感
- 色调
- 氛围
- 字幕感觉
- 字体风格
- 音乐风格

这一层更接近“语义总结”。

### 4. Style Structurer

负责把上面的总结和分析沉淀成真正可复用规则：

- `style_profile.json`
- `editing_rules.json`

这一层才是后面 `Style Retriever / Director Planner` 真正会消费的部分。

## 协议预设

这条链至少要约定清楚三类结构。

### A. `materials.json`

更偏“观察结果”：

```json
{
  "videoMetadata": {},
  "segments": [],
  "subtitlePresence": {},
  "audioProfile": {},
  "visualOverlays": []
}
```

### B. `style_profile.json`

更偏“风格画像”：

```json
{
  "styleId": "one_last_kiss",
  "styleName": "One Last Kiss",
  "paceProfile": {},
  "subtitleStyle": {},
  "fontStyle": {},
  "colorMood": {},
  "musicMood": {},
  "overlayStyle": {}
}
```

### C. `editing_rules.json`

更偏“可执行规则”：

```json
{
  "shotRules": [],
  "transitionRules": [],
  "subtitleRules": [],
  "audioRules": [],
  "overlayRules": []
}
```

## 第一版必须有的字段

第一版建议最少保证这些字段：

### `materials.json`

- `videoMetadata`
- `segments`
- `subtitlePresence`
- `audioProfile`

### `style_profile.json`

- `styleId`
- `paceProfile`
- `subtitleStyle`
- `fontStyle`
- `colorMood`
- `musicMood`

### `editing_rules.json`

- `subtitleRules`
- `audioRules`
- `transitionRules`
- `overlayRules`

## 第一版输出目录约定

建议直接固定：

- 输入：
  - `ai-service/input/stylizationvideo/`
- 输出：
  - `ai-service/output/materials/`

文件名建议：

- `one_last_kiss.materials.json`
- `one_last_kiss.style_profile.json`
- `one_last_kiss.editing_rules.json`

## 和后续链路的关系

这条链后面主要服务：

- `Style Retriever`
- `Director Planner`
- `Style Editing`

所以判断它做得好不好，不是看“分析写得像不像论文”，而是看：

```txt
后面的自动剪辑链能不能真实消费这些结构
```
