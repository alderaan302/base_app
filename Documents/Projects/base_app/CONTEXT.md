# Project Context and Session History

## Last Updated
May 26, 2026

## Project Status
✅ **PRODUCTION READY** - Application running on port 8084 with Ring camera integration

## Critical Context for Future Sessions

### 1. Ring Camera Integration Deep Dive

**Why the complex authentication chain?**
- Ring doesn't provide direct API access to snapshots
- Solution: Use Homebridge as intermediary to access Ring's refresh token
- Authentication flow: Homebridge JWT → Ring refresh token → Ring OAuth → Ring access token → Snapshot

**Key Implementation Details:**
- Ring cameras take 20-30 seconds for first snapshot (wake-up time)
- Snapshots refresh every 3 seconds in VideoFeedWidget
- Must use client_id "ring_official_android" for Ring OAuth
- Ring API endpoint: `https://api.ring.com/clients_api/snapshots/image/{device_id}`
- Timeout set to 30 seconds for snapshot requests

**Known Issues Solved:**
- ✅ Placeholder images - Fixed by implementing full Ring API integration (replaced PIL image generation)
- ✅ 403 errors - Fixed by correcting homebridge password from "Ciurz8!n0w" to "Ciurz8"
- ✅ Jinja2 template conflicts - Fixed by wrapping VideoFeedWidget in `{% raw %} {% endraw %}` tags

### 2. Architecture Decisions

**Why Flask + React CDN (not npm/webpack)?**
- Single-file deployment simplicity
- No build step required
- Easy to modify and debug
- Suitable for internal/personal dashboards

**Why Podman over Docker?**
- User preference (macOS environment)
- SELinux compatibility with `:Z` volume mounts
- Docker Desktop not installed/available

**Data Storage Pattern:**
- Settings in `settings/` directory (volume-mounted)
- Widgets saved per-report: `{report_name}_widgets.json`
- Integration configs in `settings/integrations/{integration_id}/`
- NO DATABASE - everything is file-based JSON

### 3. Integration System

**home-phill vs homebridge integration:**
- `homebridge` - Old/deprecated, had wrong password
- `home-phill` - Current/active integration for Ring cameras
- Both point to same Homebridge instance: http://192.168.68.11:8581

**Credentials Management:**
- Stored in `settings/settings.json` (NOT committed to git)
- Homebridge: username="root", password="Ciurz8"
- Ring: username="phill.ingram302@gmail.com" (not directly used - we get token from Homebridge)

### 4. Widget System Architecture

**Widget Type Registry:**
- Text Widget - Markdown with LaTeX support
- Server Info Widget - Real-time CPU/memory/disk via psutil
- Video Feed Widget - Ring camera snapshots (3s refresh)
- URL Widget - iframe embeds
- Prometheus Widget - Time-series charts
- Chart Widget - Generic chart data

**Widget State Management:**
- React state in frontend
- Auto-save to backend on changes
- Drag-and-drop via react-grid-layout
- Position/size stored as `{x, y, w, h}`

### 5. Known Quirks and Workarounds

**Jinja2 Template Escaping:**
- React JSX syntax conflicts with Jinja2 templates
- Solution: Wrap React components in `{% raw %} {% endraw %}`
- Affects: VideoFeedWidget, any component with {{ }} syntax

**Console Spam Suppression:**
- 403/404 errors from missing integrations were spamming console
- Solution: Added conditional logging based on integration existence
- Location: templates/index.html around line 2634-2650

**Git Repository Structure:**
- Repo root is `/Users/alderaan` (NOT `/Users/alderaan/Documents/Projects/base_app`)
- Project path: `Documents/Projects/base_app`
- This affects git commands - must be aware of working directory

### 6. Development Workflow

**Container Rebuild Pattern:**
```bash
podman stop base_app && \
podman rm base_app && \
podman build -t base_app -q . && \
podman run -d --name base_app -p 8084:8084 -v "$PWD/settings:/data:Z" base_app
```

**Testing Changes:**
1. Edit code
2. Rebuild container (command above)
3. Hard refresh browser (Cmd+Shift+R)
4. Check console for errors/debug logs

**Debug Logging:**
- VideoFeedWidget has extensive console.log statements
- Useful for tracking snapshot loading, blob sizes, lifecycle
- Can be removed in production if desired

### 7. Future Enhancement Ideas

