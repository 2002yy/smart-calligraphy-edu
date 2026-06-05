"""Fix all permission issues + tests - batch fix"""
import os, re

ROOT = r"C:\Users\96967\Desktop\大创\code"

def read(fp): return open(fp, encoding="utf-8").read()
def write(fp, s): open(fp, "w", encoding="utf-8").write(s)

# ========== Fix 1: evaluation.py auth ==========
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "evaluation.py")
s = read(fp)
s = s.replace("from fastapi import APIRouter, Depends", "from fastapi import APIRouter, Depends, HTTPException")
s = s.replace(
    "from app.services import EvaluationService",
    "from app.repositories import HomeworkRepository\nfrom app.services import EvaluationService\nfrom app.services.auth_service import get_current_user"
)
old_eval = 'def start_evaluation(payload: EvaluationStartRequest, db: Session = Depends(get_db)):\n    data = EvaluationStartRead(\n        **EvaluationService.start(\n            db,\n            payload.homework_id,\n            provider=payload.provider,\n            force_refresh=payload.force_refresh,\n        )\n    )\n    return APIResponse[EvaluationStartRead](data=data)'
new_eval = 'def start_evaluation(payload: EvaluationStartRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n    if current_user["role"] == "student":\n        hw = HomeworkRepository.get_by_id(db, payload.homework_id)\n        if not hw or hw.student_id != current_user["id"]:\n            raise HTTPException(status_code=403, detail="学生只能评测自己的作业")\n    data = EvaluationStartRead(\n        **EvaluationService.start(\n            db,\n            payload.homework_id,\n            provider=payload.provider,\n            force_refresh=payload.force_refresh,\n        )\n    )\n    return APIResponse[EvaluationStartRead](data=data)'
assert old_eval in s, "eval start not found"
s = s.replace(old_eval, new_eval)

old_get = 'def get_evaluation(homework_id: int, db: Session = Depends(get_db)):\n    data = EvaluationRead(**EvaluationService.get(db, homework_id))\n    return APIResponse[EvaluationRead](data=data)'
new_get = 'def get_evaluation(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n    if current_user["role"] == "student":\n        hw = HomeworkRepository.get_by_id(db, homework_id)\n        if not hw or hw.student_id != current_user["id"]:\n            raise HTTPException(status_code=403, detail="学生只能查看自己作业的评测")\n    data = EvaluationRead(**EvaluationService.get(db, homework_id))\n    return APIResponse[EvaluationRead](data=data)'
assert old_get in s, "eval get not found"
s = s.replace(old_get, new_get)
write(fp, s)
print("[1] evaluation.py")

# ========== Fix 2: courses.py auth ==========
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "courses.py")
s = read(fp)
s = s.replace(
    "from app.services import CourseService",
    "from app.services import CourseService\nfrom app.services.auth_service import require_role"
)
s = s.replace(
    "def create_course(payload: CourseCreate, db: Session = Depends(get_db)):",
    "def create_course(payload: CourseCreate, current_user: dict = Depends(require_role([\"teacher\"])), db: Session = Depends(get_db)):"
)
write(fp, s)
print("[2] courses.py")

# ========== Fix 3: classes.py auth ==========
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "classes.py")
s = read(fp)
s = s.replace(
    "from app.services import ClassService",
    "from app.services import ClassService\nfrom app.services.auth_service import get_current_user, require_role"
)
s = s.replace(
    'def create_class(payload: ClassCreate, db: Session = Depends(get_db)):',
    'def create_class(payload: ClassCreate, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):'
)
s = s.replace(
    'def join_class(class_id: int, payload: ClassJoinRequest, db: Session = Depends(get_db)):',
    'def join_class(class_id: int, payload: ClassJoinRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):'
)
s = s.replace(
    'def get_members(class_id: int, db: Session = Depends(get_db)):',
    'def get_members(class_id: int, current_user: dict = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):'
)
write(fp, s)
print("[3] classes.py")

# ========== Fix 4: users.py auth + service ==========
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "users.py")
s = read(fp)
s = s.replace(
    "from app.services import UserService",
    "from app.services import UserService\nfrom app.services.auth_service import get_current_user"
)
s = s.replace("def get_user(user_id: int, db: Session = Depends(get_db)):", "def get_user(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):")
s = s.replace("def get_growth(user_id: int, db: Session = Depends(get_db)):", "def get_growth(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):")
s = s.replace("UserService.get_user(db, user_id)", "UserService.get_user(db, user_id, current_user)")
s = s.replace("UserService.get_growth(db, user_id)", "UserService.get_growth(db, user_id, current_user)")
write(fp, s)
print("[4] users.py")

fp = os.path.join(ROOT, "api-server", "app", "services", "user_service.py")
s = read(fp)
old_get = '''    @staticmethod
    def get_user(db: Session, user_id: int) -> dict:'''
new_get = '''    @staticmethod
    def get_user(db: Session, user_id: int, current_user: dict | None = None) -> dict:
        if current_user and current_user.get("role") == "student" and current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="学生只能查看自己的信息")'''
s = s.replace(old_get, new_get)
old_growth = '''    @staticmethod
    def get_growth(db: Session, user_id: int) -> dict:'''
new_growth = '''    @staticmethod
    def get_growth(db: Session, user_id: int, current_user: dict | None = None) -> dict:
        if current_user and current_user.get("role") == "student" and current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="学生只能查看自己的成长数据")'''
s = s.replace(old_growth, new_growth)
write(fp, s)
print("[4b] user_service.py")

