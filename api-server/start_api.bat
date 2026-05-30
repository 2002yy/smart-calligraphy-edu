@echo off
cd /d "%~dp0"
echo 智慧书法 API Server
echo 地址: http://localhost:8000
echo 文档: http://localhost:8000/docs
echo.
call python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
