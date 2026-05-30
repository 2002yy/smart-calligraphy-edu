# 智慧书法教学软件 API 文档草案

## 1. 文档目标

这份文档用于定义智慧书法教学软件首版 MVP 的前后端接口边界，方便：

- 学生端 `uni-app` 联调
- 教师端 `Vue 3` 联调
- 业务后端 `FastAPI` 开发
- AI 服务 `Python + FastAPI` 对接

本文档以 `首版可运行闭环` 为目标，优先覆盖：

- 登录与角色区分
- 课程与班级
- 任务发布
- 作业上传
- AI 评分
- 教师批阅
- 学情看板

## 2. 接口设计原则

### 2.1 基本原则

- 接口统一使用 `RESTful` 风格
- 请求体统一使用 `JSON`
- 文件上传使用 `multipart/form-data`
- 所有时间字段统一使用 ISO 8601 字符串
- 所有接口统一返回 `code + message + data`

### 2.2 通用返回格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

说明：

- `code = 0` 表示成功
- 非 `0` 表示失败

错误示例：

```json
{
  "code": 4001,
  "message": "用户未登录",
  "data": null
}
```

### 2.3 认证方式

首版建议使用：

- 登录后返回 `access_token`
- 前端通过请求头传递：

```text
Authorization: Bearer <token>
```

## 3. 服务划分

建议分为两个服务：

### 3.1 业务后端 `api-server`

负责：

- 用户登录
- 角色与权限
- 课程管理
- 班级管理
- 任务管理
- 作业记录
- 批阅记录
- 报告数据聚合

### 3.2 AI 服务 `ai-service`

负责：

- 图片预处理
- 单字切分
- 基础评分
- 问题标签生成
- 推荐练习生成

## 4. 接口模块总览

### 4.1 业务后端接口模块

- 认证模块 `auth`
- 用户模块 `users`
- 课程模块 `courses`
- 班级模块 `classes`
- 任务模块 `tasks`
- 作业模块 `homework`
- 批阅模块 `reviews`
- 数据看板模块 `dashboard`
- 报告模块 `reports`

### 4.2 AI 服务接口模块

- 预处理模块 `preprocess`
- 评分模块 `score`
- 推荐模块 `recommend`

## 5. 认证模块

接口前缀：`/api/v1/auth`

### 5.1 登录

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

### 5.2 获取当前用户信息

`GET /api/v1/auth/me`

返回字段：

- `id`
- `name`
- `role`
- `school_name`
- `class_ids`

## 6. 用户模块

接口前缀：`/api/v1/users`

### 6.1 获取用户详情

`GET /api/v1/users/{user_id}`

### 6.2 获取学生成长信息

`GET /api/v1/users/{user_id}/growth`

返回字段建议：

- 累计练习次数
- 平均分
- 最近 10 次成绩
- 常见问题标签
- 最新作品列表

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_practice_count": 28,
    "avg_score": 84,
    "score_trend": [72, 75, 78, 80, 84],
    "top_issues": ["右部偏窄", "横画不足"],
    "recent_works": [
      {
        "homework_id": 101,
        "score": 84,
        "submitted_at": "2026-04-11T20:30:00"
      }
    ]
  }
}
```

## 7. 课程模块

接口前缀：`/api/v1/courses`

### 7.1 创建课程

`POST /api/v1/courses`

请求示例：

```json
{
  "name": "大学生书法素养提升课",
  "term": "2026春",
  "description": "面向非书法专业学生的基础书法训练课程"
}
```

### 7.2 获取课程列表

`GET /api/v1/courses`

支持参数：

- `role`
- `teacher_id`
- `student_id`

### 7.3 获取课程详情

`GET /api/v1/courses/{course_id}`

## 8. 班级模块

接口前缀：`/api/v1/classes`

### 8.1 创建班级

`POST /api/v1/classes`

### 8.2 获取班级列表

`GET /api/v1/classes?course_id=1`

### 8.3 学生加入班级

`POST /api/v1/classes/{class_id}/join`

请求示例：

```json
{
  "invite_code": "CALLI2026"
}
```

### 8.4 获取班级成员

`GET /api/v1/classes/{class_id}/members`

## 9. 任务模块

接口前缀：`/api/v1/tasks`

### 9.1 创建任务

`POST /api/v1/tasks`

请求示例：

```json
{
  "course_id": 1,
  "class_id": 2,
  "title": "欧楷基本笔画训练",
  "description": "掌握横、竖、撇、捺的基本写法",
  "practice_chars": ["永", "天", "木", "人"],
  "score_weights": {
    "structure": 40,
    "center": 30,
    "stroke_order": 30
  },
  "deadline": "2026-04-12T21:00:00"
}
```

### 9.2 获取任务列表

`GET /api/v1/tasks`

支持参数：

- `course_id`
- `class_id`
- `student_id`
- `status`

### 9.3 获取任务详情

`GET /api/v1/tasks/{task_id}`

返回字段建议：

- 任务标题
- 描述
- 练习字列表
- 评分权重
- 截止时间
- 关联范字资源

## 10. 作业模块

接口前缀：`/api/v1/homework`

### 10.1 上传作业图片

`POST /api/v1/homework/upload`

请求类型：

- `multipart/form-data`

表单字段：

- `task_id`
- `student_id`
- `file`

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "file_url": "/uploads/homework/20260411_001.jpg",
    "homework_id": 1001
  }
}
```

