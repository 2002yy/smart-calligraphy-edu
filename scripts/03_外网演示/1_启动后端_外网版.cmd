@echo off
setlocal
cd /d "%~dp0..\..\api-server"

echo == Public demo mode: Step 1 of 3 ==
echo.
echo Mode: Cloudflare Tunnel public demo
echo.
echo This window starts api-server.
echo Next:
echo 1. Open another terminal and run:
echo    cloudflared tunnel --url http://localhost:8000
echo 2. Put the public API URL into:
echo    teacher-web\.env.local
echo    student-app\.env.local
echo 3. Then run:
echo    the teacher public script in scripts\03_外网演示
echo.

call python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

endlocal
