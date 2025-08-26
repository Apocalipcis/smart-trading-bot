#!/usr/bin/env python3
"""
Main entry point for examples when running as a module.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import and run the demo
from .backtest_demo import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
