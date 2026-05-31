# Workspace Storage And Target Schema

这份文档专门回答：

- workspace 里的文件应该怎么落
- 哪些数据应该放本地文件系统，哪些应该进数据库
- P0 目标表应该有哪些
- 每条核心 use case 会读写哪些表和哪些本地文件

它不重新定义：

- 系统总体拓扑
- Client / Backend / Agent Runtime / Tool Runtime 的职责边界
- runtime 核心概念

这些请先看：

- [`../../03-architecture/03-system-architecture/README.md`](../../03-architecture/03-system-architecture/README.md)
- [`../../03-architecture/01-workspace-agent-runtime-model/README.md`](../../03-architecture/01-workspace-agent-runtime-model/README.md)

## 1. Storage Rule By Data Type

推荐固定成这张表：

| Data Type | Source of Truth | Storage Location | Why |
| --- | --- | --- | --- |
| raw video assets | local workspace | `workspace/assets/*` | 大文件、本地优先 |
| extracted frames | local workspace | `workspace/artifacts/materials/frames/*` | 工具链中间产物 |
| audio features | local workspace | `workspace/artifacts/materials/audio_features.json` | 分析结果 |
| transcripts | local workspace | `workspace/artifacts/materials/transcript.json` | 分析结果 |
| style profile | local workspace | `workspace/artifacts/materials/style_profile.json` | 可复用 artifact |
| timeline plan | local workspace | `workspace/artifacts/plans/timeline_plan.json` | 可执行规划 |
| editing job | local workspace | `workspace/artifacts/plans/editing_job.json` | 执行输入 |
| final render | local workspace | `workspace/artifacts/renders/final.mp4` | 最终产物 |
| conversation records | PostgreSQL | `conversations` / `conversation_messages` | 业务记录 |
| task records | PostgreSQL + local checkpoint | `agent_tasks` + `workspace/tasks/*.json` | 业务查询 + 恢复 |
| tool call summaries | PostgreSQL + local logs | `task_tool_calls` + `workspace/logs/*` | 调试和审计 |
| artifact metadata | PostgreSQL + local memory | `workspace_artifacts` + `workspace/memory/artifact_memory.json` | 快速索引 + 本地恢复 |
| workspace memory | local workspace | `workspace/memory/*.json` | 本地持续工作 |

## 2. Workspace Folder Layout

推荐固定成：

```txt
<workspace-folder>/
  workspace.json
  assets/
    reference/
    source/
    images/
    audio/
  artifacts/
    materials/
      frames/
      transcript.json
      audio_features.json
      style_profile.json
      editing_rules.json
    plans/
      timeline_plan.json
      editing_job.json
      revision_instruction.json
    renders/
      final.mp4
      preview.mp4
  memory/
    workspace_memory.json
    artifact_memory.json
    conversation_summary.json
    preference_memory.json
  tasks/
    task_001.json
    task_002.json
  logs/
    agent_trace.log
    render.log
```

## 3. Database Design

这里要分清：

- `current`
  - 当前代码里已经有的表
- `target`
  - 按 P0 架构需要补齐的表

### 3.1 Current Tables

#### `conversations`

关键字段：

- `conversation_id`
- `workspace_id`
- `user_id`
- `session_id`
- `title`
- `status`
- `created_at`
- `updated_at`

#### `conversation_messages`

关键字段：

- `message_id`
- `conversation_id`
- `role`
- `content`
- `status`
- `trace_json`
- `created_at`

### 3.2 Target P0 Tables

#### `agent_tasks`

建议字段：

- `task_id`
- `workspace_id`
- `conversation_id`
- `task_type`
- `status`
- `current_stage`
- `entry_message_id`
- `latest_artifact_id`
- `error_code`
- `error_message`
- `created_at`
- `updated_at`
- `completed_at`

#### `task_tool_calls`

建议字段：

- `tool_call_id`
- `task_id`
- `tool_name`
- `tool_phase`
- `status`
- `input_summary_json`
- `output_summary_json`
- `started_at`
- `finished_at`

#### `workspace_artifacts`

建议字段：

- `artifact_id`
- `workspace_id`
- `task_id`
- `artifact_type`
- `path`
- `version`
- `summary`
- `reusable`
- `created_at`

#### `workspace_asset_index`

建议字段：

- `asset_id`
- `workspace_id`
- `asset_role`
- `path`
- `mime_type`
- `duration_ms`
- `width`
- `height`
- `size_bytes`
- `created_at`

#### `task_artifact_links`

建议字段：

- `task_artifact_link_id`
- `task_id`
- `artifact_id`
- `link_role`

### 3.3 What Should Not Be Stored In DB

- 原始视频二进制
- 抽帧全集
- 音频波形大文件
- `final.mp4`
- 大体积渲染中间件缓存

## 4. Use Case To Storage Mapping

### 4.1 Analyze Reference Video

涉及表：

- `conversations`
- `conversation_messages`
- `agent_tasks`
- `task_tool_calls`
- `workspace_artifacts`
- `task_artifact_links`

涉及本地文件：

- `assets/reference/*`
- `artifacts/materials/frames/*`
- `artifacts/materials/transcript.json`
- `artifacts/materials/audio_features.json`
- `artifacts/materials/style_profile.json`
- `artifacts/materials/editing_rules.json`
- `memory/artifact_memory.json`
- `tasks/task_<id>.json`

### 4.2 Create Styled Video From Source Videos

涉及表：

- `conversations`
- `conversation_messages`
- `agent_tasks`
- `task_tool_calls`
- `workspace_artifacts`
- `workspace_asset_index`
- `task_artifact_links`

涉及本地文件：

- `assets/reference/*`
- `assets/source/*`
- `artifacts/materials/style_profile.json`
- `artifacts/plans/timeline_plan.json`
- `artifacts/plans/editing_job.json`
- `artifacts/renders/final.mp4`
- `memory/artifact_memory.json`
- `tasks/task_<id>.json`

### 4.3 Revise Existing Output

涉及表：

- `conversations`
- `conversation_messages`
- `agent_tasks`
- `task_tool_calls`
- `workspace_artifacts`
- `task_artifact_links`

涉及本地文件：

- `artifacts/plans/timeline_plan.json`
- `artifacts/plans/revision_instruction.json`
- `artifacts/plans/editing_job.json`
- `artifacts/renders/final.mp4`
- `memory/conversation_summary.json`
- `memory/artifact_memory.json`
- `tasks/task_<id>.json`

### 4.4 Resume Workspace And Continue Work

涉及表：

- `conversations`
- `conversation_messages`
- `agent_tasks`
- `workspace_artifacts`
- `workspace_asset_index`

涉及本地文件：

- `workspace.json`
- `assets/**/*`
- `memory/*.json`
- `tasks/*.json`
- `artifacts/**/*`

## 5. Related Docs

- System Architecture：[`../../03-architecture/03-system-architecture/README.md`](../../03-architecture/03-system-architecture/README.md)
- Database Storage：[`../04-database-storage-design/README.md`](../04-database-storage-design/README.md)
