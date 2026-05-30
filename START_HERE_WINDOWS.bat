@echo off
echo.
echo  ================================================
echo   LeaseLens — Windows Quick Start Checker
echo  ================================================
echo.

echo Checking required tools...
echo.

python --version 2>nul
if %errorlevel% neq 0 (
    echo  [MISSING] Python not found!
    echo  Download from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during install!
    pause
    exit /b 1
) else (
    echo  [OK] Python found
)

node --version 2>nul
if %errorlevel% neq 0 (
    echo  [MISSING] Node.js not found!
    echo  Download from: https://nodejs.org (click LTS)
    pause
    exit /b 1
) else (
    echo  [OK] Node.js found
)

git --version 2>nul
if %errorlevel% neq 0 (
    echo  [MISSING] Git not found!
    echo  Download from: https://git-scm.com/download/win
    pause
    exit /b 1
) else (
    echo  [OK] Git found
)

echo.
echo  All tools found! Now follow WINDOWS_SETUP.md to configure and run.
echo.
pause
