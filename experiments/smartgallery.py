# Smart Gallery for ComfyUI
# Author: Biagio Maffettone © 2025-2026 — MIT License (free to use and modify)
#
# Version: 1.53.1 - January 9, 2026
# Check the GitHub repository for updates, bug fixes, and contributions.
#
# Contact: biagiomaf@gmail.com
# GitHub: https://github.com/biagiomaf/smart-comfyui-gallery

import os
import hashlib
import cv2
import json
import shutil
import re
import sqlite3
import time
from datetime import datetime
import glob
import sys
import subprocess
import base64
import zipfile
import io
from flask import Flask, render_template, send_from_directory, abort, send_file, url_for, redirect, request, jsonify, Response
from PIL import Image, ImageSequence
import colorsys
from werkzeug.utils import secure_filename
import concurrent.futures
from tqdm import tqdm
import threading
import uuid
# Try to import tkinter for GUI dialogs, but make it optional for Docker/headless environments
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # tkinter not available (e.g., in Docker containers) - will fall back to console output
import urllib.request 
import secrets


# ============================================================================
# CONFIGURATION GUIDE - PLEASE READ BEFORE SETTING UP
# ============================================================================
#
# CONFIGURATION PRIORITY:
# All settings below first check for environment variables. If an environment 
# variable is set, its value will be used automatically. 
# If you have NOT set environment variables, you only need to modify the 
# values AFTER the comma in the os.environ.get() statements.
#
# Example: os.environ.get('BASE_OUTPUT_PATH', 'C:/your/path/here')
#          - If BASE_OUTPUT_PATH environment variable exists → it will be used
#          - If NOT → the value 'C:/your/path/here' will be used instead
#          - ONLY CHANGE 'C:/your/path/here' if you haven't set environment variables
#
# ----------------------------------------------------------------------------
# HOW TO SET ENVIRONMENT VARIABLES (before running python smartgallery.py):
# ----------------------------------------------------------------------------
#
# IMPORTANT: If your paths contain SPACES, you MUST use quotes around them!
#            Replace the example paths below with YOUR actual paths!
#
# Windows (Command Prompt):
#   call venv\Scripts\activate.bat
#   set "BASE_OUTPUT_PATH=C:/ComfyUI/output"
#   set BASE_INPUT_PATH=C:/sm/Data/Packages/ComfyUI/input
#   set "BASE_SMARTGALLERY_PATH=C:/ComfyUI/output"
#   set "FFPROBE_MANUAL_PATH=C:/ffmpeg/bin/ffprobe.exe"
#   set SERVER_PORT=8189
#   set THUMBNAIL_WIDTH=300
#   set WEBP_ANIMATED_FPS=16.0
#   set PAGE_SIZE=100
#   set BATCH_SIZE=500
#   set ENABLE_AI_SEARCH=false
#   REM Leave MAX_PARALLEL_WORKERS empty to use all CPU cores (recommended)
#   set "MAX_PARALLEL_WORKERS="
#   python smartgallery.py
#
# Windows (PowerShell):
#   venv\Scripts\Activate.ps1
#   $env:BASE_OUTPUT_PATH="C:/ComfyUI/output"
#   $env:BASE_INPUT_PATH="C:/sm/Data/Packages/ComfyUI/input"
#   $env:BASE_SMARTGALLERY_PATH="C:/ComfyUI/output"
#   $env:FFPROBE_MANUAL_PATH="C:/ffmpeg/bin/ffprobe.exe"
#   $env:SERVER_PORT="8189"
#   $env:THUMBNAIL_WIDTH="300"
#   $env:WEBP_ANIMATED_FPS="16.0"
#   $env:PAGE_SIZE="100"
#   $env:BATCH_SIZE="500"
#   $env:ENABLE_AI_SEARCH="false"
#   # Leave MAX_PARALLEL_WORKERS empty to use all CPU cores (recommended)
#   $env:MAX_PARALLEL_WORKERS=""
#   python smartgallery.py
#
# Linux/Mac (bash/zsh):
#   source venv/bin/activate
#   export BASE_OUTPUT_PATH="$HOME/ComfyUI/output"
#   export BASE_INPUT_PATH="/path/to/ComfyUI/input"
#   export BASE_SMARTGALLERY_PATH="$HOME/ComfyUI/output"
#   export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
#   export DELETE_TO="/path/to/trash" # Optional, set to disable permanent delete
#   export SERVER_PORT=8189
#   export THUMBNAIL_WIDTH=300
#   export WEBP_ANIMATED_FPS=16.0
#   export PAGE_SIZE=100
#   export BATCH_SIZE=500
#   export ENABLE_AI_SEARCH=false
#   # Leave MAX_PARALLEL_WORKERS empty to use all CPU cores (recommended)
#   export MAX_PARALLEL_WORKERS=""
#   python smartgallery.py
#
#
# IMPORTANT NOTES:
# - Even on Windows, always use forward slashes (/) in paths, 
#   not backslashes (\), to ensure compatibility.
# - Use QUOTES around paths containing spaces to avoid errors.
# - Replace example paths (C:/ComfyUI/, $HOME/ComfyUI/) with YOUR actual paths!
# - Set MAX_PARALLEL_WORKERS="" (empty string) to use all available CPU cores.
#   Set it to a number (e.g., 4) to limit CPU usage.
# - It is strongly recommended to have ffmpeg installed, 
#   since some features depend on it.
#
# ============================================================================


# ============================================================================
# USER CONFIGURATION
# ============================================================================
# Adjust the parameters below to customize the gallery.
# Remember: environment variables take priority over these default values.
# ============================================================================

# Path to the ComfyUI 'output' folder.
# Common locations:
#   Windows: C:/ComfyUI/output or C:/Users/YourName/ComfyUI/output
#   Linux/Mac: /home/username/ComfyUI/output or ~/ComfyUI/output
BASE_OUTPUT_PATH = os.environ.get('BASE_OUTPUT_PATH', 'C:/ComfyUI/output')

# Path to the ComfyUI 'input' folder 
BASE_INPUT_PATH = os.environ.get('BASE_INPUT_PATH', 'C:/ComfyUI/input')

# Path for service folders (database, cache, zip files). 
# If not specified, the ComfyUI output path will be used. 
# These sub-folders won't appear in the gallery.
# Change this if you want the cache stored separately for better performance
# or to keep system files separate from gallery content.
# Leave as-is if you are unsure. 
BASE_SMARTGALLERY_PATH = os.environ.get('BASE_SMARTGALLERY_PATH', BASE_OUTPUT_PATH)

# Path to ffprobe executable (part of ffmpeg).
# Common locations:
#   Windows: C:/ffmpeg/bin/ffprobe.exe or C:/Program Files/ffmpeg/bin/ffprobe.exe
#   Linux: /usr/bin/ffprobe or /usr/local/bin/ffprobe
#   Mac: /usr/local/bin/ffprobe or /opt/homebrew/bin/ffprobe
# Required for extracting workflows from .mp4 files.
# NOTE: A full ffmpeg installation is highly recommended.
FFPROBE_MANUAL_PATH = os.environ.get('FFPROBE_MANUAL_PATH', "C:/ffmpeg/bin/ffprobe.exe")

# Port on which the gallery web server will run. 
# Must be different from the ComfyUI port (usually 8188).
# The gallery does not require ComfyUI to be running; it works independently.
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8189))

# Width (in pixels) of the generated thumbnails.
THUMBNAIL_WIDTH = int(os.environ.get('THUMBNAIL_WIDTH', 300))

# Assumed frame rate for animated WebP files.  
# Many tools, including ComfyUI, generate WebP animations at ~16 FPS.  
# Adjust this value if your WebPs use a different frame rate,  
# so that animation durations are calculated correctly.
WEBP_ANIMATED_FPS = float(os.environ.get('WEBP_ANIMATED_FPS', 16.0))

# Maximum number of files to load initially before showing a "Load more" button.  
# Use a very large number (e.g., 9999999) for "infinite" loading.
PAGE_SIZE = int(os.environ.get('PAGE_SIZE', 100))

# Names of special folders (e.g., 'video', 'audio').  
# These folders will appear in the menu only if they exist inside BASE_OUTPUT_PATH.  
# Leave as-is if unsure.
SPECIAL_FOLDERS = ['video', 'audio']

# Number of files to process at once during database sync. 
# Higher values use more memory but may be faster. 
# Lower this if you run out of memory.
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 500))

# Threshold (in MB) above which videos will be streamed (transcoded) 
# instead of loaded natively in the gallery grid preview.
# Default: 50 MB. Set to 0 to force streaming for all supported videos.
STREAM_THRESHOLD_MB = int(os.environ.get('STREAM_THRESHOLD_MB', 20))
STREAM_THRESHOLD_BYTES = STREAM_THRESHOLD_MB * 1024 * 1024

# Number of parallel processes to use for thumbnail and metadata generation.
# - None or empty string: use all available CPU cores (fastest, recommended)
# - 1: disable parallel processing (slowest, like in previous versions)
# - Specific number (e.g., 4): limit CPU usage on multi-core machines
MAX_PARALLEL_WORKERS = os.environ.get('MAX_PARALLEL_WORKERS', None)
if MAX_PARALLEL_WORKERS is not None and MAX_PARALLEL_WORKERS != "":
    MAX_PARALLEL_WORKERS = int(MAX_PARALLEL_WORKERS)
else:
    MAX_PARALLEL_WORKERS = None

# Flask secret key
# You can set it in the environment variable SECRET_KEY
# If not set, it will be generated randomly
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Maximum number of items allowed in the "Prefix" dropdown to prevent UI lag.
MAX_PREFIX_DROPDOWN_ITEMS = 100


# Optional path where deleted files will be moved instead of being permanently deleted.
# If set, files will be moved to DELETE_TO/SmartGallery/<timestamp>_<filename>
# If not set (None or empty string), files will be permanently deleted as before.
# The path MUST exist and be writable, or the application will exit with an error.
# Example: /path/to/trash or C:/Trash
DELETE_TO = os.environ.get('DELETE_TO', None)
if DELETE_TO and DELETE_TO.strip():
    DELETE_TO = DELETE_TO.strip()
    TRASH_FOLDER = os.path.join(DELETE_TO, 'SmartGallery')
    
    # Validate that DELETE_TO path exists
    if not os.path.exists(DELETE_TO):
        print(f"{Colors.RED}{Colors.BOLD}CRITICAL ERROR: DELETE_TO path does not exist: {DELETE_TO}{Colors.RESET}")
        print(f"{Colors.RED}Please create the directory or unset the DELETE_TO environment variable.{Colors.RESET}")
        sys.exit(1)
    
    # Validate that DELETE_TO is writable
    if not os.access(DELETE_TO, os.W_OK):
        print(f"{Colors.RED}{Colors.BOLD}CRITICAL ERROR: DELETE_TO path is not writable: {DELETE_TO}{Colors.RESET}")
        print(f"{Colors.RED}Please check permissions or unset the DELETE_TO environment variable.{Colors.RESET}")
        sys.exit(1)
    
    # Validate that SmartGallery subfolder exists or can be created
    if not os.path.exists(TRASH_FOLDER):
        try:
            os.makedirs(TRASH_FOLDER)
            print(f"{Colors.GREEN}Created trash folder: {TRASH_FOLDER}{Colors.RESET}")
        except OSError as e:
            print(f"{Colors.RED}{Colors.BOLD}CRITICAL ERROR: Cannot create trash folder: {TRASH_FOLDER}{Colors.RESET}")
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            sys.exit(1)
else:
    DELETE_TO = None
    TRASH_FOLDER = None

# ============================================================================
# WORKFLOW PROMPT EXTRACTION SETTINGS
# ============================================================================
# List of specific text phrases to EXCLUDE from the 'Prompt Keywords' search index.
# Some custom nodes (e.g., Wan2.1, text boxes, primitives) come with long default
# example prompts or placeholder text that gets saved in the workflow metadata 
# even if not actually used in the generation.
# Add those specific strings here to prevent them from cluttering your search results.
WORKFLOW_PROMPT_BLACKLIST = {
    "The white dragon warrior stands still, eyes full of determination and strength. The camera slowly moves closer or circles around the warrior, highlighting the powerful presence and heroic spirit of the character.",
    "undefined",
    "null",
    "None"
}

# ============================================================================
# AI SEARCH CONFIGURATION (FUTURE FEATURE)
# ============================================================================
# Enable or disable the AI Search UI features.
#
# IMPORTANT:
# The SmartGallery AI Service (Optional) required for this feature
# is currently UNDER DEVELOPMENT and HAS NOT BEEN RELEASED yet.
#
# SmartGallery works fully out-of-the-box without any AI components.
#
# Advanced features such as AI Search will be provided by a separate,
# optional service that can be installed via Docker or in a separated dedicated Python virtual environment.
#
# PLEASE KEEP THIS SETTING DISABLED (default).
# Do NOT enable this option unless the AI Service has been officially
# released and correctly installed alongside SmartGallery.
#
# Check the GitHub repository for official announcements and
# installation instructions regarding the optional AI Service.
#
#   Windows:     set ENABLE_AI_SEARCH=false
#   Linux / Mac: export ENABLE_AI_SEARCH=false
#   Docker:      -e ENABLE_AI_SEARCH=false
#
ENABLE_AI_SEARCH = os.environ.get('ENABLE_AI_SEARCH', 'false').lower() == 'true'

# ============================================================================
# END OF USER CONFIGURATION
# ============================================================================


# --- CACHE AND FOLDER NAMES ---
THUMBNAIL_CACHE_FOLDER_NAME = '.thumbnails_cache'
SQLITE_CACHE_FOLDER_NAME = '.sqlite_cache'
DATABASE_FILENAME = 'gallery_cache.sqlite'
ZIP_CACHE_FOLDER_NAME = '.zip_downloads'
AI_MODELS_FOLDER_NAME = '.AImodels'

# --- APP INFO ---
APP_VERSION = "1.53.1"
APP_VERSION_DATE = "January 9, 2026"
GITHUB_REPO_URL = "https://github.com/biagiomaf/smart-comfyui-gallery"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/biagiomaf/smart-comfyui-gallery/main/smartgallery.py"


# --- HELPER FUNCTIONS (DEFINED FIRST) ---
def path_to_key(relative_path):
    if not relative_path: return '_root_'
    return base64.urlsafe_b64encode(relative_path.replace(os.sep, '/').encode()).decode()

def key_to_path(key):
    if key == '_root_': return ''
    try:
        return base64.urlsafe_b64decode(key.encode()).decode().replace('/', os.sep)
    except Exception: return None

# --- DERIVED SETTINGS ---
DB_SCHEMA_VERSION = 27 
THUMBNAIL_CACHE_DIR = os.path.join(BASE_SMARTGALLERY_PATH, THUMBNAIL_CACHE_FOLDER_NAME)
SQLITE_CACHE_DIR = os.path.join(BASE_SMARTGALLERY_PATH, SQLITE_CACHE_FOLDER_NAME)
DATABASE_FILE = os.path.join(SQLITE_CACHE_DIR, DATABASE_FILENAME)
ZIP_CACHE_DIR = os.path.join(BASE_SMARTGALLERY_PATH, ZIP_CACHE_FOLDER_NAME)
PROTECTED_FOLDER_KEYS = {path_to_key(f) for f in SPECIAL_FOLDERS}
PROTECTED_FOLDER_KEYS.add('_root_')


# --- CONSOLE STYLING ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

# --- HELPER FOR AI PATH CONSISTENCY ---
def get_standardized_path(filepath):
    """
    Converts path to absolute, forces forward slashes, and handles case sensitivity for Windows.
    Used ONLY for AI Queue uniqueness to prevent loops on mixed-path systems.
    """
    if not filepath: return ""
    try:
        # Resolve absolute path (handles .. and current dir)
        abs_path = os.path.abspath(filepath)
        # Force forward slashes (works on Win/Linux/Mac for Python)
        std_path = abs_path.replace('\\', '/')
        # On Windows, filesystem is case-insensitive, so we lower for the DB unique key
        if os.name == 'nt':
            return std_path.lower()
        return std_path
    except:
        return str(filepath)

def normalize_smart_path(path_str):
    """
    Normalizes a path string for search comparison:
    1. Converts to lowercase.
    2. Replaces all backslashes (\\) with forward slashes (/).
    """
    if not path_str: return ""
    return str(path_str).lower().replace('\\', '/')

