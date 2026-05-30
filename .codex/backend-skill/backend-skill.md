---
name: backend-skill
description: Build structured, production-ready FastAPI backend with clear architecture, consistent API design, and maintainable code.
---

# Backend Skill (FastAPI)

## 1. When to use
Use this skill when:
- Writing FastAPI APIs
- Designing backend architecture
- Creating database models
- Building scalable backend systems

---

# 2. Architecture Rules

## 2.1 Always use layered architecture

Separate code into clear layers:

- API Layer (router)
- Service Layer (business logic)
- Schema Layer (Pydantic models)
- Model Layer (database)

Never mix these responsibilities.

---

## 2.2 Standard project structure

Always follow this structure:

app/
 ├── main.py
 ├── api/
 │    └── routes/
 │         ├── auth.py
 │         ├── users.py
 │         ├── tasks.py
 │         └── ...
 ├── services/
 │    ├── auth_service.py
 │    ├── task_service.py
 │    └── ...
 ├── schemas/
 │    ├── auth.py
 │    ├── task.py
 │    └── ...
 ├── models/
 │    ├── user.py
 │    ├── task.py
 │    └── ...
 ├── core/
 │    ├── config.py
 │    ├── security.py
 │    └── database.py

---

# 3. API Design Rules

## 3.1 RESTful naming

Use nouns, not verbs.

Correct:
- GET /tasks
- POST /tasks
- GET /tasks/{id}

Wrong:
- /getTasks
- /createTask

---

## 3.2 Unified response format

All APIs must return:

Success:
{
  "code": 0,
  "message": "ok",
  "data": {}
}

Error:
{
  "code": 4001,
  "message": "error message",
  "data": null
}

---

## 3.3 Use proper HTTP methods

- GET → read
- POST → create
- PUT/PATCH → update
- DELETE → delete

---

# 4. Schema Rules (Pydantic)

## 4.1 Always define schemas

Use Pydantic for:
- request body
- response body

Example:

class TaskCreate(BaseModel):
    title: str
    description: str

class TaskRead(BaseModel):
    id: int
    title: str

---

## 4.2 Never return raw dict if structure is important

Always use schema models.

---

# 5. Service Layer Rules

## 5.1 Business logic must be in service layer

BAD:

@router.post("/tasks")
def create_task():
    # logic here ❌

GOOD:

@router.post("/tasks")
def create_task():
    return task_service.create_task()

---

## 5.2 Keep functions small

Each function should do ONE thing.

---

## 5.3 No database logic in router

All DB operations must be inside service or model layer.

---

# 6. Error Handling

## 6.1 Use HTTPException

Example:

raise HTTPException(status_code=404, detail="Task not found")

---

## 6.2 Never crash server

Always return controlled error.

---

# 7. Validation Rules

- Validate required fields
- Validate types
- Provide default values when needed

---

# 8. Coding Style

- Use clear variable names
- Avoid deeply nested logic
- Keep functions readable
- Avoid duplication

---

# 9. Business-Oriented Design (IMPORTANT)

Always think in real workflow:

teacher → create task → student submit → AI evaluate → teacher review

APIs should follow this flow.

---

# 10. Output Requirements (VERY IMPORTANT)

When generating code:

1. First show file structure
2. Then show code per file
3. Keep formatting clean
4. Do NOT mix multiple layers in one file
5. Avoid unnecessary explanation

---

# 11. Example Pattern

## Router

@router.post("/tasks")
def create_task(data: TaskCreate):
    return success(task_service.create_task(data))

---

## Service

def create_task(data):
    task = Task(...)
    db.add(task)
    db.commit()
    return task

---

## Schema

class TaskCreate(BaseModel):
    title: str

---

# 12. Goal

Always produce backend code that is:

- structured
- scalable
- maintainable
- production-like

Avoid "demo-style" or "all-in-one-file" code.