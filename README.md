# DeepAgents Sandbox

[![CI](https://github.com/fanta079/deepagents_sandbox/actions/workflows/ci.yml/badge.svg)](https://github.com/fanta079/deepagents_sandbox/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Node Version](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat&logo=next.js)](https://nextjs.org/)

**支持多沙箱后端的 AI Agent 服务** —— 基于 FastAPI + OpenSandbox 构建。

---

## 🎯 项目简介

这是一个完整的 AI Agent 后端服务，支持通过沙箱环境执行代码、读写文件、浏览器操作等。

### 核心功能

- 🤖 **Agent 对话** — 与 Claude 模型对话，支持 SSE 流式输出
- 🐳 **多沙箱后端** — OpenSandbox / Daytona / Modal
- 🔐 **JWT 认证** — 用户注册、登录、Token 管理
- 📋 **任务队列** — 创建、管理、状态流转
- 📁 **文件管理** — 上传、下载、删除
- 🔌 **WebSocket** — 实时聊天/通知
- 📧 **邮件通知** — 任务状态变更提醒
- 📡 **Webhook** — 事件回调
- 🐳 **Docker 部署** — 一键部署

---

## 🛠️ 技术栈

### 后端
- **FastAPI** — Web 框架
- **SQLAlchemy** — ORM（SQLite）
- **Pydantic** — 数据验证
- **JWT** — 认证
- **slowapi** — API 限流

### 前端
- **Next.js 14** — React 框架
- **TypeScript** — 类型安全
- **Tailwind CSS** — 样式
- **shadcn/ui** — 组件库

### 沙箱
- **OpenSandbox** — 阿里云沙箱
- **DeepAgents** — Agent 框架

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- OpenSandbox API Key

### 1. 克隆项目

```bash
git clone https://github.com/fanta079/deepagents_sandbox.git
cd deepagents_opensandbox
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# OpenSandbox API Key（必填）
OPENSANDBOX_API_KEY=sk-your-key-here

# JWT 密钥（生产环境必改）
JWT_SECRET_KEY=your-super-secret-key

# 其他配置按需修改
```

### 3. 启动后端

```bash
cd app

# 安装依赖
uv sync

# 启动服务
uvicorn app.main:app --reload --port 8000
```

后端地址：http://localhost:8000
API 文档：http://localhost:8000/docs

### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install --legacy-peer-deps

# 启动开发服务器
npm run dev
```

前端地址：http://localhost:3000

---

## 🚀 快速部署

### Docker（一键部署）

```bash
docker-compose up -d
```

> 服务地址：http://localhost:8000 | 前端：http://localhost:3000

### Kubernetes

```bash
kubectl apply -f k8s/
```

### 环境变量配置

```bash
cp .env.example .env
# 编辑 .env 填入 OPENSANDBOX_API_KEY 和 JWT_SECRET_KEY
```

---

## 🐳 Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

服务地址：http://localhost:8000

---

## 📁 项目结构

```
deepagents_opensandbox/
├── app/                          # FastAPI 后端
│   ├── core/                     # 核心模块
│   │   ├── config.py            # 配置
│   │   ├── database.py          # 数据库
│   │   ├── security.py          # JWT
│   │   ├── auth.py              # 认证
│   │   ├── email.py             # 邮件
│   │   ├── webhook.py           # Webhook
│   │   └── rate_limit.py        # 限流
│   ├── models/                   # 数据模型
│   │   ├── user.py
│   │   └── task.py
│   ├── schemas/                  # Pydantic 模型
│   │   ├── user.py
│   │   └── task.py
│   ├── routers/                  # API 路由
│   │   ├── auth.py              # 认证
│   │   ├── users.py             # 用户管理
│   │   ├── tasks.py             # 任务队列
│   │   ├── agent.py             # Agent 对话
│   │   ├── files.py             # 文件管理
│   │   ├── sse.py               # SSE
│   │   └── websocket.py         # WebSocket
│   ├── sandbox/                  # 沙箱模块
│   │   ├── agent_runner.py      # Agent 管理
│   │   └── backends/            # 沙箱后端
│   │       ├── opensandbox_backend.py
│   │       ├── daytona_backend.py
│   │       └── modal_backend.py
│   ├── tests/                    # 单元测试
│   ├── docs/                     # 文档
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── api.md
│   └── main.py                   # 入口
├── frontend/                     # Next.js 前端
│   ├── src/
│   │   ├── app/                 # 页面
│   │   ├── components/          # 组件
│   │   ├── lib/                 # 工具
│   │   └── types/               # 类型
│   └── package.json
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 📡 API 文档

> 📖 **完整 API 文档：** http://localhost:8000/docs（启动后访问）

启动服务后访问：http://localhost:8000/docs

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /api/v1/auth/login` | POST | 登录 |
| `POST /api/v1/users/` | POST | 创建用户 |
| `GET /api/v1/users/` | GET | 用户列表 |
| `POST /api/v1/tasks/` | POST | 创建任务 |
| `GET /api/v1/tasks/` | GET | 任务列表 |
| `POST /api/v1/agent/chat` | POST | Agent 对话 |
| `POST /api/v1/agent/chat/stream` | POST | 流式对话 |
| `POST /api/v1/files/upload` | POST | 上传文件 |
| `WS /ws` | WebSocket | 实时聊天 |

---

## 🔧 开发

### 运行测试

```bash
cd app
pytest
```

### 代码规范

- 后端：PEP 8
- 前端：ESLint + Prettier

---

## 📄 License

MIT
