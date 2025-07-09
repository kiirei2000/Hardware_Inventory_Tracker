================================
Hardware Inventory Tracker
PORTABLE WINDOWS INSTALLATION GUIDE
================================

QUICK START:
1. Extract all files to a folder (e.g., C:\HardwareInventory)
2. Double-click "setup.bat" and wait for installation to complete
3. Use the desktop shortcut "Hardware Inventory" to run the app

================================

DETAILED INSTALLATION:

Step 1: Extract Files
- Extract the ZIP file to a permanent location
- Recommended: C:\HardwareInventory or C:\Program Files\HardwareInventory
- Avoid temporary folders or Desktop

Step 2: Run Setup
- Right-click "setup.bat" and "Run as administrator" (if possible)
- If admin rights unavailable, double-click normally
- Wait for completion (may take 5-10 minutes)
- Internet connection required for initial setup

Step 3: Launch Application
- Double-click the desktop shortcut "Hardware Inventory"
- OR double-click "run.bat" in the installation folder
- The application will open in your web browser
- Keep the command window open while using the app

================================

FEATURES:
- Barcode/QR code generation and scanning
- Inventory tracking with pull/return events
- Excel and Word document export
- Admin management interface
- Offline operation after initial setup
- No installation of Python or other software required

DEFAULT LOGIN:
Username: admin
Password: admin123

================================

TROUBLESHOOTING:

Problem: "Python not found" error
Solution: Re-run setup.bat, ensure internet connection

Problem: "Server failed to start"
Solution: Check if port 5000-5010 are available, close other applications

Problem: Web page won't load
Solution: Wait 30 seconds after startup, manually visit http://localhost:5000

Problem: Antivirus blocking
Solution: Add installation folder to antivirus exclusions

Problem: Setup fails downloading
Solution: Check firewall/proxy settings, run as administrator

================================

FILES INCLUDED:
- setup.bat: One-time installation script
- run.bat: Daily launcher
- launcher.py: Application launcher
- app/: Application code and templates
- README.txt: This file

CREATED DURING SETUP:
- python/: Portable Python runtime
- data/: Database and user files
- config/: Application settings
- app/static/: Web assets (Bootstrap, FontAwesome)

================================

CORPORATE ENVIRONMENT NOTES:
- No admin rights required after initial setup
- All files contained in installation folder
- No registry modifications
- No system PATH changes
- Can run from USB drive or network share
- Works with corporate proxies (during setup only)

================================

SUPPORT:
For issues, check the log files in data/logs/
The application creates detailed logs for troubleshooting.

Version: 2025.7 - Portable Windows Desktop Edition