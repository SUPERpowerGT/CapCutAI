# Backend

这里是 CapCutAI 当前阶段的 Spring Boot 主控服务。

这份 `README.md` 是 backend 当前唯一主文档。后续所有人都应该按这份文档继续开发，不要再额外维护第二份 backend 架构说明，避免版本漂移。

## 先看这里

如果你第一次进入 `backend/`，按这个顺序看：

1. 看“当前主线”
2. 看“当前目录规则”
3. 看“DTO 命名规则”
4. 看“当前 message 标准写法”
5. 看“当前配置规则”
6. 看“验证要求”

## 当前主线

当前 backend 只保留已经接上真实链路的部分：

```txt
health + conversation + message + ai-service 调用 + postgresql
```

当前真正跑在链路里的能力只有：

- 匿名 `user_id`
- 匿名 `session_id`
- 创建会话
- 查询会话
- 发送消息
- 查询消息
- 调用 `ai-service`
- 保存 assistant 回复

## 启动方式

推荐在项目根目录启动：

```bash
docker compose up --build -d backend
```

或者如果你已经启动了整套依赖：

```bash
make up
```

默认地址：

- API: `http://127.0.0.1:38080`
- Health: `GET /api/health`

当前已在的接口：

- `GET /api/health`
- `POST /api/conversations`
- `GET /api/conversations`
- `GET /api/conversations/{conversationId}/messages`
- `POST /api/conversations/{conversationId}/messages`

## 当前目录规则

当前 backend 只能按这五层继续开发：

- `api/http`
- `application`
- `domain`
- `infrastructure`
- `shared`

## 当前 backend 目录结构

当前已经落地到代码层的结构可以直接按下面理解：

```txt
backend/
├── src/main/java/com/capcutai/backend/
│   ├── api/http/
│   │   ├── common/
│   │   ├── conversation/
│   │   ├── health/
│   │   └── message/
│   ├── application/
│   │   ├── agent/
│   │   ├── conversation/
│   │   └── message/
│   ├── domain/
│   │   ├── conversation/
│   │   └── message/
│   ├── infrastructure/
│   │   ├── agent/
│   │   └── persistence/
│   └── shared/
│       └── error/
├── src/main/resources/
│   └── application.yaml
├── Dockerfile
├── build.gradle.kts
└── README.md
```

理解方式：

- `api/http` 看入口
- `application` 看流程
- `domain` 看实体和状态
- `infrastructure` 看数据库和外部服务
- `shared/error` 看统一异常

### `api/http`

负责：

- HTTP controller
- 前端 request / response DTO
- HTTP mapper
- 统一异常出口

禁止：

- 在 controller 里直接写业务流程
- 在 controller 里直接调 repository
- 在 controller 里直接拼外部服务请求

### `application`

负责：

- 用例编排
- 查询服务
- 写入服务
- 调用 domain + infrastructure 完成流程

当前例子：

- [`ConversationService`](./src/main/java/com/capcutai/backend/application/conversation/ConversationService.java)
- [`MessageQueryService`](./src/main/java/com/capcutai/backend/application/message/MessageQueryService.java)
- [`MessageCommandService`](./src/main/java/com/capcutai/backend/application/message/MessageCommandService.java)
- [`SendMessageUseCase`](./src/main/java/com/capcutai/backend/application/message/SendMessageUseCase.java)
- [`AgentOrchestrationService`](./src/main/java/com/capcutai/backend/application/agent/AgentOrchestrationService.java)

### `domain`

负责：

- 核心实体
- 枚举
- 领域状态

当前只保留：

- `conversation`
- `message`

### `infrastructure`

负责：

- JPA repository
- 外部服务 client
- 配置绑定

当前只保留：

- `agent`
- `persistence`

### `shared`

当前只保留 backend 内部统一异常模型：

- [`BackendException`](./src/main/java/com/capcutai/backend/shared/error/BackendException.java)
- [`ResourceNotFoundException`](./src/main/java/com/capcutai/backend/shared/error/ResourceNotFoundException.java)
- [`BadRequestException`](./src/main/java/com/capcutai/backend/shared/error/BadRequestException.java)
- [`ExternalServiceException`](./src/main/java/com/capcutai/backend/shared/error/ExternalServiceException.java)

## DTO 命名规则

后续所有人都要按这三类命名，不要混写。

### 1. HTTP DTO

路径：

- `api/http/*/dto`

命名规则：

- `*HttpRequest`
- `*HttpResponse`

用途：

- 只给前端 HTTP 协议用

当前例子：

- [`CreateConversationHttpRequest`](./src/main/java/com/capcutai/backend/api/http/conversation/dto/CreateConversationHttpRequest.java)
- [`ConversationHttpResponse`](./src/main/java/com/capcutai/backend/api/http/conversation/dto/ConversationHttpResponse.java)
- [`SendMessageHttpRequest`](./src/main/java/com/capcutai/backend/api/http/message/dto/SendMessageHttpRequest.java)
- [`SendMessageHttpResponse`](./src/main/java/com/capcutai/backend/api/http/message/dto/SendMessageHttpResponse.java)

### 2. Application DTO

路径：

- `application/*/dto`

命名规则：

- `*View`
- `*Result`
- `*Request`

用途：

- 只给 backend 内部用例和编排逻辑用

当前例子：

