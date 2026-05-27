#!/usr/bin/env bash
# Run BaseApp from source (for development / quick testing).
# This does NOT build a .app bundle - it just opens the native window.
#
# Usage:  ./run_dev.sh

set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing dependencies (if needed)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "==> Launching Base App..."
python launcher.py
