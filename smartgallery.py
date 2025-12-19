# Smart Gallery for ComfyUI
# Author: Biagio Maffettone © 2025 — MIT License (free to use and modify)
#
# Version: 1.51 - December 18, 2025
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
APP_VERSION = "1.51"
APP_VERSION_DATE = "December 18, 2025"
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
DB_SCHEMA_VERSION = 26 
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
    # Timeout increased to 50s to be patient with the Indexer
    conn = sqlite3.connect(DATABASE_FILE, timeout=50)
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
        
    # Main files table - UPDATED SCHEMA with all new columns
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
            
            -- Version 24+ Columns included natively for fresh installs
            last_scanned REAL DEFAULT 0,
            workflow_files TEXT DEFAULT '',
            workflow_prompt TEXT DEFAULT '',
            
            -- AI Columns
            ai_last_scanned REAL DEFAULT 0,
            ai_caption TEXT,
            ai_embedding BLOB,
            ai_error TEXT
        )
    ''')

    # AI Search Queue Table
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
    
    # AI Search Results Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            file_id TEXT NOT NULL,
            score REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES ai_search_queue(session_id)
        );
    ''')
    
    # AI Metadata Table
    conn.execute("CREATE TABLE IF NOT EXISTS ai_metadata (key TEXT PRIMARY KEY, value TEXT, updated_at REAL)")
    
    # Indices
    conn.execute('CREATE INDEX IF NOT EXISTS idx_queue_status ON ai_search_queue(status);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_results_session ON ai_search_results(session_id);')

    conn.commit()
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
            'mtime': root_mtime 
        }
    }

    try:
        all_folders = {}
        for dirpath, dirnames, _ in os.walk(BASE_OUTPUT_PATH):
            dirnames[:] = [d for d in dirnames if d not in [THUMBNAIL_CACHE_FOLDER_NAME, SQLITE_CACHE_FOLDER_NAME, ZIP_CACHE_FOLDER_NAME, AI_MODELS_FOLDER_NAME]]
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

            dynamic_config[key] = {
                'display_name': folder_data['display_name'],
                'path': folder_data['full_path'],
                'relative_path': rel_path,
                'parent': parent_key,
                'children': [],
                'mtime': folder_data['mtime']
            }
    except FileNotFoundError:
        print(f"WARNING: The base directory '{BASE_OUTPUT_PATH}' was not found.")
    
    folder_config_cache = dynamic_config
    return dynamic_config
    
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
                            WHEN files.mtime != excluded.mtime THEN 0  
                            ELSE files.is_favorite                     
                        END,
                        
                        ai_caption = CASE 
                            WHEN files.mtime != excluded.mtime THEN NULL 
                            ELSE files.ai_caption                        
                        END,
                        
                        ai_embedding = CASE 
                            WHEN files.mtime != excluded.mtime THEN NULL 
                            ELSE files.ai_embedding 
                        END,

                        ai_last_scanned = CASE 
                            WHEN files.mtime != excluded.mtime THEN 0 
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
                                WHEN files.mtime != excluded.mtime THEN 0  
                                ELSE files.is_favorite                     
                            END,
                            
                            ai_caption = CASE 
                                WHEN files.mtime != excluded.mtime THEN NULL 
                                ELSE files.ai_caption                        
                            END,
                            
                            ai_embedding = CASE 
                                WHEN files.mtime != excluded.mtime THEN NULL 
                                ELSE files.ai_embedding 
                            END,

                            ai_last_scanned = CASE 
                                WHEN files.mtime != excluded.mtime THEN 0 
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
        
def scan_folder_and_extract_options(folder_path):
    extensions, prefixes = set(), set()
    file_count = 0
    try:
        if not os.path.isdir(folder_path): return 0, [], []
        for filename in os.listdir(folder_path):
            if os.path.isfile(os.path.join(folder_path, filename)):
                ext = os.path.splitext(filename)[1]
                if ext and ext.lower() not in ['.json', '.sqlite']: 
                    extensions.add(ext.lstrip('.').lower())
                    file_count += 1
                if '_' in filename: prefixes.add(filename.split('_')[0])
    except Exception as e: print(f"ERROR: Could not scan folder '{folder_path}': {e}")
    return file_count, sorted(list(extensions)), sorted(list(prefixes))

