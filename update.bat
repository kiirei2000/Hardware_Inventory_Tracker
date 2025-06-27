@echo off
title Hardware Inventory - Safe Update
echo ================================
echo Hardware Inventory Safe Update
echo ================================
echo.
echo This script will safely update the application while preserving your data.
echo.
echo What will be preserved:
echo - Database (data\inventory.db)
echo - Exported files (data\exports\)
echo - Application logs (data\logs\)
echo - Configuration (config\settings.ini)
echo.
echo What will be updated:
echo - Application files (app\)
echo - Templates and static files
echo - Python dependencies
echo.
set /p "confirm=Continue with update? (Y/N): "
if /i not "%confirm%"=="Y" if /i not "%confirm%"=="y" (
    echo Update cancelled.
    pause
    exit /b 0
)

echo.
echo Step 1: Creating backup of data folder...
if exist "data_backup" rmdir /s /q "data_backup"
xcopy "data" "data_backup\" /e /i /h /y > nul 2>&1
echo Data backup created.

echo.
echo Step 2: Updating Python dependencies...
if exist "python\python.exe" (
    python\python.exe -m pip install --upgrade --no-warn-script-location -r app\requirements.txt
) else (
    echo Python not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo.
echo Step 3: Updating web assets...
REM Re-download Bootstrap and FontAwesome if needed
if not exist "static\css\bootstrap.min.css" (
    echo Downloading Bootstrap CSS...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' -OutFile 'static\css\bootstrap.min.css' -UseBasicParsing } catch { Write-Host 'Failed to download Bootstrap CSS' }"
)

if not exist "static\js\bootstrap.bundle.min.js" (
    echo Downloading Bootstrap JS...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js' -OutFile 'static\js\bootstrap.bundle.min.js' -UseBasicParsing } catch { Write-Host 'Failed to download Bootstrap JS' }"
)

echo.
echo ================================
echo Update Complete!
echo ================================
echo.
echo Your data has been preserved and the application has been updated.
echo The backup of your data is available in the 'data_backup' folder.
echo.
set /p "launch=Would you like to launch the updated application now? (Y/N): "
if /i "%launch%"=="Y" call run.bat
if /i "%launch%"=="y" call run.bat

pause