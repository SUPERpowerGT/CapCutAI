# Database Storage

这里专门记录 CapCutAI 当前阶段的数据库存储方式。

当前主线是：

```txt
IM + agent 最小闭环
```

所以这里重点只讲：

- conversation 如何存
- message 如何存
- 本地如何进入 PostgreSQL 查看

## 当前存储链路

一条消息现在的流转顺序是：

```txt
Frontend IM
  -> Next.js /api/im/* 代理
  -> Spring Boot Backend
  -> PostgreSQL 先保存 USER message
  -> Backend 调 ai-service
  -> PostgreSQL 再保存 ASSISTANT message
```

也就是说：

- `ai-service` 当前不负责持久化
- 真正落库的是 `backend`
- 数据库存储介质是 Docker 里的 PostgreSQL

## 当前数据库

默认容器：

```txt
capcutai-postgres
```

默认数据库连接信息：

- database: `capcutai`
- user: `capcutai`
- password: `capcutai`
- host port: `55432`

这些默认值来自根目录 [`.env.example`](../../.env.example)。

## 当前主要表

当前最重要的是两张表：

### 1. `conversations`

对应实体：

- [`ConversationEntity.java`](../../backend/src/main/java/com/capcutai/backend/domain/conversation/ConversationEntity.java)

主要字段：

- `conversation_id`
- `user_id`
- `session_id`
- `workspace_id`
- `title`
- `status`
- `created_at`
- `updated_at`

用途：

- 表示一个会话
- 绑定当前匿名用户标识
- 绑定当前匿名 session 标识
- 绑定当前 workspace / project 上下文
- 保存会话标题和状态
- 记录会话创建与最近更新时间

当前桌面客户端语义已经明确：

```txt
一个窗口 = 一个 workspace
workspace 下再挂 conversation
```

所以 `workspace_id` 现在是 conversation 的一级隔离字段：

- 不同窗口的新工作区应当有不同 `workspace_id`
- conversation 列表默认按 `workspace_id` 过滤
- 后续 asset、plan、render 也应逐步归属到同一个 `workspace_id`

### 2. `conversation_messages`

对应实体：

- [`ConversationMessageEntity.java`](../../backend/src/main/java/com/capcutai/backend/domain/message/ConversationMessageEntity.java)

主要字段：

- `message_id`
- `conversation_id`
- `role`
- `content`
- `status`
- `trace_json`
- `created_at`

用途：

- 保存用户消息和 assistant 消息
- `role` 区分 `USER / ASSISTANT / SYSTEM`
- `trace_json` 保存当前 agent trace

## 本地如何查看 PostgreSQL

进入容器：

```bash
docker exec -it capcutai-postgres psql -U capcutai -d capcutai
```

查看所有表：

```sql
\dt
```

查看 `conversations`：

```sql
select * from conversations order by created_at desc limit 20;
```

查看 `conversation_messages`：

```sql
select * from conversation_messages order by created_at desc limit 20;
```

查看某个会话的消息：

```sql
select
  message_id,
  conversation_id,
  role,
  content,
  status,
  trace_json,
  created_at
from conversation_messages
where conversation_id = '你的 conversationId'
order by created_at asc;
```

查看表结构：

```sql
\d conversations
\d conversation_messages
```

退出：

```sql
\q
```

## 当前要点

- 现在消息已经是持久化的，不是只存在内存里
- `make smoke` 跑一次后，就能在数据库里看到新会话和两条消息
- 当前 schema 还比较轻，后面如果接真实 agent 历史、工具调用、附件、素材索引，可以继续在这个目录扩展文档

## 参考

- [`../README.md`](../README.md)
- [`../../backend/README.md`](../../backend/README.md)
