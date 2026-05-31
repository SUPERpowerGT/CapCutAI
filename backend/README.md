# Backend

这里是 CapCutAI 当前阶段的 Spring Boot 主控服务。

当前主线只保留：

```txt
health
conversation
message
ai-service orchestration
postgresql
```

## 这层负责什么

- 提供前端 API
- 管 conversation / message
- 调 `ai-service`
- 保存消息和回复
- 用 `workspace_id` 做当前工作流隔离

当前 backend 不负责：

- 本地 workspace 文件夹生命周期
- 本地素材目录管理
- 真实视频剪辑执行
- 直接替模型做 tool routing 或 runtime orchestration

## 怎么启动

推荐在项目根目录：

```bash
make up
```

或只起 backend：

```bash
docker compose up --build -d backend
```

健康检查：

- `http://127.0.0.1:38080/api/health`

## 当前主要接口

- `GET /api/health`
- `POST /api/conversations`
- `GET /api/conversations`
- `DELETE /api/conversations/{conversationId}`
- `GET /api/conversations/{conversationId}/messages`
- `POST /api/conversations/{conversationId}/messages`

## 当前目录

```txt
api/http/         HTTP 入口、DTO、mapper
application/      用例与编排
domain/           实体与状态
infrastructure/   数据库、外部服务、配置
shared/           统一错误模型
```

## DTO 规则

### HTTP DTO

- 路径：`api/http/*/dto`
- 命名：
  - `*HttpRequest`
  - `*HttpResponse`

### Application DTO

- 路径：`application/*/dto`
- 命名：
  - `*Request`
  - `*View`
  - `*Result`

### Service-to-Service DTO

- 路径：`infrastructure/agent/dto`
- 用于 backend 和 `ai-service` 通信

## 当前工作区语义

当前桌面客户端按：

```txt
一个窗口 = 一个 workspace
```

backend 当前已经开始消费这个概念：

- conversation 会带 `workspace_id`
- 查询 conversation 时可按 `workspace_id` 过滤

一句话说：

```txt
workspace 的本地生命周期归客户端
workspace 下的对话与消息归 backend
```

再严格一点：

```txt
Backend 是业务记录与持久化边界
不是本地视频工具执行器
也不是客户端 UI 控制器
```

## 当前标准模块

如果你要按现有风格继续写，优先参考：

- [`MessageController.java`](./src/main/java/com/capcutai/backend/api/http/message/MessageController.java)
- [`MessageQueryService.java`](./src/main/java/com/capcutai/backend/application/message/MessageQueryService.java)
- [`MessageCommandService.java`](./src/main/java/com/capcutai/backend/application/message/MessageCommandService.java)
- [`SendMessageUseCase.java`](./src/main/java/com/capcutai/backend/application/message/SendMessageUseCase.java)

## 继续看哪里

- 总入口：[`../README.md`](../README.md)
- 启动：[`../docs/90-getting-started/README.md`](../docs/90-getting-started/README.md)
- 数据库存储：[`../docs/04-detailed-design/04-database-storage-design/README.md`](../docs/04-detailed-design/04-database-storage-design/README.md)
- 共享协议：[`../shared/README.md`](../shared/README.md)
