# Smart Calligraphy Edu — Interview Notes

## 一句话介绍

基于 Vue 3 + FastAPI + AI 视觉评测的书法教学平台，教师端管理教学流程，学生端提交作品获得 AI 即时评分反馈。

## 为什么需要教师端和学生端双端

书法教学天然分角色：
- **教师**需要发布任务、查看学生作品、批阅评分
- **学生**需要查看任务、上传作品、查看评分和反馈

双端分离避免了角色混用导致的权限复杂问题，也方便各自独立迭代。

## FastAPI 后端怎么组织

```
api-server/
├── main.py           # 应用入口、路由注册
├── models/           # SQLAlchemy 模型
├── schemas/          # Pydantic 请求/响应模型
├── routers/          # API 路由
├── services/         # 业务逻辑层
├── evaluator/        # AI 评测（真实 + Mock）
└── config.py         # 环境配置
```

FastAPI 自带 `/docs`（Swagger UI），联调时直接看 API 文档就能对接。

## AI 评分如何 fallback

项目设计了 MockEvaluator 模式：`QWEN_EVALUATION_ENABLED=false` 时使用 Mock，返回结构化的模拟评分数据；设为 `true` 并填入 API Key 后切换到真实 DashScope 调用。前端代码完全不需要感知后端用的是真实 AI 还是 Mock。

## 上传图片如何保护

- 上传目录在 `STORAGE_ROOT` 中配置，默认 `./storage`
- `SECURE_STATIC=true` 时静态资源需 Bearer Token 才能访问
- 生产环境建议 Nginx 反向代理 + 鉴权

## 外网演示如何做 CORS 和静态资源保护

`CORS_ORIGINS` 白名单只允许已知域名访问 API。`SECURE_STATIC=true` 时 `/uploads` 路径需有效 Token。

## 项目不足和后续改进

| 问题 | 改进方向 |
|------|---------|
| 无自动化测试 | pytest + Playwright/Vitest |
| SQLite 开发库 | 生产用 PostgreSQL |
| 无 CI | GitHub Actions |
| Mock 评分准确性 | 优化 prompt 或微调 |
| 缺少 Docker 编排 | 添加 docker-compose |
