@echo off
cd /d "%~dp0"

REM Check if Python is installed
if not exist "python\python.exe" (
    echo Python not found. Running setup first...
    echo.
    call setup.bat
    if errorlevel 1 (
        echo Setup failed. Please try again.
        pause
        exit /b 1
    )
)

REM Start the application
title Hardware Inventory Tracker
echo ================================
echo Hardware Inventory Tracker
echo ================================
echo.
echo Starting application...
echo The web browser will open automatically.
echo Keep this window open while using the application.
echo.
echo To stop the application, close this window or press Ctrl+C.
echo.

python\python.exe launcher.py

REM If we get here, the application has stopped
echo.
echo Application stopped.
pause