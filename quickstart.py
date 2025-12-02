#!/usr/bin/env python
"""
PharmaPOS NG - Quick Start Guide

This script helps you get started with PharmaPOS.
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text: str) -> None:
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_step(num: int, text: str) -> None:
    """Print numbered step."""
    print(f"[{num}] {text}")


def check_python() -> bool:
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print("✗ Python 3.8+ required")
        return False


def install_dependencies() -> bool:
    """Install required dependencies."""
    print_step(1, "Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed\n")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies\n")
        return False


def initialize_database() -> bool:
    """Initialize database."""
    print_step(2, "Initializing database...")
    try:
        subprocess.check_call([sys.executable, "install.py", "--init-db"])
        print("✓ Database initialized\n")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to initialize database\n")
        return False


def run_demo() -> bool:
    """Run demo script."""
    print_step(3, "Running demo...")
    try:
        subprocess.check_call([sys.executable, "demo.py"])
        print("\n✓ Demo completed\n")
        return True
    except subprocess.CalledProcessError:
        print("✗ Demo failed\n")
        return False


def run_app() -> bool:
    """Run desktop application."""
    print_step(4, "Launching desktop application...")
    try:
        subprocess.Popen([sys.executable, "app.py"])
        print("✓ Application launched\n")
        return True
    except Exception as e:
        print(f"✗ Failed to launch application: {e}\n")
        return False


def show_menu() -> str:
    """Show main menu."""
    print_header("PharmaPOS NG - Quick Start")
    print("What would you like to do?\n")
    print("1. Setup (install dependencies & initialize database)")
    print("2. Run demo (see all features in action)")
    print("3. Launch desktop application")
    print("4. View documentation")
    print("5. Exit")
    print()
    return input("Choose option (1-5): ").strip()


def view_documentation() -> None:
    """Display documentation."""
    docs = """
    PharmaPOS NG Documentation
    ==========================

    MAIN FEATURES:
    - Authentication with role-based access
    - Point of sale (POS) billing
    - Inventory management with FEFO
    - Stock transfers between stores
    - Comprehensive reporting
    - Complete audit trails

    GETTING STARTED:
    1. Run setup: python quickstart.py
    2. Try demo: python demo.py
    3. Use app: python app.py

    DEFAULT CREDENTIALS (after setup):
    Username: admin
    Password: admin123

    For more information, see:
    - README.md - Overview and features
    - IMPLEMENTATION.md - Technical details
    - demo.py - Code examples

    COMMAND LINE USAGE:
    python install.py               # Install dependencies
    python install.py --init-db     # Initialize database
    python demo.py                  # Run demo
    python app.py                   # Launch desktop app

    DATABASE:
    Default location: pharmapos.db
    Custom location: python install.py --db /path/to/db
    """
    print_header("Documentation")
    print(docs)


def main() -> None:
    """Main menu."""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check Python
    print_header("PharmaPOS NG - Setup Wizard")
    if not check_python():
        sys.exit(1)

    # Main loop
    while True:
        choice = show_menu()

        if choice == "1":
            print_header("Setup")
            if install_dependencies() and initialize_database():
                print("✓ Setup complete! You can now:")
                print("  - Run demo: python demo.py")
                print("  - Launch app: python app.py")
        
        elif choice == "2":
            print_header("Demo")
            run_demo()
            print("To explore interactively, try: python app.py")
        
        elif choice == "3":
            print_header("Desktop Application")
            if run_app():
                print("Application launched in new window")
                print("Closing this window will NOT close the application")
            input("Press Enter to return to menu...")
        
        elif choice == "4":
            view_documentation()
            input("Press Enter to return to menu...")
        
        elif choice == "5":
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
