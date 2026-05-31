@echo off
cd /d "%~dp0"

echo ==========================================
echo   智慧书法 — 一键启动（本地版）
echo ==========================================
echo.

:: 先杀残留进程
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: 1. 启动后端（新窗口）
echo [1/3] 启动后端 API Server...
start "API Server" cmd /c "cd /d api-server && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 4 /nobreak >nul

:: 2. 启动教师端（新窗口）
echo [2/3] 启动教师端...
start "Teacher Web" cmd /c "cd /d teacher-web && npm run dev"
timeout /t 3 /nobreak >nul

:: 3. 启动学生端（新窗口）
echo [3/3] 启动学生端...
start "Student App" cmd /c "cd /d student-app && npm run dev"

echo.
echo ==========================================
echo   全部启动完成！
echo   后端:    http://localhost:8000
echo   教师端:  http://localhost:5173
echo   学生端:  http://localhost:5174
echo   关闭窗口即停止服务
echo ==========================================
echo.
pause
