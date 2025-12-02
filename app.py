"""
PharmaPOS NG - Application Entry Point

Run this file to start the desktop application.
"""

import sys
import os

# Add the project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from desktop_app.ui import main

if __name__ == "__main__":
    main()
