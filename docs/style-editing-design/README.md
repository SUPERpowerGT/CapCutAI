# Style Editing Design

这份文档只讲一件事：

```txt
用户视频自动套风格链到底怎么设计
```

它不负责参考视频风格分析本身，也不负责后面的 IM 修订。

## 目标

输入：

- 用户视频
- 固定或检索到的 `style_profile`
- 用户 prompt

输出：

- `timeline_plan.json`
- `editing_job.json`
- `final.mp4`

也就是说，这条链的目的不是只给一个文字建议，而是：

```txt
把用户视频变成一个可执行的剪辑计划，并最终导出成片
```

## 这条链要回答什么问题

1. 用户至少要提供哪些输入，系统才能剪得动
2. 哪些输入可以从视频本身自动分析出来
3. planner 和 editing skills 之间怎么交接

## 推荐流程

```txt
User Video
  -> Input Normalizer
  -> Video Analyzer
  -> Style Retriever
  -> Director Planner
  -> Editing Skills
  -> outputs/plans/timeline_plan.json
  -> outputs/plans/editing_job.json
  -> outputs/renders/final.mp4
```

## 节点设计

### 1. Input Normalizer

负责整理用户显式输入：

- 用户 prompt
- 目标风格
- 额外素材
- 目标平台
- 成片时长偏好

### 2. Video Analyzer

负责从用户视频里抽基础信息：

- 时长
- 分辨率
- fps
- 音轨情况
- 镜头粗分段
- 可用画面节奏信息

### 3. Style Retriever

第一版先很简单：

- 直接命中 `one_last_kiss_style.json`

后面再演进成真正的风格检索器。

### 4. Director Planner

负责生成结构化 `timeline_plan.json`。

这一层是最核心的规划层。

### 5. Editing Skills

负责把 `timeline_plan.json` 转成更接近执行的 `editing_job.json`，
再交给后续真正的视频执行层输出最终视频。

## 协议预设

这条链至少要约定清楚三类结构。

### A. `editing_input`

更偏“系统输入”：

```json
{
  "userVideo": {},
  "videoMetadata": {},
  "editingGoal": "",
  "targetStyleId": "",
  "audioPreferences": {},
  "subtitlePreferences": {},
  "overlayPreferences": {},
  "extraAssets": [],
  "targetDurationSec": 0,
  "targetPlatform": ""
}
```

### B. `timeline_plan.json`

更偏“规划结果”：

```json
{
  "timelineId": "",
  "styleId": "",
  "tracks": [],
  "subtitlePlan": {},
  "audioPlan": {},
  "overlayPlan": {}
}
```

### C. `editing_job.json`

更偏“执行结果描述”：

```json
{
  "jobId": "",
  "timelineId": "",
  "operations": [],
  "renderHints": {}
}
```

## 第一版必须有的输入字段

第一版建议最少保证这些字段：

- `userVideo`
- `videoMetadata`
- `editingGoal`
- `targetStyleId`
- `subtitlePreferences`
- `audioPreferences`
- `targetDurationSec`

如果这些字段缺得太多，后面的自动剪辑就会建立在猜测上。

## 第一版必须有的输出字段

### `timeline_plan.json`

至少要能表达：

- 片段顺序
- 片段时长
- 字幕计划
- 音频计划
- 叠加元素计划

### `editing_job.json`

至少要能表达：

- 哪些片段要裁切
- 哪些字幕要生成
- 哪些字体 / 贴图 / 图片要叠加
- 哪些音频操作要执行

## 第一版输入输出目录约定

建议直接固定：

- 用户视频输入：
  - `ai-service/input/uservideo/`
- 规划输出：
  - `ai-service/output/plans/`
- 成片输出：
  - `ai-service/output/renders/`

文件名建议：

- `user_video.timeline_plan.json`
- `user_video.editing_job.json`
- `user_video.final.mp4`

## 和前一条链的关系

这条链高度依赖：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

所以判断它做得好不好，不是只看能不能生成一个 plan，而是看：

```txt
这个 plan 是否真的建立在前面沉淀出来的风格资产之上
```

也正因为如此，风格分析链和用户剪辑链必须同步推进。
