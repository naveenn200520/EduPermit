#!/usr/bin/env python3
"""
Fix yellow warnings in the project
"""

import subprocess
import sys

def update_packages():
    print("🔧 Fixing yellow warnings...")
    
    # Update pip first
    print("1. Updating pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
    
    # Update Flask packages
    print("2. Updating Flask...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "Flask"], capture_output=True)
    
    print("3. Updating Werkzeug...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "Werkzeug"], capture_output=True)
    
    print("4. Updating other packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "Flask-SQLAlchemy"], capture_output=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "qrcode[pil]"], capture_output=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "Pillow"], capture_output=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "python-dotenv"], capture_output=True)
    
    print("✅ All packages updated!")
    print("🚀 Run 'python app.py' to start the server")

if __name__ == "__main__":
    update_packages()
