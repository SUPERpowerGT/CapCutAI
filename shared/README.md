# Shared

这里放的是 **跨服务共享契约**，不是某一个模块自己的代码。

所以 `shared/` 放在仓库根目录是刻意的，原因很简单：

- 这里的内容会同时被 `frontend`、`backend`、`ai-service` 参考
- 它们不属于某一个单独服务
- 如果把这些文件塞进 `backend/` 或 `ai-service/`，很容易让人误解成“这是某个服务私有文档”

## 这里为什么有 OpenAPI

`shared/openapi/` 的定位是：

```txt
服务和服务之间怎么说话
```

而不是：

```txt
某个服务自己怎么实现
```

当前两个最重要的协议文件：

- [`openapi/frontend-backend.openapi.yaml`](./openapi/frontend-backend.openapi.yaml)
  - 给 `frontend` 和 `backend` 一起看
  - 描述当前真实主线：
    - `conversation`
    - `message`
    - `send message`
    - `delete conversation`

- [`openapi/backend-ai.openapi.yaml`](./openapi/backend-ai.openapi.yaml)
  - 给 `backend` 和 `ai-service` 一起看
  - 描述当前内部协议：
    - `/internal/agent/respond`
    - backend 如何把会话传给 ai-service
    - ai-service 如何返回 assistant reply

## 当前目录

```txt
shared/
├── openapi/
│   ├── frontend-backend.openapi.yaml
│   └── backend-ai.openapi.yaml
└── schemas/
    ├── source-material.schema.json
    ├── editing-experience.schema.json
    ├── timeline-plan.schema.json
    ├── editing-job.schema.json
    ├── render-result.schema.json
    └── hyperframes-composition-draft.schema.json
```

## 当前重点

当前 `shared/openapi/` 的重点是：

```txt
conversation / message / agent-response
```

也就是：

- 前端怎么调 backend
- backend 怎么调 ai-service
- 大家共同依赖哪些字段名、响应结构、状态值

当前 `shared/schemas/` 开始补剪辑器与 agent editing tools 的共享协议：

- `source-material.schema.json`
  - 表达 analyzer 对用户上传视频做完结构化理解后的结果
  - 是 planner 和 HyperFrames 前置链路的关键输入
  - 可以包含可选 style hints，但不建议把这部分作为硬依赖

- `editing-experience.schema.json`
  - 表达从爆款视频经验中沉淀出来的可复用风格经验
  - 当前可由 `data/elastic_template.json` mock 转换得到

- `timeline-plan.schema.json`
  - 表达 agent 规划出来的多轨剪辑计划
  - 前端 Editor 用它做预览，HyperFrames adapter 用它做 composition 输入

- `editing-job.schema.json`
  - 表达交给 HyperFrames 执行层的渲染任务

- `render-result.schema.json`
  - 表达最终导出结果或渲染状态

- `hyperframes-composition-draft.schema.json`
  - 表达 `timelinePlan` 进一步转换后的 HyperFrames draft composition
  - 给 Codex / Cursor / agent 继续生成真实 render composition 使用

## 规则

后续如果继续往 `shared/` 加内容，遵循这几个原则：

- 只放跨服务共享契约
- 不放某个服务自己的实现代码
- 不放只给一个模块自己看的内部文档
- 命名尽量直接表达调用关系

例如：

- `frontend-backend.openapi.yaml`
- `backend-ai.openapi.yaml`

这种命名就比抽象名字更清楚。

## 参考文档

- [`../README.md`](../README.md)
- [`../frontend/README.md`](../frontend/README.md)
- [`../backend/README.md`](../backend/README.md)
- [`../ai-service/README.md`](../ai-service/README.md)
