import json
import os
import tarfile
import shutil
import requests
import time
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from sevonev3rest import SevOneV3API
from ring_scraper import RingAPI


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_DIR = os.getenv("SETTINGS_DIR", os.path.join(BASE_DIR, "settings"))
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
INTEGRATIONS_DIR = os.path.join(SETTINGS_DIR, "integrations")
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}


DEFAULT_SETTINGS = {
    "setup_complete": False,
    "admin_username": "",
    "admin_password": "",
    "brand_text": "IBM Expert Labs",
    "info_text": "IBM Expert Labs",
    "info_image": "",
    "default_page": "integrations",
    "page_settings": {
        "integrations": {"display_text": "Welcome to Integrations", "image": "", "image_width": 600, "image_height": 400},
        "reports": {"display_text": "Reports Overview", "image": "", "image_width": 600, "image_height": 400},
        "devices": {"display_text": "Devices Management", "image": "", "image_width": 600, "image_height": 400},
        "policies": {"display_text": "Policies Configuration", "image": "", "image_width": 600, "image_height": 400},
        "maps": {"display_text": "Diagrams", "image": "", "image_width": 600, "image_height": 400},
        "instant_graphs": {"display_text": "Instant Graphs", "image": "", "image_width": 600, "image_height": 400},
        "flow_explorer": {"display_text": "Flow Explorer", "image": "", "image_width": 600, "image_height": 400}
    },
    "integrations_settings": {
        "display_text": "Welcome to Integrations",
        "image": "",
        "image_width": 600,
        "image_height": 400
    },
    "menu_items": [
        {"id": "integrations", "label": "Integrations", "children": []},
        {"id": "reports", "label": "Reports", "children": []},
        {"id": "devices", "label": "Devices", "children": []},
        {"id": "policies", "label": "Policies", "children": []},
        {"id": "maps", "label": "Maps", "children": []},
        {"id": "instant_graphs", "label": "Instant Graphs", "children": []},
        {"id": "flow_explorer", "label": "Flow Explorer", "children": []},
        {"id": "configure", "label": "Configure", "children": ["General", "Connections"]},
        {"id": "administer", "label": "Administer", "children": ["Users", "Audit Logs"]},
    ],
    "reports_columns": [
        {"key": "name", "label": "Name"},
        {"key": "description", "label": "Description"},
        {"key": "folder", "label": "Folder"},
        {"key": "owner", "label": "Owner"},
        {"key": "last_updated", "label": "Last Updated"},
        {"key": "last_opened", "label": "Last Opened"},
    ],
}


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


def merge_defaults(defaults, existing):
    if not isinstance(existing, dict):
        return json.loads(json.dumps(defaults))

    merged = json.loads(json.dumps(defaults))
    for key, value in existing.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_defaults(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_settings():
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return json.loads(json.dumps(DEFAULT_SETTINGS))

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file_handle:
            loaded = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        loaded = {}

    return merge_defaults(DEFAULT_SETTINGS, loaded)


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(settings, file_handle, indent=2)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin/reports/<path:report_path>")
def report_view(report_path):
    """Serve index.html for report views to support SPA routing"""
    return render_template("index.html")


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify(load_settings())


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    payload = request.get_json(silent=True) or {}
    settings = load_settings()

    for key in ("brand_text", "info_text", "default_page", "menu_items", "reports_columns", "integrations_settings", "page_settings"):
        if key in payload:
            settings[key] = payload[key]

    save_settings(settings)
    return jsonify({"status": "success", "settings": settings})


@app.route("/api/users", methods=["GET"])
def api_get_users():
    """Return list of users. For now, returns the admin user from settings."""
    settings = load_settings()
    users = []
    
    if settings.get("setup_complete") and settings.get("admin_username"):
        users.append({
            "id": "admin",
            "username": settings["admin_username"],
            "email": settings.get("admin_email", ""),
            "role": "admin",
            "last_login": "2024-01-15 10:30:00"
        })
    
    return jsonify({"users": users})


@app.route("/api/users/<user_id>", methods=["PUT"])
def api_update_user(user_id):
    """Update user information."""
    payload = request.get_json(silent=True) or {}
    settings = load_settings()
    
    if user_id == "admin":
        # Update admin email
        if "email" in payload:
            settings["admin_email"] = payload["email"]
            save_settings(settings)
            return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "User not found"}), 404


@app.route("/api/setup", methods=["POST"])
def api_setup_admin():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    settings = load_settings()
    settings["setup_complete"] = True
    settings["admin_username"] = username
    settings["admin_password"] = password

    for key in ("brand_text", "info_text", "menu_items", "reports_columns"):
        if key in payload:
            settings[key] = payload[key]

    save_settings(settings)
    return jsonify({"status": "success", "message": "Admin user created successfully", "settings": settings})


@app.route("/api/upload", methods=["POST"])
def api_upload_info_image():
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"status": "error", "message": "No file was uploaded."}), 400
    if uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"status": "error", "message": "Only PNG, JPG, and JPEG files are supported."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    if extension == "jpeg":
        extension = "jpg"

    filename = f"info_icon.{extension}"
    uploaded_file.save(os.path.join(SETTINGS_DIR, filename))

    settings = load_settings()
    settings["info_image"] = filename
    save_settings(settings)

    return jsonify({"status": "success", "filename": filename})


@app.route("/api/upload-widget-image", methods=["POST"])
def api_upload_widget_image():
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"status": "error", "message": "No file was uploaded."}), 400
    if uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"status": "error", "message": "Only PNG, JPG, and JPEG files are supported."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    unique_name = f"widget_{int(os.times().elapsed * 1000)}.{extension}"
    destination = os.path.join(SETTINGS_DIR, unique_name)

    uploaded_file.save(destination)
    return jsonify({"status": "success", "filename": unique_name})


@app.route("/widget/<filename>")
def serve_widget_image(filename):
    """Serve widget images"""
    safe_name = secure_filename(filename)
    file_path = os.path.join(SETTINGS_DIR, safe_name)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Not found."}), 404
    return send_from_directory(SETTINGS_DIR, safe_name)


