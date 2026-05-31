# AI Service Video Architecture

这份文档只回答一件事：

```txt
ai-service 应该如何从当前 IM 对话 graph，演进成视频分析 / 套风格 / 修订的本地优先 agent 服务
```

## 当前状态

现在 `ai-service` 里已经真实跑通的，只有一条最小链路：

```txt
/internal/agent/respond
  -> agent_service
  -> conversation_graph
  -> llm provider
```

也就是说，它现在本质上还是一个：

- 对话输入
- LangGraph 编排
- LLM 生成回复

的最小 agent。

这套结构适合现在的 IM 主链，但还不够承接后面的视频流程。

不过当前底层已经开始往更稳的 agent 架构收口了：

- `app/memory/`
  - 负责 conversation / workspace memory
- `app/tools/`
  - 负责 graph 可调用的基础只读工具
- `app/prompts/`
  - 负责 system prompt / graph prompt 组织

也就是说，当前最小对话链已经开始从：

```txt
messages -> prompt -> reply
```

往：

```txt
messages
-> memory
-> intent
-> tools
-> prompt
-> reply
```

演进。

## 未来 ai-service 的职责

后面 `ai-service` 不再只是“聊天回复器”，而是要逐步承担：

1. 视频素材分析
2. 风格规则检索
3. 剪辑规划生成
4. IM 对话式 revision 理解
5. LangGraph 多阶段编排
6. 对本地 Tool Runtime 的受控调度

但这里要明确：

```txt
ai-service 负责 orchestration
Local Tool Runtime 负责真实媒体执行
```

## 一个关键判断

后面 `ai-service` 的视频能力，不应该被理解成：

- 先只做参考视频分析
或
- 先只做用户视频自动剪辑

更合理的推进方式是：

```txt
参考视频分析链 和 用户视频剪辑链 同步推进
```

因为当前最重要的问题其实是：

```txt
系统需要哪些输入，才能把视频剪好
系统又要产出哪些结构化中间结果，后续节点才能继续工作
```

这意味着：

- `style_analysis_graph` 不只是“生成分析结果”
- 它还负责帮助我们定义后面可复用的 `style_profile` 结构

同时：

- `style_editing_graph` 不只是“把用户视频剪出来”
- 它还负责帮助我们反推出用户侧输入到底至少需要哪些字段

所以这两个 graph 在 MVP 阶段应该同步收敛，不应该完全串行。

如果要看这两条链的具体业务设计，请继续看：

- [`../05-style-analysis-design/README.md`](../05-style-analysis-design/README.md)
- [`../06-style-editing-design/README.md`](../06-style-editing-design/README.md)

## 推荐总链路

后面视频主链建议按这个执行模型统一：

```txt
Client UI 收集 workspace facts
-> Agent Runtime 构造 context
-> Memory Retriever 选相关沉淀
-> Graph / planner 生成结构化 plan
-> Local Tool Runtime 执行分析 / 渲染
-> Artifacts 写回本地 workspace
-> Client UI 展示状态与预览
```

## 推荐按三条 graph 长出来

### 1. `conversation_graph`

保留现有能力，用于：

- 纯 IM 对话
- 通用 agent 回复
- 当前最小链路验证

### 2. `style_analysis_graph`

用于：

- 参考视频分析
- 风格拆解
- 结构化总结输出

输入：

- `reference_video`

输出：

- `materials.json`
- `style_profile.json`
- `editing_rules.json`

这条 graph 除了产出分析结果，还有一个更重要的职责：

- 帮助我们把 `Style Analysis Output Schema` 定清楚

### 3. `style_editing_graph`

用于：

- 用户视频自动套风格
- 生成 timeline plan
- 生成 editing job

输入：

- `user_video`
- `style_profile`
- 用户 prompt

输出：

- `timeline_plan.json`
- `editing_job`

这条 graph 除了生成 plan，还有一个更重要的职责：

- 帮助我们把 `User Editing Input Schema` 定清楚

