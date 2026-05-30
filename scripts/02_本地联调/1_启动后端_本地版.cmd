@echo off
setlocal
cd /d "%~dp0..\..\api-server"

echo == Local mode: Step 1 of 3 ==
echo.
echo Start api-server for local development.
echo Use this mode for:
echo - local coding
echo - same-LAN testing
echo - Swagger debugging
echo.
echo Next:
echo Open the teacher local script in scripts\02_本地联调
echo.

call python -m uvicorn app.main:app --reload

endlocal
