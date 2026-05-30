# FastAPI 路由清单与数据表字段设计

## 1. 路由清单总览

业务后端当前建议的路由模块如下：

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

AI 服务当前建议的路由模块如下：

- `/ai/v1/preprocess`
- `/ai/v1/segment`
- `/ai/v1/score`
- `/ai/v1/recommend`
- `/ai/v1/qa`

## 2. 业务后端 FastAPI 路由清单

### 2.1 `auth.py`

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### 2.2 `users.py`

- `GET /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}/growth`

### 2.3 `courses.py`

- `GET /api/v1/courses`
- `POST /api/v1/courses`
- `GET /api/v1/courses/{course_id}`

### 2.4 `classes.py`

- `GET /api/v1/classes`
- `POST /api/v1/classes`
- `POST /api/v1/classes/{class_id}/join`
- `GET /api/v1/classes/{class_id}/members`

### 2.5 `tasks.py`

- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`

### 2.6 `homework.py`

- `POST /api/v1/homework/upload`
- `POST /api/v1/homework`
- `GET /api/v1/homework`
- `GET /api/v1/homework/{homework_id}`

### 2.7 `evaluation.py`

- `POST /api/v1/evaluation/start`
- `GET /api/v1/evaluation/{homework_id}`

### 2.8 `reviews.py`

- `POST /api/v1/reviews`
- `GET /api/v1/reviews/{homework_id}`

### 2.9 `dashboard.py`

- `GET /api/v1/dashboard/class/{class_id}`

### 2.10 `reports.py`

- `GET /api/v1/reports/student/{student_id}`
- `GET /api/v1/reports/class/{class_id}`
- `POST /api/v1/reports/export`

## 3. AI 服务 FastAPI 路由清单

### 3.1 `preprocess.py`

- `POST /ai/v1/preprocess`

### 3.2 `segment.py`

- `POST /ai/v1/segment`

### 3.3 `score.py`

- `POST /ai/v1/score`

### 3.4 `recommend.py`

- `POST /ai/v1/recommend`

### 3.5 `qa.py`

- `POST /ai/v1/qa`

## 4. 数据表设计建议

首版建议至少设计以下数据表：

- `users`
- `courses`
- `classes`
- `class_members`
- `tasks`
- `task_characters`
- `homework`
- `evaluations`
- `reviews`
- `resources`

## 5. 主要数据表字段设计

## 5.1 用户表 `users`

建议字段：

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| username | varchar(50) | 登录账号 |
| password_hash | varchar(255) | 密码哈希 |
| name | varchar(50) | 用户姓名 |
| role | varchar(20) | student / teacher / admin |
| school_name | varchar(100) | 学校名称 |
| avatar_url | varchar(255) | 头像地址 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 5.2 课程表 `courses`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| name | varchar(100) | 课程名称 |
| term | varchar(50) | 学期 |
| teacher_id | bigint | 教师 ID |
| description | text | 课程说明 |
| status | varchar(20) | active / closed |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 5.3 班级表 `classes`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| course_id | bigint | 所属课程 ID |
| name | varchar(100) | 班级名称 |
| invite_code | varchar(50) | 加入码 |
| student_count | int | 学生人数 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 5.4 班级成员表 `class_members`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| class_id | bigint | 班级 ID |
| student_id | bigint | 学生 ID |
| joined_at | datetime | 加入时间 |

## 5.5 任务表 `tasks`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| course_id | bigint | 课程 ID |
| class_id | bigint | 班级 ID |
| title | varchar(100) | 任务标题 |
| description | text | 任务描述 |
| deadline | datetime | 截止时间 |
| structure_weight | int | 结构评分权重 |
| center_weight | int | 重心评分权重 |
| stroke_order_weight | int | 笔顺评分权重 |
| created_by | bigint | 创建人 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 5.6 任务练习字表 `task_characters`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| task_id | bigint | 任务 ID |
| character | varchar(10) | 练习字 |
| sort_order | int | 排序 |

## 5.7 作业表 `homework`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| task_id | bigint | 任务 ID |
| student_id | bigint | 学生 ID |
| image_url | varchar(255) | 原始图片地址 |
| processed_image_url | varchar(255) | 预处理图片地址 |
| status | varchar(20) | submitted / scoring / scored / reviewed |
| submitted_at | datetime | 提交时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 5.8 评分结果表 `evaluations`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| homework_id | bigint | 作业 ID |
| total_score | decimal(5,2) | 总分 |
| structure_score | decimal(5,2) | 结构分 |
| center_score | decimal(5,2) | 重心分 |
| stroke_order_score | decimal(5,2) | 笔顺分 |
| issues_json | json | 问题标签数组 |
| advice_text | text | 建议文本 |
| compare_image_url | varchar(255) | 对比图地址 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 5.9 教师批阅表 `reviews`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| homework_id | bigint | 作业 ID |
| teacher_id | bigint | 教师 ID |
| comment | text | 教师点评 |
| final_score | decimal(5,2) | 教师确认分数 |
| review_status | varchar(20) | reviewed / returned |
| reviewed_at | datetime | 批阅时间 |
| created_at | datetime | 创建时间 |

## 5.10 资源表 `resources`

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |
| type | varchar(20) | character /碑帖 /书法家 |
| title | varchar(100) | 标题 |
| author_name | varchar(100) | 书法家 |
| script_type | varchar(50) | 书体 |
| image_url | varchar(255) | 图片地址 |
| meta_json | json | 附加元数据 |
| created_at | datetime | 创建时间 |

## 6. 首版建议先建的核心表

如果时间有限，建议数据库首版优先建这 7 张表：

- `users`
- `courses`
- `classes`
- `class_members`
- `tasks`
- `homework`
- `evaluations`

这 7 张表已经足够支撑：

- 教师建课
- 学生入班
- 任务发布
- 作业上传
- AI 评分
- 基本结果展示

## 7. 第二阶段再补的表

后续再补：

- `task_characters`
- `reviews`
- `resources`

这样可以避免首版数据库设计过重。

## 8. 开发建议

在 `FastAPI` 中建议对应为：

- `models/`
  - 放 SQLAlchemy 模型
- `schemas/`
  - 放 Pydantic 请求和响应结构
- `repositories/`
  - 放数据库读写
- `services/`
  - 放业务逻辑

建议优先落地顺序：

1. `users`
2. `courses`
3. `classes`
4. `tasks`
5. `homework`
6. `evaluations`

这样最符合首版闭环开发。

