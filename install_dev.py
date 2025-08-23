#!/usr/bin/env python3
"""
Install the smart-trading-bot package in development mode.
This resolves import issues by making the src package available system-wide.
"""

import subprocess
import sys
from pathlib import Path

def install_dev_package():
    """Install the package in development mode."""
    try:
        # Change to the project root directory
        project_root = Path(__file__).parent
        print(f"Installing package from: {project_root}")
        
        # Install in development mode
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Package installed successfully in development mode!")
            print("You can now run examples and tests without import issues.")
        else:
            print("❌ Installation failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Installing smart-trading-bot in development mode...")
    success = install_dev_package()
    
    if success:
        print("\n🎉 Installation complete!")
        print("You can now run:")
        print("  python examples/backtest_demo.py")
        print("  python -m examples")
        print("  pytest tests/")
    else:
        print("\n💥 Installation failed. Please check the error messages above.")
        sys.exit(1)
