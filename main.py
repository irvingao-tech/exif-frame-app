"""
EXIF Frame Card — 摄影卡片边框
Main entry point. Run this file to start the application.

Usage:
    python main.py
    or
    python -m src.app
"""

import sys
import os

# Ensure the project root is on the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.app import main

if __name__ == '__main__':
    main()