def _worker_extract_wf_string(filepath):
    """
    Worker helper for migration: Extracts just the workflow string.
    """
    try:
        wf_json = extract_workflow(filepath)
        if wf_json:
            return extract_workflow_files_string(wf_json)
    except Exception:
        pass
    return ""

def _worker_extract_wf_prompt(filepath):
    """
    Worker helper for migration: Extracts just the workflow prompt (positive).
    """
    try:
        wf_json = extract_workflow(filepath)
        if wf_json:
            return extract_workflow_prompt_string(wf_json)
    except Exception:
        pass
    return ""

def initialize_gallery():
    print("INFO: Initializing gallery...")
    global FFPROBE_EXECUTABLE_PATH
    FFPROBE_EXECUTABLE_PATH = find_ffprobe_path()
    os.makedirs(THUMBNAIL_CACHE_DIR, exist_ok=True)
    os.makedirs(SQLITE_CACHE_DIR, exist_ok=True)
    
    with get_db_connection() as conn:
        try:
            # ==========================================
            # SCENARIO A: FRESH INSTALL (No Database)
            # ==========================================
            table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'").fetchone()
            
            if not table_check:
                print(f"{Colors.GREEN}INFO: New installation detected. Creating database (v{DB_SCHEMA_VERSION})...{Colors.RESET}")
                # 1. Create Tables (schema is already up to date in init_db)
                init_db(conn)
                # 2. Initial Scan
                print(f"{Colors.BLUE}INFO: Performing initial file scan...{Colors.RESET}")
                full_sync_database(conn)
                # 3. Set Version
                conn.execute(f'PRAGMA user_version = {DB_SCHEMA_VERSION}')
                conn.commit()
                print(f"{Colors.GREEN}INFO: Initialization complete.{Colors.RESET}")
                return # Exit function, everything is ready.

            # ==========================================
            # SCENARIO B: UPGRADE / EXISTING DATABASE
            # ==========================================
            
            # 1. Check & Add Missing Columns (Non-destructive Migration)
            cursor = conn.execute("PRAGMA table_info(files)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # List of columns to check/add
            migrations = {
                'last_scanned': 'REAL DEFAULT 0',
                'ai_last_scanned': 'REAL DEFAULT 0',
                'ai_caption': 'TEXT',
                'ai_embedding': 'BLOB',
                'ai_error': 'TEXT',
                'workflow_files': "TEXT DEFAULT ''",
                'workflow_prompt': "TEXT DEFAULT ''"
            }
            
            for col_name, col_def in migrations.items():
                if col_name not in columns:
                    print(f"INFO: Migrating DB... Adding column '{col_name}'")
                    conn.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_def}")
            
            conn.commit()

            # 2. Data Backfill (Populate new columns for existing files)
            
            # Backfill: Workflow Files
            missing_wf_data = conn.execute(
                "SELECT id, path FROM files WHERE has_workflow = 1 AND (workflow_files IS NULL OR workflow_files = '')"
            ).fetchall()
            
            if missing_wf_data:
                count = len(missing_wf_data)
                print(f"{Colors.YELLOW}INFO: Migrating {count} files to populate 'workflow_files'...{Colors.RESET}")
                updates = []
                with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
                    futures = {executor.submit(_worker_extract_wf_string, row['path']): row['id'] for row in missing_wf_data}
                    for future in tqdm(concurrent.futures.as_completed(futures), total=count, desc="Migrating Files", unit="files"):
                        try:
                            wf_string = future.result()
                            if wf_string: updates.append((wf_string, futures[future]))
                        except: pass
                if updates:
                    conn.executemany("UPDATE files SET workflow_files = ? WHERE id = ?", updates)
                    conn.commit()

            # Backfill: Workflow Prompt
            missing_prompt_data = conn.execute(
                "SELECT id, path FROM files WHERE has_workflow = 1 AND (workflow_prompt IS NULL OR workflow_prompt = '')"
            ).fetchall()
            
            if missing_prompt_data:
                count = len(missing_prompt_data)
                print(f"{Colors.YELLOW}INFO: Migrating {count} files to populate 'workflow_prompt'...{Colors.RESET}")
                print(f"{Colors.DIM}      This runs only once. Please wait...{Colors.RESET}")
                updates = []
                with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
                    futures = {executor.submit(_worker_extract_wf_prompt, row['path']): row['id'] for row in missing_prompt_data}
                    for future in tqdm(concurrent.futures.as_completed(futures), total=count, desc="Migrating Prompts", unit="files"):
                        try:
                            wf_prompt = future.result()
                            updates.append((wf_prompt, futures[future]))
                        except: pass
                if updates:
                    conn.executemany("UPDATE files SET workflow_prompt = ? WHERE id = ?", updates)
                    conn.commit()
                print(f"{Colors.GREEN}INFO: Prompt migration complete.{Colors.RESET}")

            # 3. Final Version Update
            # We update the version number only after migrations are successful
            try: 
                stored_version = conn.execute('PRAGMA user_version').fetchone()[0]
            except: 
                stored_version = 0
                
            if stored_version < DB_SCHEMA_VERSION:
                print(f"INFO: Updating DB Internal Version: {stored_version} -> {DB_SCHEMA_VERSION}")
                conn.execute(f'PRAGMA user_version = {DB_SCHEMA_VERSION}')
                conn.commit()
            
            # 4. Fallback check for empty DB on existing install
            # (In case a user has the DB file but 0 records for some reason)
            file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            if file_count == 0:
                print(f"{Colors.BLUE}INFO: Database file exists but is empty. Scanning...{Colors.RESET}")
                full_sync_database(conn)

        except sqlite3.DatabaseError as e:
            print(f"ERROR initializing database: {e}")
            