def print_configuration():
    """Prints the current configuration in a neat, aligned table."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}--- CURRENT CONFIGURATION ---{Colors.RESET}")
    
    # Helper for aligned printing
    def print_row(key, value, is_path=False):
        color = Colors.CYAN if is_path else Colors.GREEN
        print(f" {Colors.BOLD}{key:<25}{Colors.RESET} : {color}{value}{Colors.RESET}")

    print_row("Server Port", SERVER_PORT)
    print_row("Base Output Path", BASE_OUTPUT_PATH, True)
    print_row("Base Input Path", BASE_INPUT_PATH, True)
    print_row("SmartGallery Path", BASE_SMARTGALLERY_PATH, True)
    print_row("FFprobe Path", FFPROBE_MANUAL_PATH, True)
    print_row("Delete To (Trash)", DELETE_TO if DELETE_TO else "Disabled (Permanent Delete)", DELETE_TO is not None)
    print_row("Thumbnail Width", f"{THUMBNAIL_WIDTH}px")
    print_row("WebP Animated FPS", WEBP_ANIMATED_FPS)
    print_row("Page Size", PAGE_SIZE)
    print_row("Batch Size", BATCH_SIZE)
    print_row("Stream Threshold", f"{STREAM_THRESHOLD_MB} MB")
    print_row("Max Parallel Workers", MAX_PARALLEL_WORKERS if MAX_PARALLEL_WORKERS else "All Cores")
    print_row("AI Search", "Enabled" if ENABLE_AI_SEARCH else "Disabled")
    print(f"{Colors.HEADER}-----------------------------{Colors.RESET}\n")

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)
app.secret_key = SECRET_KEY
gallery_view_cache = []
folder_config_cache = None
FFPROBE_EXECUTABLE_PATH = None


# Data structures for node categorization and analysis
NODE_CATEGORIES_ORDER = ["input", "model", "processing", "output", "others"]
NODE_CATEGORIES = {
    "Load Checkpoint": "input", "CheckpointLoaderSimple": "input", "Empty Latent Image": "input",
    "CLIPTextEncode": "input", "Load Image": "input",
    "ModelMerger": "model",
    "KSampler": "processing", "KSamplerAdvanced": "processing", "VAEDecode": "processing",
    "VAEEncode": "processing", "LatentUpscale": "processing", "ConditioningCombine": "processing",
    "PreviewImage": "output", "SaveImage": "output",
     "LoadImageOutput": "input"
}
NODE_PARAM_NAMES = {
    "CLIPTextEncode": ["text"],
    "KSampler": ["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
    "KSamplerAdvanced": ["add_noise", "noise_seed", "steps", "cfg", "sampler_name", "scheduler", "start_at_step", "end_at_step", "return_with_leftover_noise"],
    "Load Checkpoint": ["ckpt_name"],
    "CheckpointLoaderSimple": ["ckpt_name"],
    "Empty Latent Image": ["width", "height", "batch_size"],
    "LatentUpscale": ["upscale_method", "width", "height"],
    "SaveImage": ["filename_prefix"],
    "ModelMerger": ["ckpt_name1", "ckpt_name2", "ratio"],
    "Load Image": ["image"],         
    "LoadImageMask": ["image"],      
    "VHS_LoadVideo": ["video"],
    "LoadAudio": ["audio"],
    "AudioLoader": ["audio"],
    "LoadImageOutput": ["image"]
}

# Cache for node colors
_node_colors_cache = {}

def get_node_color(node_type):
    """Generates a unique and consistent color for a node type."""
    if node_type not in _node_colors_cache:
        # Use a hash to get a consistent color for the same node type
        hue = (hash(node_type + "a_salt_string") % 360) / 360.0
        rgb = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.7, 0.85)]
        _node_colors_cache[node_type] = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    return _node_colors_cache[node_type]

def filter_enabled_nodes(workflow_data):
    """Filters and returns only active nodes and links (mode=0) from a workflow."""
    if not isinstance(workflow_data, dict): return {'nodes': [], 'links': []}
    
    active_nodes = [n for n in workflow_data.get("nodes", []) if n.get("mode", 0) == 0]
    active_node_ids = {str(n["id"]) for n in active_nodes}
    
    active_links = [
        l for l in workflow_data.get("links", [])
        if str(l[1]) in active_node_ids and str(l[3]) in active_node_ids
    ]
    return {"nodes": active_nodes, "links": active_links}

def generate_node_summary(workflow_json_string):
    """
    Analyzes a workflow JSON, extracts active nodes, and identifies input media.
    Robust version: handles ComfyUI specific suffixes like ' [output]'.
    """
    try:
        workflow_data = json.loads(workflow_json_string)
    except json.JSONDecodeError:
        return None

    nodes = []
    is_api_format = False

    if 'nodes' in workflow_data and isinstance(workflow_data['nodes'], list):
        active_workflow = filter_enabled_nodes(workflow_data)
        nodes = active_workflow.get('nodes', [])
    else:
        is_api_format = True
        for node_id, node_data in workflow_data.items():
            if isinstance(node_data, dict) and 'class_type' in node_data:
                node_entry = node_data.copy()
                node_entry['id'] = node_id
                node_entry['type'] = node_data['class_type']
                node_entry['inputs'] = node_data.get('inputs', {})
                nodes.append(node_entry)

    if not nodes:
        return []

    def get_id_safe(n):
        try: return int(n.get('id', 0))
        except: return str(n.get('id', 0))

    sorted_nodes = sorted(nodes, key=lambda n: (
        NODE_CATEGORIES_ORDER.index(NODE_CATEGORIES.get(n.get('type'), 'others')),
        get_id_safe(n)
    ))
    
    summary_list = []
    
    valid_media_exts = {
        '.png', '.jpg', '.jpeg', '.webp', '.gif', '.jfif', '.bmp', '.tiff',
        '.mp4', '.mov', '.webm', '.mkv', '.avi',
        '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'
    }

    base_input_norm = os.path.normpath(BASE_INPUT_PATH)

    for node in sorted_nodes:
        node_type = node.get('type', 'Unknown')
        params_list = []
        
        raw_params = {}
        if is_api_format:
            raw_params = node.get('inputs', {})
        else:
            widgets_values = node.get('widgets_values', [])
            param_names_list = NODE_PARAM_NAMES.get(node_type, [])
            for i, value in enumerate(widgets_values):
                name = param_names_list[i] if i < len(param_names_list) else f"param_{i+1}"
                raw_params[name] = value

        for name, value in raw_params.items():
            display_value = value
            is_input_file = False
            input_url = None
            
            if isinstance(value, list):
                if len(value) == 2 and isinstance(value[0], str):
                     display_value = f"(Link to {value[0]})"
                else:
                     display_value = str(value)
            
            if isinstance(value, str) and value.strip():
                # 1. Pulizia aggressiva per rimuovere suffissi tipo " [output]" o " [input]"
                clean_value = value.replace('\\', '/').strip()
                # Rimuovi suffissi comuni tra parentesi quadre alla fine della stringa
                clean_value = re.sub(r'\s*\[.*?\]$', '', clean_value)
                
                _, ext = os.path.splitext(clean_value)
                
                if ext.lower() in valid_media_exts:
                    filename_only = os.path.basename(clean_value)
                    
                    candidates = [
                        os.path.join(BASE_INPUT_PATH, clean_value),
                        os.path.join(BASE_INPUT_PATH, filename_only),
                        os.path.normpath(os.path.join(BASE_INPUT_PATH, clean_value))
                    ]

                    for candidate_path in candidates:
                        try:
                            if os.path.isfile(candidate_path):
                                abs_candidate = os.path.abspath(candidate_path)
                                abs_base = os.path.abspath(BASE_INPUT_PATH)
                                
                                if abs_candidate.startswith(abs_base):
                                    is_input_file = True
                                    rel_path = os.path.relpath(abs_candidate, abs_base).replace('\\', '/')
                                    input_url = f"/galleryout/input_file/{rel_path}"
                                    # Aggiorniamo anche il valore mostrato a video per pulirlo
                                    display_value = clean_value 
                                    break 
                        except Exception:
                            continue

            params_list.append({
                "name": name, 
                "value": display_value,
                "is_input_file": is_input_file,
                "input_url": input_url
            })

        summary_list.append({
            "id": node.get('id', 'N/A'),
            "type": node_type,
            "category": NODE_CATEGORIES.get(node_type, 'others'),
            "color": get_node_color(node_type),
            "params": params_list
        })
        
    return summary_list
    
# --- ALL UTILITY AND HELPER FUNCTIONS ARE DEFINED HERE, BEFORE ANY ROUTES ---

def safe_delete_file(filepath):
    """
    Safely delete a file by either moving it to trash (if DELETE_TO is configured)
    or permanently deleting it.
    
    Args:
        filepath: Path to the file to delete
        
    Raises:
        OSError: If deletion/move fails
    """
    if DELETE_TO and TRASH_FOLDER:
        # Move to trash (folder already validated at startup)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(filepath)
        trash_filename = f"{timestamp}_{filename}"
        trash_path = os.path.join(TRASH_FOLDER, trash_filename)
        
        # Handle duplicate filenames in trash
        counter = 1
        while os.path.exists(trash_path):
            name_without_ext, ext = os.path.splitext(filename)
            trash_filename = f"{timestamp}_{name_without_ext}_{counter}{ext}"
            trash_path = os.path.join(TRASH_FOLDER, trash_filename)
            counter += 1
        
        shutil.move(filepath, trash_path)
        print(f"INFO: Moved file to trash: {trash_path}")
    else:
        # Permanently delete
        os.remove(filepath)

def find_ffprobe_path():
    if FFPROBE_MANUAL_PATH and os.path.isfile(FFPROBE_MANUAL_PATH):
        try:
            subprocess.run([FFPROBE_MANUAL_PATH, "-version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            return FFPROBE_MANUAL_PATH
        except Exception: pass
    base_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    try:
        subprocess.run([base_name, "-version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        return base_name
    except Exception: pass
    print("WARNING: ffprobe not found. Video metadata analysis will be disabled.")
    return None

def _validate_and_get_workflow(json_string):
    try:
        data = json.loads(json_string)
        # Check for UI format (has 'nodes')
        workflow_data = data.get('workflow', data.get('prompt', data))
        
        if isinstance(workflow_data, dict):
            if 'nodes' in workflow_data:
                return json.dumps(workflow_data), 'ui'
            
            # Check for API format (keys are IDs, values have class_type)
            # Heuristic: Check if it looks like a dict of nodes
            is_api = False
            for k, v in workflow_data.items():
                if isinstance(v, dict) and 'class_type' in v:
                    is_api = True
                    break
            if is_api:
                return json.dumps(workflow_data), 'api'

    except Exception: 
        pass

    return None, None

def _scan_bytes_for_workflow(content_bytes):
    """
    Generator that yields all valid JSON objects found in the byte stream.
    Searches for matching curly braces.
    """
    try:
        stream_str = content_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return

    start_pos = 0
    while True:
        first_brace = stream_str.find('{', start_pos)
        if first_brace == -1:
            break
        
        open_braces = 0
        start_index = first_brace
        
        for i in range(start_index, len(stream_str)):
            char = stream_str[i]
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
            
            if open_braces == 0:
                candidate = stream_str[start_index : i + 1]
                # FIX: Use 'except Exception' to allow GeneratorExit to pass through
                try:
                    json.loads(candidate)
                    yield candidate
                except Exception:
                    pass
                
                # Move start_pos to after this candidate to find the next one
                start_pos = i + 1
                break
        else:
            # If loop finishes without open_braces hitting 0, no more valid JSON here
            break
            
def extract_workflow(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    video_exts = ['.mp4', '.mkv', '.webm', '.mov', '.avi']
    
    best_workflow = None
    
    def update_best(wf, wf_type):
        nonlocal best_workflow
        if wf_type == 'ui':
            best_workflow = wf
            return True # Found best, stop searching
        if wf_type == 'api' and best_workflow is None:
            best_workflow = wf
        return False

    if ext in video_exts:
        # --- FIX: Risoluzione del path anche nei processi Worker ---
        # Se la variabile globale è vuota (succede nel multiprocessing), la cerchiamo ora.
        current_ffprobe_path = FFPROBE_EXECUTABLE_PATH
        if not current_ffprobe_path:
             current_ffprobe_path = find_ffprobe_path()
        # -----------------------------------------------------------

        if current_ffprobe_path:
            try:
                # Usiamo current_ffprobe_path invece della globale
                cmd = [current_ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                data = json.loads(result.stdout)
                if 'format' in data and 'tags' in data['format']:
                    for value in data['format']['tags'].values():
                        if isinstance(value, str) and value.strip().startswith('{'):
                            wf, wf_type = _validate_and_get_workflow(value)
                            if wf:
                                if update_best(wf, wf_type): return best_workflow
            except Exception: pass
    else:
        try:
            with Image.open(filepath) as img:
                # Check standard keys first
                for key in ['workflow', 'prompt']:
                    val = img.info.get(key)
                    if val:
                        wf, wf_type = _validate_and_get_workflow(val)
                        if wf:
                            if update_best(wf, wf_type): return best_workflow

                exif_data = img.info.get('exif')
                if exif_data and isinstance(exif_data, bytes):
                    # Check for "workflow:" prefix which some tools use
                    try:
                        exif_str = exif_data.decode('utf-8', errors='ignore')
                        if 'workflow:{' in exif_str:
                            # Extract the JSON part after "workflow:"
                            start = exif_str.find('workflow:{') + len('workflow:')
                            # Try to parse this specific part first
                            for json_candidate in _scan_bytes_for_workflow(exif_str[start:].encode('utf-8')):
                                wf, wf_type = _validate_and_get_workflow(json_candidate)
                                if wf:
                                    if update_best(wf, wf_type): return best_workflow
                                    break 
                    except Exception: pass
                    
                    # Fallback to standard scan of the entire exif_data if not already returned
                    if best_workflow is None:
                        for json_str in _scan_bytes_for_workflow(exif_data):
                            wf, wf_type = _validate_and_get_workflow(json_str)
                            if wf:
                                if update_best(wf, wf_type): return best_workflow
        except Exception: pass

    # Raw byte scan (fallback for any file type)
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        for json_str in _scan_bytes_for_workflow(content):
            wf, wf_type = _validate_and_get_workflow(json_str)
            if wf:
                if update_best(wf, wf_type): return best_workflow
    except Exception: pass
                
    return best_workflow
    
def is_webp_animated(filepath):
    try:
        with Image.open(filepath) as img: return getattr(img, 'is_animated', False)
    except: return False

def format_duration(seconds):
    if not seconds or seconds < 0: return ""
    m, s = divmod(int(seconds), 60); h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def analyze_file_metadata(filepath):
    details = {'type': 'unknown', 'duration': '', 'dimensions': '', 'has_workflow': 0}
    ext_lower = os.path.splitext(filepath)[1].lower()
    type_map = {'.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'animated_image', '.mp4': 'video', '.webm': 'video', '.mov': 'video', '.mp3': 'audio', '.wav': 'audio', '.ogg': 'audio', '.flac': 'audio'}
    details['type'] = type_map.get(ext_lower, 'unknown')
    if details['type'] == 'unknown' and ext_lower == '.webp': details['type'] = 'animated_image' if is_webp_animated(filepath) else 'image'
    if 'image' in details['type']:
        try:
            with Image.open(filepath) as img: details['dimensions'] = f"{img.width}x{img.height}"
        except Exception: pass
    if extract_workflow(filepath): details['has_workflow'] = 1
    total_duration_sec = 0
    if details['type'] == 'video':
        try:
            cap = cv2.VideoCapture(filepath)
            if cap.isOpened():
                fps, count = cap.get(cv2.CAP_PROP_FPS), cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if fps > 0 and count > 0: total_duration_sec = count / fps
                details['dimensions'] = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                cap.release()
        except Exception: pass
    elif details['type'] == 'animated_image':
        try:
            with Image.open(filepath) as img:
                if getattr(img, 'is_animated', False):
                    if ext_lower == '.gif': total_duration_sec = sum(frame.info.get('duration', 100) for frame in ImageSequence.Iterator(img)) / 1000
                    elif ext_lower == '.webp': total_duration_sec = getattr(img, 'n_frames', 1) / WEBP_ANIMATED_FPS
        except Exception: pass
    if total_duration_sec > 0: details['duration'] = format_duration(total_duration_sec)
    return details

def create_thumbnail(filepath, file_hash, file_type):
    Image.MAX_IMAGE_PIXELS = None 
    if file_type in ['image', 'animated_image']:
        try:
            with Image.open(filepath) as img:
                fmt = 'gif' if img.format == 'GIF' else 'webp' if img.format == 'WEBP' else 'jpeg'
                cache_path = os.path.join(THUMBNAIL_CACHE_DIR, f"{file_hash}.{fmt}")
                if file_type == 'animated_image' and getattr(img, 'is_animated', False):
                    frames = [fr.copy() for fr in ImageSequence.Iterator(img)]
                    if frames:
                        for frame in frames: frame.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_WIDTH * 2), Image.Resampling.LANCZOS)
                        processed_frames = [frame.convert('RGBA').convert('RGB') for frame in frames]
                        if processed_frames:
                            processed_frames[0].save(cache_path, save_all=True, append_images=processed_frames[1:], duration=img.info.get('duration', 100), loop=img.info.get('loop', 0), optimize=True)
                else:
                    img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_WIDTH * 2), Image.Resampling.LANCZOS)
                    if img.mode != 'RGB': img = img.convert('RGB')
                    img.save(cache_path, 'JPEG', quality=85)
                return cache_path
        except Exception as e: print(f"ERROR (Pillow): Could not create thumbnail for {os.path.basename(filepath)}: {e}")
    elif file_type == 'video':
        try:
            cap = cv2.VideoCapture(filepath)
            success, frame = cap.read()
            cap.release()
            if success:
                cache_path = os.path.join(THUMBNAIL_CACHE_DIR, f"{file_hash}.jpeg")
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_WIDTH * 2), Image.Resampling.LANCZOS)
                img.save(cache_path, 'JPEG', quality=80)
                return cache_path
        except Exception as e: print(f"ERROR (OpenCV): Could not create thumbnail for {os.path.basename(filepath)}: {e}")
    return None

def extract_workflow_files_string(workflow_json_string):
    """
    Parses workflow and returns a normalized string containing ONLY filenames 
    (models, images, videos) used in the workflow.
    Filters out prompts, settings, and comments based on extensions and path structure.
    """
    if not workflow_json_string: return ""
    
    try:
        data = json.loads(workflow_json_string)
    except:
        return ""

    # Normalize structure (UI vs API format)
    nodes = []
    if 'nodes' in data and isinstance(data['nodes'], list):
        nodes = data['nodes'] # UI Format
    else:
        # API Format fallback
        for nid, n in data.items():
            if isinstance(n, dict):
                n['id'] = nid
                nodes.append(n)

    # 1. Blocklist Nodes (Comments)
    ignored_types = {'Note', 'NotePrimitive', 'Reroute', 'PrimitiveNode'}
    
    # 2. Whitelist Extensions (The most important filter)
    valid_extensions = {
        # Models
        '.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf', '.lora', '.sft',
        # Images
        '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff',
        # Video/Audio
        '.mp4', '.mov', '.webm', '.mkv', '.avi', '.mp3', '.wav', '.ogg', '.flac', '.m4a'
    }

    found_tokens = set()
    
    for node in nodes:
        node_type = node.get('type', node.get('class_type', ''))
        
        # Skip comment nodes
        if node_type in ignored_types:
            continue
            
        # Collect values from widgets_values (UI) or inputs (API)
        values_to_check = []
        
        # UI Format values
        if 'widgets_values' in node and isinstance(node['widgets_values'], list):
            values_to_check.extend(node['widgets_values'])
            
        # API Format inputs
        if 'inputs' in node and isinstance(node['inputs'], dict):
            values_to_check.extend(node['inputs'].values())

        for val in values_to_check:
            if isinstance(val, str) and val.strip():
                # Normalize immediately
                norm_val = normalize_smart_path(val.strip())
                
                # --- FILTER LOGIC ---
                
                # Check A: Valid Extension?
                # We check if the string ends with one of the valid extensions
                has_valid_ext = any(norm_val.endswith(ext) for ext in valid_extensions)
                
                # Check B: Absolute Path? (For folders or files without standard extensions)
                # Matches "c:/..." or "/home/..."
                # Must be shorter than 260 chars to avoid catching long prompts starting with /
                is_abs_path = (len(norm_val) < 260) and (
                    (len(norm_val) > 2 and norm_val[1] == ':') or # Windows Drive (c:)
                    norm_val.startswith('/') # Unix/Linux root
                )

                # Keep ONLY if it looks like a file/path
                if has_valid_ext or is_abs_path:
                    found_tokens.add(norm_val)

    return " ||| ".join(sorted(list(found_tokens)))

def extract_workflow_prompt_string(workflow_json_string):
    """
    Parses workflow and extracts ALL text prompts found in nodes.
    
    New Logic (Broad Extraction with Blacklist):
    Scans all nodes for text parameters, filtering out technical values,
    filenames, specific default prompt examples defined in global config,
    and strictly ignoring Comment/Note nodes (including Markdown notes).
    
    Returns: A joined string of all found text prompts.
    """
    if not workflow_json_string: return ""
    
    try:
        data = json.loads(workflow_json_string)
    except:
        return ""

    nodes = []
    
    # Normalize Structure
    if 'nodes' in data and isinstance(data['nodes'], list):
        nodes = data['nodes'] # UI Format
    else:
        # API Format fallback
        for nid, n in data.items():
            if isinstance(n, dict):
                n['id'] = nid
                nodes.append(n)
    
    found_texts = set()
    
    # 1. Types to strictly ignore (Comments, Routing, structural nodes)
    # Updated to include MarkdownNote and other common note types
    ignored_types = {
        'Note', 'NotePrimitive', 'Reroute', 'PrimitiveNode', 
        'ShowText', 'PreviewText', 'ViewInfo', 'SaveImage', 'PreviewImage',
        'MarkdownNote', 'Text Note', 'StickyNote'
    }
    
    for node in nodes:
        node_type = node.get('type', node.get('class_type', '')).strip()
        
        # Skip ignored node types
        if node_type in ignored_types: continue

        # Gather values to check
        values_to_check = []
        
        # UI Format: check 'widgets_values'
        if 'widgets_values' in node and isinstance(node['widgets_values'], list):
            values_to_check.extend(node['widgets_values'])
            
        # API Format: check 'inputs' values
        if 'inputs' in node and isinstance(node['inputs'], dict):
            values_to_check.extend(node['inputs'].values())

        # Analyze values
        for val in values_to_check:
            # We are only interested in Strings
            if isinstance(val, str) and val.strip():
                text = val.strip()
                
                # --- FILTERING LOGIC ---
                
                # A. Blacklist Check (Uses the Global Configuration Variable)
                if text in WORKFLOW_PROMPT_BLACKLIST:
                    continue
                
                # B. Ignore short strings (likely garbage or symbols)
                if len(text) < 2: continue
                
                # C. Ignore numeric strings (seeds, steps, cfg, dimensions)
                try:
                    float(text)
                    continue 
                except ValueError:
                    pass 
                
                # D. Ignore filenames (extensions)
                if '.' in text and ' ' not in text:
                    ext = os.path.splitext(text)[1].lower()
                    if ext in ['.safetensors', '.ckpt', '.pt', '.png', '.jpg', '.webp']:
                        continue

                # E. Ignore common tech keywords
                tech_keywords = {'euler', 'dpm', 'normal', 'karras', 'gpu', 'cpu', 'auto', 'enable', 'disable', 'fixed', 'increment', 'randomized'}
                if text.lower() in tech_keywords:
                    continue

                # If passed all filters, it's likely a prompt
                found_texts.add(text)

    # Join with a separator
    return " , ".join(list(found_texts))
    
def process_single_file(filepath):
    """
    Worker function to perform all heavy processing for a single file.
    Designed to be run in a parallel process pool.
    """
    try:
        mtime = os.path.getmtime(filepath)
        metadata = analyze_file_metadata(filepath)
        file_hash_for_thumbnail = hashlib.md5((filepath + str(mtime)).encode()).hexdigest()
        
        if not glob.glob(os.path.join(THUMBNAIL_CACHE_DIR, f"{file_hash_for_thumbnail}.*")):
            create_thumbnail(filepath, file_hash_for_thumbnail, metadata['type'])
        
        file_id = hashlib.md5(filepath.encode()).hexdigest()
        file_size = os.path.getsize(filepath)
        
        # Extract workflow data
        workflow_files_content = ""
        workflow_prompt_content = "" 
        
        if metadata['has_workflow']:
            wf_json = extract_workflow(filepath)
            if wf_json:
                workflow_files_content = extract_workflow_files_string(wf_json)
                workflow_prompt_content = extract_workflow_prompt_string(wf_json) # NEW
        
        return (
            file_id, filepath, mtime, os.path.basename(filepath),
            metadata['type'], metadata['duration'], metadata['dimensions'], 
            metadata['has_workflow'], file_size, time.time(), 
            workflow_files_content, 
            workflow_prompt_content # NEW return value
        )
    except Exception as e:
        print(f"ERROR: Failed to process file {os.path.basename(filepath)} in worker: {e}")
        return None
        
def get_db_connection():
    # Timeout increased to 60s to be patient with the Indexer
    conn = sqlite3.connect(DATABASE_FILE, timeout=60)
    conn.row_factory = sqlite3.Row
    # CONCURRENCY OPTIMIZATION:
    # WAL: Allows non-blocking reads.
    # NORMAL: Makes transactions (commits) instant, reducing lock time drastically.
    conn.execute('PRAGMA journal_mode=WAL;') 
    conn.execute('PRAGMA synchronous=NORMAL;') 
    return conn

def init_db(conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
        
    try:
        # 1. CORE TABLE CREATION (Safe: creates only if missing)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY, 
                path TEXT NOT NULL UNIQUE, 
                mtime REAL NOT NULL,
                name TEXT NOT NULL, 
                type TEXT, 
                duration TEXT, 
                dimensions TEXT,
                has_workflow INTEGER, 
                is_favorite INTEGER DEFAULT 0, 
                size INTEGER DEFAULT 0,
                last_scanned REAL DEFAULT 0,
                workflow_files TEXT DEFAULT '',
                workflow_prompt TEXT DEFAULT '',
                ai_last_scanned REAL DEFAULT 0,
                ai_caption TEXT,
                ai_embedding BLOB,
                ai_error TEXT
            )
        ''')

        # 2. AI TABLE CREATION
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_search_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                query TEXT NOT NULL,
                limit_results INTEGER DEFAULT 100,
                status TEXT DEFAULT 'pending', 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL
            );
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                score REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES ai_search_queue(session_id)
            );
        ''')
        
        conn.execute('CREATE INDEX IF NOT EXISTS idx_queue_status ON ai_search_queue(status);')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_results_session ON ai_search_results(session_id);')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_indexing_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_id TEXT,
                status TEXT DEFAULT 'pending', 
                force_index INTEGER DEFAULT 0,
                params TEXT DEFAULT '{}',
                created_at REAL,
                updated_at REAL,
                error_msg TEXT,
                UNIQUE(file_path) ON CONFLICT REPLACE
            );
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_ai_idx_status ON ai_indexing_queue(status);')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_watched_folders (
                path TEXT PRIMARY KEY,
                recursive INTEGER DEFAULT 0,
                added_at REAL
            );
        ''')
        
        conn.execute("CREATE TABLE IF NOT EXISTS ai_metadata (key TEXT PRIMARY KEY, value TEXT, updated_at REAL)")

        # 3. COLUMN MIGRATION
        required_columns = {
            'last_scanned': 'REAL DEFAULT 0',
            'workflow_files': "TEXT DEFAULT ''",
            'workflow_prompt': "TEXT DEFAULT ''",
            'ai_last_scanned': 'REAL DEFAULT 0',
            'ai_caption': 'TEXT',
            'ai_embedding': 'BLOB',
            'ai_error': 'TEXT'
        }

        cursor = conn.execute("PRAGMA table_info(files)")
        existing_columns = {row['name'] for row in cursor.fetchall()}

        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                print(f"INFO: Updating Database Schema... Adding missing column '{col_name}'")
                try:
                    conn.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"WARNING: Could not add column {col_name}: {e}")

        # 4. SCHEMA VERSION CONTROL (Versioning)
        # We check and update the internal version ONLY if everything above succeeded.
        try:
            cur = conn.execute("PRAGMA user_version")
            current_ver = cur.fetchone()[0]
            
            if current_ver != DB_SCHEMA_VERSION:
                print(f"INFO: Updating Database Schema Version: {current_ver} -> {DB_SCHEMA_VERSION}")
                conn.execute(f"PRAGMA user_version = {DB_SCHEMA_VERSION}")
        except Exception as e:
            print(f"WARNING: Could not update DB schema version: {e}")

        # Final Commit for all operations
        conn.commit()
        
    except Exception as e:
        print(f"CRITICAL DATABASE ERROR: {e}")
        
    finally:
        if close_conn: conn.close()
        
def get_dynamic_folder_config(force_refresh=False):
    global folder_config_cache
    if folder_config_cache is not None and not force_refresh:
        return folder_config_cache

    print("INFO: Refreshing folder configuration by scanning directory tree...")

    base_path_normalized = os.path.normpath(BASE_OUTPUT_PATH).replace('\\', '/')
    
    try:
        root_mtime = os.path.getmtime(BASE_OUTPUT_PATH)
    except OSError:
        root_mtime = time.time()

    dynamic_config = {
        '_root_': {
            'display_name': 'Main',
            'path': base_path_normalized,
            'relative_path': '',
            'parent': None,
            'children': [],
            'mtime': root_mtime,
            'is_watched': False,
            'is_explicitly_watched': False # NEW flag
        }
    }

    try:
        # --- NEW: Fetch Watched Status with Recursive Logic ---
        # We store tuples of (normalized_path, is_recursive_bool)
        watched_rules = [] 
        if ENABLE_AI_SEARCH:
            try:
                with get_db_connection() as conn:
                    rows = conn.execute("SELECT path, recursive FROM ai_watched_folders").fetchall()
                    for r in rows:
                        # Normalize watched paths for consistent comparison (force forward slashes)
                        w_path = os.path.normpath(r['path']).replace('\\', '/')
                        watched_rules.append((w_path, bool(r['recursive'])))
            except: pass
        # ---------------------------------

        all_folders = {}
        for dirpath, dirnames, _ in os.walk(BASE_OUTPUT_PATH):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in [THUMBNAIL_CACHE_FOLDER_NAME, SQLITE_CACHE_FOLDER_NAME, ZIP_CACHE_FOLDER_NAME, AI_MODELS_FOLDER_NAME]]
            for dirname in dirnames:
                full_path = os.path.normpath(os.path.join(dirpath, dirname)).replace('\\', '/')
                relative_path = os.path.relpath(full_path, BASE_OUTPUT_PATH).replace('\\', '/')
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    mtime = time.time()
                
                all_folders[relative_path] = {
                    'full_path': full_path,
                    'display_name': dirname,
                    'mtime': mtime
                }

        sorted_paths = sorted(all_folders.keys(), key=lambda x: x.count('/'))

        for rel_path in sorted_paths:
            folder_data = all_folders[rel_path]
            key = path_to_key(rel_path)
            parent_rel_path = os.path.dirname(rel_path).replace('\\', '/')
            parent_key = '_root_' if parent_rel_path == '.' or parent_rel_path == '' else path_to_key(parent_rel_path)

            if parent_key in dynamic_config:
                dynamic_config[parent_key]['children'].append(key)

            # --- Check if this folder is Watched (Directly or via Parent) ---
            current_path = folder_data['full_path']
            is_watched_folder = False
            is_explicitly_watched = False # NEW flag
            
            for w_path, is_recursive in watched_rules:
                # 1. Exact Match (Explicit)
                if current_path == w_path:
                    is_watched_folder = True
                    is_explicitly_watched = True
                    break
                # 2. Child of a Recursive Watched Folder (Implicit)
                if is_recursive and current_path.startswith(w_path + '/'):
                    is_watched_folder = True
                    # is_explicitly_watched remains False
                    break

            dynamic_config[key] = {
                'display_name': folder_data['display_name'],
                'path': current_path,
                'relative_path': rel_path,
                'parent': parent_key,
                'children': [],
                'mtime': folder_data['mtime'],
                'is_watched': is_watched_folder,
                'is_explicitly_watched': is_explicitly_watched # Pass to frontend
            }
    except FileNotFoundError:
        print(f"WARNING: The base directory '{BASE_OUTPUT_PATH}' was not found.")
    
    folder_config_cache = dynamic_config
    return dynamic_config
    
# --- BACKGROUND WATCHER THREAD ---
def background_watcher_task():
    """
    Periodically scans watched folders.
    Ensures TRUE incremental indexing:
    1. Ignores files currently 'pending' or 'processing'.
    2. Checks 'files' DB: if ai_data is missing or outdated -> queues it.
    3. Revives 'completed'/'error' queue entries back to 'pending' if the file is dirty.
    """
    print("INFO: AI Background Watcher started (Incremental Mode).")
    while True:
        try:
            if ENABLE_AI_SEARCH:
                with get_db_connection() as conn:
                    # 1. Cleanup very old jobs to keep table light (> 3 days)
                    conn.execute("DELETE FROM ai_indexing_queue WHERE status='completed' AND created_at < ?", (time.time() - 259200,))
                    
                    watched = conn.execute("SELECT path, recursive FROM ai_watched_folders").fetchall()
                    
                    for row in watched:
                        folder_path = row['path'] 
                        is_recursive = row['recursive']
                        
                        valid_exts = {'.png','.jpg','.jpeg','.webp','.gif','.mp4','.mov','.avi','.webm'}
                        EXCLUDED = {'.thumbnails_cache', '.sqlite_cache', '.zip_downloads', '.AImodels', 'venv', 'venv-ai', '.git'}
                        
                        files_to_check = []

                        if os.path.isdir(folder_path):
                            if is_recursive:
                                for root, dirs, files in os.walk(folder_path, topdown=True):
                                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in EXCLUDED]
                                    for f in files:
                                        if os.path.splitext(f)[1].lower() in valid_exts:
                                            files_to_check.append(os.path.join(root, f))
                            else:
                                try:
                                    for f in os.listdir(folder_path):
                                        full = os.path.join(folder_path, f)
                                        if os.path.isfile(full) and os.path.splitext(f)[1].lower() in valid_exts:
                                            files_to_check.append(full)
                                except: pass
                        
                        # Process Candidates
                        for raw_path in files_to_check:
                            p_key = get_standardized_path(raw_path)
                            
                            # 1. CHECK ACTIVE STATUS
                            # Only skip if it is actively waiting or running. 
                            # Do NOT skip if it is 'completed' or 'error' (we might need to retry/update).
                            active_job = conn.execute("""
                                SELECT 1 FROM ai_indexing_queue 
                                WHERE file_path = ? AND status IN ('pending', 'processing', 'waiting_gpu')
                            """, (p_key,)).fetchone()
                            
                            if active_job: 
                                continue # Busy, come back later

                            # 2. CHECK FILE STATE IN DB
                            # We need to find the file ID and its scan timestamp
                            # We use the robust path lookup logic (normalized slash match)
                            # to ensure we find the record even if slashes differ.
                            
                            # Try exact match first
                            file_row = conn.execute("SELECT id, mtime, ai_last_scanned FROM files WHERE path = ?", (raw_path,)).fetchone()
                            
                            # Fallback: Normalized Match
                            if not file_row:
                                norm_p = raw_path.replace('\\', '/')
                                file_row = conn.execute("SELECT id, mtime, ai_last_scanned FROM files WHERE REPLACE(path, '\\', '/') = ?", (norm_p,)).fetchone()

                            if not file_row:
                                # File exists on disk but NOT in DB. 
                                # We cannot index it yet (missing metadata/dimensions).
                                # The main 'files' sync must run first. We skip it silently.
                                continue
                            
                            file_id = file_row['id']
                            last_scan_ts = file_row['ai_last_scanned'] if file_row['ai_last_scanned'] is not None else 0
                            mtime = file_row['mtime']
                            
                            # 3. DIRTY CHECK (The Core Incremental Logic)
                            needs_index = False
                            
                            if last_scan_ts == 0:
                                needs_index = True # Never scanned or Reset by user
                            elif last_scan_ts < mtime:
                                needs_index = True # File modified on disk after last scan
                            
                            if needs_index:
                                # UPSERT: If exists (e.g. 'completed'), revive to 'pending'. If new, insert.
                                # This fixes the issue where completed items were ignored even after reset.
                                conn.execute("""
                                    INSERT INTO ai_indexing_queue 
                                    (file_path, file_id, status, created_at, force_index, params)
                                    VALUES (?, ?, 'pending', ?, 0, '{}')
                                    ON CONFLICT(file_path) DO UPDATE SET
                                        status = 'pending',
                                        file_id = excluded.file_id,
                                        created_at = excluded.created_at
                                """, (p_key, file_id, time.time()))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"Watcher Loop Error: {e}")
            
        time.sleep(10) # Faster check cycle (10s instead of 60s) to feel responsive
        
def full_sync_database(conn):
    print("INFO: Starting full file scan...")
    start_time = time.time()

    all_folders = get_dynamic_folder_config(force_refresh=True)
    db_files = {row['path']: row['mtime'] for row in conn.execute('SELECT path, mtime FROM files').fetchall()}
    
    disk_files = {}
    print("INFO: Scanning directories on disk...")
    for folder_data in all_folders.values():
        folder_path = folder_data['path']
        if not os.path.isdir(folder_path): continue
        try:
            for name in os.listdir(folder_path):
                filepath = os.path.join(folder_path, name)
                if os.path.isfile(filepath) and os.path.splitext(name)[1].lower() not in ['.json', '.sqlite']:
                    disk_files[filepath] = os.path.getmtime(filepath)
        except OSError as e:
            print(f"WARNING: Could not access folder {folder_path}: {e}")
            
    db_paths = set(db_files.keys())
    disk_paths = set(disk_files.keys())
    
    to_delete = db_paths - disk_paths
    to_add = disk_paths - db_paths
    to_check = disk_paths & db_paths
    to_update = {path for path in to_check if int(disk_files.get(path, 0)) > int(db_files.get(path, 0))}
    
    files_to_process = list(to_add.union(to_update))
    
    if files_to_process:
        print(f"INFO: Processing {len(files_to_process)} files in parallel using up to {MAX_PARALLEL_WORKERS or 'all'} CPU cores...")
        
        results = []
        # --- CORRECT BLOCK FOR PROGRESS BAR ---
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
            # Submit all jobs to the pool and get future objects
            futures = {executor.submit(process_single_file, path): path for path in files_to_process}
            
            # Create the progress bar with the correct total
            with tqdm(total=len(files_to_process), desc="Processing files") as pbar:
                # Iterate over the jobs as they are COMPLETED
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
                    # Update the bar by 1 step for each completed job
                    pbar.update(1)

        if results:
            print(f"INFO: Inserting {len(results)} processed records into the database...")
            for i in range(0, len(results), BATCH_SIZE):
                batch = results[i:i + BATCH_SIZE]
                conn.executemany("""
                    INSERT INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow, size, last_scanned, workflow_files, workflow_prompt) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        path = excluded.path,
                        name = excluded.name,
                        type = excluded.type,
                        duration = excluded.duration,
                        dimensions = excluded.dimensions,
                        has_workflow = excluded.has_workflow,
                        size = excluded.size,
                        last_scanned = excluded.last_scanned,
                        workflow_files = excluded.workflow_files,
                        workflow_prompt = excluded.workflow_prompt,
                        
                        -- LOGICA CONDIZIONALE:
                        is_favorite = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0  
                            ELSE files.is_favorite                     
                        END,
                        
                        ai_caption = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL 
                            ELSE files.ai_caption                        
                        END,
                        
                        ai_embedding = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL 
                            ELSE files.ai_embedding 
                        END,

                        ai_last_scanned = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0 
                            ELSE files.ai_last_scanned 
                        END,

                        -- Aggiorna mtime alla fine
                        mtime = excluded.mtime
                """, batch) 
                conn.commit()

    if to_delete:
        print(f"INFO: Removing {len(to_delete)} obsolete file entries from the database...")
        conn.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in to_delete])
        conn.commit()

    print(f"INFO: Full scan completed in {time.time() - start_time:.2f} seconds.")
    
def sync_folder_on_demand(folder_path):
    yield f"data: {json.dumps({'message': 'Checking folder for changes...', 'current': 0, 'total': 1})}\n\n"
    
    try:
        with get_db_connection() as conn:
            disk_files, valid_extensions = {}, {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.mkv', '.webm', '.mov', '.avi', '.mp3', '.wav', '.ogg', '.flac'}
            if os.path.isdir(folder_path):
                for name in os.listdir(folder_path):
                    filepath = os.path.join(folder_path, name)
                    if os.path.isfile(filepath) and os.path.splitext(name)[1].lower() in valid_extensions:
                        disk_files[filepath] = os.path.getmtime(filepath)
            
            db_files_query = conn.execute("SELECT path, mtime FROM files WHERE path LIKE ?", (folder_path + os.sep + '%',)).fetchall()
            db_files = {row['path']: row['mtime'] for row in db_files_query if os.path.normpath(os.path.dirname(row['path'])) == os.path.normpath(folder_path)}
            
            disk_filepaths, db_filepaths = set(disk_files.keys()), set(db_files.keys())
            files_to_add = disk_filepaths - db_filepaths
            files_to_delete = db_filepaths - disk_filepaths
            files_to_update = {path for path in (disk_filepaths & db_filepaths) if int(disk_files[path]) > int(db_files[path])}
            
            if not files_to_add and not files_to_update and not files_to_delete:
                yield f"data: {json.dumps({'message': 'Folder is up-to-date.', 'status': 'no_changes', 'current': 1, 'total': 1})}\n\n"
                return

            files_to_process = list(files_to_add.union(files_to_update))
            total_files = len(files_to_process)
            
            if total_files > 0:
                yield f"data: {json.dumps({'message': f'Found {total_files} new/modified files. Processing...', 'current': 0, 'total': total_files})}\n\n"
                
                data_to_upsert = []
                processed_count = 0

                with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
                    futures = {executor.submit(process_single_file, path): path for path in files_to_process}
                    
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result:
                            data_to_upsert.append(result)
                        
                        processed_count += 1
                        path = futures[future]
                        progress_data = {
                            'message': f'Processing: {os.path.basename(path)}',
                            'current': processed_count,
                            'total': total_files
                        }
                        yield f"data: {json.dumps(progress_data)}\n\n"

                if data_to_upsert: 
                    conn.executemany("""
                        INSERT INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow, size, last_scanned, workflow_files, workflow_prompt) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            path = excluded.path,
                            name = excluded.name,
                            type = excluded.type,
                            duration = excluded.duration,
                            dimensions = excluded.dimensions,
                            has_workflow = excluded.has_workflow,
                            size = excluded.size,
                            last_scanned = excluded.last_scanned,
                            workflow_files = excluded.workflow_files,
                            workflow_prompt = excluded.workflow_prompt,
                        
                            -- LOGICA CONDIZIONALE:
                            is_favorite = CASE 
                                WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0  
                                ELSE files.is_favorite                     
                            END,
                            
                            ai_caption = CASE 
                                WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL 
                                ELSE files.ai_caption                        
                            END,
                            
                            ai_embedding = CASE 
                                WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL 
                                ELSE files.ai_embedding 
                            END,

                            ai_last_scanned = CASE 
                                WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0 
                                ELSE files.ai_last_scanned 
                            END,

                            -- Aggiorna mtime alla fine
                            mtime = excluded.mtime
                    """, data_to_upsert) 
                    
            if files_to_delete:
                conn.executemany("DELETE FROM files WHERE path IN (?)", [(p,) for p in files_to_delete])

            conn.commit()
            yield f"data: {json.dumps({'message': 'Sync complete. Reloading...', 'status': 'reloading', 'current': total_files, 'total': total_files})}\n\n"

    except Exception as e:
        error_message = f"Error during sync: {e}"
        print(f"ERROR: {error_message}")
        yield f"data: {json.dumps({'message': error_message, 'current': 1, 'total': 1, 'error': True})}\n\n"
        
def scan_folder_and_extract_options(folder_path, recursive=False):
    """
    Scans the physical folder to count files and extract metadata.
    Supports recursive mode to include subfolders in the count.
    """
    extensions, prefixes = set(), set()
    file_count = 0
    try:
        if not os.path.isdir(folder_path): 
            return 0, [], []
        
        if recursive:
            # Recursive scan using os.walk
            for root, dirs, files in os.walk(folder_path):
                # Filter out hidden/protected folders in-place
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [THUMBNAIL_CACHE_FOLDER_NAME, SQLITE_CACHE_FOLDER_NAME, ZIP_CACHE_FOLDER_NAME, AI_MODELS_FOLDER_NAME]]
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext and ext not in ['.json', '.sqlite']:
                        file_count += 1
                        extensions.add(ext.lstrip('.'))
                        if '_' in filename: prefixes.add(filename.split('_')[0])
        else:
            # Single folder scan using os.scandir (faster)
            for entry in os.scandir(folder_path):
                if entry.is_file():
                    filename = entry.name
                    ext = os.path.splitext(filename)[1].lower()
                    if ext and ext not in ['.json', '.sqlite']:
                        file_count += 1
                        extensions.add(ext.lstrip('.'))
                        if '_' in filename: prefixes.add(filename.split('_')[0])
                        
    except Exception as e: 
        print(f"ERROR: Could not scan folder '{folder_path}': {e}")
        
    return file_count, sorted(list(extensions)), sorted(list(prefixes))
    
def initialize_gallery():
    print("INFO: Initializing gallery...")
    global FFPROBE_EXECUTABLE_PATH
    FFPROBE_EXECUTABLE_PATH = find_ffprobe_path()
    os.makedirs(THUMBNAIL_CACHE_DIR, exist_ok=True)
    os.makedirs(SQLITE_CACHE_DIR, exist_ok=True)
    
    with get_db_connection() as conn:
        try:
            init_db(conn) 
            # 4. Fallback check for empty DB on existing install
            file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            if file_count == 0:
                print(f"{Colors.BLUE}INFO: Database file exists but is empty. Scanning...{Colors.RESET}")
                full_sync_database(conn)

        except sqlite3.DatabaseError as e:
            print(f"ERROR initializing database: {e}")
            
def get_filter_options_from_db(conn, scope, folder_path=None, recursive=False):
    """
    Extracts extensions and prefixes for dropdowns using a robust 
    Python-side path filtering to handle mixed slashes and cross-platform issues.
    """
    extensions, prefixes = set(), set()
    prefix_limit_reached = False
    
    # Identical helper to gallery_view for consistency
    def safe_path_norm(p):
        if not p: return ""
        return os.path.normpath(str(p).replace('\\', '/')).replace('\\', '/').lower().rstrip('/')

    try:
        # We fetch all names and paths. For very large DBs (100k+ files), 
        # this is still faster than failing with a wrong SQL LIKE.
        cursor = conn.execute("SELECT name, path FROM files")
        
        target_norm = safe_path_norm(folder_path)

        for row in cursor:
            f_path_raw = row['path']
            f_name = row['name']
            
            # NORMALIZATION STEP
            f_path_norm = safe_path_norm(f_path_raw)
            f_dir_norm = safe_path_norm(os.path.dirname(f_path_norm))

            # FILTERING LOGIC (Same as Gallery View)
            show_file = False
            if scope == 'global':
                show_file = True
            elif recursive:
                # Check if it's inside the target folder tree
                if f_path_norm.startswith(target_norm + '/'):
                    show_file = True
            else:
                # Strict local: must be in this exact folder
                if f_dir_norm == target_norm:
                    show_file = True

            if show_file:
                # 1. Extensions
                _, ext = os.path.splitext(f_name)
                if ext: 
                    extensions.add(ext.lstrip('.').lower())
                
                # 2. Prefixes
                if not prefix_limit_reached and '_' in f_name:
                    pfx = f_name.split('_')[0]
                    if pfx:
                        prefixes.add(pfx)
                        if len(prefixes) > MAX_PREFIX_DROPDOWN_ITEMS:
                            prefix_limit_reached = True
                            prefixes.clear()
                            
    except Exception as e: 
        print(f"Error extracting options: {e}")
        
    return sorted(list(extensions)), sorted(list(prefixes)), prefix_limit_reached
    

# --- FLASK ROUTES ---
@app.route('/galleryout/')
@app.route('/')
def gallery_redirect_base():
    return redirect(url_for('gallery_view', folder_key='_root_'))

# AI QUEUE SUBMISSION ROUTE
@app.route('/galleryout/ai_queue', methods=['POST'])
def ai_queue_search():
    """
    Receives a search query from the frontend and adds it to the DB queue.
    Also performs basic housekeeping (cleaning old requests).
    """
    data = request.json
    query = data.get('query', '').strip()
    # FIX: Leggi il limite dal JSON (default 100 se non presente)
    limit = int(data.get('limit', 100)) 
    
    if not query:
        return jsonify({'status': 'error', 'message': 'Query cannot be empty'}), 400
        
    session_id = str(uuid.uuid4())
    
    try:
        with get_db_connection() as conn:
            # 1. Housekeeping
            conn.execute("DELETE FROM ai_search_queue WHERE created_at < datetime('now', '-1 hour')")
            conn.execute("DELETE FROM ai_search_results WHERE session_id NOT IN (SELECT session_id FROM ai_search_queue)")
            
            # 2. Insert new request WITH LIMIT
            # Assicurati che la query SQL includa la colonna limit_results
            conn.execute('''
                INSERT INTO ai_search_queue (session_id, query, limit_results, status)
                VALUES (?, ?, ?, 'pending')
            ''', (session_id, query, limit))
            conn.commit()
            
        return jsonify({'status': 'queued', 'session_id': session_id})
    except Exception as e:
        print(f"AI Queue Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
# AI STATUS CHECK ROUTE (POLLING)
@app.route('/galleryout/ai_check/<session_id>', methods=['GET'])
def ai_check_status(session_id):
    """Checks the status of a specific search session."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT status FROM ai_search_queue WHERE session_id = ?", (session_id,)).fetchone()
        
        if not row:
            return jsonify({'status': 'not_found'})
            
        return jsonify({'status': row['status']})