**Performance Optimizations:**
- Cache Ring access tokens (currently re-authenticates every request)
- Implement token refresh logic (tokens expire)
- Add snapshot request caching (Ring has rate limits)
- Consider WebSocket for live updates instead of polling

**Feature Additions:**
- Motion detection alerts via Ring webhook
- Support for RTSP streams (non-Ring cameras)
- Configurable refresh intervals per widget
- Snapshot timestamp overlay
- Multi-camera grid view widget

**Code Quality:**
- Extract Ring API logic to separate module
- Add proper error handling for Ring API failures
- Implement retry logic with exponential backoff
- Add unit tests for critical paths

### 8. Debugging Checklist

**Ring Camera Not Working:**
1. ✅ Check Homebridge is accessible: `curl http://192.168.68.11:8581`
2. ✅ Verify credentials in settings.json
3. ✅ Check browser console for auth errors
4. ✅ Confirm camera name matches Ring device name exactly
5. ✅ Wait 30 seconds for first snapshot (camera wake-up)
6. ✅ Check backend logs: `podman logs base_app`

**Widget Not Displaying:**
1. Check widget type is in WidgetRenderer switch statement
2. Verify widget config saved in `{report}_widgets.json`
3. Hard refresh browser (Cmd+Shift+R)
4. Check for Jinja2 template syntax conflicts
5. Review console for React errors

**Integration 403/401:**
1. Verify credentials in settings.json
2. Test integration URL directly (curl/browser)
3. Check for password changes
4. Confirm API version compatibility

### 9. Important File Locations

**Key Files to Understand:**
- `app.py` (lines 2142-2260) - Ring camera snapshot endpoint
- `templates/index.html` (lines 1519-1641) - VideoFeedWidget component
- `templates/index.html` (line 5489) - Widget rendering logic
- `settings/settings.json` - All credentials and config
- `settings/reports.json` - Report definitions

**Sensitive Files (Never Commit):**
- `settings/settings.json` - Contains all passwords/API keys
- `settings/*_widgets.json` - May contain sensitive URLs/data
- Any file with credentials or tokens

### 10. Production Deployment Notes

**Current Environment:**
- macOS (arm64)
- Podman container runtime
- Port 8084 exposed
- SELinux-compatible volume mounts (`:Z` flag)

**Security Considerations:**
- All credentials in plaintext JSON files
- No authentication on dashboard (assumes private network)
- Ring refresh token is sensitive - protects entire Ring account
- Consider using HashiCorp Vault for production credentials

**Backup Strategy:**
- `settings/` directory contains all user data
- Regular backups recommended
- Git repository for code only (not settings)

## Session Highlights

### Phase 38 Summary (Ring Camera Implementation)
1. Created home-phill integration for Homebridge
2. Built Video Feed widget UI with camera selection
3. Implemented VideoFeedWidget React component with auto-refresh
4. Debugged multiple issues:
   - 403 errors from wrong homebridge password
   - Jinja2 template syntax conflicts
   - Placeholder image instead of real feed
5. **Final solution**: Complete Ring API integration with OAuth flow
6. Result: Live Ring camera snapshots updating every 3 seconds

### Key Learnings
- Ring API requires multi-step authentication through Homebridge
- Jinja2 and React JSX syntax can conflict without proper escaping
- Ring cameras need wake-up time (20-30s) for first snapshot
- Browser cache can hide issues - always hard refresh during debugging
- Debug logging is essential for async operations like snapshot loading

## Quick Start for New Session

**To pick up where we left off:**

1. **Verify running state:**
   ```bash
   podman ps | grep base_app
   curl -s http://localhost:8084 > /dev/null && echo "✓ Running" || echo "✗ Down"
   ```

2. **Check recent changes:**
   ```bash
   cd /Users/alderaan/Documents/Projects/base_app
   git log --oneline -10
   ```

3. **Review current integrations:**
   ```bash
   cat settings/settings.json | grep -A 3 '"home-phill"'
   ```

4. **Test Ring camera:**
   - Open http://localhost:8084
   - Navigate to Reports
   - Open report with Video Feed widget
   - Verify camera snapshot loads and refreshes

5. **Key context files to read:**
   - README.md (project overview)
   - This file (CONTEXT.md)
   - app.py lines 2142-2260 (Ring API)
   - templates/index.html lines 1519-1641 (VideoFeedWidget)

## Contact
Phill Ingram - phill.ingram@gmail.com

GitHub: https://github.com/alderaan302/base_app
