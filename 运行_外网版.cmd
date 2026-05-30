@echo off
setlocal
cd /d "%~dp0"

echo == Smart Calligraphy: Public demo entry ==
echo.
echo Use this entry for Cloudflare Tunnel demo mode.
echo.
echo Order:
echo 1. scripts\03_外网演示\1_启动后端_外网版.cmd
echo 2. Run: cloudflared tunnel --url http://localhost:8000
echo 3. Update teacher-web\.env.local and student-app\.env.local
echo 4. scripts\03_外网演示\2_启动教师端_外网版.cmd
echo 5. Run: cloudflared tunnel --url http://localhost:4174
echo 6. scripts\03_外网演示\3_启动学生端_外网版.cmd
echo 7. Run: cloudflared tunnel --url http://localhost:4175
echo.
echo The first script will be opened now.
echo.

if not exist "scripts\03_外网演示\1_启动后端_外网版.cmd" (
  echo [ERROR] Public demo entry script was not found.
  echo Expected: scripts\03_外网演示\1_启动后端_外网版.cmd
  echo.
  pause
  exit /b 1
)

call "scripts\03_外网演示\1_启动后端_外网版.cmd"

endlocal
