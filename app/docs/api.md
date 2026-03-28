# API 接口文档 / API Reference

> **项目名称**: DeepAgents FastAPI  
> **版本**: 1.0.0  
> **基础路径**: `http://localhost:8000`  
> **交互文档**: [Swagger UI](/docs) | [ReDoc](/redoc)

---

## 1. 健康检查

### 1.1 全局健康检查

```
GET /health
```

**描述**: 检查整个服务的可用性，不涉及业务逻辑。

**响应**

| 状态码 | 内容 |
|--------|------|
| 200 | `{"status": "ok"}` |

**示例响应**

```json
{
  "status": "ok"
}
```

---

### 1.2 Agent 健康检查

```
GET /api/v1/agent/health
```

**描述**: 检查 Agent 模块是否可用。

**响应**

| 状态码 | 内容 |
|--------|------|
| 200 | `{"status": "ok", "backend": "opensandbox"}` |

**示例响应**

```json
{
  "status": "ok",
  "backend": "opensandbox"
}
```

---

## 2. 用户管理 `/api/v1/users`

### 2.1 创建用户

```
POST /api/v1/users/
```

**描述**: 创建新用户。用户名和邮箱必须唯一。

**请求体** (`UserCreate`)

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `username` | string | ✅ | 3-50 字符 | 用户名 |
| `email` | string | ✅ | 合法邮箱格式 | 邮箱 |
| `full_name` | string | ❌ | ≤100 字符 | 姓名 |
| `password` | string | ✅ | 6-128 字符 | 密码 |

**请求体示例**

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "password": "secret123"
}
```

**响应** (201 Created)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "alice",
  "email": "alice@example.com",
  "full_name": "Alice Smith",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-03-28T12:00:00",
  "updated_at": "2026-03-28T12:00:00"
}
```

**错误响应** (400 Bad Request)

```json
{
  "detail": "用户名已存在"
}
```

---

### 2.2 查询用户列表

```
GET /api/v1/users/
```

**描述**: 分页查询所有用户。

**Query 参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `skip` | integer | 0 | 跳过记录数（分页偏移） |
| `limit` | integer | 100 | 返回记录数上限 |

