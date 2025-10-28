# SmartGallery Configuration Migration Guide

## Overview
SmartGallery has been upgraded to a fully configurable ComfyUI custom node with an integrated settings panel. No more manual path editing!

## What Changed?

### 1. **Auto-Detection of Paths**
SmartGallery now automatically detects your ComfyUI installation paths using ComfyUI's official `folder_paths` API:
- `output/` folder
- `input/` folder

**This works correctly with ALL ComfyUI configurations**, including:
- ✅ Standard installations (Manual, Manager, Portable, Desktop)
- ✅ Custom node paths via `--custom-nodes-path` argument
- ✅ Alternative paths configured in `extra_model_paths.yaml`
- ✅ Symlinked or network-mounted directories
- ✅ Docker containers and multi-instance setups

You only need to manually configure paths if you want to override ComfyUI's defaults.

### 2. **ComfyUI Settings Integration**
All configuration is now managed through ComfyUI's built-in settings panel:
1. Open ComfyUI
2. Click the Settings icon (⚙️)
3. Find the `[SmartGallery]` section
4. Adjust settings as needed
5. Restart ComfyUI

### 3. **Configuration File**
Settings are stored in `config.json` in the SmartGallery folder. This file is created automatically when you save settings through the UI.

**Example `config.json`:**
```json
{
    "base_output_path": "",
    "base_input_path": "",
    "server_port": 8008,
    "ffprobe_manual_path": ""
}
```

**Note:** Empty path values (`""`) trigger auto-detection.

### 4. **Command-Line Architecture**
The Flask server (`smartgallery.py`) now accepts command-line arguments:
```bash
python smartgallery.py --output-path /path/to/output --input-path /path/to/input --port 8008
```

This is handled automatically by `__init__.py` when ComfyUI starts.

## Available Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **ComfyUI Output Path** | Path to your ComfyUI output folder | Auto-detected |
| **ComfyUI Input Path** | Path to your ComfyUI input folder | Auto-detected |
| **Gallery Server Port** | Port for the web gallery | `8008` |
| **FFprobe Path** | Optional path to ffprobe.exe for video metadata | Auto-detected |

## Migration from v1.30

If you previously edited `smartgallery.py` directly to set paths:

1. **Delete your old changes** - The hardcoded configuration section has been removed
2. **Restart ComfyUI** - Paths will auto-detect on first run
3. **Optional**: Configure custom paths via Settings panel if needed
4. **Restart again** for changes to take effect

## Troubleshooting

### Gallery doesn't start
- Check the ComfyUI console for error messages
- Verify `config.json` is valid JSON (use `config.json.example` as reference)
- Ensure paths exist and are accessible

### Wrong paths detected
- Open ComfyUI Settings → `[SmartGallery]` section
- Set the correct paths manually
- Restart ComfyUI

### Port conflict
- If port 8008 is already in use, change it in Settings
- Must be different from ComfyUI's port (usually 8188)

### Settings won't save
- Check file permissions in the SmartGallery folder
- Look for error messages in the browser console (F12)
- Verify `__init__.py` correctly imports `server` and `web` modules

## Benefits of the New System

✅ **Zero Configuration**: Works out of the box for standard ComfyUI installations  
✅ **User-Friendly**: All settings in one place, no code editing required  
✅ **Portable**: Easy to deploy across multiple ComfyUI instances  
✅ **Manager Ready**: Fully compatible with ComfyUI Manager  
✅ **Professional**: Follows ComfyUI best practices for custom nodes  
✅ **Clean Shutdown**: Automatically terminates gallery when ComfyUI closes (no orphaned processes)  
✅ **No Port Conflicts**: Prevents "Address already in use" errors on restart  

## Technical Details: Process Lifecycle Management

### The Orphaned Process Problem (Solved)
Previous versions had a critical bug: when ComfyUI closed, the gallery server would continue running as an "orphaned" background process. This caused:
- **Resource leaks**: Memory and CPU usage even after closing ComfyUI
- **Port conflicts**: The next ComfyUI startup would fail with "Address already in use"
- **Manual cleanup required**: Users had to kill the process in Task Manager

### The Solution: `atexit` Module
The current implementation uses Python's `atexit` module to register a cleanup function that runs when ComfyUI exits. This ensures:
1. **Graceful shutdown**: Sends SIGTERM signal to the gallery process
2. **5-second timeout**: Waits for clean shutdown
3. **Force kill fallback**: Uses SIGKILL if needed
4. **Clean state**: Guarantees no orphaned processes

### How It Works
```python
gallery_process = None  # Global reference to subprocess

def cleanup_gallery_process():
    """Called automatically when ComfyUI exits."""
    if gallery_process is not None:
        gallery_process.terminate()  # Graceful shutdown
        gallery_process.wait(timeout=5)  # Wait up to 5 seconds
        # If still running, force kill
        
atexit.register(cleanup_gallery_process)  # Register on module load
```

This implementation ensures professional-grade process management and prevents common user frustrations.  

## Robust Path Detection

### How It Works
SmartGallery uses ComfyUI's official `folder_paths` module to detect paths, ensuring compatibility with all configurations:

```python
import folder_paths

# Get paths from ComfyUI's authoritative source
default_output_path = folder_paths.get_output_directory()
default_input_path = folder_paths.get_input_directory()
```

