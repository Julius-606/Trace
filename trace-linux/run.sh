#!/usr/bin/env bash
# ==============================================================================
# TRACE Desktop (Linux Client) - Quick Launch Script for Xubuntu / XFCE
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[*] Checking Python environment for TRACE Desktop..."

if ! python3 -c "import PyQt6" &>/dev/null && ! python3 -c "import PySide6" &>/dev/null; then
    echo "[!] Neither PyQt6 nor PySide6 detected."
    echo "[*] Attempting to install PyQt6 via pip..."
    pip install -r requirements.txt || sudo apt-get install -y python3-pyqt6
fi

echo "[*] Launching TRACE Desktop Client..."
python3 main.py "$@"