- [`ConversationView`](./src/main/java/com/capcutai/backend/application/conversation/dto/ConversationView.java)
- [`MessageView`](./src/main/java/com/capcutai/backend/application/message/dto/MessageView.java)
- [`SendMessageResult`](./src/main/java/com/capcutai/backend/application/message/dto/SendMessageResult.java)
- [`CreateConversationRequest`](./src/main/java/com/capcutai/backend/application/conversation/dto/CreateConversationRequest.java)

### 3. Service-to-Service Contract DTO

路径：

- `infrastructure/agent/dto`

用途：

- backend 和 `ai-service` 之间的协议对象

不是：

- 前端 DTO
- application DTO

当前例子：

- [`AgentRespondRequest`](./src/main/java/com/capcutai/backend/infrastructure/agent/dto/AgentRespondRequest.java)
- [`AgentRespondResponse`](./src/main/java/com/capcutai/backend/infrastructure/agent/dto/AgentRespondResponse.java)

## 当前 message 标准写法

`message` 模块是当前最标准的一块，后面新功能优先照着它的风格写。

当前结构：

- HTTP 入口
  - [`MessageController`](./src/main/java/com/capcutai/backend/api/http/message/MessageController.java)

- HTTP DTO / mapper
  - [`api/http/message/dto`](./src/main/java/com/capcutai/backend/api/http/message/dto)
  - [`MessageHttpMapper`](./src/main/java/com/capcutai/backend/api/http/message/MessageHttpMapper.java)

- application 查询 / 写入 / 用例
  - [`MessageQueryService`](./src/main/java/com/capcutai/backend/application/message/MessageQueryService.java)
  - [`MessageCommandService`](./src/main/java/com/capcutai/backend/application/message/MessageCommandService.java)
  - [`SendMessageUseCase`](./src/main/java/com/capcutai/backend/application/message/SendMessageUseCase.java)

- application view mapper
  - [`MessageViewMapper`](./src/main/java/com/capcutai/backend/application/message/MessageViewMapper.java)

- domain
  - [`ConversationMessageEntity`](./src/main/java/com/capcutai/backend/domain/message/ConversationMessageEntity.java)
  - [`MessageRole`](./src/main/java/com/capcutai/backend/domain/message/MessageRole.java)
  - [`MessageStatus`](./src/main/java/com/capcutai/backend/domain/message/MessageStatus.java)

## 当前配置规则

当前只保留实际用到的配置：

- `spring.datasource.*`
- `spring.jpa.*`
- `server.port`
- `app.ai-service.base-url`

其中自定义配置必须走类型化绑定，不要到处散落 `@Value`。

当前例子：

- [`AiServiceProperties`](./src/main/java/com/capcutai/backend/infrastructure/agent/AiServiceProperties.java)

## 当前明确不写的东西

在真实链路没接上之前，不要把这些内容重新加回来：

- project
- asset upload
- editing
- render
- workspace
- login

原因很简单：

- 现在前端没接
- 数据库主链没接
- ai-service 主链没接
- 先写只会制造假骨架和阅读噪音

## 如何新增一个功能模块

后面如果要新增真正接入主链的功能，默认按 `message` 这套方式落，不要自己发明新结构。

推荐顺序：

### 1. 先确认它是不是“真实主链需求”

先问三件事：

- 前端是不是已经要接它
- 数据库是不是已经需要存它
- ai-service 或其他服务是不是已经真的要用它

如果这三件都没有，就先不要写。

### 2. 先定清楚它属于哪一层

新增代码前先想清楚：

- HTTP 入口放 `api/http`
- 用例编排放 `application`
- 实体 / 枚举 / 状态放 `domain`
- repository / 外部 client / 配置绑定放 `infrastructure`
- 通用异常放 `shared/error`

不要把 controller、service、dto、client 再乱放到顶层。

### 3. 先补 HTTP DTO，再补 application DTO

命名固定按这套：

- 前端协议：
  - `*HttpRequest`
  - `*HttpResponse`

- backend 内部：
  - `*View`
  - `*Result`
  - `*Request`

不要让一个 DTO 同时承担“给前端返回”和“给内部 use case 传递”两种职责。

### 4. 至少拆成 controller + use case + query/command

如果这个功能会读写数据，默认至少拆成：

- `*Controller`
- `*UseCase`
- `*QueryService`
- `*CommandService`

简单功能不一定每次都要四个类完全齐，但至少要遵守一个原则：

- controller 不写流程
- use case 不直接表现 HTTP
- query 和 command 尽量分开

### 5. 补 mapper 和异常

一个新模块如果有 HTTP 输出，默认要有：

- `*HttpMapper`

如果有明确失败场景，优先复用：

- `ResourceNotFoundException`
- `BadRequestException`
- `ExternalServiceException`

不要再随手抛一堆没有语义的异常。

### 6. 改完必须验证

至少跑：

```bash
docker compose up --build -d backend
make smoke
```

如果主链被你改挂了，这个功能就不算完成。

## 新功能模板

如果以后要新增一个真正接入主链的模块，建议先照着这个 checklist 走：

1. 先写 `api/http/<module>/...`
2. 再写 `application/<module>/...`
3. 再补 `domain/<module>/...`
4. 最后接 `infrastructure/...`
5. 再补 DTO mapper
6. 再补异常路径
7. 最后跑验证

一句话记住：

```txt
先判断值不值得进主链，再按现有层次往下落
不要先摆空骨架
```

## 验证要求

任何 backend 结构调整后，至少要过：

```bash
docker compose up --build -d backend
make smoke
```

## 参考文档

- [`../README.md`](../README.md)
- [`../docs/database-storage/README.md`](../docs/database-storage/README.md)