### 4. `revision_graph`

用于：

- 基于已有 timeline 做 IM 修订
- 把对话理解成结构化 revision instruction

输入：

- `conversation`
- `timeline_version`
- `style_profile`
- `materials`

输出：

- `revision_instruction`
- 新的 `timeline_version`
- 新的 `editing_job`

## 控制面与数据面

推荐固定成这个理解：

- 控制面
  - user intent
  - AgentState
  - task orchestration
  - tool selection
  - plan / revision generation
- 数据面
  - raw videos
  - extracted frames
  - transcripts
  - audio features
  - timeline artifacts
  - final renders

其中：

- `ai-service` 主要编排控制面
- `workspace + Local Tool Runtime` 主要承载数据面

## 推荐目录结构

后面 `ai-service` 建议逐步长成这样：

```txt
ai-service/
├── app/
│   ├── api/
│   │   ├── health_api.py
│   │   ├── internal_agent_api.py
│   │   ├── style_analysis_api.py
│   │   ├── style_editing_api.py
│   │   └── revision_api.py
│   ├── graph/
│   │   ├── conversation/
│   │   │   ├── graph.py
│   │   │   └── state.py
│   │   ├── style_analysis/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   └── nodes/
│   │   ├── style_editing/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   └── nodes/
│   │   └── revision/
│   │       ├── graph.py
│   │       ├── state.py
│   │       └── nodes/
│   ├── schemas/
│   │   ├── common/
│   │   ├── conversation/
│   │   ├── style_analysis/
│   │   ├── style_editing/
│   │   └── revision/
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── style_analysis_service.py
│   │   ├── style_editing_service.py
│   │   └── revision_service.py
│   ├── providers/
│   ├── prompts/
│   ├── assets/
│   │   └── styles/
│   └── utils/
├── input/
│   ├── stylizationvideo/
│   └── uservideo/
└── output/
    ├── materials/
    ├── plans/
    └── renders/
```

## 当前最值得先加的目录

不用一步到位。推荐先按最小增量加这几个：

```txt
app/graph/style_analysis/
app/graph/style_editing/
app/schemas/style_analysis/
app/schemas/style_editing/
app/services/style_analysis_service.py
app/services/style_editing_service.py
app/assets/styles/
input/stylizationvideo/
input/uservideo/
output/materials/
output/plans/
output/renders/
```

这样不会一下子把现有 `conversation_graph` 打散，但又给后面视频链留出了正经位置。

当前这一步其实已经开始做了：

```txt
app/memory/
app/tools/
app/prompts/
```

所以后面真正扩 `style_analysis_graph / style_editing_graph / revision_graph` 时，
已经不是从零开始搭 agent 底层。

并且这也符合当前 MVP 的推进方式：

- 用 `input/stylizationvideo/` 收敛分析输出
- 用 `input/uservideo/` 收敛剪辑输入
- 用 `output/` 验证中间结构是否足够支撑后续节点

## 推荐状态对象

### 当前 `conversation_graph` state

现在只有：

- `conversation_id`
- `messages`
- `latest_user_message`
- `reply_content`
- `trace`
- `artifacts`
- `status`
- `model_name`

这只够对话。

### `style_analysis_graph` state 推荐增加

- `reference_video_path`
- `video_metadata`
- `materials`
- `style_profile`
- `editing_rules`
- `analysis_summary`
- `trace`
- `status`
- `materials_output_path`
- `style_profile_output_path`
- `editing_rules_output_path`

这里的关键不是“字段越多越好”，而是：

- 这些字段能不能稳定表达风格
- 后面 planner 能不能真正消费它们

### `style_editing_graph` state 推荐增加

- `user_video_path`
- `style_profile`
- `materials`
- `editing_goal`
- `timeline_plan`
- `editing_job`
- `trace`
- `status`
- `timeline_plan_output_path`
- `editing_job_output_path`
- `final_render_output_path`

