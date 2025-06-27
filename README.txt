====================================
HARDWARE INVENTORY TRACKER
Portable Windows Desktop Application
====================================

QUICK START:
1. Double-click "setup.bat" (one-time setup)
2. Double-click "Hardware Inventory" desktop icon (daily use)

====================================
SYSTEM REQUIREMENTS
====================================

✓ Windows 10 or Windows 11
✓ No admin rights required
✓ No Python installation needed
✓ Internet connection for initial setup only
✓ 200MB free disk space

====================================
INSTALLATION INSTRUCTIONS
====================================

FIRST TIME SETUP:
1. Extract the ZIP file to any folder (e.g., Desktop, Documents)
2. Double-click "setup.bat"
3. Wait 3-5 minutes for automatic installation
4. Desktop shortcut will be created automatically
5. Choose to launch immediately or close setup

DAILY USE:
- Double-click "Hardware Inventory" icon on desktop
- OR double-click "run.bat" in the application folder
- Application opens automatically in your web browser
- Close the browser when finished (server stops automatically)

====================================
TROUBLESHOOTING GUIDE
====================================

PROBLEM: "Python not found" error
SOLUTION: Run setup.bat first to install dependencies

PROBLEM: Setup fails during download
SOLUTION: 
- Check internet connection
- Try running setup.bat as different user
- Temporarily disable antivirus during setup
- Use "setup_offline.bat" if available

PROBLEM: Port 5000 already in use
SOLUTION: 
- Close other applications using port 5000
- Restart computer and try again
- The app will automatically try ports 5001-5010

PROBLEM: Browser doesn't open automatically
SOLUTION: 
- Manually open browser and go to: http://localhost:5000
- Check Windows Firewall settings
- Try different browser (Chrome, Edge, Firefox)

PROBLEM: Cannot create desktop shortcut
SOLUTION:
- Run "create_shortcut.bat" manually
- Check desktop permissions
- Create shortcut manually pointing to "run.bat"

PROBLEM: Application runs slowly
SOLUTION:
- Close other memory-intensive programs
- Restart the application
- Check available disk space (need 50MB minimum)

PROBLEM: Database errors or corruption
SOLUTION:
- Close application completely
- Copy "data" folder as backup
- Delete "data\inventory.db" file
- Restart application (new empty database created)
- Re-import data if available

PROBLEM: Missing barcode images
SOLUTION:
- Check "static\barcodes" folder permissions
- Restart application with admin rights (one time)
- Clear browser cache and refresh

PROBLEM: Excel/Word export fails
SOLUTION:
- Check "data\exports" folder permissions
- Ensure sufficient disk space
- Try different export format
- Restart application

====================================
CORPORATE/WORK LAPTOP RESTRICTIONS
====================================

If your work laptop has restrictions:

PROBLEM: PowerShell execution blocked
SOLUTION: Ask IT to run setup.bat or use offline installer

PROBLEM: Internet downloads blocked
SOLUTION: Download on personal computer, transfer via USB

PROBLEM: Cannot run .bat files
SOLUTION: 
- Run Python directly: python\python.exe launcher.py
- Contact IT for exception approval

PROBLEM: Cannot install to C: drive
SOLUTION: Extract to Documents, Desktop, or external USB drive

PROBLEM: Antivirus blocks application
SOLUTION: 
- Add application folder to antivirus exclusions
- Run setup.bat when antivirus is temporarily disabled
- Contact IT for application approval

====================================
FILE STRUCTURE
====================================

HardwareInventory/
├── python/                    # Portable Python runtime
├── app/                       # Application code
├── static/                    # Web assets (CSS, JS, images)
├── templates/                 # HTML templates
├── data/                      # YOUR DATA (preserved during updates)
│   ├── inventory.db           # Database file
│   ├── exports/               # Excel/Word exports
│   └── logs/                  # Application logs
├── config/                    # Settings (preserved during updates)
│   └── settings.ini           # Admin credentials and config
├── setup.bat                  # One-time installer
├── run.bat                    # Main application launcher
├── update.bat                 # Safe update script
└── README.txt                 # This file

====================================
DATA BACKUP & RECOVERY
====================================

BACKING UP YOUR DATA:
- Copy the entire "data" folder to external drive/cloud
- Backup includes: database, exports, logs, settings
- Backup before major updates

RESTORING DATA:
- Replace "data" folder with your backup
- Restart application
- All inventory data will be restored

MOVING TO NEW COMPUTER:
- Copy entire HardwareInventory folder
- Run setup.bat on new computer
- All data and settings preserved

====================================
UPDATING THE APPLICATION
====================================

SAFE UPDATE (RECOMMENDED):
1. Download new version
2. Extract to temporary folder
3. Run "update.bat" in original folder
4. Your data is automatically preserved

MANUAL UPDATE:
1. Backup "data" and "config" folders
2. Delete old application files (not data/config)
3. Extract new version
4. Copy back "data" and "config" folders
5. Run setup.bat if needed

====================================
ADMIN CREDENTIALS
====================================

DEFAULT LOGIN:
Username: admin
Password: admin123

CHANGING PASSWORD:
1. Open "config\settings.ini" in text editor
2. Change password under [admin] section
3. Save file and restart application

====================================
PERFORMANCE OPTIMIZATION
====================================

FOR BEST PERFORMANCE:
- Close unnecessary programs while running
- Keep at least 100MB free disk space
- Restart application weekly
- Keep database under 10,000 records
- Regular data cleanup/export

====================================
OFFLINE OPERATION
====================================

✓ No internet required after initial setup
✓ All features work offline
✓ Database stored locally
✓ Barcode generation works offline
✓ Excel/Word export works offline
✓ Print functionality preserved

====================================
SECURITY NOTES
====================================

- Database is stored locally on your computer
- No data sent to external servers
- Admin password stored in local config file
- Application runs on localhost only
- All data stays on your machine

====================================
SUPPORT & ISSUES
====================================

For technical issues:
1. Check this README troubleshooting section
2. Restart application and try again
3. Check application logs in "data\logs" folder
4. Try safe update with "update.bat"
5. Create backup and reinstall if necessary

Common log file locations:
- data\logs\barcode_generation.log
- data\logs\application.log

====================================
VERSION INFORMATION
====================================

Application: Hardware Inventory Tracker
Version: 2.0 (Portable Desktop Edition)
Python: 3.11 (Embedded)
Database: SQLite
Web Framework: Flask

Last Updated: June 2025
Compatible: Windows 10/11 (64-bit)

====================================