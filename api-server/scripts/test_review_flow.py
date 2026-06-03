"""验证: 评测后自动创建批阅记录"""
import httpx, sys, json, time
from pathlib import Path

BASE = "http://127.0.0.1:8000/api/v1"
IMG = Path(r"C:\Users\96967\Desktop\大创\code\test-images\good\ouyangxun_yong.jpg")

# 学生登录
r = httpx.post(f"{BASE}/auth/login", json={"username": "student01", "password": "123456"})
s = r.json()["data"]
sh = {"Authorization": f"Bearer {s['access_token']}"}

# 上传
with open(IMG, "rb") as f:
    r = httpx.post(f"{BASE}/homework/upload", headers=sh,
        files={"file": ("test.jpg", f, "image/jpeg")},
        data={"task_id": "1", "student_id": "2"})
hw = r.json()["data"]
hwid, furl = hw["homework_id"], hw["file_url"]
print(f"1. 上传 OK: homework_id={hwid}")

# 提交
httpx.post(f"{BASE}/homework", headers=sh, json={
    "homework_id": hwid, "task_id": 1, "student_id": 2, "image_url": furl})
print("2. 提交 OK")

# 评测
print("3. 评测中（约30秒）...")
r = httpx.post(f"{BASE}/evaluation/start", headers=sh, json={
    "homework_id": hwid, "provider": "qwen", "force_refresh": True}, timeout=60)
print(f"   结果: {r.status_code} provider={r.json().get('data',{}).get('provider','?')}")

# 教师查看批阅
r = httpx.post(f"{BASE}/auth/login", json={"username": "teacher01", "password": "123456"})
th = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
r = httpx.get(f"{BASE}/reviews?teacher_id=1", headers=th)
data = r.json().get("data", [])
print(f"\n4. 教师端批阅记录: {len(data)} 条")
if data:
    for rev in data:
        print(f"   homework={rev['homework_id']} 学生={rev.get('student_name','?')}  AI分={rev.get('score','?')}  终评={rev.get('final_score','?')}  状态={rev['status']}")
else:
    print("   ❌ 没有记录！")
    print("\n正在调试...")
    import sqlite3, os
    os.chdir(r"C:\Users\96967\Desktop\大创\code\api-server")
    conn = sqlite3.connect("smart_calligraphy.db")
    c = conn.cursor()
    c.execute("SELECT count(*) FROM reviews")
    print(f"   DB中reviews表: {c.fetchone()[0]} 条")
    c.execute("SELECT id, homework_id, teacher_id, review_status, final_score FROM reviews")
    for row in c.fetchall():
        print(f"    {row}")
    conn.close()
