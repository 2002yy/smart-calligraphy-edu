@echo off
setlocal
cd /d "%~dp0"

echo == Smart Calligraphy: Repair teacher-web ==
echo.
echo This entry will run:
echo scripts\01_安装与修复\2_修复教师端依赖.cmd
echo.

if not exist "scripts\01_安装与修复\2_修复教师端依赖.cmd" (
  echo [ERROR] Repair script was not found.
  echo Expected: scripts\01_安装与修复\2_修复教师端依赖.cmd
  echo.
  pause
  exit /b 1
)

call "scripts\01_安装与修复\2_修复教师端依赖.cmd"

endlocal
