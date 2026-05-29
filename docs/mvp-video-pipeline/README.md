# MVP Video Pipeline

这份文档定义 CapCutAI 当前与后续视频能力的主线。

目标不是一次把所有功能做完，而是先把路线讲清楚，避免后面：

- `IM`
- `agent`
- `backend`
- `素材 / 视频`
- `编辑执行`

几条线各自长偏。

## 总体目标

CapCutAI 后面不只是一个聊天工具，而是一个：

```txt
参考视频分析 + 用户视频自动生成 + IM 对话式修订
```

的 AI 视频编辑系统。

## 一个关键前提

当前阶段不能把问题简单理解成：

- 先只做爆款分析
或
- 先只做用户视频自动剪辑

更准确的推进方式是：

```txt
参考视频分析链 和 用户视频剪辑链 要同步往前走
```

原因很简单：

- 只分析爆款视频，无法证明这些分析结果到底够不够支撑后面的自动剪辑
- 只做用户视频自动剪辑，又不知道前面到底应该从参考视频里沉淀出哪些结构化风格规则

所以当前最重要的问题其实是：

```txt
系统到底需要哪些输入，才能把视频剪好
系统又必须产出哪些结构化中间结果，后面的 planner 和 editing skills 才能继续工作
```

这意味着：

- 风格分析链要帮我们定义 `style_profile` 应该长什么样
- 用户剪辑链要帮我们定义 `editing input` 至少应该包含什么

这两边必须同步收敛。

如果要看两条链的具体设计，请继续看：

- [`../style-analysis-design/README.md`](../style-analysis-design/README.md)
- [`../style-editing-design/README.md`](../style-editing-design/README.md)

## 三条主链路

### 1. 参考视频分析链

目标：

- 用户上传爆款视频
- agent 分析并拆解视频风格
- 产出一套可复用的结构化风格规则

输入：

- `reference_video`

输出：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

分析维度至少包括：

- 节奏
- 镜头组织
- 转场规律
- 字幕样式
- 字体与排版
- 音乐 / 音效使用方式
- 图片 / 贴纸 / 装饰元素
- 整体剪辑策略

这一条链的意义是：

```txt
把“爆款视频经验”沉淀成后面可以复用的 style profile
```

同时它还承担一个更底层的任务：

```txt
反推出 Style Analysis Output Schema 到底需要哪些字段
```

也就是：

- 哪些风格字段是必须有的
- 哪些只是可选增强项
- 哪些分析结果后面其实喂不进 planner

### 2. 用户视频自动套风格链

目标：

- 用户上传自己的视频
- agent 结合既有 style profile
- 自动生成同风格成片

输入：

- `user_video`
- `style_profile`

输出：

- `timeline_plan.json`
- `editing_job`
- `final.mp4`

执行内容会涉及：

- 视频剪辑
- 音频处理
- 字幕生成
- 字幕排版
- 帧上叠加风格化字体
- 图片 / 贴纸 / 装饰元素叠加

这一条链的意义是：

```txt
把结构化风格规则应用到用户自己的视频上
```

同时它也承担另一个关键任务：

```txt
反推出 User Editing Input Schema 到底至少需要哪些输入
```

例如后面很可能会逐步收敛这些输入字段：

- 原始视频文件
- 视频时长 / fps / 分辨率
- 是否保留原声
- 是否允许自动配乐
- 是否需要自动字幕
- 是否允许叠加图片 / 贴图 / 风格化字体
- 是否有额外图片素材
- 是否有额外音频素材
- 最终成片时长目标
- 目标平台

### 3. IM 对话式修订链

目标：

- 用户看到初版成片后
- 继续通过 IM 自然语言修改
- agent 基于现有 timeline 做增量修订

典型指令：

- “前半段节奏再快一点”
- “字幕字体换细一点”
- “结尾音乐安静一点”
- “片尾再加一句字幕”
- “封面加一张图片”

输入：

- `conversation`
- `current_timeline_version`
- `style_profile`
- `materials`

输出：

- `timeline_version_v2 / v3 / ...`
- 新的 `editing_job`
- 新的 `final.mp4`

这一条链的意义是：

```txt
让 IM 不只是入口，而是后续视频修订控制台
```

## MVP 分阶段建议

### MVP Phase 1

第一版只做最小闭环：

- 只支持固定风格：`One Last Kiss`
- 用户上传视频
- 用户输入：
  - `帮我做成 One Last Kiss 风格`
- 系统执行：
  1. Material Analyzer
  2. Style Retriever
  3. Director Planner
  4. Editing Skills
  5. 输出 `final.mp4`

这里的风格文件先固定成：

- `one_last_kiss_style.json`

这时不需要多风格系统，不需要复杂风格检索平台。

但这里的“最小闭环”不应该被误解成“只做其中一边”。

更准确地说，Phase 1 要同步推进两件事：

1. 用 `One Last Kiss` 参考视频，收敛风格分析输出结构
2. 用用户视频，收敛剪辑链真正需要的输入结构

也就是说，Phase 1 的真正目标是：

```txt
一边做风格分析，一边做用户视频套风格，并用它们一起收敛输入输出契约
```