# ========== Fix 5: homework_service submit_homework ownership check ==========
fp = os.path.join(ROOT, "api-server", "app", "services", "homework_service.py")
s = read(fp)
old_hw = '''    @staticmethod
    def submit_homework(db: Session, payload: HomeworkSubmitRequest) -> dict:
        if payload.homework_id is not None:
            homework = HomeworkRepository.get_by_id(db, payload.homework_id)
            if not homework:
                raise HTTPException(status_code=404, detail="homework not found")
            if payload.image_url:
                homework.image_url = payload.image_url
            homework.status = "submitted"
            homework = HomeworkRepository.update_homework(db, homework)
            return HomeworkService._serialize(homework)'''
new_hw = '''    @staticmethod
    def submit_homework(db: Session, payload: HomeworkSubmitRequest, current_user: dict | None = None) -> dict:
        if payload.homework_id is not None:
            homework = HomeworkRepository.get_by_id(db, payload.homework_id)
            if not homework:
                raise HTTPException(status_code=404, detail="homework not found")
            if current_user and current_user.get("role") == "student" and homework.student_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="学生只能提交自己的作业")
            if payload.image_url:
                homework.image_url = payload.image_url
            homework.status = "submitted"
            homework = HomeworkRepository.update_homework(db, homework)
            return HomeworkService._serialize(homework)'''
s = s.replace(old_hw, new_hw)
write(fp, s)
print("[5] homework_service.py")

# ========== Fix 6: main.py static resource auth ==========
fp = os.path.join(ROOT, "api-server", "app", "main.py")
s = read(fp)
old_mw = '''            if not (token and (verify_token(token) or verify_signed_path(token))):
                return JSONResponse(status_code=403, content={"code": 1, "message": "无权访问静态资源，请先登录。", "data": None})
            # 验证签名 token 是否绑定当前请求路径
            signed_path = verify_signed_path(token)
            if signed_path and signed_path != request.url.path:
                return JSONResponse(status_code=403, content={"code": 1, "message": "签名 Token 与请求路径不匹配。", "data": None})'''
new_mw = '''            normal_auth = verify_token(token)
            if normal_auth:
                return await call_next(request)

            signed_path = verify_signed_path(token)
            if signed_path and signed_path == request.url.path:
                return await call_next(request)

            return JSONResponse(status_code=403, content={"code": 1, "message": "无权访问静态资源，请先登录。", "data": None})'''
if old_mw in s:
    s = s.replace(old_mw, new_mw)
    print("[6] main.py middleware")
else:
    print("[6] main.py - already fixed or pattern changed")

write(fp, s)

# ========== Fix 7: Tests ==========
fp = os.path.join(ROOT, "api-server", "tests", "test_api_flow.py")
s = read(fp)

# Fix course creation - add teacher token + remove teacher_id
s = s.replace(
    '''        course_response = client.post(
            "/api/v1/courses",
            json={
                "name": "Pytest Demo Course",
                "term": "2026-Spring",
                "description": "Course used by automated integration test",
                "teacher_id": 1,
            },
        )''',
    '''        course_response = client.post(
            "/api/v1/courses",
            json={
                "name": "Pytest Demo Course",
                "term": "2026-Spring",
                "description": "Course used by automated integration test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )'''
)

# Fix class creation - add teacher token
s = s.replace(
    '''        class_response = client.post(
            "/api/v1/classes",
            json={
                "course_id": course_id,
                "name": "Pytest Demo Class",
                "invite_code": "PYTEST2026",
            },
        )''',
    '''        class_response = client.post(
            "/api/v1/classes",
            json={
                "course_id": course_id,
                "name": "Pytest Demo Class",
                "invite_code": "PYTEST2026",
            },
            headers={"Authorization": f"Bearer {token}"},
        )'''
)

# Fix join - use student token
s = s.replace(
    '''        join_response = client.post(
            f"/api/v1/classes/{class_id}/join",
            json={"invite_code": "PYTEST2026", "student_id": 2},
        )''',
    '''        join_response = client.post(
            f"/api/v1/classes/{class_id}/join",
            json={"invite_code": "PYTEST2026", "student_id": 2},
            headers={"Authorization": f"Bearer {_stok}"},
        )'''
)

# Fix evaluation start - add student token
s = s.replace(
    '''        evaluation_response = client.post(
            "/api/v1/evaluation/start",
            json={"homework_id": homework_id},
        )''',
    '''        evaluation_response = client.post(
            "/api/v1/evaluation/start",
            json={"homework_id": homework_id},
            headers={"Authorization": f"Bearer {_stok}"},
        )'''
)

# Fix evaluation get - add student token
s = s.replace(
    '''        evaluation_detail_response = client.get(f"/api/v1/evaluation/{homework_id}")''',
    '''        evaluation_detail_response = client.get(f"/api/v1/evaluation/{homework_id}", headers={"Authorization": f"Bearer {_stok}"})'''
)

# Fix review - already has token from earlier fix

# Fix second test
s = s.replace(
    '''        evaluation_response = client.post(
            "/api/v1/evaluation/start",
            json={"homework_id": homework_id, "provider": "openai", "force_refresh": True},
        )''',
    '''        evaluation_response = client.post(
            "/api/v1/evaluation/start",
            json={"homework_id": homework_id, "provider": "openai", "force_refresh": True},
            headers={"Authorization": f"Bearer {_stok}"},
        )'''
)

write(fp, s)
print("[7] tests")

print("\n=== All fixes applied ===")
