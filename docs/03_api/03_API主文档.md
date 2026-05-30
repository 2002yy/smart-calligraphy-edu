# 智慧书法教学软件 API 主文档

## 1. 文档目标

本文档用于定义智慧书法教学软件首版 MVP 的前后端接口边界，服务于以下四类工作：

- 学生端 Vue 3 联调
- 教师端 Vue 3 联调
- 业务后端 FastAPI 开发
- AI 服务 Python + FastAPI 对接

首版目标聚焦于一个可运行教学闭环，优先覆盖：

- 登录与角色区分
- 课程与班级
- 任务发布
- 作业上传
- AI 评分
- 教师批阅
- 学情看板与报告导出

## 2. 接口设计原则

- 接口统一采用 RESTful 风格
- 请求体统一使用 JSON
- 文件上传使用 `multipart/form-data`
- 时间字段统一使用 ISO 8601 字符串
- 所有接口统一返回 `code + message + data` 结构

## 3. 通用返回格式

成功返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

失败返回：

```json
{
  "code": 4001,
  "message": "用户未登录",
  "data": null
}
```

其中：

- `code = 0` 表示成功
- `code != 0` 表示失败

## 4. 认证方式

首版采用基于 Token 的认证机制：

- 登录成功后返回 `access_token`
- 前端请求头统一携带：

```text
Authorization: Bearer <token>
```

## 5. 服务划分

### 5.1 业务后端 `api-server`

负责：

- 用户登录
- 角色与权限
- 课程管理
- 班级管理
- 任务管理
- 作业记录
- 批阅记录
- 报告数据聚合

### 5.2 AI 服务 `ai-service`

负责：

- 图片预处理
- 单字切分
- 基础评分
- 问题标签生成
- 推荐练习生成

## 6. 接口模块总览

### 6.1 业务后端模块

- `auth`
- `users`
- `courses`
- `classes`
- `tasks`
- `homework`
- `evaluation`
- `reviews`
- `dashboard`
- `reports`

### 6.2 AI 服务模块

- `preprocess`
- `score`
- `recommend`

可扩展模块：

- `segment`
- `qa`

## 7. 认证模块

接口前缀：`/api/v1/auth`

### 7.1 登录

`POST /api/v1/auth/login`

请求示例：

```json
{
  "username": "teacher01",
  "password": "123456"
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "xxxxxx",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "name": "刘老师",
      "role": "teacher"
    }
  }
}
```

### 7.2 获取当前用户信息

`GET /api/v1/auth/me`

返回字段：

- `id`
- `name`
- `role`
- `school_name`
- `class_ids`

## 8. 用户模块

接口前缀：`/api/v1/users`

### 8.1 获取用户详情

`GET /api/v1/users/{user_id}`

### 8.2 获取学生成长信息

`GET /api/v1/users/{user_id}/growth`

返回字段建议：

- 累计练习次数
- 平均分
- 最近成绩趋势
- 常见问题标签
- 最新作品列表

## 9. 课程模块

接口前缀：`/api/v1/courses`

### 9.1 创建课程

`POST /api/v1/courses`

### 9.2 获取课程列表

`GET /api/v1/courses`

支持参数：

- `role`
- `teacher_id`
- `student_id`

### 9.3 获取课程详情

`GET /api/v1/courses/{course_id}`

## 10. 班级模块

接口前缀：`/api/v1/classes`

### 10.1 创建班级

`POST /api/v1/classes`

### 10.2 获取班级列表

`GET /api/v1/classes?course_id=1`

### 10.3 学生加入班级

`POST /api/v1/classes/{class_id}/join`

### 10.4 获取班级成员

`GET /api/v1/classes/{class_id}/members`

## 11. 任务模块

接口前缀：`/api/v1/tasks`

### 11.1 创建任务

`POST /api/v1/tasks`

任务核心字段建议包括：

- `course_id`
- `class_id`
- `title`
- `description`
- `practice_chars`
- `structure_weight`
- `center_weight`
- `stroke_order_weight`
- `deadline`
- `created_by`

### 11.2 获取任务列表

`GET /api/v1/tasks`

支持参数：

- `course_id`
- `class_id`
- `student_id`
- `status`

### 11.3 获取任务详情

`GET /api/v1/tasks/{task_id}`

## 12. 作业模块

接口前缀：`/api/v1/homework`

### 12.1 上传作业图片

`POST /api/v1/homework/upload`

请求类型：

- `multipart/form-data`

表单字段：

- `task_id`
- `student_id`
- `file`

### 12.2 提交作业

`POST /api/v1/homework`

请求字段建议：

- `task_id`
- `student_id`
- `image_url`

### 12.3 获取学生作业列表

`GET /api/v1/homework?student_id=10`

### 12.4 获取任务作业列表

`GET /api/v1/homework?task_id=1`

### 12.5 获取作业详情

`GET /api/v1/homework/{homework_id}`

## 13. 评测模块

接口前缀：`/api/v1/evaluation`

首版由业务后端调用 AI 服务，再统一向前端返回结果。

### 13.1 触发评分

`POST /api/v1/evaluation/start`

### 13.2 获取评分结果

`GET /api/v1/evaluation/{homework_id}`

返回字段建议：

- `total_score`
- `structure_score`
- `center_score`
- `stroke_order_score`
- `issues`
- `advice`
- `compare_image_url`
- `status`

## 14. 批阅模块

接口前缀：`/api/v1/reviews`

### 14.1 教师提交批阅

`POST /api/v1/reviews`

核心字段：

- `homework_id`
- `teacher_id`
- `comment`
- `final_score`
- `status`

### 14.2 获取作业批阅结果

`GET /api/v1/reviews/{homework_id}`

### 14.3 获取教师批阅列表

`GET /api/v1/reviews`

## 15. 教师看板模块

接口前缀：`/api/v1/dashboard`

### 15.1 获取班级看板数据

`GET /api/v1/dashboard/class/{class_id}`

返回字段建议：

- 班级人数
- 提交率
- 平均分
- 共性问题 Top5
- 重点关注学生
- 进步最快学生

## 16. 报告模块

接口前缀：`/api/v1/reports`

### 16.1 获取学生成长报告

`GET /api/v1/reports/student/{student_id}`

### 16.2 获取班级统计报告

`GET /api/v1/reports/class/{class_id}`

### 16.3 导出报告文件

`POST /api/v1/reports/export`

## 17. AI 服务接口

接口前缀建议：

- `POST /ai/v1/preprocess`
- `POST /ai/v1/segment`
- `POST /ai/v1/score`
- `POST /ai/v1/recommend`
- `POST /ai/v1/qa`

首版主文档重点保留：

- `preprocess`
- `score`
- `recommend`

## 18. 默认演示账号

用于 Swagger、本地联调与答辩演示：

- 教师账号：`teacher01`
- 教师密码：`123456`
- 学生账号：`student01`
- 学生密码：`123456`

## 19. 附录：当前实现一致的核心业务路由

- `/api/v1/auth`
- `/api/v1/users`
- `/api/v1/courses`
- `/api/v1/classes`
- `/api/v1/tasks`
- `/api/v1/homework`
- `/api/v1/evaluation`
- `/api/v1/reviews`
- `/api/v1/dashboard`
- `/api/v1/reports`
