"""
TRACE Desktop (Linux Client) - XDG Compliance & Path Configuration
FILE: trace-linux/config.py
VERSION: 1.0.0
ROLE: Resolves Linux system paths strictly conforming to the XDG Base Directory
      Specification ($XDG_DATA_HOME, $XDG_CONFIG_HOME, $XDG_CACHE_HOME).
"""

import os
import sys
from pathlib import Path

# Application Metadata
APP_NAME = "trace"
APP_DISPLAY_NAME = "TRACE Desktop"
APP_VERSION = "1.0.0"

# XDG Base Directory Resolution
# 1. Data Home (default: ~/.local/share)
XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
TRACE_DATA_DIR = XDG_DATA_HOME / APP_NAME

# 2. Config Home (default: ~/.config)
XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
TRACE_CONFIG_DIR = XDG_CONFIG_HOME / APP_NAME

# 3. Cache Home (default: ~/.cache)
XDG_CACHE_HOME = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
TRACE_CACHE_DIR = XDG_CACHE_HOME / APP_NAME

# 4. Local Database Location
DATABASE_FILE = TRACE_DATA_DIR / "trace_local.db"
DATABASE_URI = f"sqlite:///{DATABASE_FILE}"

# Subdirectories required by runtime
SYLLABI_DIR = TRACE_DATA_DIR / "syllabi"
ASSETS_DIR = TRACE_DATA_DIR / "assets"
LOGS_DIR = TRACE_DATA_DIR / "logs"

# Central Backend API Endpoint (Satellite Routing)
DEFAULT_BACKEND_URL = os.environ.get("TRACE_API_URL", "http://127.0.0.1:7860")
CLOUD_BACKEND_URL = os.environ.get("TRACE_CLOUD_URL", "https://huggingface.co/spaces/Agent606/Trace")

# Initial Currency Grant for New Profiles
INITIAL_NEURONS_BALANCE = 200
DEFAULT_UNIT_PRICE_NEURONS = 20


def ensure_xdg_directories() -> None:
    """
    Auto-creates all required XDG application directories and copies bundled
    default assets/syllabi if they do not yet exist in the local share directory.
    """
    for folder in [TRACE_DATA_DIR, TRACE_CONFIG_DIR, TRACE_CACHE_DIR, SYLLABI_DIR, ASSETS_DIR, LOGS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    # Seed bundled syllabi from source tree if local data folder is empty
    bundled_syllabi_dir = Path(__file__).resolve().parent / "syllabi"
    if bundled_syllabi_dir.exists():
        for syllabus_file in bundled_syllabi_dir.glob("*.json"):
            dest_file = SYLLABI_DIR / syllabus_file.name
            if not dest_file.exists():
                try:
                    dest_file.write_text(syllabus_file.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception as exc:
                    print(f"[TRACE-CONFIG] Warning: Could not seed syllabus {syllabus_file.name}: {exc}")


# Auto-initialize directories on import
ensure_xdg_directories()
