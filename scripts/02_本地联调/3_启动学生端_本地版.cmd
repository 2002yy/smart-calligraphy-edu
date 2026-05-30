@echo off
setlocal
cd /d "%~dp0..\..\student-app"

echo == Local mode: Step 3 of 3 ==
echo.
echo Start student-app in Vite dev mode.
echo You are now in local development mode.
echo If you need public demo mode, use:
echo scripts\03_外网演示
echo.

call npm run dev

endlocal