**响应** (200 OK)

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "username": "alice",
    "email": "alice@example.com",
    "full_name": "Alice Smith",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-03-28T12:00:00",
    "updated_at": "2026-03-28T12:00:00"
  }
]
```

---

### 2.3 获取单个用户

```
GET /api/v1/users/{user_id}
```

**描述**: 根据 `user_id` 获取用户详情。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | string (UUID) | 用户 ID |

**响应** (200 OK) — 同 2.2 中的用户对象

**错误响应** (404 Not Found)

```json
{
  "detail": "用户不存在"
}
```

---

### 2.4 更新用户

```
PATCH /api/v1/users/{user_id}
```

**描述**: 部分更新用户信息，所有字段均可选。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | string (UUID) | 用户 ID |

**请求体** (`UserUpdate`)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | string | ❌ | 新邮箱 |
| `full_name` | string | ❌ | 新姓名 |
| `password` | string | ❌ | 新密码 |
| `is_active` | boolean | ❌ | 是否启用 |

**请求体示例**

```json
{
  "email": "newalice@example.com",
  "is_active": true
}
```

**响应** (200 OK) — 返回更新后的完整用户对象（同 2.2）

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 404 | 用户不存在 |
| 400 | 邮箱已被注册 |

---

### 2.5 删除用户

```
DELETE /api/v1/users/{user_id}
```

**描述**: 物理删除用户，其关联的任务一并删除（CASCADE）。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | string (UUID) | 用户 ID |

**响应** (204 No Content) — 无响应体

**错误响应** (404 Not Found)

```json
{
  "detail": "用户不存在"
}
```

---

## 3. 任务队列 `/api/v1/tasks`

### 3.1 创建任务

```
POST /api/v1/tasks/
```

**描述**: 创建一个新任务，关联到指定用户。

**请求体** (`TaskCreate`)

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `title` | string | ✅ | 1-200 字符 | 任务标题 |
| `description` | string | ❌ | — | 任务描述 |
| `priority` | enum | ❌ | 默认 `normal` | 优先级：`low`, `normal`, `high`, `urgent` |
| `owner_id` | string | ✅ | UUID | 所属用户 ID |
| `max_retries` | integer | ❌ | 0-10，默认 3 | 最大重试次数 |

**请求体示例**

```json
{
  "title": "数据清洗任务",
  "description": "清洗用户数据中的重复记录",
  "priority": "high",
  "owner_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "max_retries": 3
}
```

**响应** (201 Created)

```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "title": "数据清洗任务",
  "description": "清洗用户数据中的重复记录",
  "status": "pending",
  "priority": "high",
  "result": null,
  "error": null,
  "progress": 0,
  "retry_count": 0,
  "max_retries": 3,
  "owner_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-03-28T12:05:00",
  "updated_at": "2026-03-28T12:05:00",
  "started_at": null,
  "completed_at": null
}
```

**错误响应** (404 Not Found)

```json
{
  "detail": "所属用户不存在"
}
```

---

### 3.2 查询任务列表

```
GET /api/v1/tasks/
```

**描述**: 查询任务列表，支持按状态和用户过滤，分页返回。

**Query 参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `status` | enum | — | 按状态过滤：`pending`, `running`, `success`, `failed`, `cancelled` |
| `owner_id` | string | — | 按用户 ID 过滤 |
| `skip` | integer | 0 | 跳过记录数 |
| `limit` | integer | 100 | 返回记录数（最大 500） |

**示例请求**

```
GET /api/v1/tasks/?status=pending&owner_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890&limit=10
```

**响应** (200 OK)

```json
[
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "title": "数据清洗任务",
    "description": "清洗用户数据中的重复记录",
    "status": "pending",
    "priority": "high",
    "result": null,
    "error": null,
    "progress": 0,
    "retry_count": 0,
    "max_retries": 3,
    "owner_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "created_at": "2026-03-28T12:05:00",
    "updated_at": "2026-03-28T12:05:00",
    "started_at": null,
    "completed_at": null
  }
]
```

---

### 3.3 获取单个任务

```
GET /api/v1/tasks/{task_id}
```

**描述**: 根据 `task_id` 获取任务详情。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**响应** (200 OK) — 返回完整任务对象（同 3.1 响应格式）

**错误响应** (404 Not Found)

```json
{
  "detail": "任务不存在"
}
```

---

### 3.4 更新任务

```
PATCH /api/v1/tasks/{task_id}
```

**描述**: 部分更新任务信息。任务开始后（non-pending），只能更新 `progress` 和 `status`。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体** (`TaskUpdate`)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ❌ | 新标题（pending 状态才可改） |
| `description` | string | ❌ | 新描述（pending 状态才可改） |
| `priority` | enum | ❌ | 新优先级（pending 状态才可改） |
| `max_retries` | integer | ❌ | 新最大重试次数（pending 状态才可改） |
| `progress` | integer | ❌ | 进度 0-100（任意状态可改） |

**错误响应** (400 Bad Request — 任务已开始)

```json
{
  "detail": "任务已开始，不允许修改 title"
}
```

---

### 3.5 更新任务状态

```
PATCH /api/v1/tasks/{task_id}/status
```

**描述**: 更新任务状态（任务执行器调用此接口），自动更新 `started_at` / `completed_at` 时间戳。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体** (`TaskStatusUpdate`)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | enum | ✅ | 新状态：`pending`, `running`, `success`, `failed`, `cancelled` |
| `result` | string | ❌ | 执行结果（成功时写入） |
| `error` | string | ❌ | 错误信息（失败时写入） |
| `progress` | integer | ❌ | 进度 0-100 |

**请求体示例**

```json
{
  "status": "running",
  "progress": 0
}
```

**状态流转规则**

| 当前状态 | 可流转至 |
|----------|----------|
| `pending` | `running`, `cancelled` |
| `running` | `success`, `failed`, `cancelled` |
| `failed` | `pending`（通过 retry 接口） |
| `success` | 不可流转 |
| `cancelled` | 不可流转 |

**时间戳行为**

| 新状态 | 副作用 |
|--------|--------|
| `running` | 若 `started_at` 为空，自动设置为当前时间 |
| `success` / `failed` / `cancelled` | 自动设置 `completed_at` 为当前时间 |

**响应** (200 OK) — 返回更新后的任务对象

---

### 3.6 取消任务

```
POST /api/v1/tasks/{task_id}/cancel
```

**描述**: 取消任务。只有 `pending` 或 `running` 状态的任务可以取消。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**响应** (200 OK) — 任务状态更新为 `cancelled`，`completed_at` 设为当前时间

**错误响应** (400 Bad Request)

```json
{
  "detail": "当前状态 success 无法取消"
}
```

---

### 3.7 重试任务

```
POST /api/v1/tasks/{task_id}/retry
```

**描述**: 重试一个失败的任务。任务重置为 `pending`，`retry_count` +1。

**前置条件**

- 任务状态必须为 `failed`
- `retry_count < max_retries`

**重置字段**

- `status` → `pending`
- `retry_count` += 1
- `error` → `null`
- `started_at` → `null`
- `completed_at` → `null`
- `progress` → `0`

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**响应** (200 OK) — 返回重置后的任务对象

**错误响应**

| 状态码 | 原因 |
|--------|------|
| 400 | 只有失败任务可以重试 |
| 400 | 已达到最大重试次数 |
| 404 | 任务不存在 |

---

### 3.8 删除任务

```
DELETE /api/v1/tasks/{task_id}
```

**描述**: 删除任务。正在运行（running）的任务无法删除。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**响应** (204 No Content) — 无响应体

**错误响应** (400 Bad Request)

```json
{
  "detail": "任务正在运行，无法删除"
}
```

---

## 4. Agent 对话 `/api/v1/agent`

### 4.1 普通对话（同步）

```
POST /api/v1/agent/chat
```

**描述**: 与 Agent 对话（非流式），返回完整回复。

**请求体** (`ChatRequest`)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `messages` | array[Message] | ✅ | — | 消息历史列表 |
| `backend` | string | ❌ | `opensandbox` | 沙箱后端：`opensandbox`, `daytona`, `modal` |
| `stream` | boolean | ❌ | `false` | 保留字段（本接口为同步） |

**Message 结构**

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | string | 角色：`user` / `assistant` / `system` |
| `content` | string | 消息内容 |

**请求体示例**

```json
{
  "messages": [
    {"role": "system", "content": "你是一个有帮助的编程助手。"},
    {"role": "user", "content": "帮我写一个快速排序算法"}
  ],
  "backend": "opensandbox",
  "stream": false
}
```

**响应** (200 OK)

```json
{
  "message": "以下是 Python 实现的快速排序算法...\n\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
  "finish_reason": "stop",
  "backend": "opensandbox"
}
```

**错误响应** (500 Internal Server Error)

```json
{
  "detail": "OpenSandbox API key not configured"
}
```

---

### 4.2 流式对话（SSE）

```
POST /api/v1/agent/chat/stream
```

**描述**: 通过 SSE（Server-Sent Events）流式返回 Agent 回复，适合实时打字机效果。

**请求体** — 同 4.1 `ChatRequest`

**响应** — `StreamingResponse`

| 头信息 | 值 |
|--------|-----|
| `Content-Type` | `text/event-stream` |
| `Cache-Control` | `no-cache` |
| `Connection` | `keep-alive` |
| `X-Accel-Buffering` | `no` |

**SSE 数据格式**

| 事件 | 内容 |
|------|------|
| 正常片段 | `data: <内容片段>\n\n` |
| 结束 | `data: [DONE]\n\n` |
| 错误 | `data: ERROR: <错误信息>\n\n` |

**SSE 事件流示例**

```
data: 以下
data:  是
data:  Python
data:  实现
data:  的
data:  快速排序
data:  算法
data:  ...
data: [DONE]
```

**前端消费示例（JavaScript）**

```javascript
const response = await fetch('/api/v1/agent/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [{ role: 'user', content: '帮我写一个快排' }],
    backend: 'opensandbox'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  // chunk 格式: "data: <内容>\n\n"
  console.log(chunk);
}
```

---

### 4.3 重置沙箱

```
POST /api/v1/agent/reset
```

**描述**: 销毁当前沙箱实例，下次对话时自动冷启动新实例。用于解决沙箱状态异常或内存泄漏问题。

**Query 参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `backend` | string | `opensandbox` | 指定沙箱后端 |

**响应** (200 OK)

```json
{
  "status": "reset",
  "message": "opensandbox 沙箱已重置，下次请求会自动冷启动",
  "backend": "opensandbox"
}
```

**错误响应** (500 Internal Server Error)

```json
{
  "detail": "Failed to shutdown sandbox"
}
```

---

## 5. SSE 模块 `/api/v1/sse`

### 5.1 SSE 事件流

```
GET /api/v1/sse
```

**描述**: 基础 SSE 演示端点，发送 10 条模拟事件后自动结束。每条事件间隔 1 秒。

**响应** — `StreamingResponse`

| 头信息 | 值 |
|--------|-----|
| `Content-Type` | `text/event-stream` |
| `Cache-Control` | `no-cache` |
| `Connection` | `keep-alive` |

**SSE 事件格式**

```
data: {"index": 0, "time": "2026-03-28 12:00:00", "message": "Event #1"}\n\n
data: {"index": 1, "time": "2026-03-28 12:00:01", "message": "Event #2"}\n\n
...
data: {"index": 9, "time": "2026-03-28 12:00:09", "message": "Event #10"}\n\n
```

**使用场景**: 作为 SSE 接入参考，了解 SSE 基本用法。

---

### 5.2 SSE 实时时钟

```
GET /api/v1/sse/clock
```

**描述**: 实时时钟 SSE 流，持续每秒推送当前时间，直到客户端断开连接。

**响应** — `StreamingResponse`（同 5.1）

**SSE 事件格式**

```
data: {"time": "2026-03-28 12:00:00", "timestamp": 1743225600.0}\n\n
data: {"time": "2026-03-28 12:00:01", "timestamp": 1743225601.0}\n\n
data: {"time": "2026-03-28 12:00:02", "timestamp": 1743225602.0}\n\n
...
```

**使用场景**: 监控面板、实时数据展示、客户端时钟同步。

---

## 6. 通用错误码说明

| HTTP 状态码 | 含义 | 典型场景 |
|-------------|------|----------|
| `200 OK` | 请求成功 | GET 成功、PATCH 更新成功 |
| `201 Created` | 资源创建成功 | POST 创建用户/任务成功 |
| `204 No Content` | 请求成功，无返回内容 | DELETE 删除成功 |
| `400 Bad Request` | 请求参数错误或业务逻辑不允许 | 用户名重复、状态机非法流转、邮箱格式错误 |
| `404 Not Found` | 资源不存在 | user_id 或 task_id 不存在 |
| `422 Unprocessable Entity` | Pydantic 校验失败 | 必填字段缺失、字段类型不匹配、长度超限 |
| `500 Internal Server Error` | 服务器内部错误 | Agent 调用失败、数据库异常 |

**标准错误响应格式**

```json
{
  "detail": "错误描述文字"
}
```

**统一业务异常格式（AppException）**

```json
{
  "code": "NOT_FOUND",
  "message": "资源不存在"
}
```

| 错误码 | 说明 |
|--------|------|
| `NOT_FOUND` | 资源不存在（404） |
| `UNAUTHORIZED` | 未授权（401） |
| `FORBIDDEN` | 禁止访问（403） |
| `VALIDATION_ERROR` | 数据校验失败（422） |

---

## 7. 全局 Schema 一览

### 7.1 User Schema

| Schema | 用途 |
|--------|------|
| `UserBase` | 基础字段（username, email, full_name） |
| `UserCreate` | 创建请求体 = UserBase + password |
| `UserUpdate` | 更新请求体（全字段可选） |
| `UserResponse` | 响应体（包含 id, is_active, is_superuser, 时间戳） |
| `UserBrief` | 简要信息（嵌套场景使用） |
| `Token` | JWT Token 响应（仅 access_token，兼容旧接口） |
| `TokenResponse` | 完整 Token 响应（access_token + refresh_token） |
| `RefreshRequest` | 刷新 Token 请求体（refresh_token） |

### 7.2 Task Schema

| Schema | 用途 |
|--------|------|
| `TaskBase` | 基础字段（title, description, priority） |
| `TaskCreate` | 创建请求体 = TaskBase + owner_id + max_retries |
| `TaskUpdate` | 更新请求体（全字段可选，进度单独校验 0-100） |
| `TaskStatusUpdate` | 状态更新专用（status + result/error/progress） |
| `TaskResponse` | 响应体（完整任务信息） |
| `TaskBrief` | 简要信息 |

### 7.3 Agent Schema

| Schema | 用途 |
|--------|------|
| `Message` | 消息结构 {role, content} |
| `ChatRequest` | 对话请求体 {messages, backend, stream} |
| `ChatResponse` | 同步对话响应 {message, finish_reason, backend} |

---

## 8. 数据类型定义

### 8.1 TaskStatus 枚举

| 值 | 说明 |
|-----|------|
| `pending` | 待执行 |
| `running` | 执行中 |
| `success` | 执行成功 |
| `failed` | 执行失败（可重试） |
| `cancelled` | 已取消 |

### 8.2 TaskPriority 枚举

| 值 | 说明 |
|-----|------|
| `low` | 低优先级 |
| `normal` | 普通优先级（默认） |
| `high` | 高优先级 |
| `urgent` | 紧急优先级 |

---

*文档版本: 1.0.0 | 最后更新: 2026-03-28*

---

## 9. 认证 `/api/v1/users`

### 9.1 用户登录

```
POST /api/v1/auth/login
```

**描述**: 用户登录，获取 JWT Access Token 和 Refresh Token。

**请求体** (`LoginRequest`)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | ✅ | 用户名 |
| `password` | string | ✅ | 密码 |

**响应** (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | string | JWT Access Token，有效期 30 分钟 |
| `refresh_token` | string | JWT Refresh Token，有效期 7 天 |
| `token_type` | string | 固定为 `bearer` |

**错误响应** (401 Unauthorized)

```json
{
  "detail": "用户名或密码错误"
}
```

---

### 9.2 刷新 Token

```
POST /api/v1/auth/refresh
```

**描述**: 使用 Refresh Token 换取新的 Access Token 和 Refresh Token。

**请求体** (`RefreshRequest`)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `refresh_token` | string | ✅ | 登录时获取的 Refresh Token |

**响应** (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应** (401 Unauthorized)

```json
{
  "code": "UNAUTHORIZED",
  "message": "Refresh Token 无效或已过期"
}
```

### 9.3 登出

```
POST /api/v1/auth/logout
```

**描述**: 用户登出，将当前 Access Token 加入黑名单。Token 黑名单有效期最长 1 天。

**请求体** (`LogoutRequest`)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `token` | string | ✅ | 当前 Access Token |

**请求体示例**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应** (200 OK)

```json
{
  "message": "登出成功"
}
```

**错误响应** (401 Unauthorized)

```json
{
  "detail": "Token 无效"
}
```

---

## 10. 文件管理 `/api/v1/files`

### 10.1 上传文件

```
POST /api/v1/files/upload
```

**描述**: 上传单个文件（最大 10MB）。

**请求**: `multipart/form-data`，字段名 `file`

**响应** (201 Created)

```json
{
  "filename": "a1b2c3d4e5f6.png",
  "original_filename": "avatar.png",
  "size": 102400,
  "url": "/api/v1/files/a1b2c3d4e5f6.png"
}
```

**错误响应** (413 Request Entity Too Large)

```json
{
  "detail": "文件大小超过限制（最大 10MB）"
}
```

### 10.2 下载文件

```
GET /api/v1/files/{filename}
```

**描述**: 下载已上传的文件。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `filename` | string | 上传时返回的文件名 |

**响应**: 文件流（application/octet-stream）

**错误响应** (404 Not Found)

```json
{
  "detail": "文件不存在"
}
```

### 10.3 删除文件

```
DELETE /api/v1/files/{filename}
```

**响应** (204 No Content)

---

## 11. WebSocket `/ws`

### 11.1 WebSocket 连接

```
WS /ws?user_id=xxx
```

**描述**: WebSocket 实时聊天/通知连接，支持广播和个人消息。

**Query 参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_id` | string | `anonymous` | 用户标识 |

