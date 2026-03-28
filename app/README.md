# DeepAgents FastAPI

> 多沙箱后端 AI Agent 服务，基于 FastAPI 构建

## 技术栈

- **框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy (async)
- **Agent**: DeepAgents + LangChain + ChatAnthropic
- **沙箱后端**: OpenSandbox / Daytona (预留) / Modal (预留)

## 快速启动

```bash
cd app

# 安装依赖
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-dotenv

# 启动服务
uvicorn app.main:app --reload --port 8000
```

访问:
- API 文档: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## 项目结构

```
app/
├── main.py              # FastAPI 主入口
├── core/
│   ├── config.py        # Settings 配置
│   └── database.py      # SQLite + SQLAlchemy 初始化
├── models/
│   ├── user.py          # User ORM 模型
│   └── task.py          # Task ORM 模型（状态机）
├── schemas/
│   ├── user.py          # User Pydantic schemas
│   └── task.py          # Task Pydantic schemas
├── routers/
│   ├── users.py         # 用户 CRUD 路由
│   ├── tasks.py         # 任务队列路由
│   ├── agent.py         # Agent 对话路由
│   ├── example.py       # 示例路由
│   └── sse.py           # SSE 流式路由
└── sandbox/
    ├── agent_runner.py  # DeepAgent 集成
    └── backends/
        ├── opensandbox_backend.py  # OpenSandbox 后端
        ├── daytona_backend.py      # Daytona 占位（未接入）
        └── modal_backend.py        # Modal 占位（未接入）
```

## API 路由概览

### 用户管理 `/api/v1/users`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/users/` | 创建用户 |
| GET | `/api/v1/users/` | 查询用户列表 |
| GET | `/api/v1/users/{id}` | 获取单个用户 |
| PATCH | `/api/v1/users/{id}` | 更新用户 |
| DELETE | `/api/v1/users/{id}` | 删除用户 |

### 任务队列 `/api/v1/tasks`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/tasks/` | 创建任务 |
| GET | `/api/v1/tasks/` | 查询任务列表（支持 status/owner_id 过滤） |
| GET | `/api/v1/tasks/{id}` | 获取单个任务 |
| PATCH | `/api/v1/tasks/{id}` | 更新任务 |
| PATCH | `/api/v1/tasks/{id}/status` | 更新任务状态（核心接口） |
| DELETE | `/api/v1/tasks/{id}` | 删除任务 |
| POST | `/api/v1/tasks/{id}/cancel` | 取消任务 |
| POST | `/api/v1/tasks/{id}/retry` | 重试失败任务 |

### Agent `/api/v1/agent`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/agent/chat` | 对话（非流式） |
| POST | `/api/v1/agent/chat/stream` | 对话（流式 SSE） |
| POST | `/api/v1/agent/reset` | 重置沙箱 |
| GET | `/api/v1/agent/health` | 健康检查 |

## 数据模型

### TaskStatus 状态机

```
pending → running → success
                   → failed → (可重试) → pending
                   → cancelled
```

### TaskPriority

- `low` / `normal` / `high` / `urgent`

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///fastapi_project.db` | 数据库连接 |
| `OPENSANDBOX_API_KEY` | — | OpenSandbox API Key |
| `OPENSANDBOX_DOMAIN` | `api.opensandbox.io` | OpenSandbox 域名 |
| `OPENSANDBOX_IMAGE` | `ubuntu` | 沙箱镜像 |
| `DAYTONA_API_KEY` | — | Daytona API Key（预留） |
| `MODAL_APP_NAME` | `deepagent` | Modal App 名称（预留） |

## 数据库

SQLite 数据库文件: `fastapi_project.db`（项目根目录）

表结构自动创建于首次启动（通过 `init_db()`）。

## 其他后端（预留）

- **Daytona**: `app/sandbox/backends/daytona_backend.py` — 占位框架，待 SDK 接入
- **Modal**: `app/sandbox/backends/modal_backend.py` — 占位框架，待 SDK 接入
