# Terraform Deployment

This scaffold manages a Podman container with Terraform using the `decafcode/podman` provider.

## How to use
1. Make sure Podman is installed and the Podman API socket is available.
2. Terraform auto-detects your default Podman connection via `podman system connection list`.
3. If needed, override detection by passing `container_host` explicitly.
4. From this `terraform/` directory, run:
   - `terraform init`
   - `terraform apply`
5. Open the app at `http://127.0.0.1:8084`.

## What Terraform does
- Pulls the `python:3.11-slim` base image with the Podman provider.
- Uploads the app files into the container at creation time.
- Starts the Flask app inside the container with a `pip install` + `python app.py` command.
- Removes the container on `terraform destroy`.

## Notes
- The app listens on port `8084`.
- The provider requires Terraform 1.11 or newer.
- If you want a different host port, override `host_port` when you apply.
- The uploaded app files are the current workspace sources, so changing `app.py` or `templates/index.html` will recreate the container.
- If auto-detection cannot resolve a URI, set `container_host` manually (or export `CONTAINER_HOST`).
- For `ssh://` Podman URIs without a fragment, this config appends `#trust_unknown_host=1` automatically. For stricter security, pass `container_host` with `#pubkey=...` or `#ca=...`.
