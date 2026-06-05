"""Fix remaining P1 issues: reports auth, permission fail-close, teacher list scope"""
import os

ROOT = r"C:\Users\96967\Desktop\大创\code"

def fix(fp, old, new, label):
    with open(fp, encoding="utf-8") as f:
        s = f.read()
    if old not in s:
        print(f"  [SKIP] {label}")
        return
    s = s.replace(old, new)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(s)
    print(f"  [OK] {label}")


# === 1: reports.py — add actual auth ===
print("\n=== 1. reports.py ===")
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "reports.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

# Fix student_report
old = (
    'def student_report(student_id: int, current_user: dict = Depends(require_role(["teacher"])),'
    ' db: Session = Depends(get_db)):'
)
new = (
    'def student_report(student_id: int, current_user: dict = Depends(get_current_user),'
    ' db: Session = Depends(get_db)):\n'
    '    if current_user["role"] == "student" and current_user["id"] != student_id:\n'
    '        raise HTTPException(status_code=403, detail="学生只能查看自己的报告")'
)
if old in s:
    s = s.replace(old, new)
    print("  [OK] student_report")
else:
    print("  [WARN] student_report pattern not found")

# Fix class_report
old = (
    'def class_report(class_id: int, current_user: dict = Depends(require_role(["teacher"])),'
    ' db: Session = Depends(get_db)):'
)
new = (
    'def class_report(class_id: int, current_user: dict = Depends(require_role(["teacher"])),'
    ' db: Session = Depends(get_db)):\n'
    '    assert_owns_class(db, current_user, class_id)'
)
if old in s:
    s = s.replace(old, new)
    print("  [OK] class_report")
else:
    print("  [WARN] class_report pattern not found")

# Fix export
if 'def export_report(payload: ReportExportRequest, db: Session = Depends(get_db)):' in s:
    s = s.replace(
        'def export_report(payload: ReportExportRequest, db: Session = Depends(get_db)):',
        'def export_report(payload: ReportExportRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):'
    )
    print("  [OK] export_report")

# Add missing imports
s = s.replace(
    "from app.services import ReportService\nfrom app.repositories import CourseRepository, ClassroomRepository",
    "from app.repositories import CourseRepository, ClassroomRepository\nfrom app.services import ReportService\nfrom app.services.auth_service import get_current_user, require_role\nfrom app.services.permission_service import assert_owns_class"
)

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)


# === 2: permission_service.py — fail-close ===
print("\n=== 2. permission_service.py ===")
fp = os.path.join(ROOT, "api-server", "app", "services", "permission_service.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

old_own = (
    "def assert_owns_homework(db: Session, current_user: dict, homework_id: int) -> dict:\n"
    '    hw = HomeworkRepository.get_by_id(db, homework_id)\n'
    '    if not hw:\n'
    '        raise HTTPException(status_code=404, detail="homework not found")\n'
    '    if current_user["role"] == "student" and hw.student_id != current_user["id"]:\n'
    '        _crash("学生只能操作自己的作业")\n'
    '    if current_user["role"] == "teacher":\n'
    '        task = TaskRepository.get_by_id(db, hw.task_id)\n'
    '        if task:\n'
    '            course = CourseRepository.get_by_id(db, task.course_id)\n'
    '            if course and course.teacher_id != current_user["id"]:\n'
    '                _crash("教师只能操作自己课程下的作业")\n'
    '    return hw'
)

new_own = (
    "def assert_owns_homework(db: Session, current_user: dict, homework_id: int) -> dict:\n"
    '    hw = HomeworkRepository.get_by_id(db, homework_id)\n'
    '    if not hw:\n'
    '        raise HTTPException(status_code=404, detail="homework not found")\n'
    '    role = current_user.get("role")\n'
    '    if role == "student":\n'
    '        if hw.student_id != current_user["id"]:\n'
    '            _crash("学生只能操作自己的作业")\n'
    '        return hw\n'
    '    if role == "teacher":\n'
    '        task = TaskRepository.get_by_id(db, hw.task_id)\n'
    '        if not task:\n'
    '            _crash("作业任务不存在，无法校验权限")\n'
    '        course = CourseRepository.get_by_id(db, task.course_id)\n'
    '        if not course or course.teacher_id != current_user["id"]:\n'
    '            _crash("教师只能操作自己课程下的作业")\n'
    '        return hw\n'
    '    _crash("无权操作该作业")'
)

if old_own in s:
    s = s.replace(old_own, new_own)
    print("  [OK] assert_owns_homework fail-close")
else:
    print("  [WARN] assert_owns_homework not found")

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)


