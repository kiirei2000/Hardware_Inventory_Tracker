#!/usr/bin/env python3
"""
Hardware Inventory Tracker - Desktop Launcher
Portable Windows desktop application launcher
"""

import os
import sys
import webbrowser
import socket
import time
import subprocess
import configparser
import threading
from pathlib import Path
import signal
import atexit

class HardwareInventoryLauncher:
    def __init__(self):
        self.app_dir = Path(__file__).parent.absolute()
        self.python_exe = self.app_dir / "python" / "python.exe"
        self.data_dir = self.app_dir / "data"
        self.config_dir = self.app_dir / "config"
        self.static_dir = self.app_dir / "static"
        self.flask_process = None
        self.port = None
        
    def setup_directories(self):
        """Create required directories if missing"""
        dirs_to_create = [
            self.data_dir,
            self.data_dir / "exports",
            self.data_dir / "logs",
            self.static_dir / "barcodes",
            self.config_dir
        ]
        
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
            
        print(f"✓ Created data directories")
        
    def create_default_config(self):
        """Create default configuration file if missing"""
        config_file = self.config_dir / "settings.ini"
        if not config_file.exists():
            config = configparser.ConfigParser()
            config['admin'] = {
                'username': 'admin',
                'password': 'admin123'
            }
            config['database'] = {
                'path': 'data/inventory.db'
            }
            config['app'] = {
                'port': '5000',
                'debug': 'false',
                'auto_open_browser': 'true'
            }
            
            with open(config_file, 'w') as f:
                config.write(f)
            print(f"✓ Created default configuration")
    
    def find_free_port(self, start=5000, end=5010):
        """Find available port in range"""
        for port in range(start, end + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return None
    
    def setup_environment(self):
        """Set up environment variables"""
        os.environ['FLASK_APP'] = str(self.app_dir / "app" / "app.py")
        os.environ['FLASK_ENV'] = 'production'
        os.environ['DATABASE_URL'] = f"sqlite:///{self.data_dir / 'inventory.db'}"
        os.environ['SESSION_SECRET'] = 'hardware-inventory-secret-key-2025'
        
        # Add python to PATH for this session
        python_dir = str(self.python_exe.parent)
        current_path = os.environ.get('PATH', '')
        os.environ['PATH'] = f"{python_dir};{current_path}"
        
    def start_flask_server(self, port):
        """Start Flask server on specified port"""
        try:
            # Change to app directory
            app_dir = self.app_dir / "app"
            
            # Start gunicorn server
            cmd = [
                str(self.python_exe),
                "-m", "gunicorn",
                "--bind", f"0.0.0.0:{port}",
                "--reuse-port",
                "--reload",
                "app:app"
            ]
            
            print(f"Starting server on port {port}...")
            self.flask_process = subprocess.Popen(
                cmd,
                cwd=str(app_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if process is still running
            if self.flask_process.poll() is None:
                print(f"✓ Server started successfully on port {port}")
                return True
            else:
                print(f"✗ Server failed to start")
                return False
                
        except Exception as e:
            print(f"✗ Error starting server: {e}")
            return False
    
    def open_browser(self, port):
        """Open default browser to app"""
        try:
            url = f"http://localhost:{port}"
            print(f"Opening browser to {url}")
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"✗ Error opening browser: {e}")
            print(f"Please manually open: http://localhost:{port}")
            return False
    
    def cleanup(self):
        """Clean shutdown of Flask server"""
        if self.flask_process and self.flask_process.poll() is None:
            print("Shutting down server...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
            print("✓ Server stopped")
    
    def check_python_installation(self):
        """Check if portable Python is available"""
        if not self.python_exe.exists():
            print("✗ Portable Python not found!")
            print("Please run setup.exe first to install dependencies.")
            input("Press Enter to exit...")
            return False
        print("✓ Portable Python found")
        return True
    
    def wait_for_exit(self):
        """Wait for user to close the application"""
        try:
            print("\n" + "="*50)
            print("Hardware Inventory is now running!")
            print("Close this window or press Ctrl+C to stop the server.")
            print("="*50)
            
            while True:
                if self.flask_process and self.flask_process.poll() is not None:
                    print("Server process ended")
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nReceived shutdown signal...")
        except Exception as e:
            print(f"Error in wait loop: {e}")
    
    def run(self, setup_only=False):
        """Main application runner"""
        print("Hardware Inventory Tracker - Starting...")
        print("="*50)
        
        # Check Python installation
        if not self.check_python_installation():
            return False
        
        # Setup directories and config
        self.setup_directories()
        self.create_default_config()
        self.setup_environment()
        
        if setup_only:
            print("✓ Setup complete")
            return True
        
        # Find available port
        self.port = self.find_free_port()
        if not self.port:
            print("✗ No available ports (5000-5010)")
            print("Please close other applications and try again.")
            input("Press Enter to exit...")
            return False
        
        print(f"✓ Using port {self.port}")
        
        # Start Flask server
        if not self.start_flask_server(self.port):
            input("Press Enter to exit...")
            return False
        
        # Open browser
        self.open_browser(self.port)
        
        # Wait for exit
        self.wait_for_exit()
        
        # Cleanup
        self.cleanup()
        return True

def main():
    # Register cleanup function
    launcher = HardwareInventoryLauncher()
    atexit.register(launcher.cleanup)
    
    # Handle command line arguments
    setup_only = '--setup-only' in sys.argv
    
    try:
        success = launcher.run(setup_only)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == '__main__':
    main()