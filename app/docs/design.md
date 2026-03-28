# 设计文档 / Design Document

> **项目名称**: DeepAgents FastAPI  
> **版本**: 1.0.0  
> **日期**: 2026-03-28

---

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           客户端层                                   │
│   (浏览器 / Postman / 前端应用 / 第三方 API 消费者)                   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │  HTTP / SSE
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI 应用层                               │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Users   │  │  Tasks   │  │  Agent   │  │   SSE    │            │
│  │ Router   │  │ Router   │  │ Router   │  │ Router   │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │             │             │                   │
│       ▼             ▼             ▼             │                   │
│  ┌─────────────────────────────────────┐       │                   │
│  │         Pydantic Schemas            │       │                   │
│  │   (请求校验 / 响应序列化)              │       │                   │
│  └─────────────────┬───────────────────┘       │                   │
└────────────────────┼───────────────────────────┼───────────────────┘
                     │                           │
                     ▼                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         数据层                                       │
│                                                                      │
│   ┌─────────────────┐              ┌─────────────────┐              │
│   │  SQLite (dev)   │              │  PostgreSQL     │              │
│   │  aiosqlite      │              │  (production)   │              │
│   └────────┬────────┘              └────────┬────────┘              │
│            │  async SQLAlchemy              │                        │
│   ┌────────▼─────────────────────────────────▼────────┐              │
│   │              SQLAlchemy ORM Models                │              │
│   │              User  │  Task                       │              │
│   └───────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent / 沙箱后端层                                  │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │              SandboxAgent (统一封装)                       │      │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │      │
│   │  │ OpenSandbox│  │  Daytona   │  │   Modal    │          │      │
│   │  │  Backend   │  │  Backend   │  │  Backend   │          │      │
│   │  └────────────┘  └────────────┘  └────────────┘          │      │
│   └──────────────────────────────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │  DeepAgent + LangChain (ChatAnthropic / Claude)          │      │
│   └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 架构说明

| 层级 | 组件 | 职责 |
|------|------|------|
| **客户端层** | 浏览器 / Postman / 前端 | 发起 HTTP 请求消费 API |
| **应用层** | FastAPI + Routers | 路由分发、请求校验、业务逻辑编排 |
| **数据层** | SQLAlchemy ORM + SQLite | 数据持久化、异步数据库操作 |
| **Agent 层** | DeepAgent + LangChain + 沙箱 | AI 推理、沙箱环境管理 |

---

## 2. 技术选型说明

### 2.1 核心技术栈

| 技术 | 选型 | 理由 |
|------|------|------|
| **Web 框架** | FastAPI | 异步原生支持、自动 OpenAPI 生成、Pydantic 深度集成 |
| **ORM** | SQLAlchemy 2.0 (async) | 类型安全、async 全面支持、社区成熟 |
| **数据库** | SQLite (dev) / PostgreSQL (prod) | 开发零配置；生产可切换（同异步接口不变） |
| **数据校验** | Pydantic v2 | 与 FastAPI 无缝集成，自动生成 JSON Schema |
| **配置管理** | pydantic-settings | 环境变量驱动，符合 12-Factor 原则 |
| **AI Agent** | DeepAgents + LangChain | 统一封装多种沙箱后端，支持流式输出 |
| **LLM** | ChatAnthropic (Claude) | 与沙箱结合实现 Code Agent 能力 |
| **异步驱动** | aiosqlite | SQLite 异步访问，不阻塞事件循环 |

### 2.2 替代方案对比

| 方案 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| 异步支持 | ✅ 原生 async/await | ❌ 同步 | ❌ 同步 |
| OpenAPI | ✅ 自动生成 | ❌ 需 Flask-RESTX | ✅ DRF 可选 |
| 类型安全 | ✅ Pydantic | ❌ 无 | ❌ 无 |
| 性能 | ✅ 高（Starlette） | 一般 | 一般 |
| 生态 | 丰富（LangChain 适配） | 丰富 | 丰富 |

---

## 3. 数据模型设计

### 3.1 ER 图（实体关系）

