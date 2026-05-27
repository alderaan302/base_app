# Deployment Guide

This application can be deployed as a Podman container using either Terraform or manual commands.

## Terraform Deployment (Recommended)

### Prerequisites

- Terraform >= 1.5.0
- Podman installed and running

### Deploy with Terraform

```bash
cd terraform
terraform init
terraform apply
```

This will:
1. Build the container image (`localhost/ibm-expert-labs-app:latest`)
2. Deploy the container with:
   - Name: `ibm-expert-labs-app`
   - Port mapping: `8084:8084`
   - Restart policy: `unless-stopped`

### Terraform Features

- **Automatic Rebuilds**: Changes to source files trigger automatic rebuilds
- **Idempotent**: Safe to run multiple times
- **Clean Destroy**: `terraform destroy` cleanly removes the container

### Infrastructure Details

The Terraform configuration uses `null_resource` with `local-exec` provisioners to run Podman commands directly. This approach:
- Avoids SSH authentication complexities with the Podman provider
- Works reliably with Podman Machine on macOS
- Mirrors the successful pattern from the `cloudmanager` project

## Manual Deployment with Podman

### Build the Image

```bash
podman build -t ibm-expert-labs-app .
```

### Run the Container

```bash
podman run -d \
  --name ibm-expert-labs-app \
  -p 8084:8084 \
  --restart unless-stopped \
  ibm-expert-labs-app
```

### Verify the Container

```bash
podman ps | grep ibm-expert-labs-app
```

### Test the Application

```bash
curl http://localhost:8084/api/settings
```

Or open in your browser: http://localhost:8084

## Container Management

### View Logs

```bash
podman logs ibm-expert-labs-app
```

### Stop the Container

```bash
podman stop ibm-expert-labs-app
```

### Restart the Container

```bash
podman restart ibm-expert-labs-app
```

### Remove the Container

```bash
podman rm -f ibm-expert-labs-app
```

### Remove the Image

```bash
podman rmi ibm-expert-labs-app
```

## Container Management

### View Logs

```bash
podman logs ibm-expert-labs-app
```

### Stop the Container

```bash
podman stop ibm-expert-labs-app
```

### Restart the Container

```bash
podman restart ibm-expert-labs-app
```

### Remove the Container

```bash
podman rm -f ibm-expert-labs-app
```

### Remove the Image

```bash
podman rmi ibm-expert-labs-app
```

## Application Features

- **Flask Backend**: REST API for settings management
- **React Frontend**: IBM Carbon-styled dark mode UI
- **Settings Persistence**: JSON-based configuration storage
- **Image Upload**: Support for custom info icons
- **Port**: Runs on port 8084

## Access the Application

Once deployed, access the application at:
- **URL**: http://localhost:8084
- **API**: http://localhost:8084/api/settings
