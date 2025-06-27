@echo off
title Hardware Inventory Setup
echo ================================
echo Hardware Inventory Tracker Setup
echo ================================
echo.

REM Check if already set up
if exist "python\python.exe" (
    echo Python already installed! Creating desktop shortcut...
    goto :create_shortcut
)

echo Step 1: Downloading Python (this may take a few minutes)...
echo Please wait while we download portable Python...

REM Download portable Python 3.11
powershell -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip' -OutFile 'python.zip' -UseBasicParsing } catch { Write-Host 'Download failed. Please check your internet connection.'; exit 1 }"

if not exist "python.zip" (
    echo Failed to download Python. Please check your internet connection.
    pause
    exit /b 1
)

echo Step 2: Extracting Python...
powershell -Command "try { Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force } catch { Write-Host 'Extraction failed.'; exit 1 }"
del python.zip

REM Configure Python to use pip
echo import sys > python\sitecustomize.py
echo sys.path.append('.') >> python\sitecustomize.py

REM Get pip
echo Step 3: Installing pip...
powershell -Command "try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing } catch { Write-Host 'Failed to download pip installer.'; exit 1 }"
python\python.exe get-pip.py --no-warn-script-location
del get-pip.py

echo Step 4: Installing application dependencies...
python\python.exe -m pip install --no-warn-script-location -r app\requirements.txt

echo Step 5: Downloading web assets...
REM Create static directories
if not exist "static" mkdir static
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
if not exist "static\fonts" mkdir static\fonts

REM Download Bootstrap CSS
powershell -Command "try { Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' -OutFile 'static\css\bootstrap.min.css' -UseBasicParsing } catch { Write-Host 'Failed to download Bootstrap CSS' }"

REM Download Bootstrap JS
powershell -Command "try { Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js' -OutFile 'static\js\bootstrap.bundle.min.js' -UseBasicParsing } catch { Write-Host 'Failed to download Bootstrap JS' }"

REM Create basic FontAwesome CSS
echo /* FontAwesome Icons - Essential subset for Hardware Inventory */ > static\css\fontawesome.min.css
echo .fa, .fas { font-family: "Font Awesome 6 Free"; font-weight: 900; } >> static\css\fontawesome.min.css
echo .fa-barcode:before { content: "\f02a"; } >> static\css\fontawesome.min.css
echo .fa-boxes:before { content: "\f468"; } >> static\css\fontawesome.min.css
echo .fa-plus:before { content: "\f067"; } >> static\css\fontawesome.min.css
echo .fa-edit:before { content: "\f044"; } >> static\css\fontawesome.min.css
echo .fa-trash:before { content: "\f1f8"; } >> static\css\fontawesome.min.css
echo .fa-print:before { content: "\f02f"; } >> static\css\fontawesome.min.css
echo .fa-download:before { content: "\f019"; } >> static\css\fontawesome.min.css
echo .fa-search:before { content: "\f002"; } >> static\css\fontawesome.min.css
echo .fa-user:before { content: "\f007"; } >> static\css\fontawesome.min.css
echo .fa-cog:before { content: "\f013"; } >> static\css\fontawesome.min.css

echo Step 6: Setting up database and directories...
python\python.exe launcher.py --setup-only

:create_shortcut
echo Step 7: Creating desktop shortcut...
powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Hardware Inventory.lnk'); $Shortcut.TargetPath = '%CD%\run.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Save() } catch { Write-Host 'Failed to create desktop shortcut (non-critical)' }"

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo A desktop shortcut has been created.
echo You can now:
echo 1. Double-click "Hardware Inventory" on your desktop
echo 2. Or double-click "run.bat" in this folder
echo.
echo The application will open in your web browser.
echo.
set /p "launch=Would you like to launch the application now? (Y/N): "
if /i "%launch%"=="Y" call run.bat
if /i "%launch%"=="y" call run.bat

pause