**消息格式（客户端发送）**

```json
// 普通广播消息
{"type": "message", "content": "Hello everyone!"}

// 系统消息
{"type": "system", "content": "系统通知内容"}

// 个人消息
{"type": "personal", "to": "target_user_id", "content": "Private message"}
```

**消息格式（服务端推送）**

```json
{
  "type": "message",
  "user_id": "user_xxx",
  "content": "Hello everyone!",
  "timestamp": "2026-03-28T12:00:00"
}
```

---

## 12. 任务增强功能

### 12.1 任务标签

任务新增 `tags` 字段（JSON 数组），支持在创建和更新任务时指定。

**创建任务时指定标签**

```json
{
  "title": "数据清洗任务",
  "owner_id": "...",
  "tags": ["清洗", "ETL", "重要"]
}
```

### 12.2 任务重试

```
PATCH /api/v1/tasks/{task_id}/retry
```

**描述**: 重试失败任务。任务重置为 `pending`，`retry_count` +1。

**前置条件**: 任务状态必须为 `failed`，且 `retry_count < max_retries`。

**重置字段**: `status` → `pending`，`error` → `null`，`started_at` → `null`，`completed_at` → `null`，`progress` → `0`。

---

## 13. 限流规则

| 端点 | 限制 |
|------|------|
| 全局（所有接口） | 100 次/分钟 |
| `/api/v1/agent/*` | 10 次/分钟 |

