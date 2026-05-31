@echo off
cd /d "%~dp0..\..\api-server"
echo 智慧书法 API Server
echo 地址: http://localhost:8000
echo.
:: 清理残留进程
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

call python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
