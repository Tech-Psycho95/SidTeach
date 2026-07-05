#!/usr/bin/env python3
"""
Development setup script for Personal Tutor Agent

This script helps developers get started quickly with the project.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description="Running command"):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def setup_virtual_environment():
    """Create and activate virtual environment"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
        return False
    
    print("✅ Virtual environment created")
    return True

def install_dependencies():
    """Install Python dependencies"""
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_path = "venv/bin/pip"
    
    if not os.path.exists(pip_path):
        pip_path = "pip"  # Fallback to system pip
    
    return run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")

def setup_environment_file():
    """Setup .env file from template"""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    try:
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from template")
        print("📝 Please edit .env with your Cognee API key before running the app")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def run_tests():
    """Run basic tests to verify setup"""
    if os.name == 'nt':
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    if not os.path.exists(python_path):
        python_path = sys.executable
    
    return run_command(f"{python_path} -m pytest tests/test_simple.py -v", "Running basic tests")

def main():
    """Main setup routine"""
    print("🎓 Personal Tutor Agent - Development Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Python version", check_python_version),
        ("Virtual environment", setup_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Environment file", setup_environment_file),
        ("Basic tests", run_tests)
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        if step_name != "Python version":  # Already checked
            if step_func():
                success_count += 1
            else:
                print(f"❌ Setup failed at step: {step_name}")
                break
    
    print("\n" + "=" * 50)
    if success_count == len(steps) - 1:  # -1 because we skip the first check
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env with your Cognee API key")
        print("2. Run: python main.py")
        print("3. Visit: http://localhost:8000")
        print("\nOr use: make run")
    else:
        print("❌ Setup incomplete. Please check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()