**触发限流时返回** (429 Too Many Requests)

```json
{
  "detail": "请求过于频繁，请稍后再试。"
}
```

---

## 14. Webhook 回调

任务状态变更时，系统会自动触发 Webhook（异步，不阻塞主流程）。

**触发时机**: `task.created`, `task.status_changed`, `task.retried`, `task.cancelled`

**Payload 示例**

```json
{
  "event": "task.status_changed",
  "task": {
    "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
    "title": "数据清洗任务",
    "status": "success",
    "result": "处理了 1000 条记录",
    "error": null,
    "owner_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

**配置方式**: 在 `.env` 中设置 `WEBHOOK_URL=https://your-webhook-endpoint.com/notify`

---

## 15. 邮件通知

任务状态变更为 `success` 或 `failed` 时，自动发送邮件通知（需配置 SMTP）。

**.env SMTP 配置示例**

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_password
SMTP_FROM=noreply@example.com
```

---

*文档版本: 1.2.0 | 最后更新: 2026-03-28*

---

## 16. 统一错误码

所有业务错误均使用统一错误码，便于客户端程序化处理。

### 16.1 错误码一览

| 错误码 | 说明 |
|--------|------|
| `AUTH_001` | Invalid credentials — 用户名或密码错误 |
| `AUTH_002` | Token expired — Token 已过期 |
| `AUTH_003` | Token invalid — Token 无效或已被黑名单 |
| `USER_001` | User not found — 用户不存在 |
| `USER_002` | User already exists — 用户名或邮箱已被注册 |
| `TASK_001` | Task not found — 任务不存在 |
| `TASK_002` | Invalid task status — 非法任务状态或状态流转 |
| `VALIDATION_001` | Validation error — 数据校验失败 |

### 16.2 Token 黑名单

登出后 Token 会被加入黑名单，黑名单基于 JWT `jti`（JWT ID）标识，有效期最长 1 天。

**后端存储**:

- Redis（优先）：`token:blacklist:<jti>`
- 内存回退（Redis 不可用时）：进程重启后黑名单丢失

---

## 17. 缓存层

### 17.1 缓存策略

| 缓存项 | 后端 | TTL | 说明 |
|--------|------|-----|------|
| Token 黑名单 | Redis / 内存 | ≤ 86400s | logout 后 token 失效 |
| 其他业务缓存 | Redis / 内存 | 可配置 | — |

### 17.2 Redis 不可用时

系统自动检测 Redis 可用性，不可用时回退到进程内内存字典。内存模式下缓存重启后丢失，但不影响核心功能。

---

## 18. API v2 版本控制 `/api/v2`

> v2 在 v1 基础上新增批量操作、GraphQL 端点及多语言支持。

### 18.1 用户管理 v2 `/api/v2/users`

v2 用户路由与 v1 (`/api/v1/users`) 共享相同基础功能，额外提供以下端点：

#### 批量删除用户

```
POST /api/v2/users/batch/delete
```

**请求体**

```json
{
  "user_ids": ["id1", "id2", "id3"]
}
```

**响应** (204 No Content)

---

#### 批量更新用户状态

```
PATCH /api/v2/users/batch/update
```

**请求体**

```json
{
  "user_ids": ["id1", "id2"],
  "is_active": false
}
```

**响应** (200 OK) — 返回更新后的用户对象列表

---

#### 批量检查用户存在性

```
GET /api/v2/users/batch/exists?user_ids=id1,id2,id3
```

**响应** (200 OK)

```json
{
  "exists": {
    "id1": true,
    "id2": false,
    "id3": true
  },
  "all_exist": false
}
```

---

### 18.2 任务队列 v2 `/api/v2/tasks`

#### 批量创建任务

```
POST /api/v2/tasks/batch
```

**请求体**

```json
{
  "tasks": [
    {
      "title": "任务1",
      "owner_id": "user_uuid",
      "priority": "normal"
    },
    {
      "title": "任务2",
      "owner_id": "user_uuid",
      "priority": "high"
    }
  ]
}
```

**响应** (201 Created) — 返回创建的任务对象列表

---

#### 批量分发任务

```
POST /api/v2/tasks/batch/dispatch
```

**请求体**

```json
{
  "task_ids": ["task_id1", "task_id2"]
}
```

**响应** (200 OK)

```json
{
  "dispatched": ["task_id1"],
  "skipped": [{"task_id": "task_id2", "status": "running"}],
  "mode": "async"
}
```

---

## 19. GraphQL API `/graphql`

> Strawberry GraphQL 支持，兼容 FastAPI。访问 `/graphql` 使用交互式 Playground。

### 19.1 Query

#### 获取用户列表

```graphql
query {
  users(limit: 10) {
    id
    username
    email
    createdAt
  }
}
```

#### 获取单个用户

```graphql
query {
  user(userId: "uuid") {
    id
    username
    email
    createdAt
  }
}
```

#### 获取任务列表

```graphql
query {
  tasks(status: "pending", ownerId: "uuid", limit: 20) {
    id
    title
    status
    priority
    createdAt
    updatedAt
  }
}
```

#### 获取任务状态统计

```graphql
query {
  taskStats {
    pending
    running
    success
    failed
    cancelled
  }
}
```

#### 健康检查

```graphql
query {
  health {
    status
    version
  }
}
```

### 19.2 Mutation

#### Agent 对话

```graphql
mutation {
  chat(message: "你好") {
    message
    success
  }
}
```

#### 重置 Agent

```graphql
mutation {
  resetAgent(backend: "opensandbox") {
    message
    success
  }
}
```

---

## 20. 国际化 (i18n)

### 20.1 支持语言

| 语言代码 | 说明 |
|----------|------|
| `zh_CN` | 简体中文（默认） |
| `en_US` | 英语 |
| `ja_JP` | 日语 |
| `ko_KR` | 韩语 |

### 20.2 语言检测

系统通过请求头 `Accept-Language` 自动检测语言，按以下优先级：

1. `Accept-Language` 请求头（精确匹配）
2. 默认语言 `zh_CN`

### 20.3 翻译消息结构

```python
from app.i18n import get_message

# 示例
get_message("zh_CN", "auth.login_success")
# -> "登录成功"

get_message("en_US", "user.not_found")
# -> "User not found"

# 支持嵌套 key
get_message("zh_CN", "task.status_updated")
# -> "状态已更新"
```

### 20.4 翻译文件位置

```
app/i18n/
├── __init__.py
├── middleware.py
└── locales/
    ├── zh_CN.json
    ├── en_US.json
    ├── ja_JP.json
    └── ko_KR.json
```

### 20.5 中间件

`I18nMiddleware` 自动将语言代码注入 `request.state.lang`，路由中可通过 `request.state.lang` 访问当前语言。

---

*文档版本: 2.0.0 | 最后更新: 2026-03-28*