### 10.2 提交作业

`POST /api/v1/homework`

请求示例：

```json
{
  "task_id": 1,
  "student_id": 10,
  "image_url": "/uploads/homework/20260411_001.jpg"
}
```

返回字段建议：

- `homework_id`
- `status`
- `submitted_at`

### 10.3 获取学生作业列表

`GET /api/v1/homework?student_id=10`

### 10.4 获取任务作业列表

`GET /api/v1/homework?task_id=1`

### 10.5 获取作业详情

`GET /api/v1/homework/{homework_id}`

返回字段建议：

- 作业图片地址
- 任务信息
- 学生信息
- 当前评分状态
- 批阅状态

## 11. 评分模块

这里建议由业务后端调用 AI 服务，然后统一对前端返回结果。

接口前缀：`/api/v1/evaluation`

### 11.1 触发评分

`POST /api/v1/evaluation/start`

请求示例：

```json
{
  "homework_id": 1001
}
```

### 11.2 获取评分结果

`GET /api/v1/evaluation/{homework_id}`

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_score": 84,
    "sub_scores": {
      "structure": 86,
      "center": 80,
      "stroke_order": 87
    },
    "issues": [
      "右部偏窄",
      "横画不足",
      "重心偏左"
    ],
    "advice": "建议继续练习都、部、郭三字，重点加强右耳刀结构展开。",
    "comparison_image_url": "/results/compare_1001.png",
    "status": "finished"
  }
}
```

## 12. 批阅模块

接口前缀：`/api/v1/reviews`

### 12.1 教师提交批阅

`POST /api/v1/reviews`

请求示例：

```json
{
  "homework_id": 1001,
  "teacher_id": 1,
  "comment": "整体进步明显，但右部仍略窄，建议继续练习左右结构。",
  "final_score": 85,
  "status": "reviewed"
}
```

### 12.2 获取作业批阅结果

`GET /api/v1/reviews/{homework_id}`

## 13. 教师看板模块

接口前缀：`/api/v1/dashboard`

### 13.1 获取班级看板数据

`GET /api/v1/dashboard/class/{class_id}`

返回字段建议：

- 班级人数
- 提交率
- 平均分
- 共性问题 Top5
- 重点关注学生
- 进步最快学生

返回示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "student_count": 56,
    "submit_rate": 0.82,
    "avg_score": 78,
    "top_issues": [
      "左右结构偏窄",
      "横画不足",
      "重心偏左"
    ],
    "focus_students": [
      {
        "student_id": 11,
        "name": "张三"
      }
    ]
  }
}
```

## 14. 报告模块

接口前缀：`/api/v1/reports`

### 14.1 获取学生个人报告数据

`GET /api/v1/reports/student/{student_id}`

### 14.2 获取班级报告数据

`GET /api/v1/reports/class/{class_id}`

### 14.3 导出报告

`POST /api/v1/reports/export`

请求示例：

```json
{
  "type": "class",
  "target_id": 2,
  "format": "pdf"
}
```

## 15. AI 服务接口草案

AI 服务建议只提供内部接口，默认由业务后端调用，不直接暴露给学生端和教师端。

接口前缀：`/ai/v1`

### 15.1 图片预处理

`POST /ai/v1/preprocess`

请求示例：

```json
{
  "image_url": "/uploads/homework/20260411_001.jpg"
}
```

返回字段：

- 裁剪后图片地址
- 透视矫正状态
- 清晰度结果

### 15.2 基础评分

`POST /ai/v1/score`

请求示例：

```json
{
  "image_url": "/uploads/homework/20260411_001.jpg",
  "task_id": 1,
  "practice_chars": ["永", "天", "木", "人"]
}
```

返回字段：

- 总分
- 分项分
- 问题标签
- 推荐练习字
- 对比图地址

### 15.3 推荐练习

`POST /ai/v1/recommend`

请求示例：

```json
{
  "issues": ["右部偏窄", "横画不足"],
  "student_level": "beginner"
}
```

返回字段：

- 推荐练习字
- 推荐训练包
- 推荐说明

## 16. 首版联调优先顺序

建议按下面顺序联调接口：

### 第一批

- 登录
- 获取当前用户
- 获取任务列表
- 获取任务详情

### 第二批

- 上传作业
- 提交作业
- 获取评分结果

### 第三批

- 教师获取作业列表
- 教师提交批阅
- 获取班级看板

### 第四批

- 获取成长档案
- 获取报告数据

## 17. 首版不建议过度复杂化的部分

为了保证联调效率，首版接口暂时不建议过度展开：

- 不必先做复杂的权限树
- 不必先做过于复杂的消息通知系统
- 不必先做完整文件中心
- 不必先做复杂的工作流引擎

首版最重要的是跑通：

`任务 -> 上传 -> 评分 -> 批阅 -> 看板`

这条业务链路。

