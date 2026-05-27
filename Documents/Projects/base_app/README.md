# Base App - Customizable Dashboard Platform

A Flask-based dashboard application with customizable widgets, integrations, and real-time monitoring capabilities.

## Overview

Base App is a web-based dashboard platform that allows users to create custom reports with various widget types, integrate with external services, and monitor infrastructure in real-time. The application features a modern React-based frontend with a Flask backend.

## Key Features

### 📊 Widget System
- **Text Widgets**: Markdown-supported text with rich formatting, tables, code blocks, and LaTeX math
- **Server Info Widgets**: Real-time server monitoring with CPU, memory, disk usage metrics
- **Video Feed Widgets**: Live Ring camera snapshots with auto-refresh (3-second intervals)
- **URL Widgets**: Embed external web pages and services
- **Chart Widgets**: Prometheus metrics visualization
- **Prometheus Widgets**: Time-series metric charts from Prometheus data sources

### 🔌 Integrations
Pre-configured integrations with multiple services:
- **Homebridge/Home-Phill**: Apple HomeKit device management and Ring camera access
- **Ring**: Direct camera snapshot API integration with OAuth authentication
- **HashiCorp Vault**: Secrets management and health monitoring
- **HashiCorp Terraform**: Infrastructure state inspection
- **Prometheus**: Metrics collection and monitoring
- **SevOne NMS**: Network monitoring REST API
- **VirtualBox**: VM management via REST API
- **Podman**: Container management and monitoring
- **Apple UTM**: Virtualization management
- **Google Gemini**: AI integration

### 📱 Reports System
- Create multiple named reports
- Drag-and-drop widget arrangement
- Resizable widgets with customizable layouts
- Real-time auto-save functionality
- Report sharing and management

## Technical Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0 with Python 3.9+
- **API Endpoints**:
  - `/api/reports` - Report CRUD operations
  - `/api/widgets` - Widget management
  - `/api/integrations` - Integration configuration
  - `/api/camera/snapshot` - Ring camera snapshot proxy
  - `/api/server/info` - Server metrics
  - `/api/prometheus/*` - Prometheus metric queries
  - `/api/vault/*` - Vault API proxy
  - `/api/terraform/*` - Terraform state access

### Frontend (React)
- **Framework**: React 18.2.0 (CDN-based, no build step)
- **UI Library**: Material-UI (MUI) 5.x
- **Key Components**:
  - `Dashboard`: Main application shell with navigation
  - `ReportView`: Widget container with drag-and-drop
  - `WidgetRenderer`: Dynamic widget type renderer
  - `VideoFeedWidget`: Ring camera live feed display
  - `ServerInfoWidget`: Real-time server monitoring
  - `IntegrationManager`: Integration configuration UI

### Data Storage
- **Location**: `settings/` directory (volume-mounted in containers)
- **Files**:
  - `settings.json` - Global settings and integration credentials
  - `reports.json` - Report definitions
  - `{report_name}_widgets.json` - Widget configurations per report
  - `integrations/{integration_id}/` - Integration-specific settings

### Containerization
- **Engine**: Podman (Docker-compatible)
- **Base Image**: Python 3.9-slim
- **Port**: 8084 (host) → 8084 (container)
- **Volume**: `./settings:/data:Z` (SELinux-compatible)
- **Build**: `podman build -t base_app .`
- **Run**: `podman run -d --name base_app -p 8084:8084 -v "$PWD/settings:/data:Z" base_app`

## Installation

### Prerequisites
- Python 3.9+
- Podman or Docker
- Access to integrations (Homebridge, Prometheus, etc.)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alderaan302/base_app.git
   cd base_app
   ```

2. **Configure integrations**:
   Edit `settings/settings.json` with your credentials:
   ```json
   {
     "integrations": {
       "home-phill": {
         "homebridge_url": "http://YOUR_HOMEBRIDGE_IP:8581",
         "username": "admin",
         "password": "your_password"
       }
     }
   }
   ```

3. **Build and run**:
   ```bash
   podman build -t base_app .
   podman run -d --name base_app -p 8084:8084 -v "$PWD/settings:/data:Z" base_app
   ```

4. **Access the application**:
   Open http://localhost:8084

## Ring Camera Integration

### How It Works
The Ring camera integration uses a multi-step authentication chain:

1. **Authenticate to Homebridge**: 
   - POST `/api/auth/login` with username/password
   - Receive JWT access token

2. **Extract Ring Refresh Token**:
   - GET `/api/config-editor` from Homebridge
   - Parse Ring platform configuration
   - Extract `refreshToken` from platforms array

3. **Authenticate to Ring API**:
   - POST `https://oauth.ring.com/oauth/token`
   - Body: `{"grant_type": "refresh_token", "refresh_token": "...", "client_id": "ring_official_android"}`
   - Receive Ring access token

