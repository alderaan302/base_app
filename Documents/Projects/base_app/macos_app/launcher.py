"""
Base App - macOS Desktop Wrapper
=================================
Native macOS application wrapping the Flask + React dashboard.

Architecture:
- Starts the existing Flask app on a local port in a background thread
- Opens a native macOS window via pywebview pointing to the Flask server
- Stores user settings in ~/Library/Application Support/BaseApp/
- All integrations, reports, and widgets work identically to the web version

Usage:
    python launcher.py                # Run from source
    python setup.py py2app            # Build .app bundle
"""

import os
import sys
import threading
import time
import socket
import shutil
from pathlib import Path

import webview

# ---------------------------------------------------------------------------
# Paths & Data Directory Setup
# ---------------------------------------------------------------------------

APP_NAME = "BaseApp"

# When bundled with py2app, the project lives inside the .app Resources dir.
if getattr(sys, "frozen", False):
    # Running as a bundled .app
    BUNDLE_DIR = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path(sys.executable).parent
    PROJECT_DIR = BUNDLE_DIR / "project"
else:
    # Running from source: project is the parent directory of macos_app/
    PROJECT_DIR = Path(__file__).resolve().parent.parent

# User-writable application support directory on macOS
USER_DATA_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
SETTINGS_DIR = USER_DATA_DIR / "settings"


def initialize_user_data():
    """Seed the user's Application Support directory with default settings
    from the bundled project on first launch.
    """
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    bundled_settings = PROJECT_DIR / "settings"
    if not SETTINGS_DIR.exists() and bundled_settings.exists():
        print(f"First launch detected. Seeding settings from {bundled_settings}")
        shutil.copytree(bundled_settings, SETTINGS_DIR)
    else:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Flask Server (background thread)
# ---------------------------------------------------------------------------

def find_free_port(preferred: int = 8084) -> int:
    """Try preferred port first; if taken, ask OS for any free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_flask(port: int):
    """Import and run the existing Flask app on the given port."""
    # Tell the Flask app where to read/write settings
    os.environ["SETTINGS_DIR"] = str(SETTINGS_DIR)

    # Ensure the project directory is on sys.path so `import app` works
    sys.path.insert(0, str(PROJECT_DIR))

    # Import here (after env vars set) so app.py picks up SETTINGS_DIR
    from app import app as flask_app  # noqa: E402

    # Use Flask's built-in server (sufficient for single-user desktop app)
    flask_app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


def wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """Poll the Flask URL until it responds or timeout elapses."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(0.25)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Starting {APP_NAME}...")
    print(f"  Project directory: {PROJECT_DIR}")
    print(f"  User data:         {USER_DATA_DIR}")

    initialize_user_data()

    port = find_free_port(8084)
    url = f"http://127.0.0.1:{port}"
    print(f"  Flask URL:         {url}")

    # Launch Flask in a daemon thread so it dies with the GUI
    flask_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()

    if not wait_for_server(url):
        print("ERROR: Flask server failed to start within timeout.")
        sys.exit(1)

    # Create the native macOS window
    window = webview.create_window(
        title="Base App",
        url=url,
        width=1400,
        height=900,
        min_size=(900, 600),
        resizable=True,
        confirm_close=False,
    )

    # Use the native macOS WebKit backend (no Chromium dependency)
    webview.start(gui="cocoa", debug=False)


if __name__ == "__main__":
    main()
