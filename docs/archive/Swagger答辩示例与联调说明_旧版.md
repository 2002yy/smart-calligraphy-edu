# Swagger 答辩示例与联调说明

本文档用于配合 `api-server` 的 Swagger 页面演示。启动后访问：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

## 1. 推荐答辩演示链路

建议按下面顺序演示系统闭环：

1. 教师登录：`POST /api/v1/auth/login`
2. 教师查看课程：`GET /api/v1/courses`
3. 教师查看班级：`GET /api/v1/classes`
4. 教师发布任务：`POST /api/v1/tasks`
5. 学生提交作业：`POST /api/v1/homework`
6. 触发智能评测：`POST /api/v1/evaluation/start`
7. 教师查看批阅：`POST /api/v1/reviews`
8. 教师查看班级看板：`GET /api/v1/dashboard/class/{class_id}`
9. 导出成长报告：`POST /api/v1/reports/export`

## 2. 默认演示账号

- 教师账号：`teacher01`
- 教师密码：`123456`
- 学生账号：`student01`
- 学生密码：`123456`

## 3. 示例请求与返回

### 3.1 教师登录

接口：`POST /api/v1/auth/login`

请求体：

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
    "access_token": "dev-token-1",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "teacher01",
      "name": "刘老师",
      "role": "teacher",
      "school_name": "四川大学",
      "avatar_url": null
    }
  }
}
```

### 3.2 创建课程

接口：`POST /api/v1/courses`

请求体：

```json
{
  "name": "大学生书法素养提升课",
  "term": "2026春",
  "description": "面向非书法专业学生的基础书法训练课程",
  "teacher_id": 1
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 2,
    "name": "大学生书法素养提升课",
    "term": "2026春",
    "description": "面向非书法专业学生的基础书法训练课程",
    "teacher_id": 1,
    "status": "active",
    "created_at": "2026-04-12T10:00:00"
  }
}
```

### 3.3 创建任务

接口：`POST /api/v1/tasks`

请求体：

```json
{
  "course_id": 1,
  "class_id": 1,
  "title": "欧楷基本笔画训练",
  "description": "掌握横、竖、撇、捺的基础书写方式",
  "practice_chars": ["永", "大", "木", "中"],
  "structure_weight": 40,
  "center_weight": 30,
  "stroke_order_weight": 30,
  "deadline": "2026-04-20T23:59:59",
  "created_by": 1
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 2,
    "course_id": 1,
    "class_id": 1,
    "title": "欧楷基本笔画训练",
    "description": "掌握横、竖、撇、捺的基础书写方式",
    "practice_chars": ["永", "大", "木", "中"],
    "structure_weight": 40,
    "center_weight": 30,
    "stroke_order_weight": 30,
    "deadline": "2026-04-20T23:59:59",
    "created_by": 1,
    "created_at": "2026-04-12T10:10:00"
  }
}
```

### 3.4 学生提交作业

接口：`POST /api/v1/homework`

请求体：

```json
{
  "task_id": 1,
  "student_id": 2,
  "image_url": "/uploads/homework/2/1/demo.png"
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "task_id": 1,
    "student_id": 2,
    "status": "submitted",
    "image_url": "/uploads/homework/2/1/demo.png",
    "processed_image_url": null,
    "submitted_at": "2026-04-12T10:20:00"
  }
}
```

### 3.5 启动智能评测

接口：`POST /api/v1/evaluation/start`

请求体：

```json
{
  "homework_id": 1
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "finished",
    "homework_id": 1,
    "evaluation_id": 1
  }
}
```

### 3.6 获取评测详情

接口：`GET /api/v1/evaluation/1`

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "homework_id": 1,
    "total_score": 8.7,
    "structure_score": 9.0,
    "center_score": 8.6,
    "stroke_order_score": 8.9,
    "issues": ["重心略偏左", "右部收笔不够稳"],
    "advice": "建议继续练习永、大、木、中四字，重点加强左右结构展开与横画稳定性。",
    "compare_image_url": "/outputs/evaluation/1_compare.png",
    "status": "finished",
    "created_at": "2026-04-12T10:25:00"
  }
}
```

### 3.7 教师批阅作业

接口：`POST /api/v1/reviews`

请求体：

```json
{
  "homework_id": 1,
  "teacher_id": 1,
  "comment": "整体结构较稳，建议继续加强横画起收笔变化。",
  "final_score": 90,
  "status": "reviewed"
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "homework_id": 1,
    "teacher_id": 1,
    "comment": "整体结构较稳，建议继续加强横画起收笔变化。",
    "final_score": 90,
    "status": "reviewed",
    "reviewed_at": "2026-04-12T10:30:00"
  }
}
```

### 3.8 查看班级看板

接口：`GET /api/v1/dashboard/class/1`

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "class_id": 1,
    "class_name": "2026春季1班",
    "student_count": 30,
    "task_count": 4,
    "homework_count": 92,
    "evaluated_count": 80,
    "avg_score": 87.4,
    "submit_rate": 0.77,
    "top_issues": ["重心略偏左", "横画不够稳", "字形偏紧"]
  }
}
```

### 3.9 导出报告

接口：`POST /api/v1/reports/export`

请求体：

```json
{
  "type": "student",
  "target_id": 2,
  "format": "pdf"
}
```

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "file_url": "/reports/student_2.pdf",
    "generated_at": "2026-04-12T10:45:00"
  }
}
```

## 4. 答辩演示建议

- 打开 Swagger 后先展开 `auth`、`tasks`、`homework`、`evaluation` 这四组接口，突出“教学闭环”。
- 再展示 `reviews`、`dashboard`、`reports`，强调“教师管理能力”和“数据沉淀能力”。
- 讲解时可以突出：当前评测结果为可演示的结构化输出，后续可无缝替换为真实 AI 模型推理结果。
