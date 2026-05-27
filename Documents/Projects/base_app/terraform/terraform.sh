#!/bin/bash
# Wrapper script to run Terraform with Podman connection environment

# Get the default Podman connection URI
PODMAN_URI=$(podman system connection list --format '{{if .Default}}{{.URI}}{{end}}' | head -n 1)

if [ -z "$PODMAN_URI" ]; then
    echo "Error: No default Podman connection found"
    exit 1
fi

echo "Using Podman connection: $PODMAN_URI"

# Export CONTAINER_HOST for the Terraform provider
export CONTAINER_HOST="$PODMAN_URI"

# Run terraform with all provided arguments
terraform "$@"
