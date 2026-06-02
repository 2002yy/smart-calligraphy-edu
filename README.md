# 智慧书法教学系统 — Smart Calligraphy Education

> **课程项目 / 原型开发** — 基于 AI 视觉评测的书法教学平台
> 本仓库是课程设计项目，本人为唯一贡献者（全栈开发）。非生产级系统。

---

## 1. 📌 项目一句话定位

**智慧书法教育展示系统的课程项目原型** — 教师端管理教学流程，学生端提交书法作品并获得 AI 即时评分反馈。基于 Vue 3 + FastAPI + 阿里云百炼 qwen3.5-omni-plus 构建。

> ⚠️ **定位说明**：这是课程项目/毕业设计原型，用于展示全栈开发能力（Vue 3 + FastAPI + AI 集成），不作为生产级系统部署。

---

## 2. 🖼️ Screenshots / Demo

> 待补充截图 / 录屏

---

## 3. ⚡ Tech Stack

| 模块 | 技术 | 说明 |
|------|------|------|
| **教师端** | Vue 3 + Vite + Pinia | 教学管理前端 |
| **学生端** | Vue 3 + Vite + Pinia | 学习空间前端 |
| **业务后端** | FastAPI + SQLAlchemy | API 服务 |
| **AI 评测** | qwen3.5-omni-plus (DashScope) | 书法作品智能评分 |
| **数据库** | SQLite | 本地开发 |
| **测试** | Playwright | 端到端烟雾测试 |

---

## 4. 🎯 Core Features

- 👨‍🏫 **教师端** — 教学流程管理、学生作品批阅、评分查看
- 👩‍🎓 **学生端** — 作品提交、AI 即时评分反馈
- 🤖 **AI 书法评测** — 基于视觉大模型的书法质量评分
- 🔄 **前后端分离** — Vue 3 + FastAPI 标准架构

---

## 5. 🏗️ Architecture

```
teacher-web ─┐
              ├─► api-server ──► SQLite
student-app ──┘       │
                      └──► qwen3.5-omni-plus (DashScope)
```

| 模块 | 端口 | 说明 |
|------|------|------|
| `teacher-web` | 5173 | 教师教学管理前端（Vue 3） |
| `student-app` | 5174 | 学生学习空间前端（Vue 3） |
| `api-server` | 8000 | FastAPI 业务后端 |
| `ai-service` | — | AI 评测服务配置 |

---

## 6. 🚀 Quick Start

### 前置条件
- Node.js 18+
- Python 3.10+
- 阿里云百炼 DashScope API Key

### 本地运行

```bash
# ① 启动后端
cd api-server
pip install -r requirements.txt
cp .env.example .env    # 编辑填入 API Key
uvicorn main:app --reload --port 8000

# ② 启动教师端
cd teacher-web
npm install
npm run dev

# ③ 启动学生端
cd student-app
npm install
npm run dev
```

---

## 7. 📄 Portfolio Notes

### 作品集说明

本仓库是 **课程项目 / 毕业设计原型**，不作为核心求职项目展示。

**保留原因：**
- 展示 Vue 3 + FastAPI 全栈开发能力
- 展示 AI 大模型 API 集成经验
- 展示前后端分离架构设计

**不公开的原因：**
- 课程作业阶段产物，非生产级工程
- 部分实现偏原型化

### License

MIT License
