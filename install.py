"""
Simple dependency installer for PharmaPOS NG Phase 1.

Usage:
  python install.py               # installs from requirements.txt
  python install.py --init-db     # installs and initializes the local SQLite DB
  python install.py --db path.db  # custom DB path for initialization
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def install_requirements(requirements_path: str = "requirements.txt") -> None:
    if not os.path.exists(requirements_path):
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
    print("Dependencies installed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PharmaPOS NG installer")
    parser.add_argument("--init-db", action="store_true", help="Initialize the local SQLite database after install")
    parser.add_argument("--db", dest="db_path", default=None, help="Custom path to the SQLite database file")
    parser.add_argument("--requirements", dest="requirements_path", default="requirements.txt", help="Path to requirements file")
    args = parser.parse_args()

    install_requirements(args.requirements_path)

    if args.init_db:
        from desktop_app.database import init_db

        init_db(args.db_path)


if __name__ == "__main__":
    main()