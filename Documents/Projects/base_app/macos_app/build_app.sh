#!/usr/bin/env bash
# Build the BaseApp.app bundle for macOS.
# Usage:  ./build_app.sh

set -e
cd "$(dirname "$0")"

echo "==> Creating virtual environment (if missing)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing build requirements..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

echo "==> Cleaning previous build artifacts..."
rm -rf build dist

echo "==> Building BaseApp.app with py2app..."
python setup.py py2app

echo ""
echo "✅ Build complete!"
echo "   App bundle: $(pwd)/dist/BaseApp.app"
echo ""
echo "   To install:  mv dist/BaseApp.app /Applications/"
echo "   To run:      open dist/BaseApp.app"