### MVP Phase 2

再加参考视频分析链：

- 上传爆款视频
- 自动输出 `style_profile`
- 让 `One Last Kiss` 不再只是手工配置，而是可分析、可沉淀、可复用

### MVP Phase 3

最后再加 IM 修订链：

- 用户在生成后继续通过聊天做 revision
- agent 根据已有 timeline 做增量修改

## MVP Phase 1 详细闭环

当前最小闭环定义如下：

1. 用户上传视频
2. 用户输入：
   - `帮我做成 One Last Kiss 风格`
3. Material Analyzer
   - 输出 `materials.json`
4. Style Retriever
   - 命中 `one_last_kiss_style.json`
5. Director Planner
   - 生成 `timeline_plan.json`
6. Editing Skills
   - 执行 `timeline plan`
7. 输出：
   - `final.mp4`

### 这条闭环背后真正要验证什么

除了“能跑通”之外，Phase 1 更重要的是验证下面两件事：

#### A. Style Analysis Output 是否足够

也就是：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

这些结构化结果，到底能不能支撑后面的 planner

#### B. User Editing Input 是否足够

也就是：

- 用户现在提供的输入
- 系统自己从用户视频里分析出的输入

加起来到底够不够让后面的 editing pipeline 成立

如果不够，就必须继续补字段，而不是硬往后做。

所以 Phase 1 实际上是在同步收敛两套 schema：

1. `Style Analysis Output Schema`
2. `User Editing Input Schema`

## 第一版目录落点建议

为了让第一版闭环落得清楚，建议先固定这些目录：

- 参考风格视频：
  - `ai-service/input/stylizationvideo/`
- 用户视频：
  - `ai-service/input/uservideo/`
- 分析产物：
  - `ai-service/output/materials/`
- 规划产物：
  - `ai-service/output/plans/`
- 最终视频：
  - `ai-service/output/renders/`

这样后面看到目录就知道：

- 输入视频在哪里
- 中间产物在哪里
- 最终视频在哪里

## 系统对象建议

即使现在不全部实现，后面这些对象也应该从架构上预留：

- `reference_video`
- `user_video`
- `style_profile`
- `materials`
- `timeline_plan`
- `editing_job`
- `timeline_version`
- `render_output`
- `final_video`

如果后面接 IM 修订，还建议预留：

- `revision_instruction`
- `edit_session`

## 第一版最值得优先定义的两个 schema

即使现在还不立刻写成正式 JSON Schema，也应该先在设计层面把这两套结构想清楚：

### 1. Style Analysis Output Schema

回答：

```txt
参考视频分析完之后，系统到底要输出什么字段
```

至少应逐步收敛这些方向：

- `pace_profile`
- `shot_pattern`
- `subtitle_style`
- `font_style`
- `color_mood`
- `music_mood`
- `transition_rules`
- `overlay_rules`

### 2. User Editing Input Schema

回答：

```txt
用户想让系统自动剪视频时，到底至少要给什么输入
```

至少应逐步收敛这些方向：

- `user_video`
- `video_metadata`
- `audio_preferences`
- `subtitle_preferences`
- `overlay_preferences`
- `extra_assets`
- `target_duration`
- `target_platform`
- `editing_goal`

这两套 schema 是后面：

- Material Analyzer
- Style Retriever
- Director Planner
- Editing Skills

能不能顺利协作的前提。

更具体的协议预设见：

- [`../style-analysis-design/README.md`](../style-analysis-design/README.md)
- [`../style-editing-design/README.md`](../style-editing-design/README.md)

## 各模块职责

### frontend

负责：

- 上传入口
- IM 输入
- 展示当前视频状态
- 展示当前会话与修订历史

### backend

负责：

- 会话与消息主控
- 视频任务编排
- style / timeline / revision 元数据管理
- agent 调度入口

### ai-service

负责：

- Material Analyzer
- Style Retriever
- Director Planner
- IM revision understanding
- LangGraph 编排

### 编辑执行层

后续会负责：

- 真正执行 timeline plan
- 处理视频、音频、字幕、图片、贴纸、字体叠加
- 产出最终视频

## 当前最重要的架构提醒

### 1. IM 不是单独工具

IM 后面会同时承担：

- 初版生成入口
- 二次修订入口

所以它必须和：

- `timeline`
- `style_profile`
- `editing_job`

这些对象有明确关联。

### 2. 结果必须版本化

后面不能只保留一个最终视频。

至少要能表达：

- 初版 timeline
- 修订后的 timeline v2 / v3
- 每次 IM 修改对应哪一个版本

### 3. 风格要结构化

参考视频分析结果不能只是一段文字总结。

必须逐渐沉淀成：

- 可存储
- 可复用
- 可被 planner 使用

的结构化数据。

## 当前结论

如果按最现实的 MVP 推进，推荐顺序是：

1. 先固定风格 `One Last Kiss`
2. 同步推进：
   - `爆款视频 -> style_profile`
   - `用户视频 -> timeline_plan / final.mp4`
3. 用这两条链一起收敛输入输出 schema
4. 最后再做 `IM 对话式修订`

这样最稳，也最符合当前项目阶段。
