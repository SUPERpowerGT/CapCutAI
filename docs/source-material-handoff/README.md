# Source Material Handoff

这份文档定义一个前提：

```txt
用户视频理解和素材拆解
不由剪辑器负责
```

剪辑器、agent editing tools、HyperFrames adapter 后续都假定已经拿到了：

```txt
source_material.json
```

也就是说，当前视频链路应该拆成两段：

```txt
Source Video
  -> Video Analyzer / Material Analyzer
  -> source_material.json

source_material.json
  + editing_experience.json
  -> planner
  -> timeline_plan.json
  -> editing_job.json
  -> HyperFrames render
  -> final.mp4
```

## 这份文档解决什么问题

它主要解决一个边界问题：

- 经验沉淀同学负责把原视频分析成结构化素材理解结果
- 剪辑器同学不再猜视频内容
- agent 不直接“看原视频做决定”，而是消费结构化 `source_material.json`

这样后面的规划、渲染、修订才有稳定输入。

## 当前协作前提

从现在开始，剪辑器和 agent 侧默认假定：

1. `source_material.json` 已存在
2. 它和经验数据一样，属于 planner 可消费的结构化输入
3. 如果 analyzer 还没接好，就先使用 mock `source_material.json`

当前我们不补 analyzer 本身。

## `source_material.json` 在链路中的角色

`editing_experience.json` 回答的是：

```txt
目标风格应该长什么样
```

`source_material.json` 回答的是：

```txt
用户这批素材里到底有什么
哪些内容能拿来填到目标风格的各个 phase
```

所以在 planner 阶段，这两份输入缺一不可：

```txt
editing_experience
  -> 给出目标节奏、叙事结构、视觉规则

source_material
  -> 给出可用镜头、内容语义、人声台词、候选片段
```

## 第一版建议字段

第一版不追求一步到位，但至少建议有这些字段：

### 1. `video_metadata`

回答视频最基础的客观信息：

```json
{
  "assetId": "",
  "durationMs": 0,
  "width": 0,
  "height": 0,
  "fps": 0,
  "hasAudio": true
}
```

### 2. `segments`

回答视频被切成了哪些粗粒度片段：

```json
[
  {
    "segmentId": "",
    "startMs": 0,
    "endMs": 0,
    "durationMs": 0
  }
]
```

### 3. `visual_summary`

回答每个片段在画面上大概是什么：

```json
[
  {
    "segmentId": "",
    "sceneType": "",
    "subjects": [],
    "actions": [],
    "cameraMotion": "",
    "shotType": ""
  }
]
```

### 4. `speech_blocks`

回答哪里有人声、说了什么。

如果 ASR 还没接好，可以先允许空数组：

```json
[
  {
    "blockId": "",
    "startMs": 0,
    "endMs": 0,
    "text": "",
    "speakerType": ""
  }
]
```

### 5. `candidate_roles`

回答哪些片段更适合承担剪辑叙事角色：

```json
[
  {
    "segmentId": "",
    "roles": [
      "hook_candidate",
      "transition_candidate",
      "ending_candidate"
    ]
  }
]
```

这个字段很重要，因为它是经验模板和用户素材之间最直接的桥。

## 和经验数据的映射关系

当前经验数据例如：

- `style_metadata`
- `storyline_structure`
- `dynamic_pacing_blueprint`

它们描述的是：

```txt
理想的视频应该怎么组织
```

而 `source_material.json` 描述的是：

```txt
当前手上的素材能提供什么
```

planner 的实际工作就是做映射：

- `storyline_structure.PHASE_HOOK`
  - 去找 `source_material.candidate_roles` 里最适合 `hook_candidate` 的片段

- `storyline_structure.PHASE_PROBLEM`
  - 去找能承担中段叙事推进的片段

- `dynamic_pacing_blueprint`
  - 决定这些片段应该在哪些时间点切进去

## 对剪辑器的意义

剪辑器 UI 不需要直接展示完整 `source_material.json`。

但剪辑器后续应该能消费它生成出来的：

- `timeline_plan.json`
- `editing_job.json`
- `render_result.json`

如果后面要补素材检查面板，最多展示：

- 当前已加载的 `source material` 是否可用
- 每个 Source Video 是否已有 analyzer 输出
- 当前 planner 使用的是哪一版 `source_material.json`

## 对 agent tool 的意义

当前我们已经有：

- `load_editing_experience`
- `create_timeline_plan`
- `create_hyperframes_composition`
- `render_with_hyperframes`

在接入 `source_material.json` 之后，应当补一个更明确的工具输入：

### `load_source_material`

输入：

```json
{
  "sourceMaterialPaths": [
    "ai-service/output/materials/source_material.case-a.json",
    "ai-service/output/materials/source_material.case-b.json"
  ]
}
```

输出：

```json
{
  "sourceMaterials": []
}
```

然后 `create_timeline_plan` 的输入应该更新为：

```json
{
  "sourceMaterials": [],
  "editingExperience": {}
}
```

而不是只看 `sourceAssets` metadata。

## 当前推荐开发顺序

1. 经验沉淀同学补齐 analyzer 或 mock `source_material.json`
2. 我们把 `source_material.json` schema 固定下来
3. 更新 planner，让它消费：
   - `editingExperience`
   - `sourceMaterials`
4. 再接 HyperFrames render

## 当前结论

当前如果没有 `source_material.json`，我们只能做：

- 素材预览
- package 导出
- timeline draft 占位

一旦有了 `source_material.json`，我们才真正具备：

```txt
按内容规划剪辑
```

这也是后续进入真实闭环测试的关键前提。

## 当前 mock 数据映射

当前 `data/test_case/<case_id>/` 下的 mock 数据已经接近这条链路：

- `step1_audio.json`
  - 提供：
    - `bpm`
    - `beats_ms`
    - `drops_ms`
    - `duration_ms`

- `step2_transcript.json`
  - 提供：
    - `full_text`
    - `sentences[]`

- `step3_visual.json`
  - 提供：
    - `shots[]`
    - 每个 shot 的：
      - `shot_type`
      - `content_type`
      - `emotional_tone`
      - `b_roll_semantic_prompt`
      - `camera_motion_effect`
      - `editing_utility`

- `elastic_template.json`
  - 当前更适合视为：
    - 可选 style hints
    - 调试中间产物
  - 不建议把它当成 `source_material.json` 的硬依赖

## 当前取舍建议

如果担心风格字段干扰 agent 判断，当前建议是：

1. `step1_audio.json`
   保留，属于用户素材客观信息
2. `step2_transcript.json`
   保留，属于用户素材语义信息
3. `step3_visual.json`
   保留，属于用户素材镜头信息
4. `elastic_template.json`
   在 `source_material.json` 中只保留为可选 `optionalStyleHints`
   或者开发阶段完全不进入 planner 主输入

也就是说，当前 planner 最稳妥的主输入建议是：

```txt
audio + transcript + visual
```

而不是：

```txt
audio + transcript + visual + style_metadata + storyline_structure
```

后者更适合作为调试辅助，而不是硬规则。
