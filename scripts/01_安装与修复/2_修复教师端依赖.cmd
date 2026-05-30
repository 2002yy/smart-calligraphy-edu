@echo off
setlocal
cd /d "%~dp0..\..\teacher-web"

echo == Step 2: Repair teacher-web dependencies ==
echo.
echo Use this script when:
echo 1. npm install was interrupted
echo 2. vite cannot be found
echo 3. node_modules is broken
echo.
echo Actions:
echo - remove node_modules
echo - remove package-lock.json
echo - verify npm cache
echo - reinstall dependencies
echo.

if not exist ".\package.json" (
  echo [ERROR] teacher-web\package.json was not found.
  echo Check whether the current project structure is complete.
  echo.
  pause
  exit /b 1
)

if exist ".\node_modules" (
  echo [1/4] Removing node_modules...
  rmdir /s /q ".\node_modules"
)

if exist ".\package-lock.json" (
  echo [2/4] Removing package-lock.json...
  del /f /q ".\package-lock.json"
)

echo [3/4] Verifying npm cache...
call npm cache verify
if errorlevel 1 (
  echo.
  echo [ERROR] npm cache verification failed for teacher-web.
  echo.
  pause
  exit /b 1
)

echo [4/4] Reinstalling teacher-web dependencies...
call npm install --fetch-retries 5 --fetch-retry-maxtimeout 120000
if errorlevel 1 (
  echo.
  echo [ERROR] teacher-web dependency reinstall failed.
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