@app.route('/galleryout/sync_status/<string:folder_key>')
def sync_status(folder_key):
    folders = get_dynamic_folder_config()
    if folder_key not in folders:
        abort(404)
    folder_path = folders[folder_key]['path']
    return Response(sync_folder_on_demand(folder_path), mimetype='text/event-stream')

@app.route('/galleryout/api/search_options')
def api_search_options():
    scope = request.args.get('scope', 'local')
    folder_key = request.args.get('folder_key', '_root_')
    is_rec = request.args.get('recursive', 'false').lower() == 'true' # Added
    
    folders = get_dynamic_folder_config()
    folder_path = folders.get(folder_key, {}).get('path', BASE_OUTPUT_PATH)
    
    with get_db_connection() as conn:
        # Now passing the recursive flag to the options extractor
        exts, pfxs, limit_reached = get_filter_options_from_db(conn, scope, folder_path, recursive=is_rec)
        
    return jsonify({'extensions': exts, 'prefixes': pfxs, 'prefix_limit_reached': limit_reached})

# --- AI MANAGER API ROUTES ---
@app.route('/galleryout/ai_indexing/reset', methods=['POST'])
def ai_indexing_reset():
    """
    Resets AI metadata (caption, embedding, timestamp) for specific files or a whole folder.
    CRITICAL: Also removes these files from the indexing queue to prevent re-processing.
    """
    if not ENABLE_AI_SEARCH: return jsonify({'status':'error'})
    data = request.json
    
    # Mode 1: Batch IDs
    file_ids = data.get('file_ids', [])
    
    # Mode 2: Folder Path
    folder_key = data.get('folder_key')
    recursive = data.get('recursive', False)
    
    count = 0
    
    try:
        with get_db_connection() as conn:
            ids_to_wipe = []
            
            # Case A: Specific File IDs (Selection or Lightbox)
            if file_ids:
                ids_to_wipe = file_ids
            
            # Case B: Folder (Recursive or Flat)
            elif folder_key:
                folders = get_dynamic_folder_config()
                if folder_key in folders:
                    folder_path = folders[folder_key]['path']
                    # Normalize for robust DB lookup
                    target_norm = os.path.normpath(folder_path).replace('\\', '/').lower()
                    if not target_norm.endswith('/'): target_norm += '/'
                    
                    # Fetch candidates to wipe
                    cursor = conn.execute("SELECT id, path FROM files WHERE ai_caption IS NOT NULL OR ai_embedding IS NOT NULL")
                    for row in cursor:
                        f_path = row['path']
                        # Normalize DB path
                        f_path_norm = os.path.normpath(f_path).replace('\\', '/').lower()
                        
                        is_match = False
                        if recursive:
                            if f_path_norm.startswith(target_norm): is_match = True
                        else:
                            # Strict parent check
                            parent_norm = os.path.dirname(f_path_norm).replace('\\', '/').lower() + '/'
                            if parent_norm == target_norm: is_match = True
                            
                        if is_match:
                            ids_to_wipe.append(row['id'])

            if ids_to_wipe:
                # Process in chunks to avoid SQL limits
                chunk_size = 500
                for i in range(0, len(ids_to_wipe), chunk_size):
                    chunk = ids_to_wipe[i:i + chunk_size]
                    placeholders = ','.join(['?'] * len(chunk))
                    
                    # 1. WIPE METADATA (Instant)
                    conn.execute(f"""
                        UPDATE files 
                        SET ai_caption=NULL, ai_embedding=NULL, ai_last_scanned=0, ai_error=NULL 
                        WHERE id IN ({placeholders})
                    """, chunk)
                    
                    # 2. REMOVE FROM PROCESSING QUEUE (Critical fix)
                    # We must delete pending jobs for these files to stop the worker from indexing them
                    conn.execute(f"""
                        DELETE FROM ai_indexing_queue 
                        WHERE file_id IN ({placeholders})
                    """, chunk)
                    
                count = len(ids_to_wipe)
                conn.commit()
                
        return jsonify({'status': 'success', 'count': count, 'message': f'AI data erased and queue cleared for {count} files.'})
        
    except Exception as e:
        print(f"AI Reset Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/galleryout/ai_indexing/add_files', methods=['POST'])
def ai_indexing_add_files():
    if not ENABLE_AI_SEARCH: return jsonify({'status':'error'})
    data = request.json
    file_ids = data.get('file_ids', [])
    force_index = data.get('force', False)
    params = json.dumps({'beams': data.get('beams', 3), 'precision': data.get('precision', 'fp16')})
    
    count = 0
    skipped = 0
    
    with get_db_connection() as conn:
        # --- NEW: WIPE DATA IF FORCED ---
        if force_index and file_ids:
            # We must wipe database fields before queuing
            placeholders = ','.join(['?'] * len(file_ids))
            conn.execute(f"""
                UPDATE files 
                SET ai_caption=NULL, ai_embedding=NULL, ai_last_scanned=0, ai_error=NULL 
                WHERE id IN ({placeholders})
            """, file_ids)

        for fid in file_ids:
            # Check current status
            row = conn.execute("SELECT path, ai_last_scanned FROM files WHERE id=?", (fid,)).fetchone()
            if row:
                # --- INCREMENTAL LOGIC ---
                has_ai_data = row['ai_last_scanned'] and row['ai_last_scanned'] > 0
                
                if not force_index and has_ai_data:
                    skipped += 1
                    continue
                
                p_key = get_standardized_path(row['path'])
                # FIX: Use "ON CONFLICT DO UPDATE" to reset status to 'pending'
                conn.execute("""
                    INSERT INTO ai_indexing_queue (file_path, file_id, status, created_at, force_index, params)
                    VALUES (?, ?, 'pending', ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        status = 'pending',
                        force_index = excluded.force_index,
                        created_at = excluded.created_at,
                        params = excluded.params
                """, (p_key, fid, time.time(), 1 if force_index else 0, params))
                count += 1
        conn.commit()
    
    # --- FEEDBACK MESSAGES ---
    if count == 0 and skipped > 0:
        return jsonify({
            'status': 'warning', 
            'message': "All selected files are already indexed. Enable 'Force Re-Index' to overwrite.",
            'count': 0
        })
        
    msg = f"Queued {count} files."
    if skipped > 0:
        msg += f" (Skipped {skipped} already indexed)"
        
    return jsonify({'status': 'success', 'count': count, 'message': msg})
    
@app.route('/galleryout/ai_indexing/add_folder', methods=['POST'])
def ai_indexing_add_folder():
    if not ENABLE_AI_SEARCH: return jsonify({'status':'error'})
    data = request.json
    
    folder_key = data.get('folder_key')
    recursive = data.get('recursive', False)
    watch = data.get('watch', False)
    force = data.get('force', False)
    
    folders = get_dynamic_folder_config()
    if folder_key not in folders: 
        return jsonify({'status':'error', 'message':'Folder not found'}), 404
    
    raw_path = folders[folder_key]['path']
    std_path = get_standardized_path(raw_path)
    
    params = json.dumps({'beams': data.get('beams', 3), 'precision': data.get('precision', 'fp16')})
    msg = "Indexing queued."

    # 1. HANDLE WATCH LIST UPDATE
    with get_db_connection() as conn:
        if watch:
            existing = conn.execute("SELECT path, recursive FROM ai_watched_folders").fetchall()
            should_add = True
            for row in existing:
                exist_std = get_standardized_path(row['path'])
                if exist_std == std_path:
                    # Update recursion if needed
                    if recursive and not row['recursive']: 
                        conn.execute("UPDATE ai_watched_folders SET recursive=1 WHERE path=?", (row['path'],))
                    should_add = False
                    break
                if std_path.startswith(exist_std + '/') and row['recursive']:
                    should_add = False
                    msg = "Covered by parent watcher."
                    break
            if should_add:
                conn.execute("INSERT OR REPLACE INTO ai_watched_folders (path, recursive, added_at) VALUES (?, ?, ?)", (raw_path, 1 if recursive else 0, time.time()))
                msg = "Folder added to Watch List & Queued."
        conn.commit()
    
    # --- CRITICAL FIX: REFRESH SERVER CACHE IMMEDIATELY ---
    # This ensures that subsequent UI calls see 'is_watched=True' right away.
    if watch:
        get_dynamic_folder_config(force_refresh=True)
    
    # 2. BACKGROUND SCAN & QUEUE
    def _scan():
        valid = {'.png','.jpg','.jpeg','.webp','.gif','.mp4','.mov','.avi','.webm'}
        exc = {'.thumbnails_cache', '.sqlite_cache', '.zip_downloads', '.AImodels', 'venv', '.git'}
        files_found = []
        try:
            if recursive:
                for r, d, f in os.walk(raw_path, topdown=True, followlinks=False):
                    d[:] = [x for x in d if not x.startswith('.') and x not in exc]
                    for x in f:
                        if os.path.splitext(x)[1].lower() in valid: files_found.append(os.path.join(r, x))
            else:
                for entry in os.scandir(raw_path):
                    if entry.is_file() and os.path.splitext(entry.name)[1].lower() in valid: files_found.append(entry.path)
        except: return

        # Optimize: Batch Operations
        with get_db_connection() as conn:
            
            ids_to_wipe = []
            queue_entries = []
            
            for fp in files_found:
                pk = get_standardized_path(fp)
                
                # --- ROBUST LOOKUP START (YOUR LOGIC) ---
                # 1. Try exact match
                row = conn.execute("SELECT id, mtime, ai_last_scanned FROM files WHERE path=?", (fp,)).fetchone()
                
                # 2. Try standardized match (case insensitive on Windows)
                if not row: 
                    row = conn.execute("SELECT id, mtime, ai_last_scanned FROM files WHERE path=?", (pk,)).fetchone()
                
                # 3. Try Normalized Slash match (Fixes subfolder mismatch issues)
                if not row:
                    norm_p = fp.replace('\\', '/')
                    row = conn.execute("SELECT id, mtime, ai_last_scanned FROM files WHERE REPLACE(path, '\\', '/') = ?", (norm_p,)).fetchone()
                # --- ROBUST LOOKUP END ---
                
                should_queue = False
                fid = None
                
                if row:
                    fid = row['id']
                    if force:
                        ids_to_wipe.append(fid)
                        should_queue = True
                    elif (row['ai_last_scanned'] or 0) < row['mtime']:
                        should_queue = True # Needs update (Incremental logic)
                else:
                    # New file not in DB yet - queue it, worker will retry later
                    should_queue = True 
                
                if should_queue:
                    # Prepare for batch insertion
                    queue_entries.append((pk, fid, time.time(), 1 if force else 0, params))

            # 3. WIPE OLD DATA IF FORCED
            if ids_to_wipe:
                chunk_size = 500
                for i in range(0, len(ids_to_wipe), chunk_size):
                    chunk = ids_to_wipe[i:i + chunk_size]
                    placeholders = ','.join(['?'] * len(chunk))
                    conn.execute(f"""
                        UPDATE files 
                        SET ai_caption=NULL, ai_embedding=NULL, ai_last_scanned=0, ai_error=NULL 
                        WHERE id IN ({placeholders})
                    """, chunk)

            # 4. BATCH INSERT INTO QUEUE (UPSERT)
            if queue_entries:
                conn.executemany("""
                    INSERT INTO ai_indexing_queue (file_path, file_id, status, created_at, force_index, params) 
                    VALUES (?, ?, 'pending', ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        status = 'pending',
                        force_index = excluded.force_index,
                        created_at = excluded.created_at,
                        params = excluded.params
                """, queue_entries)
                
            conn.commit()
            
    threading.Thread(target=_scan, daemon=True).start()
    return jsonify({'status': 'success', 'message': msg})
    
@app.route('/galleryout/ai_indexing/watched', methods=['GET', 'DELETE'])
def ai_watched_folders():
    if not ENABLE_AI_SEARCH: return jsonify({})
    with get_db_connection() as conn:
        if request.method == 'DELETE':
            path = request.json.get('folder_path')
            if not path:
                key = request.json.get('folder_key')
                folders = get_dynamic_folder_config()
                if key in folders: path = folders[key]['path']
            
            if path:
                # 1. Stop Watching
                conn.execute("DELETE FROM ai_watched_folders WHERE path=?", (path,))
                
                # 2. CLEAR QUEUE (Critical Fix)
                # When stopping watch, we ALWAYS clear pending jobs for this folder to stop immediate processing.
                # We use LIKE for path matching.
                # Ensure we handle OS separators robustly.
                std_path = get_standardized_path(path)
                # Remove exact match or subfiles
                conn.execute("DELETE FROM ai_indexing_queue WHERE file_path = ? OR file_path LIKE ?", (std_path, std_path + '/%'))
                
                # 3. WIPE DATA (Optional User Choice)
                if request.json.get('reset_data'):
                    std_target = get_standardized_path(path)
                    rows = conn.execute("SELECT id, path FROM files WHERE ai_caption IS NOT NULL OR ai_embedding IS NOT NULL").fetchall()
                    ids_to_wipe = []
                    for r in rows:
                        p_std = get_standardized_path(r['path'])
                        if p_std == std_target or p_std.startswith(std_target + '/'):
                            ids_to_wipe.append(r['id'])
                    
                    if ids_to_wipe:
                        # Chunk processing for huge folders
                        chunk_size = 500
                        for i in range(0, len(ids_to_wipe), chunk_size):
                            chunk = ids_to_wipe[i:i+chunk_size]
                            ph = ','.join(['?'] * len(chunk))
                            conn.execute(f"UPDATE files SET ai_caption=NULL, ai_embedding=NULL, ai_last_scanned=0, ai_error=NULL WHERE id IN ({ph})", chunk)
                            # (Queue already cleared above by path, but redundant check by ID is safe)
                            conn.execute(f"DELETE FROM ai_indexing_queue WHERE file_id IN ({ph})", chunk)
                
                conn.commit()
                # --- FORCE CONFIG REFRESH TO UPDATE UI COLORS IMMEDIATELY ---
                get_dynamic_folder_config(force_refresh=True)
                
                return jsonify({'status': 'success'})
            return jsonify({'status': 'error'})
        
        rows = conn.execute("SELECT path, recursive FROM ai_watched_folders").fetchall()
        folders = get_dynamic_folder_config()
        pmap = {info['path']: {'key': k, 'name': info['display_name']} for k, info in folders.items()}
        res = []
        for r in rows:
            m = pmap.get(r['path'])
            rel = r['path']
            try: rel = os.path.relpath(r['path'], BASE_OUTPUT_PATH)
            except: pass
            if m: res.append({'path': r['path'], 'rel_path': rel, 'key': m['key'], 'display_name': m['name'], 'recursive': bool(r['recursive'])})
            else: res.append({'path': r['path'], 'rel_path': rel, 'key': '_unknown', 'display_name': os.path.basename(r['path']), 'recursive': bool(r['recursive'])})
        return jsonify({'folders': res})
        
@app.route('/galleryout/ai_indexing/status')
def ai_indexing_status():
    if not ENABLE_AI_SEARCH: return jsonify({})
    try:
        with get_db_connection() as conn:
            pending = conn.execute("SELECT COUNT(*) FROM ai_indexing_queue WHERE status='pending'").fetchone()[0]
            processing = conn.execute("SELECT file_path FROM ai_indexing_queue WHERE status='processing'").fetchone()
            
            # Preview Next 10 files with PRIORITY INFO
            next_rows = conn.execute("SELECT file_path, force_index FROM ai_indexing_queue WHERE status='pending' ORDER BY force_index DESC, created_at ASC LIMIT 10").fetchall()
            
            avg = conn.execute("SELECT value FROM ai_metadata WHERE key='avg_processing_time'").fetchone()
            paused = conn.execute("SELECT value FROM ai_metadata WHERE key='indexing_paused'").fetchone()
            waiting = conn.execute("SELECT COUNT(*) FROM ai_indexing_queue WHERE status='waiting_gpu'").fetchone()[0]
            
            status = "Idle"
            if paused and paused['value'] == '1': status = "Paused"
            elif waiting > 0: status = "waiting_gpu"
            elif processing: status = "Indexing"
            elif pending > 0: status = "Queued"
            
            curr_file = ""
            if processing:
                try: curr_file = os.path.relpath(processing['file_path'], BASE_OUTPUT_PATH)
                except: curr_file = os.path.basename(processing['file_path'])
            
            next_files = []
            for r in next_rows:
                try: p = os.path.relpath(r['file_path'], BASE_OUTPUT_PATH)
                except: p = os.path.basename(r['file_path'])
                
                next_files.append({
                    'path': p,
                    'is_priority': bool(r['force_index'])
                })

            return jsonify({
                'global_status': status, 'pending_count': pending, 'current_file': curr_file,
                'gpu_usage': 0, 'avg_time': float(avg['value']) if avg else 0.0,
                'current_job_progress': 0, 'current_job_total': pending + (1 if processing else 0),
                'next_files': next_files
            })
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/galleryout/ai_indexing/control', methods=['POST'])
def ai_indexing_control():
    if not ENABLE_AI_SEARCH: return jsonify({'status':'error'})
    action = request.json.get('action')
    with get_db_connection() as conn:
        if action == 'pause': conn.execute("INSERT OR REPLACE INTO ai_metadata (key, value) VALUES ('indexing_paused', '1')")
        elif action == 'resume':
            conn.execute("INSERT OR REPLACE INTO ai_metadata (key, value) VALUES ('indexing_paused', '0')")
            conn.execute("UPDATE ai_indexing_queue SET status='pending' WHERE status='waiting_gpu'")
        elif action == 'clear': conn.execute("DELETE FROM ai_indexing_queue WHERE status != 'processing'")
        conn.commit()
    return jsonify({'status': 'success', 'message': f'Queue {action}d'})
    
@app.route('/galleryout/view/<string:folder_key>')
def gallery_view(folder_key):
    global gallery_view_cache
    folders = get_dynamic_folder_config(force_refresh=True)
    if folder_key not in folders:
        return redirect(url_for('gallery_view', folder_key='_root_'))
    
    current_folder_info = folders[folder_key]
    folder_path = current_folder_info['path']
    
    # 1. Capture All Request Parameters
    is_recursive = request.args.get('recursive', 'false').lower() == 'true'
    search_scope = request.args.get('scope', 'local')
    is_global_search = (search_scope == 'global')
    ai_session_id = request.args.get('ai_session_id')
    
    # Text filters
    search_term = request.args.get('search', '').strip()
    wf_files = request.args.get('workflow_files', '').strip()
    wf_prompt = request.args.get('workflow_prompt', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    selected_exts = request.args.getlist('extension')
    selected_prefixes = request.args.getlist('prefix')

    is_ai_search = False
    ai_query_text = ""

    # --- PATH A: AI SEARCH RESULTS ---
    if ENABLE_AI_SEARCH and ai_session_id:
        with get_db_connection() as conn:
            try:
                queue_info = conn.execute("SELECT query, status FROM ai_search_queue WHERE session_id = ?", (ai_session_id,)).fetchone()
                if queue_info and queue_info['status'] == 'completed':
                    is_ai_search = True
                    ai_query_text = queue_info['query']
                    rows = conn.execute('''
                        SELECT f.*, r.score FROM ai_search_results r
                        JOIN files f ON r.file_id = f.id
                        WHERE r.session_id = ? ORDER BY r.score DESC
                    ''', (ai_session_id,)).fetchall()
                    
                    # FIX: Clean up BLOB data (ai_embedding) which is not JSON serializable
                    files_list = []
                    for row in rows:
                        d = dict(row)
                        if 'ai_embedding' in d: 
                            del d['ai_embedding'] # Remove binary data
                        files_list.append(d)
                    
                    gallery_view_cache = files_list
            except Exception as e:
                print(f"AI Search Error: {e}")
                is_ai_search = False

    # --- PATH B: STANDARD VIEW / SEARCH (Cross-Platform Robust) ---
    if not is_ai_search:
        with get_db_connection() as conn:
            conditions, params = [], []

            # 2. Apply Metadata Filters first (Generic fields)
            if search_term:
                conditions.append("name LIKE ?")
                params.append(f"%{search_term}%")
            
            if wf_files:
                for kw in [k.strip() for k in wf_files.split(',') if k.strip()]:
                    conditions.append("workflow_files LIKE ?")
                    params.append(f"%{normalize_smart_path(kw)}%")
            
            if wf_prompt:
                for kw in [k.strip() for k in wf_prompt.split(',') if k.strip()]:
                    conditions.append("workflow_prompt LIKE ?")
                    params.append(f"%{kw}%")

            if request.args.get('favorites') == 'true': conditions.append("is_favorite = 1")
            if request.args.get('no_workflow') == 'true': conditions.append("has_workflow = 0")
            if request.args.get('no_ai_caption') == 'true': 
                conditions.append("(ai_caption IS NULL OR ai_caption = '')")

            if start_date:
                try: conditions.append("mtime >= ?"); params.append(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                except: pass
            if end_date:
                try: conditions.append("mtime <= ?"); params.append(datetime.strptime(end_date, '%Y-%m-%d').timestamp() + 86399)
                except: pass

            if selected_exts:
                e_cond = [f"name LIKE ?" for e in selected_exts if e.strip()]
                params.extend([f"%.{e.lstrip('.').lower()}" for e in selected_exts if e.strip()])
                if e_cond: conditions.append(f"({' OR '.join(e_cond)})")

            if selected_prefixes:
                p_cond = [f"name LIKE ?" for p in selected_prefixes if p.strip()]
                params.extend([f"{p.strip()}_%" for p in selected_prefixes if p.strip()])
                if p_cond: conditions.append(f"({' OR '.join(p_cond)})")

            # 3. Execution: We fetch files matching metadata, then filter paths in Python
            # This is the only way to guarantee 100% slash-agnostic behavior
            sort_by = 'name' if request.args.get('sort_by') == 'name' else 'mtime'
            sort_order = "ASC" if request.args.get('sort_order', 'desc').lower() == 'asc' else "DESC"
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"SELECT * FROM files {where_clause} ORDER BY {sort_by} {sort_order}"
            rows = conn.execute(query, params).fetchall()
            
            # --- ULTRA-ROBUST MIXED-PATH FILTERING ---
            final_files = []
            
            # Helper to normalize ANY path (mixed slashes, case, trailing)
            def safe_path_norm(p):
                if not p: return ""
                # 1. Force all backslashes to forward slashes immediately
                # 2. Lowercase for cross-platform case-insensitivity
                # 3. Clean up and remove trailing slashes
                return os.path.normpath(str(p).replace('\\', '/')).replace('\\', '/').lower().rstrip('/')

            target_norm = safe_path_norm(folder_path)
            
            for row in rows:
                f_data = dict(row)
                if 'ai_embedding' in f_data: del f_data['ai_embedding']
                
                # Normalize the DB path which might be mixed (e.g., c:/folder\img.png)
                f_path_norm = safe_path_norm(f_data['path'])
                f_dir_norm = safe_path_norm(os.path.dirname(f_path_norm))
                
                if is_global_search:
                    final_files.append(f_data)
                elif is_recursive:
                    # Check if the file is inside the target folder tree
                    # Adding a '/' ensures we don't match 'folder_backup' when looking for 'folder'
                    if f_path_norm.startswith(target_norm + '/'):
                        final_files.append(f_data)
                else:
                    # Strict match: must be exactly in the target folder
                    if f_dir_norm == target_norm:
                        final_files.append(f_data)
            
            gallery_view_cache = final_files

    # 4. Final Metadata for Template
    # --- RIGOROUS FILTER COUNTING LOGIC ---
    active_filters_count = 0
    if search_term: active_filters_count += 1
    if wf_files: active_filters_count += 1
    if wf_prompt: active_filters_count += 1
    if start_date: active_filters_count += 1
    if end_date: active_filters_count += 1
    if selected_exts: active_filters_count += 1
    if selected_prefixes: active_filters_count += 1
    if request.args.get('favorites') == 'true': active_filters_count += 1
    if request.args.get('no_workflow') == 'true': active_filters_count += 1
    if ENABLE_AI_SEARCH and request.args.get('no_ai_caption') == 'true': active_filters_count += 1

    # Scope/Recursive Logic:
    if is_global_search:
        # Global search is a major state change, counts as 1 filter
        active_filters_count += 1
    elif is_recursive:
        # Recursive only counts as a filter if we are in Local mode (modifying the default folder view)
        active_filters_count += 1

    # Important: count files correctly on disk for the badge
    total_folder_files, _, _ = scan_folder_and_extract_options(folder_path, recursive=is_recursive)
    # Initialize DB Total
    total_db_files = 0 
    with get_db_connection() as conn_opts:
        # NEW: Get the grand total of files in the database (for Global/AI context)
        try:
            total_db_files = conn_opts.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        except:
            total_db_files = 0

        scope_for_opts = 'global' if is_global_search else 'local'
        # FIX: Added recursive=is_recursive to ensure dropdowns match current view on load
        extensions, prefixes, pfx_limit = get_filter_options_from_db(conn_opts, scope_for_opts, folder_path, recursive=is_recursive)
    
    breadcrumbs, ancestor_keys = [], set()
    curr = folder_key
    while curr and curr in folders:
        f_info = folders[curr]
        breadcrumbs.append({'key': curr, 'display_name': f_info['display_name']})
        ancestor_keys.add(curr)
        curr = f_info.get('parent')
    breadcrumbs.reverse()
    return render_template('index.html', 
                           files=gallery_view_cache[:PAGE_SIZE], 
                           total_files=len(gallery_view_cache),
                           total_folder_files=total_folder_files, 
                           total_db_files=total_db_files,
                           folders=folders,
                           current_folder_key=folder_key, 
                           current_folder_info=current_folder_info,
                           breadcrumbs=breadcrumbs,
                           ancestor_keys=list(ancestor_keys),
                           available_extensions=extensions, 
                           available_prefixes=prefixes,
                           prefix_limit_reached=pfx_limit,  
                           selected_extensions=selected_exts, 
                           selected_prefixes=selected_prefixes,
                           protected_folder_keys=list(PROTECTED_FOLDER_KEYS),
                           show_favorites=request.args.get('favorites', 'false').lower() == 'true',
                           enable_ai_search=ENABLE_AI_SEARCH,
                           is_ai_search=is_ai_search,
                           ai_query=ai_query_text,
                           is_global_search=is_global_search,
                           active_filters_count=active_filters_count,
                           current_scope=search_scope,
                           is_recursive=is_recursive,
                           app_version=APP_VERSION,
                           github_url=GITHUB_REPO_URL,
                           update_available=UPDATE_AVAILABLE,
                           remote_version=REMOTE_VERSION,
                           ffmpeg_available=(FFPROBE_EXECUTABLE_PATH is not None),
                           stream_threshold=STREAM_THRESHOLD_BYTES)
    
@app.route('/galleryout/upload', methods=['POST'])
def upload_files():
    folder_key = request.form.get('folder_key')
    if not folder_key: return jsonify({'status': 'error', 'message': 'No destination folder provided.'}), 400
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Destination folder not found.'}), 404
    destination_path = folders[folder_key]['path']
    if 'files' not in request.files: return jsonify({'status': 'error', 'message': 'No files were uploaded.'}), 400
    uploaded_files, errors, success_count = request.files.getlist('files'), {}, 0
    for file in uploaded_files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            try:
                file.save(os.path.join(destination_path, filename))
                success_count += 1
            except Exception as e: errors[filename] = str(e)
    if success_count > 0: sync_folder_on_demand(destination_path)
    if errors: return jsonify({'status': 'partial_success', 'message': f'Successfully uploaded {success_count} files. The following files failed: {", ".join(errors.keys())}'}), 207
    return jsonify({'status': 'success', 'message': f'Successfully uploaded {success_count} files.'})
                           
@app.route('/galleryout/rescan_folder', methods=['POST'])
def rescan_folder():
    data = request.json
    folder_key = data.get('folder_key')
    mode = data.get('mode', 'all') # 'all' or 'recent'
    
    if not folder_key: return jsonify({'status': 'error', 'message': 'No folder provided.'}), 400
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Folder not found.'}), 404
    
    folder_path = folders[folder_key]['path']
    
    try:
        with get_db_connection() as conn:
            # Get all files in this folder
            query = "SELECT path, last_scanned FROM files WHERE path LIKE ?"
            params = (folder_path + os.sep + '%',)
            rows = conn.execute(query, params).fetchall()
            
            # Filter files strictly within this folder (not subfolders)
            folder_path_norm = os.path.normpath(folder_path)
            files_in_folder = [
                {'path': row['path'], 'last_scanned': row['last_scanned']} 
                for row in rows 
                if os.path.normpath(os.path.dirname(row['path'])) == folder_path_norm
            ]
            
            files_to_process = []
            current_time = time.time()
            
            if mode == 'recent':
                # Process files not scanned in the last 60 minutes (3600 seconds)
                cutoff_time = current_time - 3600
                files_to_process = [f['path'] for f in files_in_folder if (f['last_scanned'] or 0) < cutoff_time]
            else:
                # Process all files
                files_to_process = [f['path'] for f in files_in_folder]
            
            if not files_to_process:
                return jsonify({'status': 'success', 'message': 'No files needed rescanning.', 'count': 0})
            
            print(f"INFO: Rescanning {len(files_to_process)} files in '{folder_path}' (Mode: {mode})...")
            
            processed_count = 0
            results = []
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
                futures = {executor.submit(process_single_file, path): path for path in files_to_process}
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
                    processed_count += 1
            
            if results:
                conn.executemany("""
                    INSERT INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow, size, last_scanned, workflow_files, workflow_prompt) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        path = excluded.path,
                        name = excluded.name,
                        type = excluded.type,
                        duration = excluded.duration,
                        dimensions = excluded.dimensions,
                        has_workflow = excluded.has_workflow,
                        size = excluded.size,
                        last_scanned = excluded.last_scanned,
                        workflow_files = excluded.workflow_files,
                        workflow_prompt = excluded.workflow_prompt,
                        
                        -- LOGICA CONDIZIONALE:
                        is_favorite = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0  
                            ELSE files.is_favorite                     
                        END,
                        
                        ai_caption = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL 
                            ELSE files.ai_caption                        
                        END,
                        
                        ai_embedding = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL 
                            ELSE files.ai_embedding 
                        END,

                        ai_last_scanned = CASE 
                            WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0 
                            ELSE files.ai_last_scanned 
                        END,

                        -- Aggiorna mtime alla fine
                        mtime = excluded.mtime
                """, results) 
                conn.commit()
                
        return jsonify({'status': 'success', 'message': f'Successfully rescanned {len(results)} files.', 'count': len(results)})
        
    except Exception as e:
        print(f"ERROR: Rescan failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/galleryout/create_folder', methods=['POST'])
def create_folder():
    data = request.json
    parent_key = data.get('parent_key', '_root_')

    raw_name = data.get('folder_name', '').strip()
    folder_name = re.sub(r'[\\/:*?"<>|]', '', raw_name)
    
    if not folder_name or folder_name in ['.', '..']: 
        return jsonify({'status': 'error', 'message': 'Invalid folder name provided.'}), 400
        
    folders = get_dynamic_folder_config()
    if parent_key not in folders: return jsonify({'status': 'error', 'message': 'Parent folder not found.'}), 404
    parent_path = folders[parent_key]['path']
    new_folder_path = os.path.join(parent_path, folder_name)
    try:
        os.makedirs(new_folder_path, exist_ok=False)
        sync_folder_on_demand(parent_path)
        return jsonify({'status': 'success', 'message': f'Folder "{folder_name}" created successfully.'})
    except FileExistsError: return jsonify({'status': 'error', 'message': 'Folder already exists.'}), 400
    except Exception as e: return jsonify({'status': 'error', 'message': str(e)}), 500
    
# --- ZIP BACKGROUND JOB MANAGEMENT ---
zip_jobs = {}
def background_zip_task(job_id, file_ids):
    try:
        if not os.path.exists(ZIP_CACHE_DIR):
            try:
                os.makedirs(ZIP_CACHE_DIR, exist_ok=True)
            except Exception as e:
                print(f"ERROR: Could not create zip directory: {e}")
                zip_jobs[job_id] = {'status': 'error', 'message': f'Server permission error: {e}'}
                return
        
        zip_filename = f"smartgallery_{job_id}.zip"
        zip_filepath = os.path.join(ZIP_CACHE_DIR, zip_filename)
        
        with get_db_connection() as conn:
            placeholders = ','.join(['?'] * len(file_ids))
            query = f"SELECT path, name FROM files WHERE id IN ({placeholders})"
            files_to_zip = conn.execute(query, file_ids).fetchall()

        if not files_to_zip:
            zip_jobs[job_id] = {'status': 'error', 'message': 'No valid files found.'}
            return

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_row in files_to_zip:
                file_path = file_row['path']
                file_name = file_row['name']
                # Check the file esists 
                if os.path.exists(file_path):
                    # Add file to zip
                    zf.write(file_path, file_name)
        
        # Job completed succesfully
        zip_jobs[job_id] = {
            'status': 'ready', 
            'filename': zip_filename
        }
        
        # Clean automatic: delete zip older than 24 hours
        try:
            now = time.time()
            for f in os.listdir(ZIP_CACHE_DIR):
                fp = os.path.join(ZIP_CACHE_DIR, f)
                if os.path.isfile(fp) and os.stat(fp).st_mtime < now - 86400:
                    os.remove(fp)
        except Exception: 
            pass

    except Exception as e:
        print(f"Zip Error: {e}")
        zip_jobs[job_id] = {'status': 'error', 'message': str(e)}
        
@app.route('/galleryout/prepare_batch_zip', methods=['POST'])
def prepare_batch_zip():
    data = request.json
    file_ids = data.get('file_ids', [])
    if not file_ids:
        return jsonify({'status': 'error', 'message': 'No files specified.'}), 400

    job_id = str(uuid.uuid4())
    zip_jobs[job_id] = {'status': 'processing'}
    
    thread = threading.Thread(target=background_zip_task, args=(job_id, file_ids))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'job_id': job_id, 'message': 'Zip generation started.'})

@app.route('/galleryout/check_zip_status/<job_id>')
def check_zip_status(job_id):
    job = zip_jobs.get(job_id)
    if not job:
        return jsonify({'status': 'error', 'message': 'Job not found'}), 404
    response_data = job.copy()
    if job['status'] == 'ready' and 'filename' in job:
        response_data['download_url'] = url_for('serve_zip_file', filename=job['filename'])
        
    return jsonify(response_data)
    
@app.route('/galleryout/serve_zip/<filename>')
def serve_zip_file(filename):
    return send_from_directory(ZIP_CACHE_DIR, filename, as_attachment=True)

@app.route('/galleryout/rename_folder/<string:folder_key>', methods=['POST'])
def rename_folder(folder_key):
    if folder_key in PROTECTED_FOLDER_KEYS: return jsonify({'status': 'error', 'message': 'This folder cannot be renamed.'}), 403
    
    raw_name = request.json.get('new_name', '').strip()
    new_name = re.sub(r'[\\/:*?"<>|]', '', raw_name)
    
    if not new_name or new_name in ['.', '..']: 
        return jsonify({'status': 'error', 'message': 'Invalid name.'}), 400
        
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Folder not found.'}), 400
    
    # 1. GET EXACT FOLDER PATH FROM CONFIG (Usually has forward slashes '/')
    old_folder_path = folders[folder_key]['path']
    
    # 2. CONSTRUCT NEW FOLDER PATH (Preserving forward slashes structure)
    # We do NOT use os.path.join here for the folder part because it might force backslashes on Windows,
    # breaking consistency with get_dynamic_folder_config which enforces '/'.
    # We strip the last segment and append the new name.
    if '/' in old_folder_path:
        parent_dir = old_folder_path.rsplit('/', 1)[0]
        new_folder_path = f"{parent_dir}/{new_name}"
    else:
        # Fallback for systems strictly using backslash (unlikely given your logs, but safe)
        parent_dir = os.path.dirname(old_folder_path)
        new_folder_path = os.path.join(parent_dir, new_name)
    
    # Check existence (using normpath for OS safety check)
    if os.path.exists(os.path.normpath(new_folder_path)): 
        return jsonify({'status': 'error', 'message': 'A folder with this name already exists.'}), 400
    
    try:
        with get_db_connection() as conn:
            all_files_cursor = conn.execute("SELECT id, path FROM files")
            
            update_data = []
            ids_to_clean_collisions = []
            
            # Prepare check
            is_windows = (os.name == 'nt')
            check_old = old_folder_path.lower() if is_windows else old_folder_path
            
            for row in all_files_cursor:
                current_path = row['path']
                check_curr = current_path.lower() if is_windows else current_path
                
                # Check containment
                if check_curr.startswith(check_old):
                    
                    # 1. EXTRACT FILENAME
                    # We rely on os.path.basename. It works on "C:/A/B\file.txt" correctly on Windows.
                    filename = os.path.basename(current_path)
                    
                    # 2. CONSTRUCT NEW PATH EXACTLY LIKE THE SCANNER DOES
                    # Scanner logic: os.path.join(folder_path_from_config, filename)
                    # This produces "C:/.../NewName\filename.ext" on Windows.
                    new_file_path = os.path.join(new_folder_path, filename)
                    
                    # 3. GENERATE ID
                    new_id = hashlib.md5(new_file_path.encode()).hexdigest()
                    
                    update_data.append((new_id, new_file_path, row['id']))
                    ids_to_clean_collisions.append(new_id)

            # Cleanup Ghost records
            if ids_to_clean_collisions:
                placeholders = ','.join(['?'] * len(ids_to_clean_collisions))
                conn.execute(f"DELETE FROM files WHERE id IN ({placeholders})", ids_to_clean_collisions)

            # Physical Rename (Use normpath for OS call to be safe)
            os.rename(os.path.normpath(old_folder_path), os.path.normpath(new_folder_path))
            
            # Atomic DB Update
            if update_data: 
                conn.executemany("UPDATE files SET id = ?, path = ? WHERE id = ?", update_data)
            
            # Update Watch List
            watched_folders = conn.execute("SELECT path FROM ai_watched_folders").fetchall()
            for row in watched_folders:
                w_path = row['path']
                w_check = w_path.lower() if is_windows else w_path
                
                if w_check == check_old:
                    conn.execute("UPDATE ai_watched_folders SET path = ? WHERE path = ?", (new_folder_path, w_path))
                elif w_check.startswith(check_old):
                    # Subfolder logic: simple string replace to preserve structure
                    # We use standard string replacement which works because we enforced '/' structure above
                    if is_windows:
                        # Case insensitive replace is tricky, let's assume structure holds
                        # We reconstruct the tail
                        suffix = w_path[len(old_folder_path):]
                        new_w_path = new_folder_path + suffix
                        conn.execute("UPDATE ai_watched_folders SET path = ? WHERE path = ?", (new_w_path, w_path))
                    else:
                        new_w_path = w_path.replace(old_folder_path, new_folder_path, 1)
                        conn.execute("UPDATE ai_watched_folders SET path = ? WHERE path = ?", (new_w_path, w_path))

            conn.commit()
            
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder renamed.'})
        
    except Exception as e: 
        print(f"Rename Error: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500
        
@app.route('/galleryout/delete_folder/<string:folder_key>', methods=['POST'])
def delete_folder(folder_key):
    if folder_key in PROTECTED_FOLDER_KEYS: return jsonify({'status': 'error', 'message': 'This folder cannot be deleted.'}), 403
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Folder not found.'}), 404
    try:
        folder_path = folders[folder_key]['path']
        with get_db_connection() as conn:
            # 1. Remove files from DB
            conn.execute("DELETE FROM files WHERE path LIKE ?", (folder_path + os.sep + '%',))
            
            # 2. AI WATCHED FOLDERS CLEANUP (Logic added)
            # Remove the folder itself from watched list
            conn.execute("DELETE FROM ai_watched_folders WHERE path = ?", (folder_path,))
            # Remove any subfolders that might be in the watched list
            conn.execute("DELETE FROM ai_watched_folders WHERE path LIKE ?", (folder_path + os.sep + '%',))
            
            conn.commit()
            
        # 3. Physical deletion
        shutil.rmtree(folder_path)
        
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder deleted.'})
    except Exception as e: return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500
    
@app.route('/galleryout/load_more')
def load_more():
    offset = request.args.get('offset', 0, type=int)
    if offset >= len(gallery_view_cache): return jsonify(files=[])
    return jsonify(files=gallery_view_cache[offset:offset + PAGE_SIZE])

def get_file_info_from_db(file_id, column='*'):
    with get_db_connection() as conn:
        row = conn.execute(f"SELECT {column} FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row: abort(404)
    return dict(row) if column == '*' else row[0]

def _get_unique_filepath(destination_folder, filename):
    """
    Generates a unique filepath using the NATIVE OS separator.
    This ensures that the path matches exactly what the Scanner generates,
    preventing duplicate records in the database.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    
    # Use standard os.path.join. 
    # On Windows with base path "C:/A", it produces "C:/A\file.txt" (Matches your DB).
    # On Linux, it produces "C:/A/file.txt" (Matches Linux DB).
    full_path = os.path.join(destination_folder, filename)

    while os.path.exists(full_path):
        new_filename = f"{base}({counter}){ext}"
        full_path = os.path.join(destination_folder, new_filename)
        counter += 1
        
    return full_path
    
@app.route('/galleryout/move_batch', methods=['POST'])
def move_batch():
    data = request.json
    file_ids = data.get('file_ids', [])
    dest_key = data.get('destination_folder')
    
    folders = get_dynamic_folder_config()
    
    if not all([file_ids, dest_key, dest_key in folders]):
        return jsonify({'status': 'error', 'message': 'Invalid data provided.'}), 400
    
    moved_count, renamed_count, skipped_count = 0, 0, 0
    failed_files = []
    
    # Get destination path from config
    dest_path_raw = folders[dest_key]['path']
    
    with get_db_connection() as conn:
        for file_id in file_ids:
            source_path = None
            try:
                # 1. Fetch Source Data + AI Metadata
                query_fetch = """
                    SELECT 
                        path, name, size, has_workflow, is_favorite, type, duration, dimensions,
                        ai_last_scanned, ai_caption, ai_embedding, ai_error, workflow_files, workflow_prompt 
                    FROM files WHERE id = ?
                """
                file_info = conn.execute(query_fetch, (file_id,)).fetchone()
                
                if not file_info:
                    failed_files.append(f"ID {file_id} not found in DB")
                    continue
                
                source_path = file_info['path']
                source_filename = file_info['name']
                
                # Metadata Pack
                meta = {
                    'size': file_info['size'],
                    'has_workflow': file_info['has_workflow'],
                    'is_favorite': file_info['is_favorite'],
                    'type': file_info['type'],
                    'duration': file_info['duration'],
                    'dimensions': file_info['dimensions'],
                    'ai_last_scanned': file_info['ai_last_scanned'],
                    'ai_caption': file_info['ai_caption'],
                    'ai_embedding': file_info['ai_embedding'],
                    'ai_error': file_info['ai_error'],
                    'workflow_files': file_info['workflow_files'],
                    'workflow_prompt': file_info['workflow_prompt']
                }
                
                # Check Source vs Dest (OS Agnostic comparison)
                source_dir_norm = os.path.normpath(os.path.dirname(source_path))
                dest_dir_norm = os.path.normpath(dest_path_raw)
                is_same_folder = (source_dir_norm.lower() == dest_dir_norm.lower()) if os.name == 'nt' else (source_dir_norm == dest_dir_norm)
                
                if is_same_folder:
                    skipped_count += 1
                    continue 

                if not os.path.exists(source_path):
                    failed_files.append(f"{source_filename} (not found on disk)")
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    continue
                
                # 2. Calculate unique path NATIVELY (No separator forcing)
                # This guarantees the path string matches what the Scanner will see.
                final_dest_path = _get_unique_filepath(dest_path_raw, source_filename)
                final_filename = os.path.basename(final_dest_path)
                
                if final_filename != source_filename: 
                    renamed_count += 1
                
                # 3. Move file on disk
                shutil.move(source_path, final_dest_path)
                
                # 4. Calculate New ID based on the NATIVE path
                new_id = hashlib.md5(final_dest_path.encode()).hexdigest()
                
                # 5. DB Update / Merge Logic
                existing_target = conn.execute("SELECT id FROM files WHERE id = ?", (new_id,)).fetchone()
                
                if existing_target:
                    # MERGE: Target exists (e.g. ghost record). Overwrite with source metadata.
                    query_merge = """
                        UPDATE files 
                        SET path = ?, name = ?, mtime = ?,
                            size = ?, has_workflow = ?, is_favorite = ?, 
                            type = ?, duration = ?, dimensions = ?,
                            ai_last_scanned = ?, ai_caption = ?, ai_embedding = ?, ai_error = ?,
                            workflow_files = ?, workflow_prompt = ?
                        WHERE id = ?
                    """
                    conn.execute(query_merge, (
                        final_dest_path, final_filename, time.time(),
                        meta['size'], meta['has_workflow'], meta['is_favorite'],
                        meta['type'], meta['duration'], meta['dimensions'],
                        meta['ai_last_scanned'], meta['ai_caption'], meta['ai_embedding'], meta['ai_error'],
                        meta['workflow_files'], 
                        meta['workflow_prompt'],
                        new_id
                    ))
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                else:
                    # STANDARD: Update existing record path/name.
                    conn.execute("UPDATE files SET id = ?, path = ?, name = ? WHERE id = ?", 
                                (new_id, final_dest_path, final_filename, file_id))
                    
                moved_count += 1
                
            except Exception as e:
                filename_for_error = os.path.basename(source_path) if source_path else f"ID {file_id}"
                failed_files.append(filename_for_error)
                print(f"ERROR: Failed to move file {filename_for_error}. Reason: {e}")
                continue
        conn.commit()
    
    message = f"Successfully moved {moved_count} file(s)."
    if skipped_count > 0: message += f" {skipped_count} skipped (same folder)."
    if renamed_count > 0: message += f" {renamed_count} renamed."
    if failed_files: message += f" Failed: {len(failed_files)}."
    
    status = 'success'
    if failed_files or (skipped_count > 0 and moved_count == 0): status = 'partial_success'
        
    return jsonify({'status': status, 'message': message})
    
@app.route('/galleryout/delete_batch', methods=['POST'])
def delete_batch():
    try:
        # Preveniamo il crash gestendo tutto in un blocco try/except
        data = request.json
        file_ids = data.get('file_ids', [])
        
        if not file_ids: 
            return jsonify({'status': 'error', 'message': 'No files selected.'}), 400
        
        deleted_count = 0
        failed_files = []
        ids_to_remove_from_db = []

        with get_db_connection() as conn:
            # 1. Generazione corretta e sicura dei placeholder SQL (?,?,?)
            # Usiamo una lista esplicita per evitare errori di sintassi python
            placeholders = ','.join(['?'] * len(file_ids))
            
            # Selezioniamo i file per verificare i percorsi
            query_select = f"SELECT id, path FROM files WHERE id IN ({placeholders})"
            files_to_delete = conn.execute(query_select, file_ids).fetchall()
            
            for row in files_to_delete:
                file_path = row['path']
                file_id = row['id']
                
                try:
                    # Cancellazione Fisica (o spostamento nel cestino)
                    if os.path.exists(file_path):
                        safe_delete_file(file_path)
                    
                    # Se l'operazione su disco riesce (o il file non c'era già più),
                    # segniamo l'ID per la rimozione dal DB
                    ids_to_remove_from_db.append(file_id)
                    deleted_count += 1
                    
                except Exception as e:
                    # Se fallisce la cancellazione fisica di un file, lo annotiamo ma continuiamo
                    print(f"ERROR: Could not delete {file_path}: {e}")
                    failed_files.append(os.path.basename(file_path))
            
            # 2. Pulizia Database (Massiva)
            if ids_to_remove_from_db:
                # Generiamo nuovi placeholder solo per gli ID effettivamente cancellati
                db_placeholders = ','.join(['?'] * len(ids_to_remove_from_db))
                query_delete = f"DELETE FROM files WHERE id IN ({db_placeholders})"
                conn.execute(query_delete, ids_to_remove_from_db)
                conn.commit()
    
        # Costruzione messaggio finale
        action = "moved to trash" if DELETE_TO else "deleted"
        message = f'Successfully {action} {deleted_count} files.'
        
        status = 'success'
        if failed_files: 
            message += f" Failed to delete {len(failed_files)} files."
            status = 'partial_success'
            
        return jsonify({'status': status, 'message': message})

    except Exception as e:
        # QUESTO risolve il "doctype is not json":
        # Se c'è un errore grave, restituiamo un JSON di errore invece di una pagina HTML rotta.
        print(f"CRITICAL ERROR in delete_batch: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/galleryout/favorite_batch', methods=['POST'])
def favorite_batch():
    data = request.json
    file_ids, status = data.get('file_ids', []), data.get('status', False)
    if not file_ids: return jsonify({'status': 'error', 'message': 'No files selected'}), 400
    with get_db_connection() as conn:
        placeholders = ','.join('?' * len(file_ids))
        conn.execute(f"UPDATE files SET is_favorite = ? WHERE id IN ({placeholders})", [1 if status else 0] + file_ids)
        conn.commit()
    return jsonify({'status': 'success', 'message': f"Updated favorites for {len(file_ids)} files."})

@app.route('/galleryout/toggle_favorite/<string:file_id>', methods=['POST'])
def toggle_favorite(file_id):
    with get_db_connection() as conn:
        current = conn.execute("SELECT is_favorite FROM files WHERE id = ?", (file_id,)).fetchone()
        if not current: abort(404)
        new_status = 1 - current['is_favorite']
        conn.execute("UPDATE files SET is_favorite = ? WHERE id = ?", (new_status, file_id))
        conn.commit()
        return jsonify({'status': 'success', 'is_favorite': bool(new_status)})

# --- FIX: ROBUST DELETE ROUTE ---
@app.route('/galleryout/delete/<string:file_id>', methods=['POST'])
def delete_file(file_id):
    with get_db_connection() as conn:
        file_info = conn.execute("SELECT path FROM files WHERE id = ?", (file_id,)).fetchone()
        if not file_info:
            return jsonify({'status': 'success', 'message': 'File already deleted from database.'})
        
        filepath = file_info['path']
        
        try:
            if os.path.exists(filepath):
                safe_delete_file(filepath)
            # If file doesn't exist on disk, we still proceed to remove the DB entry, which is the desired state.
        except OSError as e:
            # A real OS error occurred (e.g., permissions).
            print(f"ERROR: Could not delete file {filepath} from disk: {e}")
            return jsonify({'status': 'error', 'message': f'Could not delete file from disk: {e}'}), 500

        # Whether the file was deleted now or was already gone, we clean up the DB.
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        action = "moved to trash" if DELETE_TO else "deleted"
        return jsonify({'status': 'success', 'message': f'File {action} successfully.'})

# --- RENAME FILE ---
@app.route('/galleryout/rename_file/<string:file_id>', methods=['POST'])
def rename_file(file_id):
    data = request.json
    new_name = data.get('new_name', '').strip()

    if not new_name or len(new_name) > 250:
        return jsonify({'status': 'error', 'message': 'Invalid filename.'}), 400
    if re.search(r'[\\/:"*?<>|]', new_name):
        return jsonify({'status': 'error', 'message': 'Invalid characters.'}), 400

    try:
        with get_db_connection() as conn:
            # 1. Fetch All Metadata
            query_fetch = """
                SELECT 
                    path, name, size, has_workflow, is_favorite, type, duration, dimensions,
                    ai_last_scanned, ai_caption, ai_embedding, ai_error, workflow_files, workflow_prompt  
                FROM files WHERE id = ?
            """
            file_info = conn.execute(query_fetch, (file_id,)).fetchone()
            
            if not file_info:
                return jsonify({'status': 'error', 'message': 'File not found.'}), 404

            old_path = file_info['path']
            old_name = file_info['name']
            
            # Metadata Pack
            meta = {
                'size': file_info['size'],
                'has_workflow': file_info['has_workflow'],
                'is_favorite': file_info['is_favorite'],
                'type': file_info['type'],
                'duration': file_info['duration'],
                'dimensions': file_info['dimensions'],
                'ai_last_scanned': file_info['ai_last_scanned'],
                'ai_caption': file_info['ai_caption'],
                'ai_embedding': file_info['ai_embedding'],
                'ai_error': file_info['ai_error'],
                'workflow_files': file_info['workflow_files'],
                'workflow_prompt': file_info['workflow_prompt']
            }
            
            # Extension logic
            _, old_ext = os.path.splitext(old_name)
            new_name_base, new_ext = os.path.splitext(new_name)
            final_new_name = new_name if new_ext else new_name + old_ext

            if final_new_name == old_name:
                return jsonify({'status': 'error', 'message': 'Name unchanged.'}), 400

            # 2. Construct Path NATIVELY using os.path.join
            # This respects the OS separator (Mixed on Win, Forward on Linux)
            # ensuring the Hash ID matches future Scans.
            dir_name = os.path.dirname(old_path)
            new_path = os.path.join(dir_name, final_new_name)

            if os.path.exists(new_path):
                 return jsonify({'status': 'error', 'message': f'File "{final_new_name}" already exists.'}), 409

            new_id = hashlib.md5(new_path.encode()).hexdigest()
            existing_db = conn.execute("SELECT id FROM files WHERE id = ?", (new_id,)).fetchone()

            os.rename(old_path, new_path)

            if existing_db:
                # MERGE SCENARIO
                query_merge = """
                    UPDATE files 
                    SET path = ?, name = ?, mtime = ?,
                        size = ?, has_workflow = ?, is_favorite = ?, 
                        type = ?, duration = ?, dimensions = ?,
                        ai_last_scanned = ?, ai_caption = ?, ai_embedding = ?, ai_error = ?,
                        workflow_files = ?, workflow_prompt = ?
                    WHERE id = ?
                """
                conn.execute(query_merge, (
                    final_dest_path, final_filename, time.time(),
                    meta['size'], meta['has_workflow'], meta['is_favorite'],
                    meta['type'], meta['duration'], meta['dimensions'],
                    meta['ai_last_scanned'], meta['ai_caption'], meta['ai_embedding'], meta['ai_error'],
                    meta['workflow_files'], 
                    meta['workflow_prompt'],
                    new_id
                ))
                conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
            else:
                # STANDARD SCENARIO
                conn.execute("UPDATE files SET id = ?, path = ?, name = ? WHERE id = ?", 
                            (new_id, new_path, final_new_name, file_id))

            conn.commit()

            return jsonify({
                'status': 'success',
                'message': 'File renamed.',
                'new_name': final_new_name,
                'new_id': new_id
            })

    except Exception as e:
        print(f"ERROR: Rename failed: {e}")
        return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500
        
@app.route('/galleryout/file/<string:file_id>')
def serve_file(file_id):
    filepath = get_file_info_from_db(file_id, 'path')
    if filepath.lower().endswith('.webp'): return send_file(filepath, mimetype='image/webp')
    return send_file(filepath)

@app.route('/galleryout/download/<string:file_id>')
def download_file(file_id):
    filepath = get_file_info_from_db(file_id, 'path')
    return send_file(filepath, as_attachment=True)

@app.route('/galleryout/workflow/<string:file_id>')
def download_workflow(file_id):
    info = get_file_info_from_db(file_id)
    filepath = info['path']
    original_filename = info['name']
    workflow_json = extract_workflow(filepath)
    if workflow_json:
        base_name, _ = os.path.splitext(original_filename)
        new_filename = f"{base_name}.json"
        headers = {'Content-Disposition': f'attachment;filename="{new_filename}"'}
        return Response(workflow_json, mimetype='application/json', headers=headers)
    abort(404)

@app.route('/galleryout/node_summary/<string:file_id>')
def get_node_summary(file_id):
    try:
        filepath = get_file_info_from_db(file_id, 'path')
        workflow_json = extract_workflow(filepath)
        if not workflow_json:
            return jsonify({'status': 'error', 'message': 'Workflow not found for this file.'}), 404
        summary_data = generate_node_summary(workflow_json)
        if summary_data is None:
            return jsonify({'status': 'error', 'message': 'Failed to parse workflow JSON.'}), 400
        return jsonify({'status': 'success', 'summary': summary_data})
    except Exception as e:
        print(f"ERROR generating node summary for {file_id}: {e}")
        return jsonify({'status': 'error', 'message': f'An internal error occurred: {e}'}), 500

@app.route('/galleryout/thumbnail/<string:file_id>')
def serve_thumbnail(file_id):
    info = get_file_info_from_db(file_id)
    filepath, mtime = info['path'], info['mtime']
    file_hash = hashlib.md5((filepath + str(mtime)).encode()).hexdigest()
    existing_thumbnails = glob.glob(os.path.join(THUMBNAIL_CACHE_DIR, f"{file_hash}.*"))
    if existing_thumbnails: return send_file(existing_thumbnails[0])
    print(f"WARN: Thumbnail not found for {os.path.basename(filepath)}, generating...")
    cache_path = create_thumbnail(filepath, file_hash, info['type'])
    if cache_path and os.path.exists(cache_path): return send_file(cache_path)
    return "Thumbnail generation failed", 404

@app.route('/galleryout/input_file/<path:filename>')
def serve_input_file(filename):
    """Serves input files directly from the ComfyUI Input folder."""
    try:
        # Prevent path traversal
        filename = secure_filename(filename)
        filepath = os.path.abspath(os.path.join(BASE_INPUT_PATH, filename))
        if not filepath.startswith(os.path.abspath(BASE_INPUT_PATH)):
            abort(403)
        
        # For webp, frocing the correct mimetype
        if filename.lower().endswith('.webp'):
            return send_from_directory(BASE_INPUT_PATH, filename, mimetype='image/webp', as_attachment=False)
        
        # For all the other files, I let Flask guessing the mimetype, but disable the attachment, just a lil trick
        return send_from_directory(BASE_INPUT_PATH, filename, as_attachment=False)
    except Exception as e:
        abort(404)

@app.route('/galleryout/check_metadata/<string:file_id>')
def check_metadata(file_id):
    """
    Lightweight endpoint to check real-time status of metadata.
    """
    try:
        with get_db_connection() as conn:
            # Aggiunto ai_last_scanned alla query
            row = conn.execute("SELECT has_workflow, ai_caption, ai_last_scanned FROM files WHERE id = ?", (file_id,)).fetchone()
            
        if not row:
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
            
        return jsonify({
            'status': 'success',
            'has_workflow': bool(row['has_workflow']),
            'has_ai_caption': bool(row['ai_caption']),
            'ai_caption': row['ai_caption'] or "",
            'ai_last_scanned': row['ai_last_scanned'] or 0 # Nuovi dati
        })
    except Exception as e:
        print(f"Metadata Check Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/galleryout/stream/<string:file_id>')
def stream_video(file_id):
    """
    Streams video files by transcoding them on-the-fly using FFmpeg.
    This allows professional formats like ProRes to be viewed in any browser.
    Includes a safety scale filter to ensure smooth playback even for 4K+ sources.
    """
    filepath = get_file_info_from_db(file_id, 'path')
    
    if not FFPROBE_EXECUTABLE_PATH:
        abort(404, description="FFmpeg/FFprobe not found on system.")

    # Determine ffmpeg executable path based on ffprobe location
    ffmpeg_dir = os.path.dirname(FFPROBE_EXECUTABLE_PATH)
    ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    ffmpeg_path = os.path.join(ffmpeg_dir, ffmpeg_name) if ffmpeg_dir else ffmpeg_name

    # FFmpeg command for fast on-the-fly transcoding
    # -preset ultrafast: minimal CPU usage
    # -vf scale: ensures the stream is not larger than 720p for performance
    # -movflags frag_keyframe+empty_moov: required for fragmented MP4 streaming
    cmd = [
        ffmpeg_path,
        '-i', filepath,
        '-vcodec', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-vf', "scale='min(1280,iw)':-2", 
        '-acodec', 'aac',
        '-b:a', '128k',
        '-f', 'mp4',
        '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
        'pipe:1'
    ]

    def generate():
        # Start ffmpeg process with specific flags to avoid console windows on Windows
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        try:
            # Read in chunks of 16KB for better streaming performance
            while True:
                data = process.stdout.read(16384)
                if not data:
                    break
                yield data
        finally:
            # Clean up: ensure the process is killed when the request ends
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

    return Response(generate(), mimetype='video/mp4')
    
def print_startup_banner():
    banner = rf"""
{Colors.GREEN}{Colors.BOLD}   _____                      _      _____       _ _                 
  / ____|                    | |    / ____|     | | |                
 | (___  _ __ ___   __ _ _ __| |_  | |  __  __ _| | | ___ _ __ _   _ 
  \___ \| '_ ` _ \ / _` | '__| __| | | |_ |/ _` | | |/ _ \ '__| | | |
  ____) | | | | | | (_| | |  | |_  | |__| | (_| | | |  __/ |  | |_| |
 |_____/|_| |_| |_|\__,_|_|   \__|  \_____|\__,_|_|_|\___|_|   \__, |
                                                                __/ |
                                                               |___/ {Colors.RESET}
    """
    print(banner)
    print(f"   {Colors.BOLD}Smart Gallery for ComfyUI{Colors.RESET}")
    print(f"   Author     : {Colors.BLUE}Biagio Maffettone{Colors.RESET}")
    print(f"   Version    : {Colors.YELLOW}{APP_VERSION}{Colors.RESET} ({APP_VERSION_DATE})")
    print(f"   GitHub     : {Colors.CYAN}{GITHUB_REPO_URL}{Colors.RESET}")
    print(f"   Contributor: {Colors.CYAN}Martial Michel (Docker & Codebase){Colors.RESET}")
    print("")

# --- GLOBAL STATE FOR UPDATES ---
UPDATE_AVAILABLE = False
REMOTE_VERSION = None  # New global variable

def check_for_updates():
    """Checks the GitHub repo for a newer version without external libs."""
    global UPDATE_AVAILABLE, REMOTE_VERSION
    print("Checking for updates...", end=" ", flush=True)
    try:
        # Timeout (3s) not blocking start if no internet connection
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=3) as response:
            content = response.read().decode('utf-8')
            
            # Regex modified to handle APP_VERSION="1.41" (string) or APP_VERSION=1.41 (number)
            match = re.search(r'APP_VERSION\s*=\s*["\']?([0-9.]+)["\']?', content)
            
            remote_version_str = None
            if match:
                remote_version_str = match.group(1)
            else:
                match_header = re.search(r'#\s*Version:\s*([0-9.]+)', content)
                if match_header:
                    remote_version_str = match_header.group(1)

            if remote_version_str:
                local_clean = re.sub(r'[^0-9.]', '', str(APP_VERSION))
                remote_clean = re.sub(r'[^0-9.]', '', str(remote_version_str))

                local_dots = local_clean.count('.')
                remote_dots = remote_clean.count('.')
                
                is_update_available = False
                
                if local_dots <= 1 and remote_dots <= 1:
                    try:
                        is_update_available = float(remote_clean) > float(local_clean)
                    except ValueError:
                        pass

                if not is_update_available:
                    local_v = tuple(map(int, local_clean.split('.'))) if local_clean else (0,)
                    remote_v = tuple(map(int, remote_clean.split('.'))) if remote_clean else (0,)
                    is_update_available = remote_v > local_v
                
                if is_update_available:
                    UPDATE_AVAILABLE = True
                    REMOTE_VERSION = remote_version_str # Store the version string
                    print(f"\n{Colors.YELLOW}{Colors.BOLD}NOTICE: A new version ({remote_version_str}) is available!{Colors.RESET}")
                else:
                    print("You are up to date.")
            else:
                print("Could not parse remote version.")
                
    except Exception:
        print("Skipped (Offline or GitHub unreachable).")
        
# --- STARTUP CHECKS AND MAIN ENTRY POINT ---
def show_config_error_and_exit(path):
    """Shows a critical error message and exits the program."""
    msg = (
        f"❌ CRITICAL ERROR: The specified path does not exist or is not accessible:\n\n"
        f"👉 {path}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. If you are launching via a script (e.g., .bat file), please edit it and set the correct 'BASE_OUTPUT_PATH' variable.\n"
        f"2. Or edit 'smartgallery.py' (USER CONFIGURATION section) and ensure the path points to an existing folder.\n\n"
        f"The program cannot continue and will now exit."
    )
    
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showerror("SmartGallery - Configuration Error", msg)
        root.destroy()
    else:
        # Fallback for headless environments (Docker, etc.)
        print(f"\n{Colors.RED}{Colors.BOLD}" + "="*70 + f"{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}{msg}{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}" + "="*70 + f"{Colors.RESET}\n")
    
    sys.exit(1)

def show_ffmpeg_warning():
    """Shows a non-blocking warning message for missing FFmpeg."""
    msg = (
        "WARNING: FFmpeg/FFprobe not found\n\n"
        "The system uses the 'ffprobe' utility to analyze video files. "
        "It seems it is missing or not configured correctly.\n\n"
        "CONSEQUENCES:\n"
        "❌ You will NOT be able to extract ComfyUI workflows from video files (.mp4, .mov, etc).\n"
        "✅ Gallery browsing, playback, and image features will still work perfectly.\n\n"
        "To fix this, install FFmpeg or check the 'FFPROBE_MANUAL_PATH' in the configuration."
    )
    
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showwarning("SmartGallery - Feature Limitation", msg)
        root.destroy()
    else:
        # Fallback for headless environments (Docker, etc.)
        print(f"\n{Colors.YELLOW}{Colors.BOLD}" + "="*70 + f"{Colors.RESET}")
        print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}" + "="*70 + f"{Colors.RESET}\n")

if __name__ == '__main__':

    print_startup_banner()
    check_for_updates()
    print_configuration()

    # --- CHECK: CRITICAL OUTPUT PATH CHECK (Blocking) ---
    if not os.path.exists(BASE_OUTPUT_PATH):
        show_config_error_and_exit(BASE_OUTPUT_PATH)

    # --- CHECK: INPUT PATH CHECK (Non-Blocking / Warning) ---
    if not os.path.exists(BASE_INPUT_PATH):
        print(f"{Colors.YELLOW}{Colors.BOLD}WARNING: Input Path not found!{Colors.RESET}")
        print(f"{Colors.YELLOW}   The path '{BASE_INPUT_PATH}' does not exist.{Colors.RESET}")
        print(f"{Colors.YELLOW}   > Source media visualization in Node Summary will be DISABLED.{Colors.RESET}")
        print(f"{Colors.YELLOW}   > The gallery will still function normally for output files.{Colors.RESET}\n")
    
    # Initialize the gallery (Creates DB, Migrations, etc.)
    initialize_gallery()
    
    # --- CHECK: FFMPEG WARNING ---
    if not FFPROBE_EXECUTABLE_PATH:
        # Check if we are in a headless environment (like Docker) where tk might fail
        if os.environ.get('DISPLAY') or os.name == 'nt':
            try:
                show_ffmpeg_warning()
            except:
                print(f"{Colors.RED}WARNING: FFmpeg not found. Video workflows extraction disabled.{Colors.RESET}")
        else:
            print(f"{Colors.RED}WARNING: FFmpeg not found. Video workflows extraction disabled.{Colors.RESET}")

    # --- START BACKGROUND WATCHER (New Integration) ---
    if ENABLE_AI_SEARCH:
        try:
            # Daemon=True ensures the thread dies when the main app stops
            watcher = threading.Thread(target=background_watcher_task, daemon=True)
            watcher.start()
            print(f"{Colors.BLUE}INFO: AI Background Watcher started.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}ERROR: Failed to start AI Watcher: {e}{Colors.RESET}")

    print(f"{Colors.GREEN}{Colors.BOLD}🚀 Gallery started successfully!{Colors.RESET}")
    print(f"👉 Access URL: {Colors.CYAN}{Colors.BOLD}http://127.0.0.1:{SERVER_PORT}/galleryout/{Colors.RESET}")
    print(f"   (Press CTRL+C to stop)")
    
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)