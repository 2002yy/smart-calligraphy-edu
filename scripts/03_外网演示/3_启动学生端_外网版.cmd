@echo off
setlocal
cd /d "%~dp0..\..\student-app"

echo == Public demo mode: Step 3 of 3 ==
echo.
echo Make sure api-server, teacher-web and their tunnels are running.
echo.
echo Next:
echo 1. This window builds and starts preview
echo 2. Open another terminal and run:
echo    cloudflared tunnel --url http://localhost:4175
echo 3. Open the student public URL on mobile/other device
echo.

:: 自动生成 .env.local（外网地址）
echo VITE_API_BASE_URL=https://twice-dealers-armstrong-quotes.trycloudflare.com > .env.local
echo [OK] .env.local created for public demo.

call npm run build
if errorlevel 1 goto end

call npm run preview -- --host 0.0.0.0 --port 4175

:end
endlocal
