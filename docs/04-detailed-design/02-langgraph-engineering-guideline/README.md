# LangGraph Guideline

这里整理 CapCutAI 后续使用 `LangGraph` 的工程约定。

目标不是只把 `LangGraph` 当成“套了一层 graph 的聊天函数”，而是把它作为：

- 工作流编排器
- tool / skill 调度器
- trace 生成器
- 多阶段 agent 执行框架

## 当前结论

以下这些都适合借 `LangGraph` 来做：

- tool
- system prompt
- skill
- workflow trace

但它们在系统里扮演的角色不同，不能混在一起理解。

## 1. 什么应该放进 graph

graph 负责：

- 节点顺序
- 条件分支
- 状态传递
- tool / skill 调用编排
- workflow trace

所以 graph 更适合表达：

```txt
当前任务要经过哪些步骤
每一步依赖什么输入
每一步的输出如何传给下一步
什么时候需要调工具
什么时候需要切到别的子流程
```

### 适合放进 graph 的例子

- `extract_latest_user_message`
- `analyze_reference_video`
- `build_style_profile`
- `plan_timeline`
- `select_editing_skills`
- `run_revision_step`

## 2. 什么不应该放进 graph

graph 不应该直接承担这些低层实现：

- 文件读写细节
- 模型 SDK 直接调用细节
- ffmpeg 执行细节
- 数据库存储细节
- 长篇硬编码 prompt 字符串拼接逻辑

这些应该交给：

- `providers/`
- `services/`
- `utils/`
- 后续的执行器模块

graph 负责“编排”，不是“把所有逻辑都塞进去”。

## 3. tool 是什么

在 CapCutAI 里，tool 更像“可调用能力”。

例如：

- 读取视频元数据
- 提取音轨信息
- 生成字幕片段
- 计算镜头切分建议
- 调用外部编辑执行器

推荐理解：

```txt
tool = graph 可调用的外部能力
```

在 CapCutAI 里再补一条硬边界：

```txt
tool != UI action
```

也就是说，graph 调的是本地 Agent Runtime 挂接的受控能力，不是直接点客户端按钮。

CapCutAI 当前已经开始落的第一批基础 tool，就是这种“graph 可直接调的只读/校验能力”：

- `describe_workspace_state`
- `list_source_videos`
- `validate_workspace_inputs`

它们先不做复杂执行，只负责：

- 读取当前 workspace / assets
- 给 graph 一份稳定的结构化结果
- 帮助 graph 决定能不能继续走分析 / 生成 / 修订

### tool 的职责

- 输入清晰
- 输出结构化
- 自己不做工作流判断
- 被 graph 或 node 调用
- 作用域尽量限制在当前 workspace
- 调用过程可记录到 trace / task history

### tool 不做什么

- 不负责决定下一步流程
- 不负责维护全局状态
- 不负责 UI 表达

## 4. skill 是什么

你们这里说的 `Editing Skills`，更适合理解成：

```txt
一组面向视频编辑任务的高层能力
```

例如：

- `subtitle_skill`
- `beat_cut_skill`
- `font_overlay_skill`
- `image_overlay_skill`
- `music_alignment_skill`

这些 skill 和 tool 的区别在于：

- tool 更偏基础能力
- skill 更偏任务语义

可以这样理解：

```txt
skill 可能内部会调用多个 tool
graph 决定什么时候调用哪个 skill
```

## 5. system prompt 应该怎么放

system prompt 不应该散落在各个函数里。

推荐按 graph / node 组织：

- `conversation_graph` 一份
- `style_analysis_graph` 一份
- `style_editing_graph` 一份
- `revision_graph` 一份

如果更细：

- `planner node` 自己一份
- `style summarizer node` 自己一份
- `revision patcher node` 自己一份

### 推荐原则

- graph 级 prompt 管全局角色
- node 级 prompt 管当前阶段任务
- prompt 和节点职责一一对应

## 6. trace 和 log 怎么分

这块一定要分清。

