#!/usr/bin/env python3
"""
Hardware Inventory Tracker - Setup Installer
Professional installer for portable Windows desktop application
"""

import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess
import configparser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import tempfile

class InstallationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hardware Inventory Tracker - Setup")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Variables
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to install...")
        self.install_thread = None
        self.cancel_requested = False
        
        self.setup_ui()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (350 // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Create the user interface"""
        # Header
        header_frame = ttk.Frame(self.root, padding="20")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame, 
            text="Hardware Inventory Tracker", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Portable Barcode Inventory Management System",
            font=("Arial", 10)
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Description
        desc_frame = ttk.Frame(self.root, padding="20")
        desc_frame.pack(fill=tk.X)
        
        description = """This installer will set up:
• Portable Python runtime (no admin rights needed)
• All required dependencies and libraries
• Local SQLite database for offline use
• Desktop shortcut for easy access
• Barcode generation and printing capabilities"""
        
        desc_label = ttk.Label(desc_frame, text=description, justify=tk.LEFT)
        desc_label.pack(anchor=tk.W)
        
        # Progress section
        progress_frame = ttk.Frame(self.root, padding="20")
        progress_frame.pack(fill=tk.X)
        
        ttk.Label(progress_frame, text="Installation Progress:").pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            maximum=100,
            length=450
        )
        self.progress_bar.pack(pady=(5, 10), fill=tk.X)
        
        self.status_label = ttk.Label(
            progress_frame, 
            textvariable=self.status_var,
            font=("Arial", 9)
        )
        self.status_label.pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(self.root, padding="20")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.install_button = ttk.Button(
            button_frame,
            text="Install",
            command=self.start_installation,
            style="Accent.TButton"
        )
        self.install_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_installation
        )
        self.cancel_button.pack(side=tk.RIGHT)
        
    def update_progress(self, value, status):
        """Thread-safe progress update"""
        self.root.after(0, self._update_progress_ui, value, status)
        
    def _update_progress_ui(self, value, status):
        """Update UI elements"""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.root.update_idletasks()
        
    def start_installation(self):
        """Start installation in separate thread"""
        self.install_button.config(state='disabled')
        self.cancel_button.config(text='Cancel', state='normal')
        
        self.install_thread = threading.Thread(target=self.run_installation)
        self.install_thread.daemon = True
        self.install_thread.start()
        
    def cancel_installation(self):
        """Cancel the installation"""
        if self.install_thread and self.install_thread.is_alive():
            self.cancel_requested = True
            self.update_progress(0, "Cancelling installation...")
        else:
            self.root.quit()
            
    def run_installation(self):
        """Main installation process"""
        try:
            app_dir = Path(__file__).parent.absolute()
            
            # Step 1: Download Python
            if not self.cancel_requested:
                self.update_progress(10, "Downloading portable Python...")
                if not self.download_python(app_dir):
                    return
            
            # Step 2: Extract Python
            if not self.cancel_requested:
                self.update_progress(30, "Extracting Python...")
                if not self.extract_python(app_dir):
                    return
            
            # Step 3: Install Python packages
            if not self.cancel_requested:
                self.update_progress(50, "Installing Python packages...")
                if not self.install_packages(app_dir):
                    return
            
            # Step 4: Download web assets
            if not self.cancel_requested:
                self.update_progress(70, "Downloading web assets...")
                if not self.download_web_assets(app_dir):
                    return
            
            # Step 5: Setup directories and database
            if not self.cancel_requested:
                self.update_progress(85, "Setting up database and directories...")
                if not self.setup_app_structure(app_dir):
                    return
            
            # Step 6: Create desktop shortcut
            if not self.cancel_requested:
                self.update_progress(95, "Creating desktop shortcut...")
                if not self.create_desktop_shortcut(app_dir):
                    return
            
            # Complete
            if not self.cancel_requested:
                self.update_progress(100, "Installation complete!")
                self.installation_complete()
                
        except Exception as e:
            self.update_progress(0, f"Installation failed: {str(e)}")
            messagebox.showerror("Installation Error", f"Installation failed:\n{str(e)}")
            self.install_button.config(state='normal')
            self.cancel_button.config(text='Close')
    
    def download_python(self, app_dir):
        """Download portable Python"""
        try:
            python_url = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip"
            python_zip = app_dir / "python.zip"
            
            # Download with progress
            urllib.request.urlretrieve(python_url, python_zip, self.download_progress_hook)
            
            if self.cancel_requested:
                python_zip.unlink(missing_ok=True)
                return False
                
            return True
            
        except Exception as e:
            self.update_progress(0, f"Failed to download Python: {e}")
            return False
    
    def download_progress_hook(self, block_num, block_size, total_size):
        """Progress hook for urllib downloads"""
        if self.cancel_requested:
            raise Exception("Download cancelled")
            
        if total_size > 0:
            percent = min((block_num * block_size / total_size) * 20 + 10, 30)
            self.update_progress(percent, "Downloading portable Python...")
    
    def extract_python(self, app_dir):
        """Extract Python zip file"""
        try:
            python_zip = app_dir / "python.zip"
            python_dir = app_dir / "python"
            
            with zipfile.ZipFile(python_zip, 'r') as zip_ref:
                zip_ref.extractall(python_dir)
            
            python_zip.unlink()  # Clean up zip file
            return True
            
        except Exception as e:
            self.update_progress(0, f"Failed to extract Python: {e}")
            return False
    
    def install_packages(self, app_dir):
        """Install required Python packages"""
        try:
            python_exe = app_dir / "python" / "python.exe"
            app_subdir = app_dir / "app"
            requirements_file = app_subdir / "requirements.txt"
            
            if not requirements_file.exists():
                # Create requirements file if missing
                requirements = [
                    "Flask==2.3.2",
                    "Flask-SQLAlchemy==3.0.5",
                    "gunicorn==21.2.0",
                    "pandas==2.0.3",
                    "openpyxl==3.1.2",
                    "python-barcode==0.15.1",
                    "qrcode==7.4.2",
                    "Pillow==10.0.0",
                    "python-docx==0.8.11"
                ]
                
                app_subdir.mkdir(exist_ok=True)
                with open(requirements_file, 'w') as f:
                    f.write('\n'.join(requirements))
            
            # Install packages
            cmd = [str(python_exe), "-m", "pip", "install", "--no-warn-script-location", "-r", str(requirements_file)]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if process.returncode != 0:
                raise Exception(f"Package installation failed: {process.stderr}")
                
            return True
            
        except Exception as e:
            self.update_progress(0, f"Failed to install packages: {e}")
            return False
    
    def download_web_assets(self, app_dir):
        """Download Bootstrap and FontAwesome assets"""
        try:
            static_dir = app_dir / "static"
            css_dir = static_dir / "css"
            js_dir = static_dir / "js"
            fonts_dir = static_dir / "fonts"
            
            # Create directories
            css_dir.mkdir(parents=True, exist_ok=True)
            js_dir.mkdir(parents=True, exist_ok=True)
            fonts_dir.mkdir(parents=True, exist_ok=True)
            
            # Download Bootstrap CSS
            bootstrap_css_url = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
            urllib.request.urlretrieve(bootstrap_css_url, css_dir / "bootstrap.min.css")
            
            # Download Bootstrap JS
            bootstrap_js_url = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
            urllib.request.urlretrieve(bootstrap_js_url, js_dir / "bootstrap.bundle.min.js")
            
            # Download FontAwesome CSS (simplified version)
            fa_css_content = """
            /* FontAwesome Icons - Essential subset for Hardware Inventory */
            .fa, .fas { font-family: "Font Awesome 6 Free"; font-weight: 900; }
            .fa-barcode:before { content: "\\f02a"; }
            .fa-boxes:before { content: "\\f468"; }
            .fa-plus:before { content: "\\f067"; }
            .fa-edit:before { content: "\\f044"; }
            .fa-trash:before { content: "\\f1f8"; }
            .fa-print:before { content: "\\f02f"; }
            .fa-download:before { content: "\\f019"; }
            .fa-search:before { content: "\\f002"; }
            .fa-user:before { content: "\\f007"; }
            .fa-cog:before { content: "\\f013"; }
            """
            
            with open(css_dir / "fontawesome.min.css", 'w') as f:
                f.write(fa_css_content)
            
            return True
            
        except Exception as e:
            self.update_progress(0, f"Failed to download web assets: {e}")
            return False
    
    def setup_app_structure(self, app_dir):
        """Set up application structure and database"""
        try:
            # Run launcher setup
            python_exe = app_dir / "python" / "python.exe"
            launcher_script = app_dir / "launcher.py"
            
            cmd = [str(python_exe), str(launcher_script), "--setup-only"]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(app_dir),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if process.returncode != 0:
                raise Exception(f"App setup failed: {process.stderr}")
                
            return True
            
        except Exception as e:
            self.update_progress(0, f"Failed to setup app structure: {e}")
            return False
    
    def create_desktop_shortcut(self, app_dir):
        """Create desktop shortcut"""
        try:
            # Create shortcut using PowerShell
            exe_path = app_dir / "HardwareInventory.exe"
            icon_path = app_dir / "app_icon.ico"
            
            # PowerShell command to create shortcut
            ps_command = f'''
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\\Desktop\\Hardware Inventory.lnk")
            $Shortcut.TargetPath = "{exe_path}"
            $Shortcut.WorkingDirectory = "{app_dir}"
            $Shortcut.IconLocation = "{icon_path}"
            $Shortcut.Save()
            '''
            
            process = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            return True
            
        except Exception as e:
            # Non-fatal error
            self.update_progress(95, "Desktop shortcut creation failed (non-fatal)")
            return True
    
    def installation_complete(self):
        """Handle successful installation"""
        self.install_button.config(state='normal', text='Launch App')
        self.cancel_button.config(text='Close')
        
        result = messagebox.askquestion(
            "Installation Complete",
            "Hardware Inventory Tracker has been installed successfully!\n\n"
            "A desktop shortcut has been created for easy access.\n\n"
            "Would you like to launch the application now?",
            icon='question'
        )
        
        if result == 'yes':
            self.launch_application()
        else:
            self.root.quit()
    
    def launch_application(self):
        """Launch the main application"""
        try:
            app_dir = Path(__file__).parent.absolute()
            launcher_exe = app_dir / "HardwareInventory.exe"
            
            if launcher_exe.exists():
                subprocess.Popen([str(launcher_exe)], cwd=str(app_dir))
            else:
                # Fallback to Python launcher
                python_exe = app_dir / "python" / "python.exe"
                launcher_script = app_dir / "launcher.py"
                subprocess.Popen([str(python_exe), str(launcher_script)], cwd=str(app_dir))
            
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch application:\n{str(e)}")
    
    def run(self):
        """Run the installer GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        # Console mode for debugging
        print("Hardware Inventory Tracker - Console Setup Mode")
        # Add console installation logic here if needed
    else:
        # GUI mode
        installer = InstallationGUI()
        installer.run()

if __name__ == '__main__':
    main()