def get_filter_options_from_db(conn, scope, folder_path=None):
    """
    Extracts available extensions and prefixes from the database based on scope.
    Enforces a limit on prefixes to prevent UI issues.
    """
    extensions = set()
    prefixes = set()
    prefix_limit_reached = False
    
    try:
        # Determine Query based on Scope
        if scope == 'global':
            cursor = conn.execute("SELECT name FROM files")
        else:
            # Local Scope: strict folder match (parent directory must match)
            # We use Python filtering for strict parent match to align with view logic,
            # or a precise SQL like 'path' logic.
            # To be fast and consistent with gallery_view, we query strictly.
            # Note: We need rows that belong strictly to this folder.
            
            # Efficient SQL for strict parent check is complex across OS separators.
            # We will grab all files in the tree and filter in python for 100% accuracy
            # or use a GLOB/LIKE and filter.
            cursor = conn.execute("SELECT name, path FROM files WHERE path LIKE ?", (folder_path + os.sep + '%',))

        # Process Results
        for row in cursor:
            # For local scope, ensure strict containment (no subfolders)
            if scope != 'global':
                file_dir = os.path.dirname(row['path'])
                # OS-agnostic comparison
                if os.path.normpath(file_dir) != os.path.normpath(folder_path):
                    continue

            name = row['name']
            
            # 1. Extensions
            _, ext = os.path.splitext(name)
            if ext: 
                extensions.add(ext.lstrip('.').lower())
            
            # 2. Prefixes (Only if limit not reached)
            if not prefix_limit_reached and '_' in name:
                pfx = name.split('_')[0]
                if pfx:
                    prefixes.add(pfx)
                    if len(prefixes) > MAX_PREFIX_DROPDOWN_ITEMS:
                        prefix_limit_reached = True
                        prefixes.clear() # Discard to save memory, UI will show fallback
                        
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
    """
    API Endpoint to fetch filter options (extensions/prefixes) dynamically
    without reloading the page.
    """
    scope = request.args.get('scope', 'local')
    folder_key = request.args.get('folder_key', '_root_')
    
    folders = get_dynamic_folder_config()
    # Resolve folder path safely
    folder_path = folders.get(folder_key, {}).get('path', BASE_OUTPUT_PATH)
    
    with get_db_connection() as conn:
        exts, pfxs, limit_reached = get_filter_options_from_db(conn, scope, folder_path)
        
    return jsonify({
        'extensions': exts,
        'prefixes': pfxs,
        'prefix_limit_reached': limit_reached
    })

