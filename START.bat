@echo off
title Sherlock Homes - AI Mortgage Underwriting
echo.
echo ==================================================
echo   SHERLOCK HOMES - AI Mortgage Underwriting
echo ==================================================
echo.
echo Starting server...
echo.

cd /d "%~dp0"

REM Try python, then python3, then py
where python >nul 2>&1
if %errorlevel%==0 (
    python run.py
    goto :end
)

where python3 >nul 2>&1
if %errorlevel%==0 (
    python3 run.py
    goto :end
)

where py >nul 2>&1
if %errorlevel%==0 (
    py run.py
    goto :end
)

echo.
echo ERROR: Python not found!
echo.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.

:end
echo.
echo Press any key to close...
pause >nul
