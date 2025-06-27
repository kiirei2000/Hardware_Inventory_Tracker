@echo off
echo Creating desktop shortcut for Hardware Inventory...

powershell -Command "try { $WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Hardware Inventory.lnk'); $Shortcut.TargetPath = '%CD%\run.bat'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Save(); Write-Host 'Desktop shortcut created successfully!' } catch { Write-Host 'Failed to create desktop shortcut. Error: ' $_.Exception.Message }"

pause