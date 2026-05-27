"""
py2app build script for Base App.

Build the .app bundle:
    cd macos_app
    python setup.py py2app

The resulting bundle will be at:
    macos_app/dist/BaseApp.app

Drag it into /Applications to install.
"""

from setuptools import setup
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent

APP = ["launcher.py"]

# Files bundled inside BaseApp.app/Contents/Resources/project/
# (Used as the seed for the user's settings folder on first launch.)
DATA_FILES = [
    (
        "project",
        [
            str(PROJECT / "app.py"),
            str(PROJECT / "requirements.txt"),
        ],
    ),
    (
        "project/templates",
        [str(p) for p in (PROJECT / "templates").glob("*")],
    ),
]

# Recursively include the settings directory
def _add_tree(rel_target: str, src_dir: Path):
    for p in src_dir.rglob("*"):
        if p.is_file() and not p.name.startswith("._") and p.name != ".DS_Store":
            sub = p.parent.relative_to(src_dir).as_posix()
            target = f"{rel_target}/{sub}" if sub != "." else rel_target
            DATA_FILES.append((target, [str(p)]))

_add_tree("project/settings", PROJECT / "settings")

OPTIONS = {
    "argv_emulation": False,
    "iconfile": str(PROJECT / "sevone-logo.png") if (PROJECT / "sevone-logo.png").exists() else None,
    "plist": {
        "CFBundleName": "Base App",
        "CFBundleDisplayName": "Base App",
        "CFBundleIdentifier": "com.alderaan.baseapp",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0",
        # Required so the embedded WebView can talk to local http://127.0.0.1
        "NSAppTransportSecurity": {
            "NSAllowsLocalNetworking": True,
            "NSAllowsArbitraryLoads": True,
        },
        "LSUIElement": False,
    },
    "packages": [
        "flask",
        "werkzeug",
        "jinja2",
        "requests",
        "PIL",
        "webview",
        "selenium",  # imported by ring_scraper at module load time
    ],
    "includes": [
        "app",
    ],
    "excludes": [
        "tkinter",
    ],
}

# Remove iconfile entry if None (py2app dislikes it)
if OPTIONS["iconfile"] is None:
    del OPTIONS["iconfile"]

setup(
    app=APP,
    name="BaseApp",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
