@echo off
cd /d "%~dp0"

echo ==========================================
echo   智慧书法 — 外网演示启动
echo ==========================================
echo.
echo 启动后需手动运行 Cloudflare Tunnel：
echo   cloudflared tunnel --url http://localhost:8000
echo   cloudflared tunnel --url http://localhost:4174
echo   cloudflared tunnel --url http://localhost:4175
echo.

:: 杀残留
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: 1. 后端
echo [1/3] 启动后端 API Server...
start "API Server" cmd /c "cd /d api-server && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 4 /nobreak >nul

:: 2. 教师端（外网版 — 自动构建+预览+生成.env.local）
echo [2/3] 构建并启动教师端（外网版）...
start "Teacher Web" cmd /c "cd /d teacher-web && echo VITE_API_BASE_URL=https://twice-dealers-armstrong-quotes.trycloudflare.com > .env.local && npm run build && npm run preview -- --host 0.0.0.0 --port 4174"
timeout /t 3 /nobreak >nul

:: 3. 学生端（外网版）
echo [3/3] 构建并启动学生端（外网版）...
start "Student App" cmd /c "cd /d student-app && echo VITE_API_BASE_URL=https://twice-dealers-armstrong-quotes.trycloudflare.com > .env.local && npm run build && npm run preview -- --host 0.0.0.0 --port 4175"

echo.
echo ==========================================
echo   启动完成！接下来要跑 3 个 Tunnel：
echo   cloudflared tunnel --url http://localhost:8000
echo   cloudflared tunnel --url http://localhost:4174
echo   cloudflared tunnel --url http://localhost:4175
echo.
echo   外网地址已在 .env.local 中预设
echo ==========================================
echo.
pause
