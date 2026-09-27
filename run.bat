@echo off
cd /d "%~dp0"
title BheedRakshak AI
echo ========================================================
echo Starting BheedRakshak AI Live Pipeline...
echo ========================================================
"C:\Users\Asus\AppData\Local\Programs\Python\Python313\python.exe" app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Pipeline exited with error code %ERRORLEVEL%.
)
echo.
echo Press any key to close this terminal.
pause >nul
