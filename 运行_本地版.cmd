@echo off
setlocal
cd /d "%~dp0"

echo == Smart Calligraphy: Local mode entry ==
echo.
echo Open these scripts in order:
echo 1. scripts\02_本地联调\1_启动后端_本地版.cmd
echo 2. scripts\02_本地联调\2_启动教师端_本地版.cmd
echo 3. scripts\02_本地联调\3_启动学生端_本地版.cmd
echo.
echo The first script will be opened now.
echo Open the remaining two in new terminals.
echo.

if not exist "scripts\02_本地联调\1_启动后端_本地版.cmd" (
  echo [ERROR] Local entry script was not found.
  echo Expected: scripts\02_本地联调\1_启动后端_本地版.cmd
  echo.
  pause
  exit /b 1
)

call "scripts\02_本地联调\1_启动后端_本地版.cmd"

endlocal
