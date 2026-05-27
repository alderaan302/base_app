# Session Notes

If you are coming back to this workspace later, start by reading this file and then inspect `app.py`, `templates/index.html`, and `terraform/`.

## What this project is now
- A Flask backend serves the app and persists configuration in `settings.json`.
- The front end is a React single-page app rendered from `templates/index.html`.
- The UI is styled to match IBM Carbon dark mode and the IBM SevOne-style layout from the screenshots, but branded as IBM Expert Labs.
- The reports page is intentionally empty but keeps sortable columns.
- The settings modal creates the initial admin user, saves branding, and uploads `info_icon.jpg` / `info_icon.png` into the workspace.
- The info icon opens a lightbox that uses the configurable text and uploaded image.
- The left navigation highlights the active item and expands submenu sections for Configure and Administer.
- Terraform now uses the `decafcode/podman` provider to pull a Python base image, upload the app files, and run the app as a local Podman container.

## Files that matter
- `app.py`: API and file persistence.
- `templates/index.html`: React UI and Carbon-like styling.
- `Dockerfile`: container entry point.
- `requirements.txt`: Python dependencies.
- `terraform/`: Podman-provider local deployment scaffold.

## Restart step
When you come back, just tell the assistant to read `session-notes.md` and continue from there.