**Why This Approach Is Superior**:
- ✅ Respects all ComfyUI configuration methods (CLI args, YAML configs, environment variables)
- ✅ Future-proof against ComfyUI directory structure changes
- ✅ Works with advanced setups (custom node paths, network storage, Docker)
- ✅ No assumptions about directory structure or installation location

**What This Means For You**:
- Zero configuration needed for any standard or advanced ComfyUI setup
- Works immediately after installation, regardless of how ComfyUI is configured
- Automatically adapts if you change ComfyUI's configuration later

## For Developers

### File Structure
```
smart-comfyui-gallery/
├── __init__.py              # Main entry point, config loader, API routes
├── smartgallery.py          # Flask server (now accepts CLI args)
├── config.json              # User settings (auto-created)
├── config.json.example      # Template for manual configuration
├── js/
│   └── gallerySettings.js   # ComfyUI settings panel integration
└── templates/
    └── index.html           # Gallery UI (unchanged)
```

### API Endpoints
- `GET /smartgallery/get_config` - Fetch current configuration
- `POST /smartgallery/save_config` - Save new configuration

### Testing Standalone
You can still run the gallery standalone for development:
```bash
python smartgallery.py --output-path "C:/path/to/output" --input-path "C:/path/to/input"
```

---

## ✨ New Configuration System (v1.33+)

Starting with version 1.33, SmartGallery features a **dedicated configuration sidebar tab** that replaces the settings panel approach.

### Accessing the New Configuration UI
1. Open ComfyUI
2. Look for the **Gallery Config** tab in the left sidebar (🖼️ icon)
3. Click to open the comprehensive configuration panel
4. Make changes and click **Save Configuration**

### Key Improvements
- ✅ **Real-time Validation**: Instant feedback on configuration errors
- 🔄 **One-Click Restart**: Restart gallery without restarting ComfyUI
- 📊 **Detailed Messages**: Clear errors and warnings with suggestions
- 🎨 **Modern UI**: Matches ComfyUI's aesthetic perfectly
- 🔧 **Backend Integration**: Purpose-built for server-side configuration

### Configuration API (v2)

#### GET `/smartgallery/config`
Retrieve current configuration with auto-detected paths.

**Response:**
```json
{
    "config": {
        "auto_detect_paths": true,
        "base_output_path": "",
        "base_input_path": "",
        "server_port": 8008,
        "enable_upload": true,
        "max_upload_size_mb": 100,
        "thumbnail_quality": 85,
        "ffprobe_manual_path": ""
    },
    "detected_paths": {
        "output_path": "C:/ComfyUI/output",
        "input_path": "C:/ComfyUI/input"
    },
    "effective_config": {
        "base_output_path": "C:/ComfyUI/output",
        "base_input_path": "C:/ComfyUI/input",
        ...
    },
    "version": "1.33"
}
```

#### POST `/smartgallery/config`
Save configuration with validation.

**Request:**
```json
{
    "auto_detect_paths": false,
    "base_output_path": "D:/AI/output",
    "base_input_path": "D:/AI/input",
    "server_port": 8009,
    "enable_upload": true,
    "max_upload_size_mb": 200,
    "thumbnail_quality": 90,
    "ffprobe_manual_path": "C:/ffmpeg/bin/ffprobe.exe"
}
```

**Response:**
```json
{
    "success": true,
    "errors": [],
    "warnings": ["FFprobe not found at specified path"],
    "message": "Configuration saved successfully",
    "requires_restart": true
}
```

#### POST `/smartgallery/config/validate`
Validate configuration without saving (for real-time feedback).

**Request:** Same as save endpoint

**Response:**
```json
{
    "success": false,
    "errors": ["Port must be between 1024 and 65535"],
    "warnings": ["Output path does not exist: D:/AI/output"]
}
```

#### POST `/smartgallery/restart`
Restart gallery server without restarting ComfyUI.

**Response:**
```json
{
    "success": true,
    "message": "Gallery server restarted successfully"
}
```

### Migration from Settings Panel

Your existing configuration is automatically migrated to the new system:
1. Configuration file format remains the same (`config.json`)
2. Legacy API routes still work for backward compatibility
3. Settings panel shows a deprecation notice
4. All new development focuses on the sidebar tab

### Programmatic Configuration

```python
import requests

base_url = "http://localhost:8188"

# Get current config
response = requests.get(f"{base_url}/smartgallery/config")
config_data = response.json()
print("Current config:", config_data["config"])
print("Detected paths:", config_data["detected_paths"])

# Update configuration
new_config = config_data["config"].copy()
new_config["server_port"] = 8009
new_config["thumbnail_quality"] = 95

response = requests.post(
    f"{base_url}/smartgallery/config",
    json=new_config
)

result = response.json()
if result["success"]:
    print("✅ Configuration saved")
    if result.get("requires_restart"):
        # Restart gallery
        requests.post(f"{base_url}/smartgallery/restart")
        print("🔄 Gallery restarted")
else:
    print("❌ Errors:", result["errors"])
    print("⚠️ Warnings:", result["warnings"])
```

---

**Questions or Issues?**  
Open an issue on GitHub: https://github.com/opj161/smart-comfyui-gallery/issues
