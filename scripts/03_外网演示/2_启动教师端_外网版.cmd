@echo off
setlocal
cd /d "%~dp0..\..\teacher-web"

echo == Public demo mode: Step 2 of 3 ==
echo.
echo Make sure api-server and its tunnel are running first.
echo.
echo Next:
echo 1. This window builds and starts preview
echo 2. Open another terminal and run:
echo    cloudflared tunnel --url http://localhost:4174
echo 3. Then run: scripts\03_外网演示\3_启动学生端_外网版.cmd
echo.

:: 自动生成 .env.local（外网地址）
echo VITE_API_BASE_URL=https://twice-dealers-armstrong-quotes.trycloudflare.com > .env.local
echo [OK] .env.local created for public demo.

call npm run build
if errorlevel 1 goto end

call npm run preview -- --host 0.0.0.0 --port 4174

:end
endlocal