```
┌─────────────────────────────────────────────────────────────┐
│                         users                                │
│  (id: UUID PK) ────────────────────────────────────────────│
│  username: String(50) UNIQUE INDEX                         │
│  email: String(255) UNIQUE INDEX                           │
│  hashed_password: String(255)                              │
│  full_name: String(100) NULLABLE                          │
│  is_active: Boolean                                        │
│  is_superuser: Boolean                                     │
│  created_at: DateTime                                      │
│  updated_at: DateTime                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N (owner_id → FK)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         tasks                                │
│  (id: UUID PK)                                             │
│  title: String(200)                                        │
│  description: Text NULLABLE                                │
│  status: Enum(PENDING/RUNNING/SUCCESS/FAILED/CANCELLED)   │
│  priority: Enum(LOW/NORMAL/HIGH/URGENT)                    │
│  result: Text NULLABLE                                    │
│  error: Text NULLABLE                                      │
│  progress: Integer (0-100)                                 │
│  retry_count: Integer                                      │
│  max_retries: Integer                                      │
│  owner_id: String(36) FK → users.id                        │
│  created_at: DateTime                                      │
│  updated_at: DateTime                                      │
│  started_at: DateTime NULLABLE                             │
│  completed_at: DateTime NULLABLE                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 字段设计说明

#### User 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID String(36) | PK | 主键，UUID v4 |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 登录用户名 |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | 邮箱地址 |
| `hashed_password` | VARCHAR(255) | NOT NULL | SHA256 哈希后的密码 |
| `full_name` | VARCHAR(100) | NULLABLE | 用户全名 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT True | 账号是否启用 |
| `is_superuser` | BOOLEAN | NOT NULL, DEFAULT False | 是否超级用户 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

#### Task 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID String(36) | PK | 主键 |
| `title` | VARCHAR(200) | NOT NULL | 任务标题 |
| `description` | TEXT | NULLABLE | 详细描述 |
| `status` | ENUM | NOT NULL, INDEX, DEFAULT pending | 当前状态 |
| `priority` | ENUM | NOT NULL, DEFAULT normal | 优先级 |
| `result` | TEXT | NULLABLE | 执行结果（完成后写入） |
| `error` | TEXT | NULLABLE | 错误信息（失败时写入） |
| `progress` | INT | NOT NULL, DEFAULT 0 | 进度 0-100 |
| `retry_count` | INT | NOT NULL, DEFAULT 0 | 已重试次数 |
| `max_retries` | INT | NOT NULL, DEFAULT 3 | 最大重试次数 |
| `owner_id` | VARCHAR(36) | FK → users.id, NOT NULL, INDEX | 所属用户 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |
| `started_at` | DATETIME | NULLABLE | 开始执行时间 |
| `completed_at` | DATETIME | NULLABLE | 完成时间 |

### 3.3 任务状态机

```
                    ┌──────────────────────────────────┐
                    │                                  │
    ┌──────┐       ┌▼────────┐       ┌───────────┐   │
    │pending│──────►│ running │──────►│  success  │   │
    └──┬───┘       └────┬─────┘       └───────────┘   │
       │               │                    ▲          │
       │               │  ┌───────────┐    │          │
       │               └──►│  failed   │────┴──────────┘ (可重试)
       │                   └──┬────────┘
       │                      │
       │              retry ──┘ (retry_count < max_retries)
       │
       │               ┌───────────┐
       └──────────────►│ cancelled│
                       └───────────┘

   状态说明:
   - pending:   任务创建，等待执行器拉取
   - running:   执行中，started_at 自动记录
   - success:   执行成功，completed_at 自动记录
   - failed:    执行失败，可重试（检查 retry_count）
   - cancelled: 用户主动取消，completed_at 自动记录
