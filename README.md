# 智慧书法教学系统 — Smart Calligraphy Education

[![CI](https://github.com/2002yy/smart-calligraphy-edu/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/2002yy/smart-calligraphy-edu/actions/workflows/ci.yml)

> **书法教育 AI 评测系统** — 基于 AI 视觉评测的书法教学平台

---

## 1. 📌 项目一句话定位

**书法教育 AI 评测系统** — 教师端管理教学流程，学生端提交书法作品并获得 AI 即时评分反馈。基于 Vue 3 + FastAPI + 阿里云百炼 qwen3.5-omni-plus 构建。

> ⚠️ **定位说明**：书法教育 AI 评测展示系统，Vue 3 + FastAPI + AI 视觉评测全栈项目。公开课程/项目演示版。

---

## 2. 🖼️ Screenshots / Demo

### 核心展示页面

| 模块 | 截图 | 说明 |
|------|------|------|
| 👨‍🏫 教师端 | [教学看板](docs/demo/screenshots/01-teacher-dashboard.png) | 登录后教学看板，左侧选择课程/班级，右侧展示班级统计数据 |
| 👨‍🏫 教师端 | [任务编排](docs/demo/screenshots/02-task-publish.png) | 发布书法练习任务、设定练习字和评分权重 |
| 👩‍🎓 学生端 | [学习总览](docs/demo/screenshots/03-student-overview.png) | 学生登录后的学习总览，展示班级、任务和最近反馈 |
| 👩‍🎓 学生端 | [作品提交](docs/demo/screenshots/04-student-upload.png) | 提交书法作品页面，支持拍照/上传 |
| 📈 成长档案 | [历史记录](docs/demo/screenshots/05-growth-archive.png) | 历次评分趋势与教师评语 |

![Teacher Dashboard](docs/demo/screenshots/01-teacher-dashboard.png)
*教师端教学看板 — 班级学习状态与统计数据*

![Task Publish](docs/demo/screenshots/02-task-publish.png)
*任务编排 — 发布书法训练任务并设定评分权重*

![Student Overview](docs/demo/screenshots/03-student-overview.png)
*学生学习总览 — 当前任务与最近反馈*

![Submit Upload](docs/demo/screenshots/04-student-upload.png)
*作品上传 — 拍照/提交书法作业*

![Growth Archive](docs/demo/screenshots/05-growth-archive.png)
*成长档案 — 历次评分趋势与反馈*

### 🎬 Demo 视频

[![Demo Video](docs/demo/screenshots/01-teacher-dashboard.png)](docs/demo/demo-recording.mp4)
*点击截图观看完整操作演示（教师登录 → 任务发布 → 学生上传 → AI 评分 → 成长档案）*

> 视频文件: [`docs/demo/demo-recording.mp4`](docs/demo/demo-recording.mp4)
> 更多截图与录制清单见 [`docs/demo/README.md`](docs/demo/README.md)

---

## 3. ⚡ Tech Stack

| 模块 | 技术 | 说明 |
|------|------|------|
| **教师端** | Vue 3 + Vite + Pinia | 教学管理前端（5173） |
| **学生端** | Vue 3 + Vite + Pinia | 学习空间前端（5174） |
| **业务后端** | FastAPI + SQLAlchemy | API 服务（8000） |
| **AI 评测** | qwen3.5-omni-plus (DashScope) | 书法作品智能评分 |
| **Mock 评测** | 内置 MockEvaluator | 无 API Key 时可用本地演示 |
| **数据库** | SQLite | 本地开发 |
| **测试** | Playwright | 端到端烟雾测试 |

---

## 4. 🎯 Core Features

- 👨‍🏫 **教师端** — 教学流程管理、学生作品批阅、评分查看
- 👩‍🎓 **学生端** — 作品提交、AI 即时评分反馈
- 🤖 **AI 书法评测** — 基于视觉大模型的书法质量评分（结构/重心/笔法三维）
- 🔄 **前后端分离** — Vue 3 + FastAPI 标准架构
- 🎭 **Mock Fallback** — 无 API Key 时使用内置 Mock 评分器演示

---

## 5. 🏗️ Architecture

```
teacher-web (5173) ─┐
                      ├─► api-server (8000) ──► SQLite
student-app (5174) ──┘       │
                              ├──► qwen3.5-omni-plus (DashScope) AI 评测
                              └──► MockEvaluator (本地回退)
```

### AI 评测流程

```
用户上传图片
  → FastAPI 接收文件
  → 读取任务/评分权重
  → 调用 qwen3.5-omni-plus 或 Mock evaluator
  → 返回 结构/重心/笔法 三维分数
  → 生成问题标签和练习建议
  → 前端展示评分和教师复盘入口
```

---

## 💡 Why This Project Matters

| 维度 | 说明 |
|------|------|
| **双端角色系统** | 教师端与学生端独立 SPA，体现真实教育业务流程 |
| **AI 评测可降级** | Qwen provider + Mock fallback，保证演示稳定，无需 API Key |
| **权限边界** | 学生只能访问自己的作业，教师只能访问自己课程下的数据 |
| **工程质量** | pytest(94) + Vitest(15) + Playwright E2E + GitHub Actions CI |
| **安全意识** | 生产环境 JWT_SECRET 检查、静态资源签名访问、路径穿越防护 |

---

## 6. 🚀 Quick Start

### ✅ 启动前检查清单

克隆后按顺序确认以下步骤：

| # | 步骤 | 说明 |
|---|------|------|
| 1 | `cp api-server/.env.example api-server/.env` | 创建后端配置（只需做一次） |
| 2 | `pip install -r api-server/requirements.txt` | 安装 Python 依赖 |
| 3 | `npm install`（teacher-web + student-app） | 安装前端依赖 |
| 4 | 启动后端 → 教师端 → 学生端 | 见下方命令 |

> **Mock 模式开箱即用**：无需 API Key。AI 评测默认走内置 Mock 评分器，`QWEN_EVALUATION_ENABLED=false` 即是 Mock 模式。
> 需要真实 AI 评测时再配置 Qwen（见 [.env.example](api-server/.env.example)）。

### 前置条件
- Node.js 18+
- Python 3.10+

### 本地运行

```bash
# ① 终端 1：启动后端
cd api-server
pip install -r requirements.txt
cp .env.example .env        # 首次只需一次
uvicorn app.main:app --reload --port 8000

# ② 终端 2：启动教师端
cd teacher-web
npm install                 # 首次只需一次
npm run dev

# ③ 终端 3：启动学生端
cd student-app
npm install                 # 首次只需一次
npm run dev
```

### 访问地址

| 端 | 地址 |
|------|------|
| 教师端 | http://localhost:5173 |
| 学生端 | http://localhost:5174 |
| API 文档 | http://localhost:8000/docs |

---

## 7. 🔐 Permission Matrix

| 资源 | Student | Teacher | Public |
|------|---------|---------|--------|
| homework upload | ✅ 自己的 | ❌ | — |
| homework submit | ✅ 自己的 | ❌ | — |
| homework list/detail | ✅ 自己的 | ✅ 自己课程下 | — |
| evaluation start/get | ✅ 自己的 | ✅ 自己课程下 | — |
| review list/submit | ❌ | ✅  从 token | — |
| course create | ❌ | ✅  从 token | — |
| class create/join | ✅ join(自己的) | ✅ create(归属校验) | — |
| class members | ❌ | ✅ 归属校验 | — |
| report student | ✅ 自己的 | ✅ | — |
| report class | ❌ | ✅  | — |
| user/growth | ✅ 自己的 | ✅ 班级关系校验 | — |
| static resources | — | — | ✅ 签名 token path 绑定 |
|  | — | — | ✅ 公开 |

---

## 8. 🗄️ Database Migration

Use Alembic for schema migration. Auto-runs on dev startup; manual for production.

```bash
cd api-server
alembic upgrade head           # apply pending migrations
alembic history                # view migration history
alembic revision --autogenerate -m "description"  # generate from model changes
```

- **dev** environment: `init_db()` runs `alembic upgrade head`, falls back to `create_all` on failure
- **production / staging**: migration failure blocks startup (no silent fallback)

Config in `alembic.ini` + `alembic/env.py` (auto-imports all models).

---

## 9. 🧪 Testing / Quality

| 类型 | 覆盖范围 | 用例数 | 状态 |
|------|---------|--------|------|
| **pytest**（后端） | 登录认证、权限校验、Mock 评测、provider 选择、分数范围、思考链、跨用户/跨角色负例、文件存储/overlay、Qwen JSON 提取/白名单过滤 | **94** | ✅ |
| **Vitest**（前端 store） | 登录/登出、班级、任务、提交、评测、文件选择 | **15** | ✅ |
| **Playwright**（E2E） | API 冒烟 → 上传 → Mock 评测 → 看板回流 → UI 截图 | **全链路** | ✅ 本地可用，✅ CI 已接入 |
| API 文档 | FastAPI `/docs` 自动生成 | — | ✅ |
| Mock Evaluator | 无 API Key 时本地演示 | — | ✅ |

---

## 10. 🛡️ Production Deployment Checklist

外网部署前，请确认以下安全配置（参考 [`api-server/.env.production.example`](api-server/.env.production.example)）：

| # | 配置项 | 强制？ | 说明 |
|---|--------|--------|------|
| 1 | `APP_ENV=production` | ✅ | 启用生产模式检查（如 JWT 默认值检测） |
| 2 | `SECURE_STATIC=true` | ✅ | 静态资源需 Bearer token 或签名路径才能访问 |
| 3 | `CORS_ORIGINS=...` | ✅ | 限制到实际域名，禁止 `*` |
| 4 | `JWT_SECRET` 设为随机字符串 | ✅ | 默认 `change_me` 在生产环境会阻止启动 |
| 5 | `CALLIGRAPHY_FONT_PATH` | ⚠️ | Linux 部署建议安装 `fonts-noto-cjk` 或手动指定路径，否则结果图中文不显示 |
| 6 | `DATABASE_URL` | ⚠️ | 生产环境建议切换 PostgreSQL/MySQL |
| 7 | `DEMO_PASSWORD` | ⚠️ | 改默认密码 |

---

### License

MIT License
