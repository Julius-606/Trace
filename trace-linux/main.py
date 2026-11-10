#!/usr/bin/env python3
"""
TRACE Desktop (Linux Client) - Application Entry Point
FILE: trace-linux/main.py
VERSION: 1.0.0
ROLE: Boots the Linux desktop client, initializes XDG storage directories,
      applies custom dark stylesheets, and launches the PyQt6/PySide6 window manager.
"""

import sys
import os
from pathlib import Path

# Ensure trace-linux directory is on Python path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Ensure XDG directories and database initialization
from config import ensure_xdg_directories, APP_DISPLAY_NAME, APP_VERSION, DATABASE_FILE
from database import init_database

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    QT_BACKEND = "PyQt6"
except ImportError:
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        QT_BACKEND = "PySide6"
    except ImportError:
        print("\n" + "=" * 70)
        print("[-] ERROR: Neither PyQt6 nor PySide6 is installed in this Python environment.")
        print("[-] To run the TRACE Linux desktop client on Xubuntu/XFCE, please execute:")
        print("    pip install PyQt6")
        print("    or: sudo apt-get install python3-pyqt6 (on Debian/Ubuntu)")
        print("=" * 70 + "\n")
        sys.exit(1)

from ui.main_window import MainWindow


def main():
    print(f"[+] Initializing {APP_DISPLAY_NAME} v{APP_VERSION} ({QT_BACKEND} Engine)...")

    # 1. Ensure XDG Directory Compliance
    ensure_xdg_directories()

    # 2. Initialize Local SQLite Schema (~/.local/share/trace/trace_local.db)
    init_database()
    print(f"[+] Local SQLite database active at: {DATABASE_FILE}")

    # 3. Create Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationVersion(APP_VERSION)

    # 4. Load Custom Dark Theme Stylesheet
    qss_path = CURRENT_DIR / "assets" / "style.qss"
    if qss_path.exists():
        try:
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[!] Warning: Could not load stylesheet: {e}")

    # 5. Launch Main Window
    window = MainWindow()
    window.show()

    print(f"[+] TRACE Desktop client successfully running. Window active.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