```

---

## 4. 模块设计

### 4.1 模块职责

| 模块路径 | 职责 | 关键类/函数 |
|----------|------|-------------|
| `app/main.py` | FastAPI 应用入口，生命周期管理 | `app: FastAPI`, `lifespan()` |
| `app/core/config.py` | 全局配置管理（Settings） | `Settings` |
| `app/core/database.py` | 数据库引擎、会话、初始化 | `AsyncSessionLocal`, `get_db()`, `init_db()` |
| `app/models/user.py` | User ORM 模型 | `class User(Base)` |
| `app/models/task.py` | Task ORM 模型 + 枚举 | `class Task(Base)`, `TaskStatus`, `TaskPriority` |
| `app/schemas/*.py` | Pydantic 请求/响应模型 | `UserCreate`, `UserResponse`, `TaskCreate`, `TaskResponse` ... |
| `app/routers/users.py` | 用户 CRUD 路由 | `router: APIRouter` |
| `app/routers/tasks.py` | 任务队列路由 | `router: APIRouter` |
| `app/routers/agent.py` | Agent 对话路由 | `router: APIRouter` |
| `app/routers/sse.py` | SSE 流式路由 | `router: APIRouter` |
| `app/routers/example.py` | 示例路由 | `router: APIRouter` |
| `app/sandbox/agent_runner.py` | 沙箱 Agent 封装 | `SandboxAgent`, `get_agent()` |
| `app/sandbox/backends/*.py` | 各沙箱后端适配器 | `OpenSandboxBackend`, `DaytonaBackend`, `ModalBackend` |

### 4.2 SandboxAgent 设计

```
SandboxAgent
├── __init__(model_name, system_prompt, backend_type)
├── _create_backend()     → 根据 backend_type 实例化对应后端
├── _create_model()       → 创建 ChatAnthropic 模型
├── initialize()         → 异步初始化（冷启动）
├── invoke(messages)      → 同步调用 Agent
└── stop()                → 异步停止沙箱

全局单例: _agent_instance (通过 get_agent() / shutdown_agent() 管理)
```

支持的 `backend_type`:
- `opensandbox` → `OpenSandboxBackend`（已实现）
- `daytona` → `DaytonaSandbox`（预留）
- `modal` → `ModalSandbox`（预留）

---

## 5. API 设计原则

### 5.1 RESTful 设计规范

| 规范 | 说明 |
|------|------|
| 路径命名 | 使用复数名词 `/api/v1/users`, `/api/v1/tasks` |
| HTTP 方法 | GET（查询）、POST（创建）、PATCH（部分更新）、DELETE（删除） |
| 状态码 | 200 OK、201 Created、204 No Content、400 Bad Request、404 Not Found、500 Internal Server Error |
| 分页 | `skip` + `limit` 参数，默认 skip=0, limit=100 |
| 过滤 | 通过 Query 参数实现，如 `?status=pending&owner_id=xxx` |

### 5.2 Pydantic Schema 设计原则

| 类型 | 用途 | 文件约定 |
|------|------|----------|
| `*Create` | POST 请求体 | `xxx.py` |
| `*Update` | PATCH 请求体（全字段可选） | `xxx.py` |
| `*Response` | 响应模型（返回给客户端） | `xxx.py` |
| `*Brief` | 简要信息（嵌套场景） | `xxx.py` |

### 5.3 错误处理规范

所有 HTTP 异常通过 `HTTPException` 抛出，格式示例：

```json
{
  "detail": "用户不存在"
}
```

错误场景覆盖：
- 400: 参数校验失败、用户名重复、状态机非法流转
- 404: 资源不存在（用户/任务）
- 500: 内部错误（Agent 调用失败等）

---

## 6. 目录结构说明

```
app/
│
├── main.py                      # FastAPI 应用入口
│                                 # - lifespan: 启动时 init_db()
│                                 # - CORS 中间件注册
│                                 # - 路由注册（users, tasks, agent, sse, example）
│
├── core/                         # 核心基础设施
│   ├── config.py                 # pydantic-settings 配置类
│   └── database.py               # SQLAlchemy async 引擎 + Session 依赖注入
│
├── models/                       # SQLAlchemy ORM 模型（数据库表映射）
│   ├── user.py                   # User 模型（用户表）
│   └── task.py                   # Task 模型（任务表）+ 枚举定义
│
├── schemas/                      # Pydantic 请求/响应模型
│   ├── user.py                   # UserCreate / UserUpdate / UserResponse
│   └── task.py                   # TaskCreate / TaskUpdate / TaskStatusUpdate / TaskResponse
│
├── routers/                      # FastAPI 路由模块（Controller 层）
│   ├── users.py                  # /api/v1/users CRUD
│   ├── tasks.py                  # /api/v1/tasks CRUD + 状态管理
│   ├── agent.py                  # /api/v1/agent/chat, /chat/stream, /reset, /health
│   ├── sse.py                    # /sse, /sse/clock
│   └── example.py                # /example (示例路由)
│
├── sandbox/                      # Agent 沙箱集成
│   ├── agent_runner.py           # SandboxAgent 封装 + 全局单例管理
│   └── backends/                 # 沙箱后端适配器
│       ├── opensandbox_backend.py   # OpenSandbox 适配（已实现）
│       ├── daytona_backend.py       # Daytona 预留
│       └── modal_backend.py         # Modal 预留
│
└── docs/                         # 项目文档（本文档目录）
    ├── requirements.md           # 需求文档
    ├── design.md                 # 设计文档
    └── api.md                    # API 接口文档
```

---

## 7. 启动与配置

### 7.1 环境变量

| 变量名 | 默认值 | 必填 | 说明 |
|--------|--------|------|------|
| `APP_NAME` | `FastAPI Project` | 否 | 服务名称 |
| `APP_VERSION` | `1.0.0` | 否 | 服务版本 |
| `DEBUG` | `True` | 否 | 调试模式 |
| `DATABASE_URL` | `sqlite+aiosqlite:///fastapi_project.db` | 否 | 数据库连接 |
| `OPENSANDBOX_API_KEY` | `""` | 是* | OpenSandbox API Key（使用 Agent 功能时必填）|
| `OPENSANDBOX_DOMAIN` | `api.opensandbox.io` | 否 | OpenSandbox 域名 |
| `OPENSANDBOX_IMAGE` | `ubuntu` | 否 | 沙箱镜像 |

### 7.2 启动命令

```bash
cd app
uvicorn app.main:app --reload --port 8000
```

访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- 根路径: `http://localhost:8000/`
