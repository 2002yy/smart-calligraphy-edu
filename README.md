# 智慧书法教学软件

本仓库用于组织智慧书法教学软件的原型、文档和代码骨架，适合大创答辩、校内试点和前后端联调演示。

## 目录结构

- `teacher-web/`：教师端，`Vue 3 + Vite + vue-router + Pinia + Axios`
- `student-app/`：学生端，`Vue 3 + Vite + vue-router + Pinia + Axios`
- `api-server/`：业务后端，`FastAPI + SQLAlchemy`
- `ai-service/`：AI 服务，`Python + FastAPI`
- `docs/`：PRD、设计方案、页面说明、API 文档、运行检查单

## 推荐演示链路

1. 启动 `api-server`
2. 启动 `teacher-web`
3. 教师登录并创建课程、班级
4. 教师发布训练任务
5. 启动 `student-app`
6. 学生登录、选择班级、提交作业
7. 学生触发 AI 评测并查看结果
8. 回到教师端查看看板、批阅记录和班级报告

## 文档入口

- [文档总导航](</c:/Users/96967/Desktop/大创/code/docs/README.md>)
- [答辩版 PRD](</c:/Users/96967/Desktop/大创/code/docs/01_PRD/01_答辩版PRD.md>)
- [页面原型与讲解](</c:/Users/96967/Desktop/大创/code/docs/02_design/02_页面原型与讲解.md>)
- [API 主文档](</c:/Users/96967/Desktop/大创/code/docs/03_api/03_API主文档.md>)
- [本地运行与联调手册](</c:/Users/96967/Desktop/大创/code/docs/05_run/05_本地运行与联调手册.md>)
- [开发任务表](</c:/Users/96967/Desktop/大创/code/docs/04_dev/06_开发任务表.md>)
