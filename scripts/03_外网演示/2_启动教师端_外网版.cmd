@echo off
setlocal
cd /d "%~dp0..\..\teacher-web"

echo == Public demo mode: Step 2 of 3 ==
echo.
echo Please confirm:
echo 1. api-server is running
echo 2. api-server tunnel is running
echo 3. teacher-web\.env.local contains public API URL
echo.
echo Next:
echo 1. This window starts preview
echo 2. Open another terminal and run:
echo    cloudflared tunnel --url http://localhost:4174
echo 3. Then run:
echo    the student public script in scripts\03_外网演示
echo.

if not exist ".env.local" (
  echo [WARN] teacher-web\.env.local was not found.
  echo Create .env.local first and set public API URL.
  echo.
)

call npm run build
if errorlevel 1 goto end

call npm run preview -- --host 0.0.0.0 --port 4174

:end
endlocal