### A. trace

trace 是给：

- 产品工作流
- 前端 activity feed
- 调试 agent 行为

看的结构化运行轨迹。

后面建议至少记录：

- 当前 graph
- 当前 node
- 调了哪个 tool / skill
- 当前 provider / model
- 关键输入输出摘要
- 当前阶段状态

推荐理解：

```txt
trace = 面向工作流和产品语义的运行轨迹
```

### B. log

log 是给：

- 工程排障
- 错误定位
- 性能分析

看的系统日志。

例如：

- request id
- stack trace
- latency
- provider API error
- file IO error

推荐理解：

```txt
log = 面向工程排障的系统日志
```

### 一条清晰原则

```txt
trace 给产品和工作流看
log 给工程和排障看
```

不要把这两者混成一个长字符串。

## 7. 后续推荐 graph 划分

当前最合理的长期结构是：

- `conversation_graph`
- `style_analysis_graph`
- `style_editing_graph`
- `revision_graph`

### `conversation_graph`

负责：

- IM 对话
- 普通问答
- 轻量指令解释

### `style_analysis_graph`

负责：

- 参考视频分析
- `materials.json`
- `style_profile.json`
- `editing_rules.json`

### `style_editing_graph`

负责：

- 用户视频输入归一化
- timeline 规划
- editing job 生成

## 8. Plan vs Execution

这里建议强制区分两层：

```txt
LLM / planner 生成的是语义层 Edit Plan
Tool Runtime 执行的是可落地的 Execution Plan
```

也就是说：

- 模型不直接输出 FFmpeg / Remotion 细节作为最终执行真相
- graph / runtime 可以把语义计划编译成时间线、参数、素材映射和渲染任务
- 具体媒体执行继续交给本地工具层

### `revision_graph`

负责：

- 已生成视频的二次修改
- 基于已有 timeline 的 patch
- revision trace

## 8. state 应该长什么样

后面 graph state 不应该只是一段聊天文本。

当前更合理的第一阶段骨架应该至少有：

- `meta`
- `workspace`
- `assets`
- `memory`
- `intent`
- `tool_calls`
- `response`
- `trace`
- `status`
- `error`

当前 `conversation_graph` 已经开始按这层走，而不是只保留：

- `messages`
- `latest_user_message`
- `reply_content`

建议逐步扩成结构化状态：

- `conversation_id`
- `reference_video_path`
- `source_video_path`
- `messages`
- `materials`
- `style_profile`
- `editing_rules`
- `timeline_plan`
- `editing_job`
- `revision_instruction`
- `artifacts`
- `trace`

一句话：

```txt
state = 工作流上下文
不是 prompt 拼接缓存
```

## 9. 推荐工程分层

推荐这样配合：

### graph

负责：

- orchestration
- branching
- state transitions

### tool / skill

负责：

- 实际能力执行
- 结构化输入输出

### provider

负责：

- LLM client
- 模型调用细节

### service

负责：

- graph 调用入口
- 上层业务桥接

## 10. 对前端的意义

如果后面你们把 trace 做对，前端右侧 `Agent Panel` 就能自然显示：

- 正在分析参考视频
- 正在生成 style profile
- 正在调用 Material Analyzer
- 正在运行 Director Planner
- 正在执行某个 subagent

所以今天前端里做的 `activity item` 结构，和这里的 LangGraph 约定其实是一套思路。

## 11. 当前推荐做法

现在最好的推进方式是：

1. 保留现有 `conversation_graph`
2. 新增视频 graph 的目录边界
3. 先定义 state/schema
4. 再把 tool / skill 明确分层
5. 最后逐步把 trace 做结构化

## 一句话总结

在 CapCutAI 里：

- `LangGraph` 负责工作流编排
- `tool` 是可调用能力
- `skill` 是更高层任务能力
- `system prompt` 按 graph / node 组织
- `trace` 是工作流轨迹
- `log` 是工程日志

后面只要沿着这套边界长，agent 就不会越来越乱。