@app.route("/api/reports/<report_name>/widgets", methods=["GET"])
def get_report_widgets(report_name):
    """Get widgets for a specific report"""
    safe_name = secure_filename(report_name)
    widgets_file = os.path.join(SETTINGS_DIR, f"{safe_name}_widgets.json")
    
    try:
        if not os.path.exists(widgets_file):
            return jsonify({"widgets": [], "tabs": [{"id": "tab_1", "name": "Initial Tab"}]})
        
        with open(widgets_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure tabs exist, provide default if not
        tabs = data.get("tabs", [{"id": "tab_1", "name": "Initial Tab"}])
        return jsonify({"widgets": data.get("widgets", []), "tabs": tabs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/<report_name>/widgets", methods=["POST"])
def save_report_widgets(report_name):
    """Save widgets for a specific report"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    widgets = data.get("widgets", [])
    tabs = data.get("tabs", [{"id": "tab_1", "name": "Initial Tab"}])
    safe_name = secure_filename(report_name)
    widgets_file = os.path.join(SETTINGS_DIR, f"{safe_name}_widgets.json")
    
    try:
        with open(widgets_file, 'w', encoding='utf-8') as f:
            json.dump({"widgets": widgets, "tabs": tabs}, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/maps/<map_id>', methods=['PUT'])
def update_map(map_id):
    """Update a map"""
    try:
        data = request.get_json()
        maps_file = os.path.join(SETTINGS_DIR, 'mapsettings.json')
        
        if not os.path.exists(maps_file):
            return jsonify({"error": "No maps found"}), 404
        
        with open(maps_file, 'r', encoding='utf-8') as f:
            maps_data = json.load(f)
        
        # Find and update the map
        map_found = False
        for i, map_obj in enumerate(maps_data.get("maps", [])):
            if map_obj.get("id") == map_id:
                maps_data["maps"][i] = {
                    "id": map_id,
                    "name": data.get("name", map_obj.get("name")),
                    "description": data.get("description", map_obj.get("description", "")),
                    "type": data.get("type", map_obj.get("type")),
                    "nodes": data.get("nodes", []),
                    "resources": data.get("resources", []),
                    "created_at": map_obj.get("created_at"),
                    "updated_at": datetime.now().isoformat()
                }
                map_found = True
                break
        
        if not map_found:
            return jsonify({"error": "Map not found"}), 404
        
        # Save updated maps
        with open(maps_file, 'w', encoding='utf-8') as f:
            json.dump(maps_data, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/integrations/<integration_id>/audit-logs", methods=["GET"])
def api_get_audit_logs(integration_id):
    """Fetch audit logs from SevOne NMS via SSH"""
    import subprocess
    import re
    
    try:
        # Get integration details from metadata.json
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if not os.path.exists(metadata_file):
            return jsonify({"error": "Integration not found"}), 404
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Only process sevone-nms-rest integrations
        if metadata.get('type') != 'sevone-nms-rest':
            return jsonify({"logs": []})
        
        # Get IP address and username from settings
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id, {})
        
        ip_address = config.get('host')
        username = config.get('username', 'sevone')
        
        if not ip_address:
            return jsonify({"error": "IP address not configured in integration settings"}), 400
        
        # SSH and get audit logs using tail to limit output
        # Using tail to get last 100 lines to avoid overwhelming the system
        ssh_command = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            f'{username}@{ip_address}',
            'sudo tail -100 /var/log/sevone'
        ]
        
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return jsonify({"error": f"SSH command failed: {result.stderr}"}), 500
        
        # Parse audit logs
        logs = []
        log_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2})\s+\S+\s+SevOne-audit\[\d+\]:\s+%NMS-\d+-\d+:\s+(.+)'
        
        for line in result.stdout.strip().split('\n'):
            match = re.match(log_pattern, line)
            if match:
                timestamp_str = match.group(1)
                log_data_str = match.group(2)
                
                # Parse key-value pairs
                log_entry = {
                    'timestamp': timestamp_str,
                    'raw': line
                }
                
                # Extract key-value pairs
                kv_pattern = r'(\w+)="([^"]*)"'
                for kv_match in re.finditer(kv_pattern, log_data_str):
                    key = kv_match.group(1)
                    value = kv_match.group(2)
                    log_entry[key] = value
                
                # Build details string
                details_parts = []
                if log_entry.get('action'):
                    details_parts.append(f"Action: {log_entry['action']}")
                if log_entry.get('entityType'):
                    details_parts.append(f"Type: {log_entry['entityType']}")
                if log_entry.get('endPoint'):
                    details_parts.append(f"Endpoint: {log_entry['endPoint']}")
                if log_entry.get('userIp'):
                    details_parts.append(f"IP: {log_entry['userIp']}")
                
                log_entry['details'] = ' | '.join(details_parts) if details_parts else log_data_str
                
                logs.append(log_entry)
        
        return jsonify({"logs": logs})
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": "SSH connection timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload-integrations", methods=["POST"])
def api_upload_integrations_image():
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"status": "error", "message": "No file was uploaded."}), 400
    if uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"status": "error", "message": "Only PNG, JPG, and JPEG files are supported."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    if extension == "jpeg":
        extension = "jpg"

    filename = f"integration.{extension}"
    uploaded_file.save(os.path.join(SETTINGS_DIR, filename))

    settings = load_settings()
    if "integrations_settings" not in settings:
        settings["integrations_settings"] = {}
    settings["integrations_settings"]["image"] = filename
    save_settings(settings)

    return jsonify({"status": "success", "filename": filename})


@app.route("/api/upload-page/<page_id>", methods=["POST"])
def api_upload_page_image(page_id):
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"status": "error", "message": "No file was uploaded."}), 400
    if uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"status": "error", "message": "Only PNG, JPG, and JPEG files are supported."}), 400

    safe_name = secure_filename(uploaded_file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    if extension == "jpeg":
        extension = "jpg"

    filename = f"{page_id}.{extension}"
    uploaded_file.save(os.path.join(SETTINGS_DIR, filename))

    settings = load_settings()
    if "page_settings" not in settings:
        settings["page_settings"] = {}
    if page_id not in settings["page_settings"]:
        settings["page_settings"][page_id] = {}
    settings["page_settings"][page_id]["image"] = filename
    save_settings(settings)

    return jsonify({"status": "success", "filename": filename})

    settings = load_settings()
    if "integrations_settings" not in settings:
        settings["integrations_settings"] = {}
    settings["integrations_settings"]["image"] = filename
    save_settings(settings)

    return jsonify({"status": "success", "filename": filename})


@app.route("/info_icon.<string:extension>")
def serve_info_image(extension):
    normalized_extension = extension.lower()
    if normalized_extension == "jpeg":
        normalized_extension = "jpg"
    if normalized_extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"status": "error", "message": "Not found."}), 404

    filename = f"info_icon.{normalized_extension}"
    file_path = os.path.join(SETTINGS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Not found."}), 404

    return send_from_directory(SETTINGS_DIR, filename)


@app.route("/integration.<string:extension>")
def serve_integration_image(extension):
    normalized_extension = extension.lower()
    if normalized_extension == "jpeg":
        normalized_extension = "jpg"
    if normalized_extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"status": "error", "message": "Not found."}), 404

    filename = f"integration.{normalized_extension}"
    file_path = os.path.join(SETTINGS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Not found."}), 404

    return send_from_directory(SETTINGS_DIR, filename)


@app.route("/page-image/<page_id>.<string:extension>")
def serve_page_image(page_id, extension):
    normalized_extension = extension.lower()
    if normalized_extension == "jpeg":
        normalized_extension = "jpg"
    if normalized_extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"status": "error", "message": "Not found."}), 404

    filename = f"{page_id}.{normalized_extension}"
    file_path = os.path.join(SETTINGS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Not found."}), 404

    return send_from_directory(SETTINGS_DIR, filename)


@app.route("/api/integrations", methods=["GET"])
def api_list_integrations():
    """List all installed integrations"""
    if not os.path.exists(INTEGRATIONS_DIR):
        return jsonify({"integrations": []})
    
    integrations = []
    try:
        for integration_name in os.listdir(INTEGRATIONS_DIR):
            integration_path = os.path.join(INTEGRATIONS_DIR, integration_name)
            if not os.path.isdir(integration_path):
                continue
            
            # Look for metadata.json
            metadata_file = os.path.join(integration_path, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {"name": integration_name, "description": ""}
            
            # Look for icon file
            icon = None
            for ext in ["svg", "png", "jpg", "jpeg"]:
                icon_file = os.path.join(integration_path, f"icon.{ext}")
                if os.path.exists(icon_file):
                    icon = f"icon.{ext}"
                    break
            
            integrations.append({
                "id": integration_name,
                "name": metadata.get("name", integration_name),
                "description": metadata.get("description", ""),
                "type": metadata.get("type", integration_name),
                "icon": icon
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"integrations": integrations})


@app.route("/api/integrations/types", methods=["GET"])
def api_list_integration_types():
    """List available integration types (templates)"""
    if not os.path.exists(INTEGRATIONS_DIR):
        return jsonify({"types": []})
    
    types = []
    try:
        for integration_name in os.listdir(INTEGRATIONS_DIR):
            integration_path = os.path.join(INTEGRATIONS_DIR, integration_name)
            if not os.path.isdir(integration_path):
                continue
            
            # Look for metadata.json to get the base type info
            metadata_file = os.path.join(integration_path, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                
                # Only include base integration types (not instances)
                type_name = metadata.get("type", integration_name)
                if type_name not in [t["type"] for t in types]:
                    types.append({
                        "type": type_name,
                        "name": metadata.get("name", integration_name),
                        "description": metadata.get("description", ""),
                        "fields": metadata.get("fields", [])
                    })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"types": types})


@app.route("/api/integrations/create", methods=["POST"])
def api_create_integration():
    """Create a new integration instance from an existing type"""
    data = request.get_json()
    integration_type = data.get("type")
    name = data.get("name")
    description = data.get("description", "")
    
    if not integration_type or not name:
        return jsonify({"status": "error", "message": "Type and name are required."}), 400
    
    try:
        # Find the source integration directory
        source_path = os.path.join(INTEGRATIONS_DIR, integration_type)
        if not os.path.exists(source_path):
            return jsonify({"status": "error", "message": f"Integration type '{integration_type}' not found."}), 404
        
        # Generate a unique ID for the new instance
        base_id = integration_type
        instance_id = base_id
        counter = 2
        while os.path.exists(os.path.join(INTEGRATIONS_DIR, instance_id)):
            instance_id = f"{base_id}_{counter}"
            counter += 1
        
        # Create new instance directory
        target_path = os.path.join(INTEGRATIONS_DIR, instance_id)
        shutil.copytree(source_path, target_path)
        
        # Update metadata.json with new name and description
        metadata_file = os.path.join(target_path, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            metadata["name"] = name
            metadata["description"] = description
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        else:
            # Create new metadata file
            metadata = {
                "type": integration_type,
                "name": name,
                "description": description
            }
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        
        return jsonify({"status": "success", "message": f"Integration '{name}' created successfully.", "integration_id": instance_id})
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to create integration: {str(e)}"}), 500


@app.route("/api/integrations/upload", methods=["POST"])
def api_upload_integration():
    """Upload and extract a .tgz integration file"""
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"status": "error", "message": "No file was uploaded."}), 400
    if uploaded_file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400
    
    # Check if it's a .tgz file
    if not uploaded_file.filename.endswith(".tgz") and not uploaded_file.filename.endswith(".tar.gz"):
        return jsonify({"status": "error", "message": "Only .tgz files are supported."}), 400
    
    try:
        # Create integrations directory if it doesn't exist
        os.makedirs(INTEGRATIONS_DIR, exist_ok=True)
        
        # Get integration name from filename
        safe_filename = secure_filename(uploaded_file.filename)
        integration_name = safe_filename.replace(".tgz", "").replace(".tar.gz", "")
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_name)
        
        # Check if integration already exists
        if os.path.exists(integration_path):
            return jsonify({"status": "error", "message": f"Integration '{integration_name}' already exists."}), 400
        
        # Save the uploaded file temporarily
        temp_file = os.path.join(INTEGRATIONS_DIR, safe_filename)
        uploaded_file.save(temp_file)
        
        # Extract the .tgz file
        os.makedirs(integration_path, exist_ok=True)
        with tarfile.open(temp_file, "r:gz") as tar:
            tar.extractall(path=integration_path)
        
        # Remove the temporary .tgz file
        os.remove(temp_file)
        
        return jsonify({"status": "success", "message": f"Integration '{integration_name}' installed successfully.", "integration_id": integration_name})
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to install integration: {str(e)}"}), 500


@app.route("/api/integrations/<integration_id>", methods=["DELETE"])
def api_delete_integration(integration_id):
    """Delete an integration"""
    safe_id = secure_filename(integration_id)
    integration_path = os.path.join(INTEGRATIONS_DIR, safe_id)
    
    if not os.path.exists(integration_path):
        return jsonify({"status": "error", "message": "Integration not found."}), 404
    
    try:
        shutil.rmtree(integration_path)
        return jsonify({"status": "success", "message": f"Integration '{integration_id}' deleted successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete integration: {str(e)}"}), 500


@app.route("/integration-icon/<integration_id>/<filename>")
def serve_integration_icon(integration_id, filename):
    """Serve integration icon files"""
    safe_id = secure_filename(integration_id)
    integration_path = os.path.join(INTEGRATIONS_DIR, safe_id)
    
    if not os.path.exists(integration_path):
        return jsonify({"status": "error", "message": "Not found."}), 404
    
    file_path = os.path.join(integration_path, filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Not found."}), 404
    
    return send_from_directory(integration_path, filename)


@app.route("/api/integrations/<integration_id>/settings", methods=["GET"])
def get_integration_settings(integration_id):
    """Get settings for a specific integration"""
    settings = load_settings()
    integration_settings = settings.get("integration_configs", {}).get(integration_id, {})
    return jsonify({"settings": integration_settings})


@app.route("/api/integrations/<integration_id>/settings", methods=["POST"])
def save_integration_settings(integration_id):
    """Save settings for a specific integration"""
    try:
        data = request.get_json()
        settings = load_settings()
        
        if "integration_configs" not in settings:
            settings["integration_configs"] = {}
        
        settings["integration_configs"][integration_id] = data
        save_settings(settings)
        
        return jsonify({
            "status": "success",
            "message": f"Settings for '{integration_id}' saved successfully."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/integrations/<integration_id>/metrics", methods=["GET"])
def get_integration_metrics(integration_id):
    """Fetch metrics from an integration"""
    try:
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id, {})
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 400
        
        # Get integration type from metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if not host:
                return jsonify({"error": "Host not configured"}), 400
            
            if version == 'v3':
                api_key = config.get('api_key')
                if not api_key:
                    return jsonify({"error": "API key not configured"}), 400
                
                # Use SevOne API client
                try:
                    client = SevOneV3API(host=host, api_key=api_key)
                    device_list = client.get_device_list()
                    return jsonify({"metrics": device_list, "integration_type": "sevone-nms-rest"})
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Failed to fetch devices: {str(e)}"}), 500
            
            elif version == 'v2':
                # Handle v2 API if needed
                return jsonify({"error": "SevOne v2 API not yet supported for metrics"}), 400
        
        # Handle Ring integration
        elif integration_type == 'ring':
            # Get Ring devices from manual camera list
            cameras_text = config.get('cameras', '')
            
            print(f"DEBUG: Ring integration - checking for manually configured cameras")
            
            if not cameras_text or not cameras_text.strip():
                print("DEBUG: No cameras configured in Ring integration")
                return jsonify({"metrics": [], "integration_type": "ring"}), 200
            
            # Parse camera names from textarea (one per line)
            camera_names = [line.strip() for line in cameras_text.split('\n') if line.strip()]
            
            # Create device objects for each camera
            devices = []
            for idx, camera_name in enumerate(camera_names):
                device = {
                    'id': f"ring_camera_{idx}",
                    'name': camera_name,
                    'displayName': camera_name,
                    'type': 'camera',
                    'status': 'online',
                    'plugin': 'ring',
                    'is_ring': True
                }
                devices.append(device)
            
            print(f"DEBUG: Returning {len(devices)} Ring cameras")
            return jsonify({"metrics": devices, "integration_type": "ring"}), 200
        
        # Handle Apple Home (home-phill) integration via Homebridge
        elif integration_type == 'home-phill':
            homebridge_url = config.get('homebridge_url', '')
            username = config.get('username', '')
            password = config.get('password', '')
            
            if not all([homebridge_url, username, password]):
                return jsonify({"metrics": [], "integration_type": "home-phill"}), 200
            
            try:
                # Login to Homebridge
                login_url = f"{homebridge_url.rstrip('/')}/api/auth/login"
                login_response = requests.post(login_url, json={"username": username, "password": password}, timeout=5)
                
                if login_response.status_code not in [200, 201]:
                    print(f"Apple Home login failed: {login_response.status_code}")
                    return jsonify({"metrics": [], "integration_type": "home-phill", "error": f"Login failed: {login_response.status_code}"}), 200
                
                token = login_response.json().get('access_token')
                if not token:
                    return jsonify({"metrics": [], "integration_type": "home-phill", "error": "No token received"}), 200
                
                # Get all accessories
                accessories_url = f"{homebridge_url.rstrip('/')}/api/accessories"
                accessories_response = requests.get(accessories_url, headers={"Authorization": f"Bearer {token}"}, timeout=5)
                
                if accessories_response.status_code != 200:
                    return jsonify({"metrics": [], "integration_type": "home-phill", "error": "Failed to fetch devices"}), 200
                
                accessories = accessories_response.json()
                
                # Transform to device format and deduplicate by name
                seen_names = {}
                devices = []
                for acc in accessories:
                    device_name = acc.get('serviceName', 'Unknown Device')
                    
                    # Skip duplicates - only keep the first occurrence of each device name
                    if device_name in seen_names:
                        continue
                    
                    seen_names[device_name] = True
                    
                    device = {
                        'id': acc.get('uniqueId', acc.get('aid', f"device_{len(devices)}")),
                        'name': device_name,
                        'displayName': device_name,
                        'type': acc.get('type', 'accessory'),
                        'room': acc.get('roomName', ''),
                        'plugin': acc.get('plugin', ''),
                        'status': 'online' if acc.get('reachable', True) else 'offline'
                    }
                    devices.append(device)
                
                print(f"Apple Home: Returning {len(devices)} unique devices (deduplicated from {len(accessories)} accessories)")
                return jsonify({"metrics": devices, "integration_type": "home-phill"}), 200
                
            except Exception as e:
                print(f"Apple Home error: {str(e)}")
                return jsonify({"metrics": [], "integration_type": "home-phill", "error": str(e)}), 200
        
        # Handle Prometheus integration (default)
        else:
            host = config.get("host", "localhost")
            port = config.get("port", "9090")
            base_url = f"http://{host}:{port}"
            
            # Prepare auth if needed
            auth = None
            if config.get("requires_auth"):
                username = config.get("username", "")
                password = config.get("password", "")
                if username and password:
                    auth = (username, password)
            
            # Fetch label values to get metric names
            response = requests.get(
                f"{base_url}/api/v1/label/__name__/values",
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    metrics = data.get("data", [])
                    return jsonify({"metrics": metrics})
            
            return jsonify({"error": "Failed to fetch metrics from Prometheus"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/objects', methods=['GET'])
def get_integration_objects(integration_id):
    """Fetch objects for a specific device from SevOne integration"""
    try:
        device_id = request.args.get('deviceId')
        if not device_id:
            return jsonify({"error": "deviceId parameter required"}), 400
        
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id, {})
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 400
        
        # Get integration type from metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if not host:
                return jsonify({"error": "Host not configured"}), 400
            
            if version == 'v3':
                api_key = config.get('api_key')
                if not api_key:
                    return jsonify({"error": "API key not configured"}), 400
                
                # Use SevOne API client
                try:
                    client = SevOneV3API(host=host, api_key=api_key)
                    object_list = client.get_object_list(int(device_id))
                    return jsonify({"objects": object_list})
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Failed to fetch objects: {str(e)}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported for objects"}), 400
        else:
            return jsonify({"error": "Objects not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/indicators', methods=['POST'])
def get_integration_indicators(integration_id):
    """Fetch indicators for a specific device from SevOne integration"""
    try:
        data = request.get_json()
        device_name = data.get('deviceName')
        object_name = data.get('objectName')  # Optional object filter
        
        if not device_name:
            return jsonify({"error": "deviceName required"}), 400
        
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id, {})
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 400
        
        # Get integration type from metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if not host:
                return jsonify({"error": "Host not configured"}), 400
            
            if version == 'v3':
                api_key = config.get('api_key')
                if not api_key:
                    return jsonify({"error": "API key not configured"}), 400
                
                # Use SevOne API client
                try:
                    client = SevOneV3API(host=host, api_key=api_key)
                    indicator_list = client.get_indicator_list(device_name, object_name)
                    return jsonify({"indicators": indicator_list})
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Failed to fetch indicators: {str(e)}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported for indicators"}), 400
        else:
            return jsonify({"error": "Indicators not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/data', methods=['POST'])
def get_integration_data(integration_id):
    """Fetch time-series data from integration"""
    try:
        # Load integration settings from main settings.json
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        # Get integration type from the integration directory metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle different integration types
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            # Get request parameters
            data = request.get_json() or {}
            indicator_id = data.get('indicatorId')
            device_id = data.get('deviceId')
            object_id = data.get('objectId')
            
            # Default to last 1 hour if not specified
            end_time = data.get('endTime', int(time.time() * 1000))  # milliseconds
            start_time = data.get('startTime', end_time - 3600000)  # 1 hour ago
            
            if not indicator_id:
                return jsonify({"error": "indicatorId is required"}), 400
            
            if version == 'v3':
                # Use API key authentication for v3
                api_key = config.get('api_key')
                headers = {
                    'X-API-KEY': api_key,
                    'Content-Type': 'application/json'
                }
                
                # Build request for performance metrics
                url = f"http://{host}/api/v3/data/performance_metrics"
                
                # Request body for SevOne data API
                request_body = {
                    "indicatorIds": [int(indicator_id)],
                    "startTime": start_time,
                    "endTime": end_time
                }
                
                # Add device and object filters if provided
                if device_id:
                    request_body["deviceIds"] = [int(device_id)]
                if object_id:
                    request_body["objectIds"] = [int(object_id)]
                
                response = requests.post(url, headers=headers, json=request_body, verify=False, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    # Transform SevOne data format to match what frontend expects
                    # SevOne returns data in format that needs to be converted to ECharts format
                    return jsonify({"data": data, "integration_type": "sevone-nms-rest"})
                else:
                    return jsonify({"error": f"Failed to fetch data: {response.status_code}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported for data"}), 400
        else:
            return jsonify({"error": "Data fetching not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/device/<device_id>/raw', methods=['GET'])
def get_device_raw_data(integration_id, device_id):
    """Fetch raw device metadata from SevOne API"""
    try:
        # Load integration settings from main settings.json
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        # Get integration type from the integration directory metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if version == 'v3':
                api_key = config.get('api_key')
                headers = {
                    'Accept': 'application/json',
                    'Authorization': f'apikey {api_key}'
                }
                
                # Fetch all devices metadata
                url = f"http://{host}/api/v3/metadata/devices/metadata"
                response = requests.get(url, headers=headers, verify=False, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    devices = data.get('devices', {})
                    
                    # Find the specific device
                    device_data = None
                    for dev in devices.values():
                        if str(dev.get('id')) == str(device_id):
                            device_data = dev
                            break
                    
                    if device_data:
                        return jsonify(device_data)
                    else:
                        return jsonify({"error": f"Device {device_id} not found"}), 404
                else:
                    return jsonify({"error": f"Failed to fetch devices: {response.status_code}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported"}), 400
        else:
            return jsonify({"error": "Raw device data not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/alerts', methods=['GET'])
def get_integration_alerts(integration_id):
    """Fetch alerts from SevOne integration"""
    try:
        # Load integration settings from main settings.json
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        # Get integration type from the integration directory metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if version == 'v3':
                api_key = config.get('api_key')
                
                # Use SevOne API client
                try:
                    client = SevOneV3API(host=host, api_key=api_key)
                    alert_counts = client.count_alerts_by_device(alert_status='OPEN')
                    
                    # Get total alerts for logging
                    alerts_data = client.get_alerts(alert_status='OPEN')
                    total_alerts = len(alerts_data.get('alerts', []))
                    
                    print(f"Alert counts by device name: {alert_counts}")
                    print(f"Total alerts: {total_alerts}")
                    
                    return jsonify({"alert_counts": alert_counts, "total_alerts": total_alerts})
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Failed to fetch alerts: {str(e)}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported"}), 400
        else:
            return jsonify({"error": "Alerts not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/alerts/details', methods=['GET'])
def get_integration_alerts_details(integration_id):
    """Fetch detailed alerts from SevOne integration for Alert Details widget"""
    try:
        # Load integration settings from main settings.json
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        # Get integration type from the integration directory metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if version == 'v3':
                api_key = config.get('api_key')
                
                # Use SevOne API client to get full alerts
                try:
                    client = SevOneV3API(host=host, api_key=api_key)
                    alerts_data = client.get_alerts(alert_status='OPEN')
                    alerts = alerts_data.get('alerts', [])
                    
                    # Format alerts for display
                    formatted_alerts = []
                    for alert in alerts:
                        device = alert.get('device', {})
                        policy = alert.get('policy', {})
                        
                        formatted_alerts.append({
                            'id': alert.get('id'),
                            'deviceName': device.get('displayName') or device.get('name', 'Unknown'),
                            'policyName': policy.get('name', 'Unknown'),
                            'severity': alert.get('severity', 'UNKNOWN'),
                            'message': alert.get('message', ''),
                            'startTime': alert.get('startTime', ''),
                            'origin': alert.get('origin', 'Unknown')
                        })
                    
                    return jsonify({"alerts": formatted_alerts})
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Failed to fetch alerts: {str(e)}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported"}), 400
        else:
            return jsonify({"error": "Alerts not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/policies', methods=['GET'])
def get_integration_policies(integration_id):
    """Fetch policies from SevOne integration"""
    try:
        # Load integration settings from main settings.json
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id, {})
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 400
        
        # Get integration type from metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle SevOne NMS REST integration
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if version == 'v3':
                api_key = config.get('api_key')
                
                # Use SevOne API client
                try:
                    client = SevOneV3API(host=host, api_key=api_key)
                    policy_list = client.get_policy_list()
                    return jsonify({"policies": policy_list})
                except requests.exceptions.RequestException as e:
                    return jsonify({"error": f"Failed to fetch policies: {str(e)}"}), 500
            
            elif version == 'v2':
                return jsonify({"error": "SevOne v2 API not yet supported"}), 400
        else:
            return jsonify({"error": "Policies not supported for this integration type"}), 400
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/policies/<policy_id>', methods=['DELETE'])
def delete_policy(integration_id, policy_id):
    """Delete a policy from SevOne"""
    try:
        # Load integration settings
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        host = config.get('host')
        api_key = config.get('api_key')
        
        if not host or not api_key:
            return jsonify({"error": "Integration not properly configured"}), 400
        
        # Delete the policy
        client = SevOneV3API(host=host, api_key=api_key)
        client.delete_policy(policy_id)
        
        return jsonify({"success": True}), 200
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/integrations/<integration_id>/test', methods=['POST'])
def test_integration(integration_id):
    """Test an integration connection by making a test API call"""
    try:
        # Load integration settings from main settings.json
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"success": False, "error": "Integration not configured"}), 404
        
        # Get integration type from the integration directory metadata
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        metadata_file = os.path.join(integration_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                integration_type = metadata.get('type', integration_id)
        else:
            integration_type = integration_id
        
        # Handle different integration types
        if integration_type == 'sevone-nms-rest':
            host = config.get('host')
            version = config.get('version', 'v2')
            
            if not host:
                return jsonify({"success": False, "error": "Host not configured"}), 400
            
            if version == 'v3':
                api_key = config.get('api_key')
                if not api_key:
                    return jsonify({"success": False, "error": "API key not configured"}), 400
                
                # Test SevOne v3 API
                url = f"http://{host}/api/v3/statistics/cluster?filter.timeFrame=ALL"
                headers = {
                    'Accept': 'application/json',
                    'Authorization': f'apikey {api_key}'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return jsonify({
                        "success": True,
                        "data": response.json()
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": f"API returned status {response.status_code}: {response.text}"
                    }), 200
                    
            elif version == 'v2':
                username = config.get('username')
                password = config.get('password')
                
                if not username or not password:
                    return jsonify({"success": False, "error": "Username and password not configured"}), 400
                
                # Test SevOne v2 API (adjust endpoint as needed for v2)
                url = f"http://{host}/api/v2/authentication/signin"
                auth = (username, password)
                
                response = requests.post(url, auth=auth, timeout=10)
                
                if response.status_code == 200:
                    return jsonify({
                        "success": True,
                        "data": response.json()
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": f"API returned status {response.status_code}: {response.text}"
                    }), 200
        
        elif integration_type == 'prometheus':
            # Test Prometheus connection
            host = config.get('host', 'localhost')
            port = config.get('port', '9090')
            base_url = f"http://{host}:{port}"
            
            auth = None
            if config.get('requires_auth'):
                username = config.get('username', '')
                password = config.get('password', '')
                if username and password:
                    auth = (username, password)
            
            response = requests.get(
                f"{base_url}/api/v1/status/config",
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                return jsonify({
                    "success": True,
                    "data": response.json()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"API returned status {response.status_code}: {response.text}"
                }), 200
        
        else:
            return jsonify({
                "success": False,
                "error": f"Testing not supported for integration type: {integration_type}"
            }), 400
            
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Connection timeout"}), 200
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "error": "Could not connect to host"}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Request error: {str(e)}"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@app.route('/api/integrations/<integration_id>/download', methods=['GET'])
def download_integration(integration_id):
    """Download an integration directory as a zip file"""
    try:
        import zipfile
        import io
        from flask import send_file
        
        # Get the integration directory path
        integration_path = os.path.join(INTEGRATIONS_DIR, integration_id)
        
        if not os.path.exists(integration_path):
            return jsonify({"error": "Integration not found"}), 404
        
        # Create a zip file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the integration directory
            for root, dirs, files in os.walk(integration_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate the archive name (relative path from integration directory)
                    arcname = os.path.relpath(file_path, integration_path)
                    zipf.write(file_path, arcname)
        
        # Seek to the beginning of the BytesIO object
        memory_file.seek(0)
        
        # Send the file
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{integration_id}.zip'
        )
        
    except Exception as e:
        return jsonify({"error": f"Failed to download integration: {str(e)}"}), 500

@app.route('/api/integrations/<integration_id>/settings', methods=['GET'])
def get_homebridge_settings(integration_id):
    """Fetch settings from Homebridge integration"""
    try:
        # Load integration settings
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        api_url = config.get('api_url')
        access_token = config.get('access_token')
        username = config.get('username')
        password = config.get('password')
        
        if not api_url:
            return jsonify({"error": "API URL is required"}), 400
        
        if not access_token and (not username or not password):
            return jsonify({"error": "Either access token or username/password is required"}), 400
        
        # Remove trailing slash and common suffixes like /swagger
        api_url = api_url.rstrip('/')
        if api_url.endswith('/swagger'):
            api_url = api_url[:-8]
        
        # If no access token provided, login to get one
        if not access_token:
            login_url = f"{api_url}/api/auth/login"
            login_payload = {
                "username": username,
                "password": password
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            login_response = requests.post(login_url, json=login_payload, headers=headers, timeout=10)
            
            if login_response.status_code != 201:
                return jsonify({"error": f"Login failed with status {login_response.status_code}. Check API URL, username, and password."}), 400
            
            login_data = login_response.json()
            access_token = login_data.get('access_token')
            
            if not access_token:
                return jsonify({"error": "No access token received"}), 400
        
        # Step 2: Fetch settings using the token
        settings_url = f"{api_url}/api/auth/settings"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        settings_response = requests.get(settings_url, headers=headers, timeout=10)
        
        if settings_response.status_code != 200:
            return jsonify({"error": f"Failed to fetch settings: {settings_response.text}"}), 400
        
        settings_data = settings_response.json()
        
        return jsonify({
            "success": True,
            "data": settings_data
        })
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Connection timeout"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Homebridge API"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/api/integrations/<integration_id>/pairings', methods=['GET'])
def get_homebridge_pairings(integration_id):
    """Fetch pairings from Homebridge integration"""
    try:
        # Load integration settings
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        api_url = config.get('api_url')
        access_token = config.get('access_token')
        username = config.get('username')
        password = config.get('password')
        
        print(f"DEBUG Pairings: api_url={api_url}, has_token={bool(access_token)}, token_length={len(access_token) if access_token else 0}, username={username}")
        
        if not api_url:
            return jsonify({"error": "API URL is required"}), 400
        
        if not access_token and (not username or not password):
            return jsonify({"error": "Either access token or username/password is required"}), 400
        
        # Remove trailing slash and common suffixes like /swagger
        api_url = api_url.rstrip('/')
        if api_url.endswith('/swagger'):
            api_url = api_url[:-8]
        
        # If no access token provided, login to get one
        if not access_token:
            login_url = f"{api_url}/api/auth/login"
            login_payload = {
                "username": username,
                "password": password
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            login_response = requests.post(login_url, json=login_payload, headers=headers, timeout=10)
            
            if login_response.status_code != 201:
                return jsonify({"error": f"Login failed with status {login_response.status_code}. API URL: {api_url}"}), login_response.status_code
            
            login_data = login_response.json()
            access_token = login_data.get('access_token')
            
            if not access_token:
                return jsonify({"error": "No access token received"}), 400
        
        # Step 2: Fetch pairings using the token
        pairings_url = f"{api_url}/api/server/pairings"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        pairings_response = requests.get(pairings_url, headers=headers, timeout=10)
        
        # Return whatever the response is, regardless of status code
        return jsonify(pairings_response.json()), pairings_response.status_code
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Connection timeout"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Homebridge API"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/api/integrations/<integration_id>/server-information', methods=['GET'])
def get_homebridge_server_info(integration_id):
    """Fetch server information from Homebridge integration"""
    try:
        # Load integration settings
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        api_url = config.get('api_url')
        access_token = config.get('access_token')
        username = config.get('username')
        password = config.get('password')
        
        if not api_url:
            return jsonify({"error": "API URL is required"}), 400
        
        if not access_token and (not username or not password):
            return jsonify({"error": "Either access token or username/password is required"}), 400
        
        # Remove trailing slash and common suffixes like /swagger
        api_url = api_url.rstrip('/')
        if api_url.endswith('/swagger'):
            api_url = api_url[:-8]
        
        # If no access token provided, login to get one
        if not access_token:
            login_url = f"{api_url}/api/auth/login"
            login_payload = {
                "username": username,
                "password": password
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            login_response = requests.post(login_url, json=login_payload, headers=headers, timeout=10)
            
            if login_response.status_code != 201:
                return jsonify({"error": f"Login failed with status {login_response.status_code}"}), login_response.status_code
            
            login_data = login_response.json()
            access_token = login_data.get('access_token')
            
            if not access_token:
                return jsonify({"error": "No access token received"}), 400
        
        # Fetch server information using the token
        server_info_url = f"{api_url}/api/status/server-information"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        server_info_response = requests.get(server_info_url, headers=headers, timeout=10)
        
        # Return whatever the response is, regardless of status code
        try:
            return jsonify(server_info_response.json()), server_info_response.status_code
        except ValueError:
            # If response is not JSON, return the text
            return jsonify({"response": server_info_response.text}), server_info_response.status_code
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Connection timeout"}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Homebridge API"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/api/integrations/<integration_id>/accessories', methods=['GET'])
def get_homebridge_accessories(integration_id):
    """Fetch accessories (devices) from Homebridge, including Ring devices"""
    try:
        # Load integration settings
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        # Support both new api_url format and old host/port format
        api_url = config.get('api_url')
        if not api_url:
            host = config.get('host', 'localhost')
            port = config.get('port', '8581')
            # Replace localhost with host.containers.internal when running in container
            if host == 'localhost':
                host = 'host.containers.internal'
            api_url = f"http://{host}:{port}"
        else:
            # Replace localhost in api_url with host.containers.internal for container networking
            api_url = api_url.replace('://localhost:', '://host.containers.internal:')
        
        access_token = config.get('access_token')
        username = config.get('username')
        password = config.get('password')
        
        if not api_url:
            return jsonify({"error": "API URL is required"}), 400
        
        if not access_token and (not username or not password):
            # Return empty devices list if Homebridge not fully configured yet
            return jsonify({"devices": [], "integration_type": "homebridge"})
        
        # Remove trailing slash and common suffixes like /swagger
        api_url = api_url.rstrip('/')
        if api_url.endswith('/swagger'):
            api_url = api_url[:-8]
        
        # If no access token provided, login to get one
        if not access_token:
            login_url = f"{api_url}/api/auth/login"
            login_payload = {
                "username": username,
                "password": password
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            try:
                login_response = requests.post(login_url, json=login_payload, headers=headers, timeout=5)
                
                if login_response.status_code != 201:
                    print(f"Homebridge login failed: {login_response.status_code}")
                    return jsonify({"devices": [], "integration_type": "homebridge", "error": f"Login failed: {login_response.status_code}"})
                
                login_data = login_response.json()
                access_token = login_data.get('access_token')
                
                if not access_token:
                    return jsonify({"devices": [], "integration_type": "homebridge", "error": "No access token received"})
            except requests.exceptions.ConnectionError:
                print(f"Cannot connect to Homebridge at {api_url}")
                return jsonify({"devices": [], "integration_type": "homebridge", "error": f"Cannot connect to Homebridge at {api_url}"})
            except requests.exceptions.Timeout:
                return jsonify({"devices": [], "integration_type": "homebridge", "error": "Connection timeout"})
        
        # Fetch accessories using the token
        accessories_url = f"{api_url}/api/accessories"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            accessories_response = requests.get(accessories_url, headers=headers, timeout=5)
            
            if accessories_response.status_code != 200:
                return jsonify({"devices": [], "integration_type": "homebridge", "error": f"Failed to fetch accessories: {accessories_response.status_code}"})
            
            accessories_data = accessories_response.json()
            
            # Transform accessories into device format
            devices = []
            for accessory in accessories_data:
                # Check if this is a Ring device
                plugin_name = accessory.get('plugin', '').lower()
                is_ring = 'ring' in plugin_name
                
                device = {
                    'id': accessory.get('uniqueId', accessory.get('aid', f"hb_{len(devices)}")),
                    'name': accessory.get('serviceName', 'Unknown Device'),
                    'displayName': accessory.get('serviceName', 'Unknown Device'),
                    'type': accessory.get('type', 'accessory'),
                    'plugin': accessory.get('plugin', ''),
                    'status': 'online' if accessory.get('reachable', True) else 'offline',
                    'room': accessory.get('roomName', ''),
                    'is_ring': is_ring
                }
                devices.append(device)
            
            print(f"Homebridge returned {len(devices)} devices ({sum(1 for d in devices if d.get('is_ring'))} Ring devices)")
            return jsonify({"devices": devices, "integration_type": "homebridge"})
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to Homebridge at {api_url}")
            return jsonify({"devices": [], "integration_type": "homebridge", "error": f"Cannot connect to Homebridge"})
        except requests.exceptions.Timeout:
            return jsonify({"devices": [], "integration_type": "homebridge", "error": "Connection timeout"})
        
    except Exception as e:
        print(f"Error in get_homebridge_accessories: {str(e)}")
        return jsonify({"devices": [], "integration_type": "homebridge", "error": f"Unexpected error: {str(e)}"})

@app.route('/api/proxy-prometheus', methods=['POST'])
def proxy_prometheus():
    """Proxy Prometheus API requests to handle CORS and authentication"""
    try:
        data = request.get_json()
        url = data.get('url')
        integration_id = data.get('integration_id')
        
        if not url or not integration_id:
            return jsonify({"error": "Missing url or integration_id"}), 400
        
        # Get integration config
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration_id)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 400
        
        # Prepare auth if needed
        auth = None
        if config.get("requires_auth"):
            username = config.get("username", "")
            password = config.get("password", "")
            if username and password:
                auth = (username, password)
        
        # Make the request to Prometheus
        response = requests.get(url, auth=auth, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Prometheus returned status {response.status_code}"}), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports", methods=["GET"])
def get_reports():
    """Get all reports"""
    reports_file = os.path.join(SETTINGS_DIR, "reports.json")
    try:
        if not os.path.exists(reports_file):
            return jsonify({"reports": []})
        
        with open(reports_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({"reports": data.get("reports", [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports", methods=["POST"])
def create_report():
    """Create a new report"""
    from datetime import datetime
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    integration_id = data.get("integrationId", "").strip()
    
    if not name:
        return jsonify({"error": "Report name is required"}), 400
    
    # Get current user from session/settings
    settings = load_settings()
    owner = settings.get("admin_username", "admin")
    
    # Create report object
    timestamp = datetime.utcnow().isoformat() + "Z"
    report = {
        "id": f"report_{int(datetime.utcnow().timestamp() * 1000)}",
        "name": name,
        "description": description,
        "integration_id": integration_id,
        "folder": "/",
        "owner": owner,
        "last_updated": timestamp,
        "last_opened": timestamp
    }
    
    # Load existing reports
    reports_file = os.path.join(SETTINGS_DIR, "reports.json")
    try:
        if os.path.exists(reports_file):
            with open(reports_file, 'r', encoding='utf-8') as f:
                reports_data = json.load(f)
        else:
            reports_data = {"reports": []}
        
        # Add new report
        reports_data["reports"].append(report)
        
        # Save reports
        with open(reports_file, 'w', encoding='utf-8') as f:
            json.dump(reports_data, f, indent=2)
        
        return jsonify({"success": True, "report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/delete", methods=["POST"])
def delete_reports():
    """Delete selected reports"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    report_ids = data.get("reportIds", [])
    if not report_ids:
        return jsonify({"error": "No report IDs provided"}), 400
    
    reports_file = os.path.join(SETTINGS_DIR, "reports.json")
    try:
        if not os.path.exists(reports_file):
            return jsonify({"error": "No reports found"}), 404
        
        with open(reports_file, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)
        
        # Filter out deleted reports
        original_count = len(reports_data.get("reports", []))
        reports_data["reports"] = [
            r for r in reports_data.get("reports", []) 
            if r.get("id") not in report_ids
        ]
        deleted_count = original_count - len(reports_data["reports"])
        
        # Save updated reports
        with open(reports_file, 'w', encoding='utf-8') as f:
            json.dump(reports_data, f, indent=2)
        
        return jsonify({"success": True, "deleted": deleted_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/markdown-files", methods=["GET"])
def list_markdown_files():
    """List all .md files in the parent directory"""
    try:
        md_files = []
        for filename in os.listdir(BASE_DIR):
            if filename.endswith('.md'):
                md_files.append(filename)
        return jsonify({"files": sorted(md_files)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/markdown/<filename>", methods=["GET"])
def get_markdown_file(filename):
    """Get the content of a markdown file"""
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename.endswith('.md'):
            return jsonify({"error": "Only .md files are allowed"}), 400
        
        file_path = os.path.join(BASE_DIR, safe_filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({"filename": safe_filename, "content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/maps', methods=['GET'])
def get_maps():
    """Get all maps"""
    try:
        maps_file = os.path.join(SETTINGS_DIR, 'mapsettings.json')
        if not os.path.exists(maps_file):
            return jsonify({"maps": []})
        
        with open(maps_file, 'r', encoding='utf-8') as f:
            maps_data = json.load(f)
        
        return jsonify({"maps": maps_data.get("maps", [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/maps', methods=['POST'])
def create_map():
    """Create a new map"""
    try:
        data = request.get_json()
        maps_file = os.path.join(SETTINGS_DIR, 'mapsettings.json')
        
        # Load existing maps or create new structure
        if os.path.exists(maps_file):
            with open(maps_file, 'r', encoding='utf-8') as f:
                maps_data = json.load(f)
        else:
            maps_data = {"maps": []}
        
        # Generate new map ID
        map_id = str(len(maps_data.get("maps", [])) + 1)
        
        # Create new map
        new_map = {
            "id": map_id,
            "name": data.get("name", "New Map"),
            "description": data.get("description", ""),
            "type": data.get("type", "Device"),
            "nodes": data.get("nodes", []),
            "resources": data.get("resources", []),
            "edges": data.get("edges", []),
            "created_at": datetime.now().isoformat()
        }
        
        maps_data["maps"].append(new_map)
        
        # Save to file
        with open(maps_file, 'w', encoding='utf-8') as f:
            json.dump(maps_data, f, indent=2)
        
        return jsonify({"success": True, "map": new_map})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/camera/snapshot', methods=['GET'])
def get_camera_snapshot():
    """Get camera snapshot from Ring via Homebridge refresh token"""
    try:
        import base64
        from io import BytesIO
        
        integration = request.args.get('integration', 'home-phill')
        camera_name = request.args.get('camera')
        
        if not camera_name:
            return jsonify({"error": "Camera name required"}), 400
        
        # Load settings to get Homebridge credentials
        settings = load_settings()
        config = settings.get("integration_configs", {}).get(integration)
        
        if not config:
            return jsonify({"error": "Integration not configured"}), 404
        
        homebridge_url = config.get("homebridge_url", "").rstrip('/')
        username = config.get("username", "")
        password = config.get("password", "")
        
        if not all([homebridge_url, username, password]):
            return jsonify({"error": "Incomplete Homebridge configuration"}), 400
        
        # Authenticate with Homebridge to get Ring refresh token from config
        login_url = f"{homebridge_url}/api/auth/login"
        login_response = requests.post(
            login_url,
            json={"username": username, "password": password},
            timeout=10
        )
        
        if login_response.status_code != 201:
            return jsonify({"error": f"Authentication failed: {login_response.status_code}"}), 401
        
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return jsonify({"error": "No authentication token received"}), 401
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get Homebridge config to extract Ring refresh token
        config_url = f"{homebridge_url}/api/config-editor"
        config_response = requests.get(config_url, headers=headers, timeout=10)
        
        if config_response.status_code != 200:
            return jsonify({"error": "Failed to fetch Homebridge config"}), 500
        
        homebridge_config = config_response.json()
        
        # Find Ring platform config
        ring_platform = None
        for platform in homebridge_config.get('platforms', []):
            if 'ring' in platform.get('platform', '').lower():
                ring_platform = platform
                break
        
        if not ring_platform or 'refreshToken' not in ring_platform:
            return jsonify({"error": "Ring refresh token not found in Homebridge config"}), 404
        
        refresh_token = ring_platform['refreshToken']
        
        # Authenticate with Ring API using refresh token
        ring_auth_url = "https://oauth.ring.com/oauth/token"
        ring_auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": "ring_official_android"
        }
        
        ring_auth_response = requests.post(ring_auth_url, json=ring_auth_data, timeout=10)
        
        if ring_auth_response.status_code != 200:
            return jsonify({"error": f"Ring authentication failed: {ring_auth_response.status_code}"}), 401
        
        ring_tokens = ring_auth_response.json()
        ring_access_token = ring_tokens.get("access_token")
        
        if not ring_access_token:
            return jsonify({"error": "No Ring access token received"}), 401
        
        # Get Ring devices
        ring_headers = {"Authorization": f"Bearer {ring_access_token}"}
        devices_url = "https://api.ring.com/clients_api/ring_devices"
        devices_response = requests.get(devices_url, headers=ring_headers, timeout=10)
        
        if devices_response.status_code != 200:
            return jsonify({"error": "Failed to fetch Ring devices"}), 500
        
        devices_data = devices_response.json()
        
        # Find the camera in the devices list
        camera_device = None
        for device_type in ['doorbots', 'stickup_cams', 'authorized_doorbots']:
            for device in devices_data.get(device_type, []):
                if device.get('description') == camera_name:
                    camera_device = device
                    break
            if camera_device:
                break
        
        if not camera_device:
            return jsonify({"error": f"Camera '{camera_name}' not found in Ring account"}), 404
        
        device_id = camera_device.get('id')
        
        # Request snapshot from Ring
        snapshot_url = f"https://api.ring.com/clients_api/snapshots/image/{device_id}"
        snapshot_response = requests.get(snapshot_url, headers=ring_headers, timeout=30)
        
        if snapshot_response.status_code == 200:
            # Return the actual Ring camera snapshot
            return snapshot_response.content, 200, {
                'Content-Type': 'image/jpeg',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        else:
            return jsonify({"error": f"Failed to get snapshot: {snapshot_response.status_code}"}), 500
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Connection timeout"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to Homebridge"}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/api/maps/<map_id>', methods=['DELETE'])
def delete_map(map_id):
    """Delete a map"""
    try:
        maps_file = os.path.join(SETTINGS_DIR, 'mapsettings.json')
        if not os.path.exists(maps_file):
            return jsonify({"error": "No maps found"}), 404
        
        with open(maps_file, 'r', encoding='utf-8') as f:
            maps_data = json.load(f)
        
        # Filter out the deleted map
        original_count = len(maps_data.get("maps", []))
        maps_data["maps"] = [m for m in maps_data.get("maps", []) if m.get("id") != map_id]
        
        if original_count == len(maps_data.get("maps", [])):
            return jsonify({"error": "Map not found"}), 404
        
        # Save updated maps
        with open(maps_file, 'w', encoding='utf-8') as f:
            json.dump(maps_data, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
