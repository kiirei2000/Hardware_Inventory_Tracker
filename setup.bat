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

REM Download portable Python 3.11 (latest stable)
powershell -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'python.zip' -UseBasicParsing } catch { Write-Host 'Download failed. Please check your internet connection.'; exit 1 }"

if not exist "python.zip" (
    echo Failed to download Python. Please check your internet connection.
    pause
    exit /b 1
)

echo Step 2: Extracting Python...
powershell -Command "try { Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force } catch { Write-Host 'Extraction failed.'; exit 1 }"
del python.zip

REM Configure Python embedded for pip and site-packages
echo python311.zip > python\python311._pth
echo . >> python\python311._pth
echo .\Lib\site-packages >> python\python311._pth
echo import site >> python\python311._pth
echo import sys; sys.path.append('.') > python\sitecustomize.py

REM Get pip
echo Step 3: Installing pip...
powershell -Command "try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing } catch { Write-Host 'Failed to download pip installer.'; exit 1 }"
python\python.exe get-pip.py --no-warn-script-location
del get-pip.py

echo Step 4: Installing application dependencies...
REM Install packages to embedded Python
python\python.exe -m pip install --no-warn-script-location --target python\Lib\site-packages -r app\requirements.txt
if errorlevel 1 (
    echo Failed to install Python packages. Please check your internet connection.
    pause
    exit /b 1
)

echo Step 5: Downloading web assets...
REM Create static directories in app folder
if not exist "app\static" mkdir app\static
if not exist "app\static\css" mkdir app\static\css
if not exist "app\static\js" mkdir app\static\js
if not exist "app\static\fonts" mkdir app\static\fonts
if not exist "app\static\barcodes" mkdir app\static\barcodes

REM Download Bootstrap CSS
powershell -Command "try { Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' -OutFile 'app\static\css\bootstrap.min.css' -UseBasicParsing } catch { Write-Host 'Failed to download Bootstrap CSS' }"

REM Download Bootstrap JS
powershell -Command "try { Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js' -OutFile 'app\static\js\bootstrap.bundle.min.js' -UseBasicParsing } catch { Write-Host 'Failed to download Bootstrap JS' }"

REM Create basic FontAwesome CSS
echo /* FontAwesome Icons - Essential subset for Hardware Inventory */ > app\static\css\fontawesome.min.css
echo .fa, .fas { font-family: "Font Awesome 6 Free"; font-weight: 900; } >> app\static\css\fontawesome.min.css
echo .fa-barcode:before { content: "\f02a"; } >> app\static\css\fontawesome.min.css
echo .fa-boxes:before { content: "\f468"; } >> app\static\css\fontawesome.min.css
echo .fa-plus:before { content: "\f067"; } >> app\static\css\fontawesome.min.css
echo .fa-edit:before { content: "\f044"; } >> app\static\css\fontawesome.min.css
echo .fa-trash:before { content: "\f1f8"; } >> app\static\css\fontawesome.min.css
echo .fa-print:before { content: "\f02f"; } >> app\static\css\fontawesome.min.css
echo .fa-download:before { content: "\f019"; } >> app\static\css\fontawesome.min.css
echo .fa-search:before { content: "\f002"; } >> app\static\css\fontawesome.min.css
echo .fa-user:before { content: "\f007"; } >> app\static\css\fontawesome.min.css
echo .fa-cog:before { content: "\f013"; } >> app\static\css\fontawesome.min.css
echo .fa-home:before { content: "\f015"; } >> app\static\css\fontawesome.min.css
echo .fa-list:before { content: "\f03a"; } >> app\static\css\fontawesome.min.css
echo .fa-qrcode:before { content: "\f029"; } >> app\static\css\fontawesome.min.css
echo .fa-file-excel:before { content: "\f1c3"; } >> app\static\css\fontawesome.min.css
echo .fa-file-word:before { content: "\f1c2"; } >> app\static\css\fontawesome.min.css

echo Step 6: Setting up database and directories...
REM Create required directories
if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\exports" mkdir data\exports
if not exist "config" mkdir config
REM Templates are included in app folder

REM Initialize database (will create on first run)
echo Database will be created on first application start.

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