@app.route('/galleryout/view/<string:folder_key>')
def gallery_view(folder_key):
    global gallery_view_cache
    folders = get_dynamic_folder_config(force_refresh=True)
    if folder_key not in folders:
        return redirect(url_for('gallery_view', folder_key='_root_'))
    
    current_folder_info = folders[folder_key]
    folder_path = current_folder_info['path']
    
    # Check if this is an AI Result View (Only if enabled)
    ai_session_id = request.args.get('ai_session_id')
    is_ai_search = False
    ai_query_text = ""
    is_global_search = False
    
    # AI Logic runs only if explicitly enabled
    if ENABLE_AI_SEARCH:
        with get_db_connection() as conn:
            # --- PATH A: AI SEARCH RESULTS ---
            if ai_session_id:
                # Verify session completion
                try:
                    queue_info = conn.execute("SELECT query, status FROM ai_search_queue WHERE session_id = ?", (ai_session_id,)).fetchone()
                    
                    if queue_info and queue_info['status'] == 'completed':
                        is_ai_search = True
                        ai_query_text = queue_info['query']
                        
                        # Retrieve files joined with search results, ordered by score
                        query_sql = '''
                            SELECT f.*, r.score 
                            FROM ai_search_results r
                            JOIN files f ON r.file_id = f.id
                            WHERE r.session_id = ?
                            ORDER BY r.score DESC
                        '''
                        all_files_raw = conn.execute(query_sql, (ai_session_id,)).fetchall()
                        
                        # Convert to dict and clean blob
                        files_list = []
                        for row in all_files_raw:
                            d = dict(row)
                            if 'ai_embedding' in d: del d['ai_embedding']
                            files_list.append(d)
                        
                        gallery_view_cache = files_list
                except Exception as e:
                    print(f"AI Search Error: {e}")
                    is_ai_search = False
    
    # --- PATH B: STANDARD FOLDER VIEW OR GLOBAL STANDARD SEARCH ---
    if not is_ai_search:
        with get_db_connection() as conn:
            conditions, params = [], []
            
            # Check for Global Search Scope
            search_scope = request.args.get('scope', 'local')
            if search_scope == 'global':
                is_global_search = True
            else:
                # Local scope: filter by path
                conditions.append("path LIKE ?")
                params.append(folder_path + os.sep + '%')
            
            sort_by = 'name' if request.args.get('sort_by') == 'name' else 'mtime'
            sort_order = 'asc' if request.args.get('sort_order', 'desc').lower() == 'asc' else 'desc'

            # 1. Text Search
            search_term = request.args.get('search', '').strip()
            if search_term:
                conditions.append("name LIKE ?")
                params.append(f"%{search_term}%")
            
            # 2. Workflow Files Search
            wf_search_raw = request.args.get('workflow_files', '').strip()
            if wf_search_raw:
                keywords = [k.strip() for k in wf_search_raw.split(',') if k.strip()]
                for kw in keywords:
                    smart_kw = normalize_smart_path(kw)
                    conditions.append("workflow_files LIKE ?")
                    params.append(f"%{smart_kw}%")
            
            # 3. Workflow PROMPT Search (NEW)
            wf_prompt_raw = request.args.get('workflow_prompt', '').strip()
            if wf_prompt_raw:
                keywords = [k.strip() for k in wf_prompt_raw.split(',') if k.strip()]
                for kw in keywords:
                    # Use standard LIKE for text matching
                    conditions.append("workflow_prompt LIKE ?")
                    params.append(f"%{kw}%")
                    
            # 4. Boolean Options
            # Favorites
            if request.args.get('favorites', 'false').lower() == 'true':
                conditions.append("is_favorite = 1")
            
            # No Workflow (New)
            if request.args.get('no_workflow', 'false').lower() == 'true':
                conditions.append("has_workflow = 0")
            
            # No AI Caption (New - Only if AI Enabled)
            if ENABLE_AI_SEARCH and request.args.get('no_ai_caption', 'false').lower() == 'true':
                conditions.append("(ai_caption IS NULL OR ai_caption = '')")

            # 5. Date Range Search (New)
            start_date_str = request.args.get('start_date', '').strip()
            end_date_str = request.args.get('end_date', '').strip()

            if start_date_str:
                try:
                    # Convert 'YYYY-MM-DD' to timestamp at 00:00:00
                    dt_start = datetime.strptime(start_date_str, '%Y-%m-%d')
                    conditions.append("mtime >= ?")
                    params.append(dt_start.timestamp())
                except ValueError:
                    pass # Ignore invalid date format
            
            if end_date_str:
                try:
                    # Convert 'YYYY-MM-DD' to timestamp at 23:59:59
                    dt_end = datetime.strptime(end_date_str, '%Y-%m-%d')
                    # Add almost one day (86399 seconds) to include the whole end day
                    end_ts = dt_end.timestamp() + 86399 
                    conditions.append("mtime <= ?")
                    params.append(end_ts)
                except ValueError:
                    pass

            # 6. Dropdown Filters (Prefix/Extensions)
            selected_prefixes = request.args.getlist('prefix')
            if selected_prefixes:
                prefix_conditions = [f"name LIKE ?" for p in selected_prefixes if p.strip()]
                params.extend([f"{p.strip()}_%" for p in selected_prefixes if p.strip()])
                if prefix_conditions: conditions.append(f"({' OR '.join(prefix_conditions)})")

            selected_extensions = request.args.getlist('extension')
            if selected_extensions:
                ext_conditions = [f"name LIKE ?" for ext in selected_extensions if ext.strip()]
                params.extend([f"%.{ext.lstrip('.').lower()}" for ext in selected_extensions if ext.strip()])
                if ext_conditions: conditions.append(f"({' OR '.join(ext_conditions)})")
            
            sort_direction = "ASC" if sort_order == 'asc' else "DESC"
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"SELECT * FROM files {where_clause} ORDER BY {sort_by} {sort_direction}"
            
            all_files_raw = conn.execute(query, params).fetchall()
            
            # Local Scope strict filtering
            if not is_global_search:
                folder_path_norm = os.path.normpath(folder_path)
                all_files_filtered = [dict(row) for row in all_files_raw if os.path.normpath(os.path.dirname(row['path'])) == folder_path_norm]
            else:
                all_files_filtered = [dict(row) for row in all_files_raw]

            # Cleanup blobs
            for f in all_files_filtered:
                if 'ai_embedding' in f: del f['ai_embedding']
                
            gallery_view_cache = all_files_filtered

    # Count active filters for UI Feedback
    active_filters_count = 0
    if request.args.get('search', '').strip(): active_filters_count += 1
    if request.args.get('workflow_files', '').strip(): active_filters_count += 1
    if request.args.get('workflow_prompt', '').strip(): active_filters_count += 1
    if request.args.get('favorites', 'false').lower() == 'true': active_filters_count += 1
    if request.args.get('no_workflow', 'false').lower() == 'true': active_filters_count += 1
    if request.args.get('no_ai_caption', 'false').lower() == 'true': active_filters_count += 1
    if request.args.get('start_date', '').strip(): active_filters_count += 1 
    if request.args.getlist('extension'): active_filters_count += 1
    if request.args.getlist('prefix'): active_filters_count += 1
    if request.args.get('scope', 'local') == 'global': active_filters_count += 1

    # Pagination Logic (Shared)
    initial_files = gallery_view_cache[:PAGE_SIZE]
    
    # --- Metadata and Options Logic ---
    
    # 1. Get total files count for the badge (Standard Local Scan)
    # We ignore the list-based options from the scan (using _) because we get them from DB now
    total_folder_files, _, _ = scan_folder_and_extract_options(folder_path)
    
    # 2. Get Filter Dropdown Options (DB Based, Scope Aware, Limited)
    scope_for_options = 'global' if is_global_search else 'local'
    
    # Initialize variables to ensure they exist even if branches are skipped
    extensions = []
    prefixes = []
    prefix_limit_reached = False

    # Check if 'conn' variable exists and is open from previous blocks (PATH B)
    if 'conn' in locals() and not is_ai_search:
        # Re-use existing connection
        extensions, prefixes, prefix_limit_reached = get_filter_options_from_db(conn, scope_for_options, folder_path)
    else:
        # Open temp connection (e.g. inside AI path or error cases)
        with get_db_connection() as db_conn_for_opts:
            extensions, prefixes, prefix_limit_reached = get_filter_options_from_db(db_conn_for_opts, scope_for_options, folder_path)
    
    # --- Breadcrumbs Logic ---
    breadcrumbs, ancestor_keys = [], set()
    curr_key = folder_key
    while curr_key is not None and curr_key in folders:
        folder_info = folders[curr_key]
        breadcrumbs.append({'key': curr_key, 'display_name': folder_info['display_name']})
        ancestor_keys.add(curr_key)
        curr_key = folder_info.get('parent')
    breadcrumbs.reverse()
    
    return render_template('index.html', 
                           files=initial_files, 
                           total_files=len(gallery_view_cache),
                           total_folder_files=total_folder_files, 
                           folders=folders,
                           current_folder_key=folder_key, 
                           current_folder_info=current_folder_info,
                           breadcrumbs=breadcrumbs,
                           ancestor_keys=list(ancestor_keys),
                           available_extensions=extensions, 
                           available_prefixes=prefixes,
                           prefix_limit_reached=prefix_limit_reached,  
                           selected_extensions=request.args.getlist('extension'), 
                           selected_prefixes=request.args.getlist('prefix'),
                           show_favorites=request.args.get('favorites', 'false').lower() == 'true', 
                           protected_folder_keys=list(PROTECTED_FOLDER_KEYS),
                           enable_ai_search=ENABLE_AI_SEARCH,
                           is_ai_search=is_ai_search,
                           ai_query=ai_query_text,
                           is_global_search=is_global_search,
                           active_filters_count=active_filters_count,
                           current_scope=request.args.get('scope', 'local'))
                           
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
                            WHEN files.mtime != excluded.mtime THEN 0  
                            ELSE files.is_favorite                     
                        END,
                        
                        ai_caption = CASE 
                            WHEN files.mtime != excluded.mtime THEN NULL 
                            ELSE files.ai_caption                        
                        END,
                        
                        ai_embedding = CASE 
                            WHEN files.mtime != excluded.mtime THEN NULL 
                            ELSE files.ai_embedding 
                        END,

                        ai_last_scanned = CASE 
                            WHEN files.mtime != excluded.mtime THEN 0 
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
    old_path = folders[folder_key]['path']
    new_path = os.path.join(os.path.dirname(old_path), new_name)
    if os.path.exists(new_path): return jsonify({'status': 'error', 'message': 'A folder with this name already exists.'}), 400
    try:
        with get_db_connection() as conn:
            old_path_like = old_path + os.sep + '%'
            files_to_update = conn.execute("SELECT id, path FROM files WHERE path LIKE ?", (old_path_like,)).fetchall()
            update_data = []
            for row in files_to_update:
                new_file_path = row['path'].replace(old_path, new_path, 1)
                new_id = hashlib.md5(new_file_path.encode()).hexdigest()
                update_data.append((new_id, new_file_path, row['id']))
            os.rename(old_path, new_path)
            if update_data: conn.executemany("UPDATE files SET id = ?, path = ? WHERE id = ?", update_data)
            conn.commit()
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder renamed.'})
    except Exception as e: return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500
    
