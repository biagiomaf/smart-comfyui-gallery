# __init__.py in smart-comfyui-gallery folder

import subprocess
import sys
import os
import threading
import time
import json
import atexit
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

gallery_process = None # Global variable to hold the subprocess reference

def load_config():
    """Loads user settings from config.json, with robust defaults from ComfyUI itself."""
    
    # Get paths directly from ComfyUI's path manager
    # This is the correct, robust way to do it - respects all ComfyUI configurations
    default_output_path = folder_paths.get_output_directory()
    default_input_path = folder_paths.get_input_directory()

    config = {
        "base_output_path": default_output_path,
        "base_input_path": default_input_path,
        "server_port": DEFAULT_PORT,
        "ffprobe_manual_path": ""
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                # Smartly update the config, ignoring empty path values from the user
                for key, value in user_config.items():
                    if "path" in key and not value:
                        continue # User left path blank, so we keep the auto-detected default
                    config[key] = value
        except Exception as e:
            print(f"!! SmartGallery: Error loading config.json, using defaults. Error: {e}")
            
    return config

def launch_gallery():
    """Launches the smartgallery.py script and stores its process reference."""
    global gallery_process
    if gallery_process is not None:
        return

    time.sleep(2) # Delay to let ComfyUI start first

    current_dir = os.path.dirname(__file__)
    script_path = os.path.join(current_dir, 'smartgallery.py')
    python_executable = sys.executable

    if not os.path.exists(script_path):
        print("!! SmartGallery: could not find smartgallery.py, skipping auto-launch.")
        return

    # Load configuration
    config = load_config()

    # Build the command-line arguments to pass to the gallery server
    cmd = [
        python_executable, script_path,
        "--output-path", config["base_output_path"],
        "--input-path", config["base_input_path"],
        "--port", str(config["server_port"]),
        "--ffprobe-path", config["ffprobe_manual_path"]
    ]

    print("## SmartGallery: Starting server...")
    
    try:
        # Store the process object in our global variable
        gallery_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            cwd=current_dir # Set the correct working directory
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
            gallery_process.terminate() # Send a termination signal
            gallery_process.wait(timeout=5) # Wait for up to 5 seconds
            print("## SmartGallery: Server shut down successfully.")
        except subprocess.TimeoutExpired:
            print("!! SmartGallery: Server did not respond to terminate, forcing shutdown.")
            gallery_process.kill() # Force kill if it doesn't close gracefully
        except Exception as e:
            print(f"!! SmartGallery: Error during shutdown: {e}")
        gallery_process = None

# --- Register the cleanup function to be called on exit ---
atexit.register(cleanup_gallery_process)

# --- ComfyUI API Routes for Settings Panel ---

print("## SmartGallery: Registering API routes...")
@server_instance.routes.get("/smartgallery/get_config")
async def get_gallery_config(request):
    """API endpoint for the JS settings panel to fetch current settings."""
    config = load_config()
    return web.json_response(config)

@server_instance.routes.post("/smartgallery/save_config")
async def save_gallery_config(request):
    """API endpoint for the JS settings panel to save new settings."""
    try:
        data = await request.json()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        message = "✅ SmartGallery settings saved. Please restart ComfyUI for changes to take effect."
        return web.json_response({"status": "success", "message": message})
    except Exception as e:
        print(f"!! SmartGallery: Error saving config: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

print("## SmartGallery: API routes registered.")

# --- ComfyUI V3 Registration ---

class SmartGalleryExtension(ComfyExtension):
    def __init__(self):
        # Call the parent class's constructor
        super().__init__()
        # Set the web_directory as an instance attribute for ComfyUI to discover
        self.web_directory = "js"

    def on_load(self):
        """Called by ComfyUI when the extension is loaded."""
        # This is the modern, clean way to handle startup logic.
        gallery_thread = threading.Thread(target=launch_gallery, daemon=True)
        gallery_thread.start()

    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        """This extension registers no nodes."""
        return []

async def comfy_entrypoint() -> SmartGalleryExtension:
    """The function ComfyUI looks for to register the extension."""
    # Instantiate the extension class without arguments
    return SmartGalleryExtension()