# === 3: homework.py — get_homework uses assert_owns_homework ===
print("\n=== 3. homework.py ===")
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "homework.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

old = (
    'def get_homework(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n'
    '    hw = HomeworkService.get_homework(db, homework_id)\n'
    '    if current_user["role"] == "student" and current_user["id"] != hw["student_id"]:\n'
    '        raise HTTPException(status_code=403, detail="学生只能查看自己的作业")\n'
    '    data = HomeworkRead(**hw)\n'
    '    return APIResponse[HomeworkRead](data=data)'
)
new = (
    'def get_homework(homework_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n'
    '    from app.services.permission_service import assert_owns_homework\n'
    '    assert_owns_homework(db, current_user, homework_id)\n'
    '    data = HomeworkRead(**HomeworkService.get_homework(db, homework_id))\n'
    '    return APIResponse[HomeworkRead](data=data)'
)
if old in s:
    s = s.replace(old, new)
    print("  [OK] get_homework")
else:
    print("  [WARN] get_homework pattern not found")

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)


# === 4: reviews.py — teacher_id from token ===
print("\n=== 4. reviews.py ===")
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "reviews.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

old_list = (
    'def list_reviews(\n'
    '    teacher_id: int | None = None,\n'
    '    homework_id: int | None = None,\n'
    '    current_user: dict = Depends(require_role(["teacher"])),\n'
    '    db: Session = Depends(get_db),\n'
    '):\n'
    '    data = [ReviewRead(**item) for item in ReviewService.list_reviews(db, teacher_id=teacher_id, homework_id=homework_id)]'
)
new_list = (
    'def list_reviews(\n'
    '    teacher_id: int | None = None,\n'
    '    homework_id: int | None = None,\n'
    '    current_user: dict = Depends(require_role(["teacher"])),\n'
    '    db: Session = Depends(get_db),\n'
    '):\n'
    '    data = [ReviewRead(**item) for item in ReviewService.list_reviews(db, teacher_id=current_user["id"], homework_id=homework_id)]'
)
if old_list in s:
    s = s.replace(old_list, new_list)
    print("  [OK] list_reviews teacher_id from token")
else:
    print("  [WARN] list_reviews not found")

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)


# === 5: classes.py — student guard + clean imports ===
print("\n=== 5. classes.py ===")
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "classes.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

old_join = (
    'def join_class(class_id: int, payload: ClassJoinRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n'
    '    payload.student_id = current_user["id"]'
)
new_join = (
    'def join_class(class_id: int, payload: ClassJoinRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):\n'
    '    if current_user["role"] != "student":\n'
    '        raise HTTPException(status_code=403, detail="仅学生可以加入班级")\n'
    '    payload.student_id = current_user["id"]'
)
if old_join in s:
    s = s.replace(old_join, new_join)
    print("  [OK] join_class student guard")

# Clean duplicate imports (simplified approach: remove duplicates line by line)
lines = s.split("\n")
seen = []
new_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith("from ") and stripped in seen:
        continue
    if stripped.startswith("from ") and stripped.startswith(("from app.services.", "from app.repositories.")):
        if stripped in seen:
            continue
        seen.append(stripped)
    new_lines.append(line)
s = "\n".join(new_lines)
with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("  [OK] cleaned duplicate imports")


# === 6: main.py — extend middleware to /storage/calligraphy_db/ ===
print("\n=== 6. main.py ===")
fp = os.path.join(ROOT, "api-server", "app", "main.py")
with open(fp, "r+", encoding="utf-8") as f:
    s = f.read()
    old = 'if request.url.path.startswith("/uploads/"):'
    new = 'if request.url.path.startswith("/uploads/") or request.url.path.startswith("/storage/calligraphy_db/"):'
    if old in s:
        s = s.replace(old, new)
        f.seek(0)
        f.write(s)
        f.truncate()
        print("  [OK] middleware extended")
    else:
        print("  [WARN] middleware pattern not found")


print("\n=== All fixes applied! ===")
