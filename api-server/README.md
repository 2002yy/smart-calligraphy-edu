# api-server

智慧书法教学软件的业务后端，基于 `FastAPI + SQLAlchemy` 构建。当前已经具备教师端、学生端首版联调所需的核心接口，并补上了可切换的书法 AI 评分链路。

## 当前能力

- 认证：登录、当前用户信息
- 课程与班级：课程创建、班级创建、学生加入班级、成员查询
- 任务：教师发布任务、任务列表、任务详情
- 作业：图片上传、作业提交、作业列表、作业详情
- 评测：`mock` 评分与 `OpenAI` 评分二选一，支持强制重跑
- 批阅：教师评语与最终得分
- 看板：班级提交率、平均分、共性问题
- 报告：学生报告、班级报告、导出文件路径

## 升级旧数据库之前（必读）

如果数据库已有历史评测，新增的 `evaluations.homework_id` 唯一约束可能因重复记录而拒绝迁移。**不要直接在仍运行的 API 上升级**。先备份并停止全部写入者，再按 [评测历史数据离线升级手册](docs/evaluation-upgrade.md) 审计与处理重复记录；确认完成后运行 `alembic upgrade head`，最后再启动服务。数据库初始化不再在迁移失败时静默回退至 `create_all()`。

## 启动命令

```powershell
cd c:\Users\96967\Desktop\大创\code\api-server
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 测试命令

```powershell
cd c:\Users\96967\Desktop\大创\code\api-server
pytest
```

## OpenAI 评分开关

默认仍然走本地 `mock` 评分，不影响你现在的联调和答辩演示。

如果你要切到真实 OpenAI 视觉评分，可以在 `.env` 里这样配置：

```env
EVALUATION_PROVIDER=openai
OPENAI_EVALUATION_ENABLED=true
OPENAI_API_KEY=你的_OpenAI_Key
OPENAI_EVALUATION_MODEL=gpt-4.1
OPENAI_IMAGE_DETAIL=low
OPENAI_IMAGE_MAX_SIZE=768
```

然后在 Swagger 或前端请求 `POST /api/v1/evaluation/start` 时：

- `provider = "auto"`：按环境配置自动选择
- `provider = "mock"`：强制走本地假数据评分
- `provider = "openai"`：强制走 OpenAI 评分
- `force_refresh = true`：对同一份作业重新评分

## 说明

- 默认数据库为本地 SQLite
- 启动时会自动建表并写入演示数据
- 上传图片会保存到本地 `storage/` 目录
- 上传后的文件可通过 `/uploads/...` 地址访问
- Swagger 地址：`http://127.0.0.1:8000/docs`
