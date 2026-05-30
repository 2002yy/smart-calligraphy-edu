@echo off
setlocal
cd /d "%~dp0..\..\teacher-web"

echo == Local mode: Step 2 of 3 ==
echo.
echo Start teacher-web in Vite dev mode.
echo Use this mode for:
echo - local UI work
echo - teacher-web debugging
echo.
echo Next:
echo Open the student local script in scripts\02_本地联调
echo.

call npm run dev

endlocal