4. **Fetch Ring Devices**:
   - GET `https://api.ring.com/clients_api/ring_devices`
   - Header: `Authorization: Bearer {ring_access_token}`
   - Find camera by name in doorbots/stickup_cams/authorized_doorbots

5. **Request Snapshot**:
   - GET `https://api.ring.com/clients_api/snapshots/image/{device_id}`
   - Timeout: 30 seconds (Ring cameras need wake-up time)
   - Return JPEG image

### Video Feed Widget
- **Auto-refresh**: Every 3 seconds
- **Browser cache**: Disabled (no-cache headers)
- **Debug logging**: Enabled in console
- **First snapshot**: May take 20-30 seconds (camera wake-up)

## Configuration Files

### settings.json Structure
```json
{
  "integrations": {
    "integration-name": {
      "display_name": "Human Readable Name",
      "api_url": "https://api.example.com",
      "username": "user",
      "password": "pass",
      "api_key": "key"
    }
  },
  "admin_email": "admin@example.com"
}
```

### Widget Configuration
```json
{
  "widgetId": {
    "type": "Video Feed",
    "x": 0,
    "y": 0,
    "w": 6,
    "h": 4,
    "cameraName": "Front Door Camera",
    "cameraId": "device-12345",
    "videoSource": "ring"
  }
}
```

## API Reference

### Camera Snapshot
```
GET /api/camera/snapshot?integration=home-phill&camera=Front%20Door%20Camera
```
Returns: JPEG image (application/jpeg)

### Server Info
```
GET /api/server/info
```
Returns: `{"cpu": 45.2, "memory": 62.3, "disk": 78.5, "timestamp": "..."}`

### Widget CRUD
```
POST /api/widgets/{report_name}
Body: {"widgetId": {...widget_config...}}

GET /api/widgets/{report_name}
Returns: {widget configurations}

DELETE /api/widgets/{report_name}/{widget_id}
```

## Development

### Project Structure
```
base_app/
├── app.py                      # Flask backend (2300+ lines)
├── templates/
│   └── index.html             # React frontend (5700+ lines)
├── settings/
│   ├── settings.json          # Global configuration
│   ├── reports.json           # Report definitions
│   └── integrations/          # Integration configs
├── Dockerfile                 # Container build
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Key Dependencies
- Flask 3.0.0
- requests 2.31.0
- psutil 5.9.0 (server metrics)
- Pillow 10.0.0 (image processing)

### Adding a New Widget Type

1. **Backend** (app.py):
   - Add API endpoint if needed
   - Handle widget-specific data fetching

2. **Frontend** (templates/index.html):
   - Create widget component (e.g., `MyCustomWidget`)
   - Add to `WidgetRenderer` switch statement
   - Add configuration UI in widget settings modal
   - Update widget type dropdown

3. **Configuration**:
   - Define widget schema in widget config
   - Add default values and validation

## Troubleshooting

### Ring Camera Not Showing
- Check Homebridge credentials in `settings.json`
- Verify Ring refresh token exists in Homebridge config
- Check browser console for authentication errors
- First snapshot may take 30 seconds (camera wake-up)

### Container Won't Start
```bash
# Check logs
podman logs base_app

# Verify port availability
lsof -i:8084

# Check volume mount
podman inspect base_app | grep -A 5 Mounts
```

### Integration 403/401 Errors
- Verify credentials in `settings.json`
- Check integration service is accessible
- Confirm API URLs are correct
- Review backend logs for detailed errors

## Security Notes

⚠️ **Important**: 
- `settings.json` contains sensitive credentials
- Add `settings/settings.json` to `.gitignore`
- Use environment variables for production deployments
- Never commit API keys or passwords
- Consider using HashiCorp Vault for secret management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Private project - All rights reserved

## Author

Phill Ingram (phill.ingram@gmail.com)

## Additional Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment instructions
- [INTEGRATIONS_FEATURE.md](INTEGRATIONS_FEATURE.md) - Integration system details
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Feature roadmap
- [TEXT_WIDGET_MARKDOWN_GUIDE.md](TEXT_WIDGET_MARKDOWN_GUIDE.md) - Markdown widget usage
