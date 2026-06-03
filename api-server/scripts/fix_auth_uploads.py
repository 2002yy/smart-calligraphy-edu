"""Fix: student_id from token + signed image URLs"""
import os

ROOT = r"C:\Users\96967\Desktop\大创\code"

# === 1. homework.py: student_id from token ===
fp = os.path.join(ROOT, "api-server", "app", "api", "routes", "homework.py")
with open(fp, encoding="utf-8") as f:
    s = f.read()

# Add import
s = s.replace(
    "from app.services import HomeworkService",
    "from app.services import HomeworkService\nfrom app.services.auth_service import get_current_user"
)

# Replace function signature
old = """def upload_homework(
    task_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):"""
new = """def upload_homework(
    task_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student_id = current_user["id"]
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="仅学生可以上传作业")"""
assert old in s, "upload signature not found!"
s = s.replace(old, new)

with open(fp, "w", encoding="utf-8") as f:
    f.write(s)
print("1. homework.py OK")


# === 2. token_service.py: add sign_path / verify_signed_path ===
fp2 = os.path.join(ROOT, "api-server", "app", "services", "token_service.py")
with open(fp2, encoding="utf-8") as f:
    s = f.read()

old_tail = """def verify_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts

        expected_sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None"""

new_tail = """def verify_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts

        expected_sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def sign_image_path(image_path: str, expires_in: int = 3600) -> str:
    \"\"\"为图片路径生成签名 token，默认 1 小时过期。\n\n    Args:\n        image_path: 图片 URL 路径，如 /uploads/homework/2/1/xxx.jpg\n        expires_in: 过期秒数\n\n    Returns:\n        签名 token 字符串\n    \"\"\"
    payload = {
        "path": image_path,
        "exp": int(time.time()) + expires_in,
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_signed_path(token: str) -> str | None:
    \"\"\"验证图片签名 token，返回图片路径。\"\"\"
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("path", "")
    except Exception:
        return None"""

assert old_tail in s, "token_service old tail not found!"
s = s.replace(old_tail, new_tail)
with open(fp2, "w", encoding="utf-8") as f:
    f.write(s)
print("2. token_service.py OK")


# === 3. main.py: accept ?token= in SECURE_STATIC middleware ===
fp3 = os.path.join(ROOT, "api-server", "app", "main.py")
with open(fp3, encoding="utf-8") as f:
    s = f.read()

old_mw = """    @app.middleware("http")
    async def protect_uploads(request: Request, call_next):
        if request.url.path.startswith("/uploads/"):
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            if not verify_token(token):
                return JSONResponse(status_code=403, content={"code": 1, "message": "无权访问静态资源，请先登录。", "data": None})
        return await call_next(request)"""

new_mw = """    @app.middleware("http")
    async def protect_uploads(request: Request, call_next):
        if request.url.path.startswith("/uploads/"):
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            # 也支持 ?token=xxx 查询参数（用于 <img> 标签直接加载）
            if not token:
                token = request.query_params.get("token", "")
            if not (token and (verify_token(token) or verify_signed_path(token))):
                return JSONResponse(status_code=403, content={"code": 1, "message": "无权访问静态资源，请先登录。", "data": None})
        return await call_next(request)"""

assert old_mw in s, "main.py middleware not found!"
s = s.replace(old_mw, new_mw)

import re
# Add verify_signed_path import if not there
if "verify_signed_path" not in s:
    s = s.replace(
        "from app.services.token_service import verify_token",
        "from app.services.token_service import sign_image_path, verify_signed_path, verify_token"
    )

with open(fp3, "w", encoding="utf-8") as f:
    f.write(s)
print("3. main.py OK")


# === 4. Add sign endpoint ===
fp4 = os.path.join(ROOT, "api-server", "app", "api", "routes", "calligraphy.py")
with open(fp4, encoding="utf-8") as f:
    s = f.read()

# Add sign url endpoint at end of file
old_eof = """@router.get(
    "/match",
    response_model=APIResponse[list[CalligraphyMatch]],
    summary="按字查询名家碑帖",
"""
new_eof = """@router.get(
    "/sign",
    summary="获取图片签名 URL",
    description="传入图片路径，返回带签名的临时 URL（用于 SECURE_STATIC=true 时 <img> 标签加载）。",
)
def sign_image(
    path: str = Query(..., description="图片路径，如 /uploads/homework/2/1/xxx.jpg"),
):
    from app.services.token_service import sign_image_path
    token = sign_image_path(path)
    return APIResponse(data={"signed_url": f"{path}?token={token}"})


@router.get(
    "/match",
    response_model=APIResponse[list[CalligraphyMatch]],
    summary="按字查询名家碑帖",
"""

assert old_eof in s, "calligraphy.py match endpoint not found!"
s = s.replace(old_eof, new_eof)

with open(fp4, "w", encoding="utf-8") as f:
    f.write(s)
print("4. calligraphy.py sign endpoint OK")


# === 5. Frontend: update upload to not send student_id ===
fp5 = os.path.join(ROOT, "student-app", "src", "api.ts")
with open(fp5, encoding="utf-8") as f:
    s = f.read()

# Remove student_id from upload
old_up = """  uploadHomework(payload: {
    task_id: number;
    student_id: number;
    file: File;
  }) {
    const formData = new FormData();
    formData.append("task_id", String(payload.task_id));
    formData.append("student_id", String(payload.student_id));
    formData.append("file", payload.file);"""

new_up = """  uploadHomework(payload: {
    task_id: number;
    file: File;
  }) {
    const formData = new FormData();
    formData.append("task_id", String(payload.task_id));
    formData.append("file", payload.file);"""

assert old_up in s, "upload in api.ts not found!"
s = s.replace(old_up, new_up)

with open(fp5, "w", encoding="utf-8") as f:
    f.write(s)
print("5. api.ts OK")


# === 6. Frontend store: update upload call ===
fp6 = os.path.join(ROOT, "student-app", "src", "stores", "student.ts")
with open(fp6, encoding="utf-8") as f:
    s = f.read()

old_store = """      const uploadResult = await studentApi.uploadHomework({
        task_id: selectedTask.value.id,
        student_id: user.value.id,
        file: selectedFile.value
      });"""

new_store = """      const uploadResult = await studentApi.uploadHomework({
        task_id: selectedTask.value.id,
        file: selectedFile.value
      });"""

assert old_store in s, "store upload call not found!"
s = s.replace(old_store, new_store)

with open(fp6, "w", encoding="utf-8") as f:
    f.write(s)
print("6. student.ts OK")


# === 7. Frontend: add signImageUrl + use for calligraphy images ===
fp7 = os.path.join(ROOT, "student-app", "src", "lib", "request.ts")
with open(fp7, encoding="utf-8") as f:
    s = f.read()

# Add as field on request object (add after timeout)
old_base = """const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 120000
});"""

new_base = """const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 120000
});

// 图片签名：生成带 token 的临时图片 URL（支持 SECURE_STATIC=true）
request.signImageUrl = async (url: string): Promise<string> => {
  if (!import.meta.env.VITE_API_BASE_URL && !window.location.origin.includes("localhost")) {
    // 外网模式才需要签名
    try {
      const res = await request.get("/api/v1/calligraphy/sign", { params: { path: url } }) as any;
      return (res as any)?.signed_url || url;
    } catch { return url; }
  }
  return url;
};"""

assert old_base in s, "request base not found!"
s = s.replace(old_base, new_base)

with open(fp7, "w", encoding="utf-8") as f:
    f.write(s)
print("7. request.ts OK")


print("\nAll done!")
