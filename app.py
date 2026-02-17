"""
PharmaPOS NG - Application Entry Point

Run this file to start the modern ERP application.
"""

import sys
import os

# Add the project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainAppWindow

def main():
    app = QApplication(sys.argv)
    
    # Initialize the new ERP interface
    window = MainAppWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