这里的关键同样不是“先凑全字段”，而是：

- 当前用户视频输入够不够支撑这些输出
- 哪些输入是必须补齐的

### `revision_graph` state 推荐增加

- `conversation_id`
- `messages`
- `timeline_version_id`
- `current_timeline`
- `style_profile`
- `materials`
- `revision_instruction`
- `updated_timeline_plan`
- `editing_job`
- `trace`
- `status`
- `revision_output_path`
- `final_render_output_path`

## 推荐 schema 分类

后面不要继续把所有 schema 都平铺在 `app/schemas/` 根下。

建议分类：

### `schemas/common`

放最稳定的公共对象：

- `message`
- `video_metadata`
- `subtitle_block`
- `timeline_clip`

### `schemas/style_analysis`

放：

- `style_analysis_request`
- `style_analysis_response`
- `materials`
- `style_profile`
- `editing_rules`

这一组 schema 主要解决的问题是：

```txt
参考视频分析完后，哪些字段是后续真的可复用的
```

### `schemas/style_editing`

放：

- `style_editing_request`
- `style_editing_response`
- `timeline_plan`
- `editing_job`

这一组 schema 主要解决的问题是：

```txt
用户侧最少要提供哪些输入，系统才能真的做自动剪辑
```

### `schemas/revision`

放：

- `revision_request`
- `revision_response`
- `revision_instruction`
- `timeline_patch`

## One Last Kiss 的落地建议

第一版既然只支持：

```txt
One Last Kiss
```

那就不要一上来做复杂 style registry。

先在：

```txt
app/assets/styles/one_last_kiss_style.json
```

放固定风格文件。

然后 `Style Retriever` 第一版可以非常简单：

- 直接命中 `one_last_kiss_style.json`
- 不做多风格召回
- 不做复杂相似度检索

## 第一版执行顺序建议

### Step 1

保留现有 `conversation_graph` 不动，继续保证 IM 主链稳定。

### Step 2

同步新增：

- `style_analysis_graph`
- `style_editing_graph`
- 对应的 service / schemas

并同步验证两件事：

```txt
参考视频 -> style_profile 到底够不够用
用户视频 -> timeline_plan 到底缺哪些输入
```

### Step 3

把这两边一起收敛成更稳定的：

- `Style Analysis Output Schema`
- `User Editing Input Schema`

### Step 4

最后新增：

- `revision_graph`

接 IM 对话式修订

## 当前最重要的架构原则

### 1. graph 要按业务链拆，不要继续把所有节点塞进一个 graph

否则后面 `conversation_graph.py` 会很快变成一坨。

### 2. state 要按链路独立

对话 state 和视频剪辑 state 不应该混成一个总状态对象。

### 3. schema 要按领域拆

不要把：

- message
- style_profile
- timeline_plan
- revision_instruction

全都平铺在一个目录里。

### 4. 固定风格先硬编码，别过早抽象

MVP 第一版先把：

- `one_last_kiss_style.json`

跑通，比一开始做多风格平台更重要。

### 5. 用双链路一起反推 schema

当前阶段真正重要的不是“哪条链先赢”，而是：

- 参考视频分析链告诉我们：
  - 风格资产应该长什么样
- 用户视频剪辑链告诉我们：
  - 用户输入至少要给什么

这两边一起收敛，后面的 planner 和 editing skills 才不会建立在猜测上。

## 输入输出目录建议

为了让视频链路更清楚，建议现在就固定目录语义：

### 输入

- `input/stylizationvideo/`
  - 放参考风格视频 / 爆款视频
- `input/uservideo/`
  - 放用户自己的源视频

### 输出

- `output/materials/`
  - 放 `materials.json`
- `output/plans/`
  - 放 `timeline_plan.json`、`editing_job.json`
- `output/renders/`
  - 放 `final.mp4`

这样第一版闭环：

```txt
input -> analyze / retrieve / plan -> output
```

会非常直观。
