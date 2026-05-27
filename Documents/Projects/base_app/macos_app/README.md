# Base App - Native macOS Application

A native macOS .app bundle that wraps the Base App Flask + React dashboard
in a real desktop window. **All your existing reports, widgets, integrations,
and settings work identically** — this is just a different way to launch and
display the same application.

## Why this approach?

- ✅ **Zero rewrite** — Your 2,300-line Flask backend and 5,700-line React
  frontend are bundled as-is.
- ✅ **Identical behavior** — Same widgets, same Ring camera integration,
  same Homebridge / Prometheus / Vault / Terraform support.
- ✅ **Native window** — Real macOS window with menu bar, no browser tab.
- ✅ **No containers required** — Runs without Podman/Docker.
- ✅ **Your data is portable** — Settings live in `~/Library/Application
  Support/BaseApp/settings/`, separate from the .app itself.

## How it works (architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                      BaseApp.app                            │
│                                                             │
│  ┌──────────────────┐         ┌────────────────────────┐    │
│  │  Native Cocoa    │  HTTP   │  Embedded Flask server │    │
│  │  WebKit window   │ ──────► │  (your existing app.py)│    │
│  │  (pywebview)     │ ◄────── │  on 127.0.0.1:8084     │    │
│  └──────────────────┘         └────────────────────────┘    │
│           ▲                              │                  │
│           │                              ▼                  │
│           │              ┌──────────────────────────────┐   │
│           └──────────────│ ~/Library/Application Support│   │
│                          │   /BaseApp/settings/         │   │
│                          │   (your reports & configs)   │   │
│                          └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

On first launch, the app seeds `~/Library/Application Support/BaseApp/settings/`
with the contents of the bundled `settings/` folder — so all your current
reports, widgets, and integrations appear immediately.

## Quick Start

### Option 1 — Build the .app bundle (recommended)

```bash
cd macos_app
./build_app.sh
```

When the build completes:

```bash
# Install
mv dist/BaseApp.app /Applications/

# Launch
open /Applications/BaseApp.app
```

You can also double-click `BaseApp.app` in Finder.

### Option 2 — Run from source (for development)

```bash
cd macos_app
./run_dev.sh
```

This opens the native window without building a bundle — useful for iterating.

## Requirements

- macOS 12.0+ (tested on Tahoe 26.4)
- Python 3.10+ (use `python3 --version` to check; Apple ships one by default)
- ~150 MB free disk space for the built .app

All Python dependencies are installed automatically into a local `.venv` by
the build scripts.

## File Layout

```
macos_app/
├── launcher.py        # The entry point - starts Flask + opens the window
├── setup.py           # py2app build configuration
├── requirements.txt   # Python dependencies (pywebview, Flask, ...)
├── build_app.sh       # One-command build → dist/BaseApp.app
├── run_dev.sh         # Run from source without bundling
└── README.md          # This file
```

## Where is my data?

| Data | Location |
|------|----------|
| Settings & credentials | `~/Library/Application Support/BaseApp/settings/settings.json` |
| Reports | `~/Library/Application Support/BaseApp/settings/reports.json` |
| Widgets per report | `~/Library/Application Support/BaseApp/settings/<report>_widgets.json` |
| Integration configs | `~/Library/Application Support/BaseApp/settings/integrations/` |

To **back up** your dashboard:
```bash
cp -R ~/Library/Application\ Support/BaseApp ~/Desktop/BaseApp-backup
```

To **start over** (re-seed from the bundled defaults):
```bash
rm -rf ~/Library/Application\ Support/BaseApp
open /Applications/BaseApp.app
```

To **migrate from the Podman container**: just copy your existing
`settings/` directory:
```bash
mkdir -p ~/Library/Application\ Support/BaseApp
cp -R /Users/alderaan/Documents/Projects/base_app/settings ~/Library/Application\ Support/BaseApp/
```

## Troubleshooting

### "App can't be opened because the developer cannot be verified"

The .app is unsigned. Right-click → **Open** → **Open** in the dialog.
Or run once from terminal: `xattr -dr com.apple.quarantine /Applications/BaseApp.app`

### Window opens blank / "connection refused"

The embedded Flask server may have failed to start. Check Console.app
logs for "BaseApp" or run from source (`./run_dev.sh`) to see Python tracebacks.

### Ring camera / integrations don't work

Same fix as the web version: edit
`~/Library/Application Support/BaseApp/settings/settings.json`
with correct credentials.

### Port 8084 already in use

The launcher automatically picks an alternative free port — no action needed.

## Building & Distributing

For a fully signed & notarized distribution:

```bash
# 1. Build
./build_app.sh

# 2. Sign with your Developer ID
codesign --deep --force --verbose \
    --sign "Developer ID Application: Your Name (TEAMID)" \
    dist/BaseApp.app

# 3. Notarize
xcrun notarytool submit dist/BaseApp.app --apple-id you@example.com \
    --team-id TEAMID --password app-specific-pw --wait
xcrun stapler staple dist/BaseApp.app
```

For personal use, signing/notarization is optional.

## Differences from the Web/Container Version

| Feature | Container | macOS App |
|---------|-----------|-----------|
| Port | 8084 (exposed) | 8084 (loopback only) |
| Settings location | `./settings/` (mounted) | `~/Library/Application Support/BaseApp/settings/` |
| Updates | `podman build` | Re-run `./build_app.sh` |
| Multi-user access | Yes (network) | No (single user, local only) |
| Auto-start on login | Manual | Add to System Settings → Login Items |