@app.route('/galleryout/delete_folder/<string:folder_key>', methods=['POST'])
def delete_folder(folder_key):
    if folder_key in PROTECTED_FOLDER_KEYS: return jsonify({'status': 'error', 'message': 'This folder cannot be deleted.'}), 403
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Folder not found.'}), 404
    try:
        folder_path = folders[folder_key]['path']
        with get_db_connection() as conn:
            conn.execute("DELETE FROM files WHERE path LIKE ?", (folder_path + os.sep + '%',))
            conn.commit()
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

@app.route('/favicon.ico')
def favicon():
    return send_file('static/galleryout/favicon.ico')

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
    Lightweight endpoint to check real-time status of metadata 
    (Workflow and AI Caption) for the Lightbox.
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT has_workflow, ai_caption FROM files WHERE id = ?", (file_id,)).fetchone()
            
        if not row:
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
            
        return jsonify({
            'status': 'success',
            'has_workflow': bool(row['has_workflow']),
            'has_ai_caption': bool(row['ai_caption']),
            'ai_caption': row['ai_caption'] or "" # Return actual text to update cache
        })
    except Exception as e:
        print(f"Metadata Check Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
          
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

def check_for_updates():
    """Checks the GitHub repo for a newer version without external libs."""
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
                # Fallback: Check header comment if variable not found
                match_header = re.search(r'#\s*Version:\s*([0-9.]+)', content)
                if match_header:
                    remote_version_str = match_header.group(1)

            if remote_version_str:
                # --- HYBRID COMPARISON LOGIC ---
                # 1. Clean both versions from non-numeric chars (except dots)
                local_clean = re.sub(r'[^0-9.]', '', str(APP_VERSION))
                remote_clean = re.sub(r'[^0-9.]', '', str(remote_version_str))

                # 2. Check if they are Legacy Float style (max 1 dot, e.g. "1.41", "1.4099")
                #    or Modern SemVer style (2+ dots, e.g. "1.51.01")
                local_dots = local_clean.count('.')
                remote_dots = remote_clean.count('.')
                
                is_update_available = False
                
                if local_dots <= 1 and remote_dots <= 1:
                    # Use Float logic (Legacy) to support 1.41 > 1.4099
                    try:
                        is_update_available = float(remote_clean) > float(local_clean)
                    except ValueError:
                        # Fallback to tuple comparison if float conversion fails
                        pass

                if not is_update_available:
                    # Use Semantic Tuple logic (Modern) if float check failed or didn't apply
                    # Examples: 1.51.1 > 1.51
                    local_v = tuple(map(int, local_clean.split('.'))) if local_clean else (0,)
                    remote_v = tuple(map(int, remote_clean.split('.'))) if remote_clean else (0,)
                    is_update_available = remote_v > local_v
                
                if is_update_available:
                    print(f"\n{Colors.YELLOW}{Colors.BOLD}NOTICE: A new version ({remote_version_str}) is available!{Colors.RESET}")
                    print(f"Please update from: {GITHUB_REPO_URL}\n")
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
    
    # Initialize the gallery
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

    print(f"{Colors.GREEN}{Colors.BOLD}🚀 Gallery started successfully!{Colors.RESET}")
    print(f"👉 Access URL: {Colors.CYAN}{Colors.BOLD}http://127.0.0.1:{SERVER_PORT}/galleryout/{Colors.RESET}")
    print(f"   (Press CTRL+C to stop)")
    
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)