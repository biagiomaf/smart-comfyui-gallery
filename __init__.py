# __init__.py in smart-comfyui-gallery folder

import subprocess
import sys
import os
import threading
import time
import json
import atexit
from pathlib import Path
from typing import Dict, Any, Optional, List
import server
import folder_paths
from comfy_api.latest import ComfyExtension, io
from aiohttp import web

# This is the main ComfyUI server instance
server_instance = server.PromptServer.instance

# --- Configuration ---
DEFAULT_PORT = 8008
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
# -----------------------------

# --- ComfyUI Web Directory Registration ---
# This tells ComfyUI where to find our JavaScript extensions
WEB_DIRECTORY = "./js"

# Required by ComfyUI even if we don't add custom nodes
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

gallery_process = None # Global variable to hold the subprocess reference


# --- Configuration Manager ---
class GalleryConfigManager:
    """
    Manages SmartGallery configuration with validation and path detection.
    This class provides robust backend configuration management separate from
    ComfyUI's settings panel system.
    """
    
    DEFAULT_CONFIG = {
        "base_output_path": "",
        "base_input_path": "",
        "server_port": 8008,
        "ffprobe_manual_path": "",
        "auto_detect_paths": True,
        "enable_upload": True,
        "max_upload_size_mb": 100,
        "thumbnail_quality": 85
    }
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config from file with fallback to defaults"""
        if not self.config_path.exists():
            print("## SmartGallery: No config.json found, using defaults with auto-detection")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to handle new keys in updates
                merged = self.DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
        except Exception as e:
            print(f"!! SmartGallery: Failed to load config.json: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and save configuration
        Returns: {"success": bool, "errors": List[str], "warnings": List[str], "message": str}
        """
        validation = self.validate_config(new_config)
        
        if not validation["success"]:
            validation["message"] = "Configuration validation failed"
            return validation
        
        try:
            # Create backup of existing config
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.bak')
                self.config_path.replace(backup_path)
                print("## SmartGallery: Created config backup")
            
            # Write new config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            
            self.config = new_config
            validation["message"] = "Configuration saved successfully"
            print("## SmartGallery: Configuration saved")
            return validation
            
        except Exception as e:
            print(f"!! SmartGallery: Failed to save config: {e}")
            return {
                "success": False,
                "errors": [f"Failed to save config: {str(e)}"],
                "warnings": [],
                "message": "Save failed"
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation with detailed feedback
        Returns: {"success": bool, "errors": List[str], "warnings": List[str]}
        """
        errors = []
        warnings = []
        
        # Validate port
        port = config.get("server_port", 8008)
        if not isinstance(port, int):
            try:
                port = int(port)
                config["server_port"] = port
            except (ValueError, TypeError):
                errors.append("Port must be a valid integer")
        
        if isinstance(port, int) and (port < 1024 or port > 65535):
            errors.append("Port must be between 1024 and 65535")
        
        # Validate paths if auto-detect is disabled
        auto_detect = config.get("auto_detect_paths", True)
        if not auto_detect:
            output_path = config.get("base_output_path", "")
            if output_path:
                output_dir = Path(output_path)
                if not output_dir.exists():
                    warnings.append(f"Output path does not exist: {output_path}")
                elif not output_dir.is_dir():
                    errors.append(f"Output path is not a directory: {output_path}")
                elif not os.access(output_path, os.R_OK):
                    errors.append(f"Output path is not readable: {output_path}")
            else:
                warnings.append("Output path is empty with auto-detect disabled")
            
            input_path = config.get("base_input_path", "")
            if input_path:
                input_dir = Path(input_path)
                if not input_dir.exists():
                    warnings.append(f"Input path does not exist: {input_path}")
                elif not input_dir.is_dir():
                    errors.append(f"Input path is not a directory: {input_path}")
        
        # Validate FFprobe path (optional)
        ffprobe = config.get("ffprobe_manual_path", "")
        if ffprobe:
            ffprobe_path = Path(ffprobe)
            if not ffprobe_path.exists():
                warnings.append(f"FFprobe not found at: {ffprobe}")
            elif not os.access(ffprobe, os.X_OK):
                # On Windows, executable check might not work reliably
                if sys.platform != 'win32':
                    warnings.append(f"FFprobe exists but may not be executable: {ffprobe}")
        
        # Validate upload settings
        if config.get("enable_upload", True):
            max_size = config.get("max_upload_size_mb", 100)
            if not isinstance(max_size, (int, float)):
                try:
                    max_size = float(max_size)
                    config["max_upload_size_mb"] = max_size
                except (ValueError, TypeError):
                    errors.append("Max upload size must be a number")
            
            if isinstance(max_size, (int, float)) and max_size <= 0:
                errors.append("Max upload size must be greater than 0")
        
        # Validate thumbnail quality
        quality = config.get("thumbnail_quality", 85)
        if not isinstance(quality, int):
            try:
                quality = int(quality)
                config["thumbnail_quality"] = quality
            except (ValueError, TypeError):
                errors.append("Thumbnail quality must be an integer")
        
        if isinstance(quality, int) and (quality < 1 or quality > 100):
            errors.append("Thumbnail quality must be between 1 and 100")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_detected_paths(self) -> Dict[str, Optional[str]]:
        """Get auto-detected paths from ComfyUI"""
        try:
            output_path = folder_paths.get_output_directory()
            input_path = folder_paths.get_input_directory()
            return {
                "output_path": output_path,
                "input_path": input_path
            }
        except Exception as e:
            print(f"!! SmartGallery: Failed to detect paths: {e}")
            return {
                "output_path": None,
                "input_path": None
            }
    
    def get_effective_config(self) -> Dict[str, Any]:
        """
        Get the effective configuration with auto-detected paths applied
        Returns config that should actually be used by the gallery
        """
        effective = self.config.copy()
        
        if effective.get("auto_detect_paths", True):
            detected = self.get_detected_paths()
            if detected["output_path"]:
                effective["base_output_path"] = detected["output_path"]
            if detected["input_path"]:
                effective["base_input_path"] = detected["input_path"]
        
        return effective


# Initialize config manager
config_manager = GalleryConfigManager(CONFIG_FILE)


def load_config():
    """
    Legacy function for backward compatibility.
    Now uses the new GalleryConfigManager.
    """
    return config_manager.get_effective_config()

def launch_gallery():
    """Launches the smartgallery.py script and stores its process reference."""
    global gallery_process
    if gallery_process is not None and gallery_process.poll() is None:
        print("## SmartGallery: Server already running.")
        return

    time.sleep(2) 

    current_dir = os.path.dirname(__file__)
    script_path = os.path.join(current_dir, 'smartgallery.py')
    python_executable = sys.executable

    if not os.path.exists(script_path):
        print("!! SmartGallery: could not find smartgallery.py, skipping auto-launch.")
        return

    config = load_config()

    cmd = [
        python_executable, script_path,
        "--output-path", config["base_output_path"],
        "--input-path", config["base_input_path"],
        "--port", str(config["server_port"]),
        "--ffprobe-path", config["ffprobe_manual_path"]
    ]

    print("## SmartGallery: Starting server...")
    
    try:
        # Keep output visible for debugging this final attempt.
        gallery_process = subprocess.Popen(
            cmd,
            # stdout=subprocess.DEVNULL, # Will be uncommented once it works
            # stderr=subprocess.STDOUT,  # Will be uncommented once it works
            cwd=current_dir
        )
        
        print("## SmartGallery: Server launched in the background.")
        print(f"## SmartGallery: URL: http://127.0.0.1:{config['server_port']}/galleryout/")
    except Exception as e:
        print(f"!! SmartGallery: Failed to start server: {e}")

def cleanup_gallery_process():
    """This function will be called on ComfyUI exit to terminate the gallery."""
    global gallery_process
    if gallery_process is not None:
        print("## SmartGallery: Shutting down server...")
        try:
            gallery_process.terminate()
            gallery_process.wait(timeout=5)
            print("## SmartGallery: Server shut down successfully.")
        except subprocess.TimeoutExpired:
            print("!! SmartGallery: Server did not respond to terminate, forcing shutdown.")
            gallery_process.kill()
        except Exception as e:
            print(f"!! SmartGallery: Error during shutdown: {e}")
        gallery_process = None

atexit.register(cleanup_gallery_process)

# --- NEW API ROUTES FOR CONFIGURATION MANAGEMENT ---
print("## SmartGallery: Registering configuration API routes...")

@server_instance.routes.get("/smartgallery/config")
async def get_gallery_config_v2(request):
    """
    GET endpoint to retrieve current configuration
    Returns: Current config + auto-detected paths + effective config
    """
    try:
        config = config_manager.config.copy()
        detected = config_manager.get_detected_paths()
        effective = config_manager.get_effective_config()
        
        return web.json_response({
            "config": config,
            "detected_paths": detected,
            "effective_config": effective,
            "version": "1.33"
        })
    except Exception as e:
        print(f"!! SmartGallery: Error getting config: {e}")
        return web.json_response({
            "error": str(e)
        }, status=500)


@server_instance.routes.post("/smartgallery/config")
async def save_gallery_config_v2(request):
    """
    POST endpoint to save configuration
    Accepts: JSON config object
    Returns: Validation result + success status
    """
    try:
        new_config = await request.json()
        result = config_manager.save_config(new_config)
        
        # If successful and gallery is running, flag for restart
        global gallery_process
        if result["success"] and gallery_process is not None:
            result["requires_restart"] = True
            result["message"] = "Configuration saved. Gallery will use new settings on next restart."
        
        return web.json_response(result)
        
    except json.JSONDecodeError:
        return web.json_response({
            "success": False,
            "errors": ["Invalid JSON in request body"],
            "warnings": [],
            "message": "Invalid JSON"
        }, status=400)
    except Exception as e:
        print(f"!! SmartGallery: Error saving config: {e}")
        return web.json_response({
            "success": False,
            "errors": [f"Server error: {str(e)}"],
            "warnings": [],
            "message": "Server error"
        }, status=500)


@server_instance.routes.post("/smartgallery/config/validate")
async def validate_gallery_config(request):
    """
    POST endpoint for validation without saving
    Useful for real-time feedback in UI
    """
    try:
        config_to_validate = await request.json()
        result = config_manager.validate_config(config_to_validate)
        return web.json_response(result)
    except json.JSONDecodeError:
        return web.json_response({
            "success": False,
            "errors": ["Invalid JSON in request body"],
            "warnings": []
        }, status=400)
    except Exception as e:
        print(f"!! SmartGallery: Error validating config: {e}")
        return web.json_response({
            "success": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": []
        }, status=400)


@server_instance.routes.post("/smartgallery/restart")
async def restart_gallery_server(request):
    """
    POST endpoint to restart gallery subprocess
    """
    global gallery_process
    
    try:
        if gallery_process is not None:
            print("## SmartGallery: Restarting gallery server...")
            gallery_process.terminate()
            try:
                gallery_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("!! SmartGallery: Server didn't stop gracefully, forcing...")
                gallery_process.kill()
            gallery_process = None
        
        # Re-launch with new config
        launch_gallery()
        
        return web.json_response({
            "success": True,
            "message": "Gallery server restarted successfully"
        })
    except Exception as e:
        print(f"!! SmartGallery: Failed to restart: {e}")
        return web.json_response({
            "success": False,
            "message": f"Failed to restart: {str(e)}"
        }, status=500)


# --- LEGACY API ROUTES (for backward compatibility) ---
print("## SmartGallery: Registering legacy API routes...")
# --- LEGACY API ROUTES (for backward compatibility) ---
print("## SmartGallery: Registering legacy API routes...")

@server_instance.routes.get("/smartgallery/get_config")
async def get_gallery_config(request):
    """Legacy endpoint - redirects to new config manager"""
    config = load_config()
    return web.json_response(config)

@server_instance.routes.post("/smartgallery/save_config")
async def save_gallery_config(request):
    """Legacy endpoint - uses new config manager"""
    try:
        data = await request.json()
        # Convert old format to new format if needed
        if "auto_detect_paths" not in data:
            data["auto_detect_paths"] = not bool(data.get("base_output_path"))
        
        result = config_manager.save_config(data)
        
        if result["success"]:
            message = "✅ SmartGallery settings saved. Please restart ComfyUI for changes to take effect."
            return web.json_response({"status": "success", "message": message})
        else:
            return web.json_response({
                "status": "error",
                "message": "; ".join(result["errors"])
            }, status=400)
    except Exception as e:
        print(f"!! SmartGallery: Error saving config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

print("## SmartGallery: API routes registered.")

# --- Start the server launch in a background thread at the module level ---
# This is the most reliable point of execution.
print("## SmartGallery: Scheduling server launch.")
gallery_thread = threading.Thread(target=launch_gallery, daemon=True)
gallery_thread.start()
# -------------------------------------------------------------------------

class SmartGalleryExtension(ComfyExtension):
    def __init__(self):
        super().__init__()
        self.web_directory = "js"

    # on_load is kept for ideal-world compatibility, but we don't rely on it.
    def on_load(self):
        print("## SmartGallery: on_load hook triggered (redundant launch check).")
        # The launch function will check if the server is already running.
        launch_gallery()

    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return []

async def comfy_entrypoint() -> SmartGalleryExtension:
    return SmartGalleryExtension()
# Export WEB_DIRECTORY so ComfyUI can find our JavaScript extensions
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
