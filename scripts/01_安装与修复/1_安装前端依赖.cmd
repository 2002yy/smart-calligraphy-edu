@echo off
setlocal
cd /d "%~dp0..\.."

echo == Step 1: Install frontend dependencies ==
echo.
echo This script will install:
echo 1. teacher-web dependencies
echo 2. student-app dependencies
echo.

if not exist "%~dp0..\..\teacher-web\package.json" (
  echo [ERROR] teacher-web\package.json was not found.
  echo Check whether the project root path is correct.
  echo.
  pause
  exit /b 1
)

if not exist "%~dp0..\..\student-app\package.json" (
  echo [ERROR] student-app\package.json was not found.
  echo Check whether the project root path is correct.
  echo.
  pause
  exit /b 1
)

echo [1/2] Installing teacher-web dependencies...
cd /d "%~dp0..\..\teacher-web"
call npm install
if errorlevel 1 (
  echo.
  echo [ERROR] teacher-web dependency installation failed.
  echo Please check npm output above.
  echo.
  pause
  exit /b 1
)

echo.
echo [2/2] Installing student-app dependencies...
cd /d "%~dp0..\..\student-app"
call npm install
if errorlevel 1 (
  echo.
  echo [ERROR] student-app dependency installation failed.
  echo Please check npm output above.
  echo.
  pause
  exit /b 1
)

:end
echo.
echo Done.
pause
endlocal
