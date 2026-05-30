@echo off
setlocal
cd /d "%~dp0..\..\student-app"

echo == Public demo mode: Step 3 of 3 ==
echo.
echo Please confirm:
echo 1. api-server is running
echo 2. api-server tunnel is running
echo 3. student-app\.env.local contains public API URL
echo.
echo Next:
echo 1. This window starts preview
echo 2. Open another terminal and run:
echo    cloudflared tunnel --url http://localhost:4175
echo 3. Open the student public URL on mobile
echo.

if not exist ".env.local" (
  echo [WARN] student-app\.env.local was not found.
  echo Create .env.local first and set public API URL.
  echo.
)

call npm run build
if errorlevel 1 goto end

call npm run preview -- --host 0.0.0.0 --port 4175

:end
endlocal
