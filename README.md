# 智慧书法教学软件

基于 AI 视觉评测的书法教学平台。教师端管理教学流程，学生端提交作品并获得即时 AI 评分反馈。

## 系统架构

```
teacher-web ─┐
              ├─► api-server ──► SQLite
student-app ──┘       │
                      └──► qwen3.5-omni-plus (阿里云百炼 DashScope)
```

| 模块 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| `teacher-web` | Vue 3 + Vite + Pinia | 5173 | 教师教学中枢 |
| `student-app` | Vue 3 + Vite + Pinia | 5174 | 学生学习空间 |
| `api-server` | FastAPI + SQLAlchemy | 8000 | 业务后端 |
| AI 评测 | qwen3.5-omni-plus (DashScope) | — | 书法作品智能评分 |

## 快速启动

### 一键启动（推荐）

```bash
# 本地开发
运行_本地版.cmd

# 外网演示（需额外配 Cloudflare Tunnel）
运行_外网版.cmd
```

### 分步启动

```bash
# 1. 安装前端依赖
cd teacher-web && npm install
cd ../student-app && npm install

# 2. 启动后端（新窗口）
cd api-server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 启动教师端（新窗口）
cd teacher-web
npm run dev

# 4. 启动学生端（新窗口）
cd student-app
npm run dev
```

启动后访问：
- 教师端：http://localhost:5173
- 学生端：http://localhost:5174
- API 文档：http://localhost:8000/docs

### 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 教师 | teacher01 | 123456 |
| 学生 | student01 | 123456 |
| 班级邀请码 | — | CALLI2026 |

## 评测说明

系统支持两种评测模式，按优先级自动选择：

| 模式 | 成本 | 依赖 |
|------|------|------|
| **Qwen3.5-omni-plus** ⭐ | ~¥0.002/次 | 已内置 API Key |
| Mock（模拟评分） | 免费 | 无，自动降级 |

> API Key 已内置，开箱即用。免费额度用完后自动从阿里云百炼余额扣费。

## 功能概览

### 教师端
- **教学看板** — 班级提交率、平均分、共性问题一览
- **课程班级** — 创建课程、创建班级、管理学生
- **任务编排** — 发布训练任务，设置练习字和评分权重
- **批阅复盘** — 查看 AI 初评结果、子维度分数、思考链，填写教师评语

### 学生端
- **学习总览** — 当前任务、班级状态、最近反馈
- **任务中心** — 查看教师发布的训练任务详情
- **提交评测** — 上传书法作品，触发 AI 评分（约 20-30 秒）
  - 7 步思考链动画展示分析过程
  - 展示结构/重心/笔顺三维度分数（10 分制）
  - 生成问题标签和练习建议
- **成长档案** — 历史评分趋势、问题标签汇总

## 项目结构

```
├── teacher-web/        # 教师端前端
│   └── src/
│       ├── views/      # 页面组件
│       ├── stores/     # Pinia 状态管理
│       ├── api.ts      # API 调用封装
│       └── lib/        # 工具库（axios 请求封装）
├── student-app/        # 学生端前端
│   └── src/
│       ├── views/      # 页面组件
│       ├── stores/     # Pinia 状态管理
│       └── api.ts      # API 调用封装
├── api-server/         # 业务后端
│   └── app/
│       ├── api/routes/     # 9 个路由模块
│       ├── services/       # 业务逻辑层
│       ├── repositories/   # 数据访问层
│       ├── models/         # SQLAlchemy 模型
│       └── core/           # 配置、数据库
├── docs/               # 项目文档
├── test-images/        # 测试用书法图片
│   ├── good/           # 碑帖范本
│   └── poor/           # 丑字 + 潦草作业
└── scripts/            # 启动脚本
```

## 文档

- [完整项目文档](docs/DOCUMENTATION_OVERVIEW.md) — 架构、数据模型、API 清单
- [业务流程文档](docs/FLOW_FALLBACK.md) — 操作流程、API 调用序列、Fallback 路径

