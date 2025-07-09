import sys
import os
from pathlib import Path

# Add app directory to path for proper imports  
sys.path.insert(0, str(Path(__file__).parent / 'app'))

# Import the Flask app from app directory
from app import app

# Export for WSGI servers (gunicorn, waitress)
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
