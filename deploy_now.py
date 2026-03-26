#!/usr/bin/env python3
"""
One-Click Deployment Script for TJS Engineering College Management System
"""

import os
import subprocess
import sys
import webbrowser

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False

def check_requirements():
    """Check if deployment tools are available"""
    print("🔍 Checking deployment tools...")
    
    tools = {
        'git': 'git --version',
        'python': 'python --version',
        'pip': 'pip --version'
    }
    
    available_tools = []
    for tool, cmd in tools.items():
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            available_tools.append(tool)
            print(f"✅ {tool} available")
        except:
            print(f"❌ {tool} not found")
    
    return len(available_tools) >= 2

def setup_deployment():
    """Setup deployment configuration"""
    print("\n⚙️ Setting up deployment configuration...")
    
    # Create .env file
    env_content = """SECRET_KEY=tjs-engineering-college-secret-key-2024
FLASK_ENV=production
DEBUG=False
DATABASE_URL=sqlite:///college.db
PORT=5000"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Environment configuration created")
    return True

def deploy_local():
    """Deploy locally with production settings"""
    print("\n🚀 Deploying locally with production settings...")
    
    commands = [
        ("pip install -r requirements.txt", "Installing dependencies"),
        ("python database.py", "Initializing database"),
        ("gunicorn --bind 0.0.0.0:5000 --workers 4 app:app", "Starting production server")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    
    return True

def main():
    """Main deployment function"""
    print("🚀 TJS Engineering College Management System - Auto Deployment")
    print("=" * 70)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install Git and Python first")
        return
    
    # Setup configuration
    if not setup_deployment():
        print("\n❌ Failed to setup configuration")
        return
    
    print("\n📋 Deployment Options:")
    print("1. Local Production Deployment")
    print("2. GitHub Repository Setup")
    print("3. Docker Deployment (if Docker available)")
    
    choice = input("\nChoose deployment option (1-3): ").strip()
    
    if choice == "1":
        print("\n🏠 Starting Local Production Deployment...")
        if deploy_local():
            print("\n🎉 Deployment successful!")
            print("📱 Access your app at: http://localhost:5000")
            print("🔐 Login with demo credentials:")
            print("   Student: 22CS001 / student123")
            print("   Staff: staff@college.edu / staff123")
            print("   HOD: hod@college.edu / hod123")
            print("   Admin: admin@college.edu / admin123")
            
            # Try to open browser
            try:
                webbrowser.open('http://localhost:5000')
            except:
                pass
        else:
            print("\n❌ Local deployment failed")
    
    elif choice == "2":
        print("\n📂 GitHub Repository Setup...")
        print("✅ Repository ready at: https://github.com/naveenn200520/tjs-engineering-college-management-system")
        print("\n📋 Next Steps for Cloud Deployment:")
        print("1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli")
        print("2. Run: heroku create")
        print("3. Run: heroku addons:create heroku-postgresql:hobby-dev")
        print("4. Run: git push heroku master")
        print("5. Run: heroku run python database.py")
        print("6. Run: heroku open")
    
    elif choice == "3":
        print("\n🐳 Docker Deployment...")
        if run_command("docker --version", "Checking Docker"):
            print("✅ Docker available")
            print("\n📋 Docker Commands:")
            print("1. Build: docker build -t tjs-college-app .")
            print("2. Run: docker run -p 5000:5000 tjs-college-app")
            print("3. With Database: docker-compose up -d")
        else:
            print("❌ Docker not available. Please install Docker first.")
    
    else:
        print("\n❌ Invalid choice")

if __name__ == "__main__":
    main()
