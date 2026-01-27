# Smart Gallery for ComfyUI
# Author: Biagio Maffettone © 2025-2026 — MIT License (free to use and modify)
#
# Version: 1.54.5-beta - January 27, 2026
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
from typing import Dict, List, Any, Optional, Union # Added for type hinting in new tools


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
APP_VERSION = "1.54.5-beta"
APP_VERSION_DATE = "January 27, 2026"
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
    "KSampler": ["seed", "control_after_generate", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
    "KSamplerAdvanced": ["add_noise", "noise_seed", "control_after_generate", "steps", "cfg", "sampler_name", "scheduler", "start_at_step", "end_at_step", "return_with_leftover_noise"],
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

# ============================================================================
# NEW INTEGRATED TOOLS (ADVANCED METADATA EXTRACTION)
# This section contains the new parsing logic integrated directly into the source
# ============================================================================

# --- Regex Patterns for Prompt Parsing ---
RE_LORA_PROMPT = re.compile(r"<lora:([\w_\s.-]+)(?::([\d.]+))*>", re.IGNORECASE)
RE_LYCO_PROMPT = re.compile(r"<lyco:([\w_\s.]+):([\d.]+)>", re.IGNORECASE)
RE_PARENS = re.compile(r"[\\/\[\](){}]+")
RE_LORA_CLOSE = re.compile(r">\s+")

def clean_prompt_text(x: str) -> Dict[str, Any]:
    """
    Cleans a raw prompt string: removes LoRA tags, normalizes whitespace,
    and extracts LoRA usage into a separate list.
    """
    if not x:
        return {"text": "", "loras": []}
        
    x = re.sub(r'\sBREAK\s', ' , BREAK , ', x)
    x = re.sub(RE_LORA_CLOSE, "> , ", x)
    x = x.replace("，", ",").replace("-", " ").replace("_", " ")
    
    clean_text = re.sub(RE_PARENS, "", x)
    
    tag_list = [t.strip() for t in x.split(",")]
    lora_list = []
    final_tags = []
    
    for tag in tag_list:
        if not tag: continue
        
        lora_match = re.search(RE_LORA_PROMPT, tag)
        lyco_match = re.search(RE_LYCO_PROMPT, tag)
        
        if lora_match:
            val = float(lora_match.group(2)) if lora_match.group(2) else 1.0
            lora_list.append({"name": lora_match.group(1), "value": val})
        elif lyco_match:
            lora_list.append({"name": lyco_match.group(1), "value": float(lyco_match.group(2))})
        else:
            clean_tag = re.sub(RE_PARENS, "", tag).strip()
            if clean_tag:
                final_tags.append(clean_tag)

    return {
        "text": ", ".join(final_tags),
        "loras": lora_list
    }

class ComfyMetadataParser:
    """
    Advanced parser that traces the workflow graph to find real generation parameters.
    Updated to resolve links for Width, Height, and other linked numeric values.
    """
    def __init__(self, workflow_json: Dict):
        self.data = workflow_json

    def parse(self) -> Dict[str, Any]:
        """
        Main parsing method. Returns a standardized dictionary.
        """
        meta = {
            "seed": None, "steps": None, "cfg": None, "sampler": None,
            "scheduler": None, "model": None, "positive_prompt": "",
            "negative_prompt": "", "positive_prompt_clean": "",
            "width": None, "height": None, "loras": []
        }

        # Strategy A: Trace from KSampler (Most accurate for Prompts/Model)
        sampler_node_id = self._find_sampler_node()
        
        if sampler_node_id:
            self._extract_sampler_params(sampler_node_id, meta)
            self._extract_prompts_from_sampler(sampler_node_id, meta)
            self._extract_model_from_sampler(sampler_node_id, meta)
            self._extract_size_from_sampler(sampler_node_id, meta)

        # Strategy B: Fallback Scan (Scans specific nodes if Strategy A missed data)
        self._fallback_scan(meta)
        
        # Cleanup
        if meta["positive_prompt"]:
            cleaned = clean_prompt_text(meta["positive_prompt"])
            meta["positive_prompt_clean"] = cleaned["text"]
            meta["loras"] = cleaned["loras"]
            
        # Deduplicate Prompts if they are identical due to tracing overlaps
        if meta["negative_prompt"] == meta["positive_prompt"]:
            meta["negative_prompt"] = ""
            
        return meta

    def _find_sampler_node(self):
        """Finds the main KSampler node ID."""
        if not isinstance(self.data, dict): return None
        for node_id, node in self.data.items():
            if not isinstance(node, dict): continue
            class_type = node.get("class_type", "")
            if "KSampler" in class_type or "SamplerCustom" in class_type:
                return node_id
        return None

    def _get_real_value(self, value):
        """
        Follows links recursively to find the actual value.
        Improved to handle UI format where values are in widgets_values.
        """
        if not isinstance(value, list):
            return value
            
        try:
            source_id = str(value[0])
            if source_id in self.data:
                node = self.data[source_id]
                
                # Check Inputs (API Format)
                inputs = node.get("inputs", {})
                for key in ["value", "int", "float", "string", "text"]:
                    if key in inputs:
                        return self._get_real_value(inputs[key])
                
                # Check Widgets (UI Format)
                widgets = node.get("widgets_values", [])
                if widgets and not isinstance(widgets[0], (list, dict)):
                    return widgets[0]
                    
                # If it's another link in widgets (ComfyUI logic), follow it
                if widgets and isinstance(widgets[0], list):
                    return self._get_real_value(widgets[0])
        except:
            pass
        return None

    def _extract_size_from_sampler(self, node_id, meta):
        """
        Traces the latent image link. 
        If direct tracing fails, it attempts to find any 'EmptyLatentImage' node.
        """
        inputs = self.data[node_id].get("inputs", {})
        found_size = False

        if "latent_image" in inputs:
            link = inputs["latent_image"]
            if isinstance(link, list):
                source_id = str(link[0])
                node = self.data.get(source_id, {})
                node_inputs = node.get("inputs", {})
                
                if "width" in node_inputs: 
                    meta["width"] = self._get_real_value(node_inputs["width"])
                    found_size = True
                if "height" in node_inputs: 
                    meta["height"] = self._get_real_value(node_inputs["height"])

        # Final attempt: if still no size, scan for any EmptyLatentImage node in the graph
        if not found_size:
            for n in self.data.values():
                if n.get("class_type") == "EmptyLatentImage":
                    meta["width"] = self._get_real_value(n.get("inputs", {}).get("width"))
                    meta["height"] = self._get_real_value(n.get("inputs", {}).get("height"))
                    break

    def _extract_sampler_params(self, node_id, meta):
        """Extracts simple scalar values from the Sampler, resolving links."""
        inputs = self.data[node_id].get("inputs", {})
        
        # Use the new resolver to get actual values instead of links
        if "seed" in inputs: meta["seed"] = self._get_real_value(inputs["seed"])
        if "noise_seed" in inputs: meta["seed"] = self._get_real_value(inputs["noise_seed"])
        if "steps" in inputs: meta["steps"] = self._get_real_value(inputs["steps"])
        if "cfg" in inputs: meta["cfg"] = self._get_real_value(inputs["cfg"])
        if "sampler_name" in inputs: meta["sampler"] = self._get_real_value(inputs["sampler_name"])
        if "scheduler" in inputs: meta["scheduler"] = self._get_real_value(inputs["scheduler"])
        if "denoise" in inputs: meta["denoise"] = self._get_real_value(inputs["denoise"])

    def _extract_prompts_from_sampler(self, node_id, meta):
        """Traces 'positive' and 'negative' links to find text."""
        inputs = self.data[node_id].get("inputs", {})
        if "positive" in inputs:
            meta["positive_prompt"] = self._trace_text(inputs["positive"])
        if "negative" in inputs:
            meta["negative_prompt"] = self._trace_text(inputs["negative"])

    def _trace_text(self, link_info) -> str:
        """Recursive helper to find text content from a link."""
        if not isinstance(link_info, list): return ""
        source_id = str(link_info[0])
        if source_id not in self.data: return ""
        
        node = self.data[source_id]
        inputs = node.get("inputs", {})

        # Handle direct text encoders
        if "text" in inputs and isinstance(inputs["text"], str):
            return inputs["text"]
        
        # Handle SD3/Flux
        if "t5xxl" in inputs and isinstance(inputs["t5xxl"], str):
            return inputs["t5xxl"]

        # Handle concatenated or linked text
        if "text" in inputs and isinstance(inputs["text"], list):
            return self._trace_text(inputs["text"])

        # Handle Conditioning / Guidance nodes
        if "conditioning" in inputs:
             return self._trace_text(inputs["conditioning"])
        
        # Fallback to widgets for UI format nodes
        widgets = node.get("widgets_values", [])
        for w in widgets:
            if isinstance(w, str) and len(w) > 5: return w

        return ""

    def _extract_model_from_sampler(self, node_id, meta):
        """Follows the model wire to find the Checkpoint name."""
        inputs = self.data[node_id].get("inputs", {})
        if "model" in inputs:
            model_link = inputs["model"]
            if isinstance(model_link, list):
                source_id = str(model_link[0])
                if source_id in self.data:
                    node = self.data[source_id]
                    # Check for loader inputs
                    if "ckpt_name" in node.get("inputs", {}):
                        meta["model"] = node["inputs"]["ckpt_name"]
                    # Follow further if it's a LoRA or Model handler
                    elif "model" in node.get("inputs", {}) and isinstance(node["inputs"]["model"], list):
                         self._extract_model_from_sampler(source_id, meta)
    
    def _fallback_scan(self, meta):
        """Scans all nodes for specific types if direct tracing missed data."""
        if not isinstance(self.data, dict): return
        for node_id, node in self.data.items():
            if not isinstance(node, dict): continue
            class_type = node.get("class_type", "")
            inputs = node.get("inputs", {})

            if meta["seed"] is None and class_type == "RandomNoise":
                if "noise_seed" in inputs: meta["seed"] = self._get_real_value(inputs["noise_seed"])

            if meta["cfg"] is None and "Guider" in class_type:
                if "cfg" in inputs: meta["cfg"] = self._get_real_value(inputs["cfg"])

            if meta["steps"] is None and "Scheduler" in class_type:
                if "steps" in inputs: meta["steps"] = self._get_real_value(inputs["steps"])
# ============================================================================
# END OF INTEGRATED TOOLS
# ============================================================================

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
            
def extract_workflow(filepath, target_type='ui'):
    """
    Extracts workflow JSON from image/video files.
    
    Args:
        filepath (str): Path to the file.
        target_type (str): 'ui' (for visual node graph/version) or 'api' (for real execution values like Seed).
                           Defaults to 'ui' to restore original compatibility.
    """
    ext = os.path.splitext(filepath)[1].lower()
    video_exts = ['.mp4', '.mkv', '.webm', '.mov', '.avi']
    
    found_workflows = {} # Stores {'ui': json_str, 'api': json_str}
    
    def analyze_json(json_str):
        # Helper to classify and store found workflows
        wf, wf_type = _validate_and_get_workflow(json_str)
        if wf and wf_type:
            if wf_type not in found_workflows:
                found_workflows[wf_type] = wf

    if ext in video_exts:
        # --- FIX: Path resolution in worker processes ---
        current_ffprobe_path = FFPROBE_EXECUTABLE_PATH
        if not current_ffprobe_path:
             current_ffprobe_path = find_ffprobe_path()

        if current_ffprobe_path:
            try:
                cmd = [current_ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                data = json.loads(result.stdout)
                if 'format' in data and 'tags' in data['format']:
                    for value in data['format']['tags'].values():
                        if isinstance(value, str) and value.strip().startswith('{'):
                            analyze_json(value)
            except Exception: pass
    else:
        try:
            with Image.open(filepath) as img:
                # Check standard keys
                for key in ['workflow', 'prompt']:
                    val = img.info.get(key)
                    if val: analyze_json(val)

                # Check Exif/UserComment (for WebP/JPG)
                exif_data = img.info.get('exif')
                if exif_data and isinstance(exif_data, bytes):
                    try:
                        exif_str = exif_data.decode('utf-8', errors='ignore')
                        # Fast path: check for workflow marker
                        if 'workflow:{' in exif_str:
                            start = exif_str.find('workflow:{') + len('workflow:')
                            for json_candidate in _scan_bytes_for_workflow(exif_str[start:].encode('utf-8')):
                                analyze_json(json_candidate)
                    except Exception: pass
                    
                    # Full scan fallback
                    for json_str in _scan_bytes_for_workflow(exif_data):
                        analyze_json(json_str)
        except Exception: pass

    # Raw byte scan (ultimate fallback)
    if not found_workflows:
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            for json_str in _scan_bytes_for_workflow(content):
                analyze_json(json_str)
                # Optimization: Stop if we found what we wanted
                if target_type in found_workflows: break
        except Exception: pass
                
    # Return Logic:
    # 1. Return the requested type if found
    if target_type in found_workflows:
        return found_workflows[target_type]
    
    # 2. Fallback: If we wanted API but only have UI (or vice versa), return what we have
    if found_workflows:
        return list(found_workflows.values())[0]
        
    return None
    
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
    #https://aistudio.google.com/prompts/1uYTqxN6LAJZucWaoD5DlOlljhj0eB1uY#:~:text=function%20showItemAtIndex(index) = {'.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'animated_image', '.mp4': 'video', '.webm': 'video', '.mov': 'video', '.mp3': 'audio', '.wav': 'audio', '.ogg': 'audio', '.flac': 'audio'}
    # Extended Type Map for Professional Formats
    type_map = {
        # Images
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image', 
        '.bmp': 'image', '.tiff': 'image', '.tif': 'image',
        # Animations
        '.gif': 'animated_image', 
        # Videos (Standard & Pro)
        '.mp4': 'video', '.webm': 'video', '.mov': 'video', 
        '.mkv': 'video', '.avi': 'video', '.m4v': 'video', 
        '.wmv': 'video', '.flv': 'video', '.mts': 'video', '.ts': 'video',
        # Audio
        '.mp3': 'audio', '.wav': 'audio', '.ogg': 'audio', '.flac': 'audio', '.m4a': 'audio'
    }
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
    
    # --- IMAGES / ANIMATIONS ---
    if file_type in ['image', 'animated_image']:
        try:
            with Image.open(filepath) as img:
                fmt = 'gif' if img.format == 'GIF' else 'webp' if img.format == 'WEBP' else 'jpeg'
                cache_path = os.path.join(THUMBNAIL_CACHE_DIR, f"{file_hash}.{fmt}")
                
                # Handle Animations (Animated WebP / GIF)
                if file_type == 'animated_image' and getattr(img, 'is_animated', False):
                    frames = [fr.copy() for fr in ImageSequence.Iterator(img)]
                    if frames:
                        for frame in frames: 
                            frame.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_WIDTH * 2), Image.Resampling.LANCZOS)
                        
                        processed_frames = [frame.convert('RGBA').convert('RGB') for frame in frames]
                        if processed_frames:
                            processed_frames[0].save(
                                cache_path, 
                                save_all=True, 
                                append_images=processed_frames[1:], 
                                duration=img.info.get('duration', 100), 
                                loop=img.info.get('loop', 0), 
                                optimize=True
                            )
                            return cache_path
                
                # Handle Static Images
                else:
                    img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_WIDTH * 2), Image.Resampling.LANCZOS)
                    if img.mode != 'RGB': img = img.convert('RGB')
                    img.save(cache_path, 'JPEG', quality=85)
                    return cache_path
                    
        except Exception as e: 
            print(f"ERROR (Pillow): Thumbnail failed for {os.path.basename(filepath)}: {e}")

    # --- VIDEOS (MP4, MOV, MKV, AVI, etc.) ---
    elif file_type == 'video':
        cache_path = os.path.join(THUMBNAIL_CACHE_DIR, f"{file_hash}.jpeg")
        
        # Method A: Try OpenCV first (Fastest)
        try:
            cap = cv2.VideoCapture(filepath)
            if cap.isOpened():
                success, frame = cap.read()
                cap.release()
                if success:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_WIDTH * 2), Image.Resampling.LANCZOS)
                    img.save(cache_path, 'JPEG', quality=80)
                    return cache_path
        except Exception: 
            pass # Fallback silently to FFmpeg

        # Method B: Fallback to FFmpeg (Most Robust for MKV/AVI/ProRes)
        if FFPROBE_EXECUTABLE_PATH:
            try:
                ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
                ffmpeg_bin = os.path.join(os.path.dirname(FFPROBE_EXECUTABLE_PATH), ffmpeg_name)
                if not os.path.exists(ffmpeg_bin): ffmpeg_bin = ffmpeg_name
                
                cmd = [
                    ffmpeg_bin, '-y', 
                    '-i', filepath, 
                    '-ss', '00:00:00', # Seek to start
                    '-vframes', '1',   # Grab 1 frame
                    '-vf', f'scale={THUMBNAIL_WIDTH}:-1', # Resize directly
                    '-q:v', '2',       # High Quality
                    cache_path
                ]
                
                creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=creation_flags)
                
                if os.path.exists(cache_path):
                    return cache_path
            except Exception as e:
                print(f"ERROR (FFmpeg): Thumbnail failed for {os.path.basename(filepath)}: {e}")

    return None
    
def extract_workflow_files_string(workflow_json_string):
    """
    Parses workflow and returns a normalized string containing ONLY filenames 
    (models, images, videos) used in the workflow.
    
    Robust version: Handles both UI (widgets_values) and API (inputs) formats safely.
    Filters out prompts, settings, and comments based on extensions and path structure.
    """
    if not workflow_json_string: return ""
    
    try:
        data = json.loads(workflow_json_string)
    except:
        return ""

    # Normalize structure (UI vs API format)
    nodes = []
    if isinstance(data, dict):
        if 'nodes' in data and isinstance(data['nodes'], list):
            nodes = data['nodes'] # UI Format
        else:
            # API Format fallback (Dict of nodes)
            # We convert it to a list for uniform processing
            nodes = list(data.values())
    elif isinstance(data, list):
        nodes = data # Raw list format

    # 1. Blocklist Nodes (Comments and structural nodes)
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
        if not isinstance(node, dict): continue
        
        node_type = node.get('type', node.get('class_type', ''))
        
        # Skip comment nodes
        if node_type in ignored_types:
            continue
            
        # Collect values to check from BOTH formats to be safe
        values_to_check = []
        
        # UI Format values
        w_vals = node.get('widgets_values')
        if isinstance(w_vals, list):
            values_to_check.extend(w_vals)
            
        # API Format inputs
        inputs = node.get('inputs')
        if isinstance(inputs, dict):
            values_to_check.extend(inputs.values())
        elif isinstance(inputs, list):
            values_to_check.extend(inputs)

        for val in values_to_check:
            # CRITICAL: Only process Strings. API inputs contain Ints/Floats/Lists(links).
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

# --- Helper to filter out garbage text (Markdown, Stats, Instructions, UI values) ---
def _is_garbage_text(text):
    if not text: return True
    t = text.strip()
    # Ignore very short strings
    if len(t) < 3: return True
    
    # 1. Detect Markdown Tables / System Stats
    if '|' in t and ('---' in t or 'VRAM' in t or 'Model' in t): return True
    if 'GPU:' in t or 'RTX' in t or 'it/s' in t: return True
    
    # 2. Detect Instructions / Notes / Shortcuts / UI Trash
    t_lower = t.lower()

    # List of phrases that identify non-prompt text. 
    # Simply add or remove strings here to update the filter.
    GARBAGE_MARKERS = (
        "ctrl +", "box-select", "don't forget to use", "partial - execution",
        "creative prompt", "bad quality", "embedding:", "🟢", "select wildcard",
        "by percentage", "what is art?", "send none", "you are an ai artist",
        "jpeg压缩残留", "/", "select the wildcard"
    )

    # If any of the markers are found in the text, it is considered garbage
    if any(marker in t_lower for marker in GARBAGE_MARKERS):
        return True

    
    # 3. Detect URLs
    if "http://" in t_lower or "https://" in t_lower: return True
    
    # 4. Detect Numbered Lists (common in notes: "1. do this")
    if len(t) > 3 and t[0].isdigit() and t[1] == '.' and t[2] == ' ': return True

    # 5. Detect Technical/UI Parameters (Extended Blacklist)
    ui_keywords = {
        'enable', 'disable', 'fixed', 'randomize', 'auto', 'simple', 'always', 
        'center', 'left', 'top', 'bottom', 'right', 'nearest', 'bilinear', 
        'bicubic', 'lanczos', 'keep proportion', 'image', 'default', 'comfyui', 
        'wan', 'crop', 'input', 'output', 'float', 'int', 'boolean',
        # Samplers & Schedulers
        'euler', 'euler_a', 'heun', 'dpm_2', 'dpmpp_2m', 'dpmpp_sde', 'ddim', 
        'uni_pc', 'lms', 'karras', 'exponential', 'sgd', 'normal'
    }
    
    # Check exact match or if it looks like a parameter
    if t_lower in ui_keywords: return True
    
    # 6. Detect Unresolved variables
    if t.startswith('%') or '${' in t: return True
    
    return False


def extract_workflow_prompt_string(workflow_json_string):
    """
    Broad extraction for Database Indexing (Searchable Keywords).
    This function scans ALL nodes to ensure keyword searches work as expected,
    while filtering out known UI noise and technical instructions.
    """
    if not workflow_json_string: return ""
    
    try:
        data = json.loads(workflow_json_string)
    except:
        return ""

    # Normalize structure (UI vs API format)
    nodes = []
    if isinstance(data, dict):
        if 'nodes' in data and isinstance(data['nodes'], list):
            nodes = data['nodes'] # UI Format
        else:
            nodes = list(data.values()) # API Format
    elif isinstance(data, list):
        nodes = data 
    
    found_texts = set()
    
    # Nodes to strictly ignore for text extraction
    ignored_types = {
        'Note', 'NotePrimitive', 'Reroute', 'PrimitiveNode', 
        'ShowText', 'Display Text', 'Simple Text', 'Text Box', 'ComfyUI', 'ExtraMetadata',
        'SaveImage', 'PreviewImage', 'VHS_VideoCombine', 'VHS_LoadVideo'
    }
    
    for node in nodes:
        if not isinstance(node, dict): continue
        node_type = node.get('type', node.get('class_type', '')).strip()
        
        if node_type in ignored_types: continue

        # Collect all possible string values from widgets and inputs
        values_to_check = []
        if 'widgets_values' in node and isinstance(node['widgets_values'], list):
            values_to_check.extend(node['widgets_values'])
        if 'inputs' in node and isinstance(node['inputs'], dict):
            values_to_check.extend(node['inputs'].values())

        for val in values_to_check:
            if isinstance(val, str) and val.strip():
                text = val.strip()
                
                # --- BROAD FILTERING FOR SEARCH ACCURACY ---
                
                # A. Global Blacklist check
                if text in WORKFLOW_PROMPT_BLACKLIST: continue
                
                # B. Advanced Garbage filtering (Instructions, technical values, etc.)
                if _is_garbage_text(text): continue
                
                # C. Ignore filenames and short numeric strings
                if text.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.safetensors', '.ckpt', '.pt')):
                    continue
                
                # D. Minimum length for a searchable keyword
                if len(text) < 3: continue

                found_texts.add(text)

    # Join everything with a separator for the Database field
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
            # UPDATED: Request 'api' format for indexing to get real execution values (seeds, clean prompts)
            # If not found, extract_workflow will automatically fallback to 'ui'
            wf_json = extract_workflow(filepath, target_type='api')
            
            if wf_json:
                workflow_files_content = extract_workflow_files_string(wf_json)
                workflow_prompt_content = extract_workflow_prompt_string(wf_json) 
        
        return (
            file_id, filepath, mtime, os.path.basename(filepath),
            metadata['type'], metadata['duration'], metadata['dimensions'], 
            metadata['has_workflow'], file_size, time.time(), 
            workflow_files_content, 
            workflow_prompt_content 
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
        
        # MOUNT POINTS TABLE ---
        conn.execute('''
            CREATE TABLE IF NOT EXISTS mounted_folders (
                path TEXT PRIMARY KEY,
                target_source TEXT,
                created_at REAL
            );
        ''')
        
        # 3. COLUMN MIGRATION
        required_columns = {
            'size': 'INTEGER DEFAULT 0', 
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
            'is_explicitly_watched': False,
            'is_mount': False # Root is never a mount
        }
    }

    try:
        # 1. Fetch Watched Status
        watched_rules = [] 
        if ENABLE_AI_SEARCH:
            try:
                with get_db_connection() as conn:
                    rows = conn.execute("SELECT path, recursive FROM ai_watched_folders").fetchall()
                    for r in rows:
                        w_path = os.path.normpath(r['path']).replace('\\', '/')
                        watched_rules.append((w_path, bool(r['recursive'])))
            except: pass
            
        # 2. Fetch Mounted Folders (New)
        mounted_paths = set()
        try:
            with get_db_connection() as conn:
                rows = conn.execute("SELECT path FROM mounted_folders").fetchall()
                for r in rows:
                    # Normalize for comparison
                    mounted_paths.add(os.path.normpath(r['path']).replace('\\', '/'))
        except: pass

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

            current_path = folder_data['full_path']
            
            # Watch Logic
            is_watched_folder = False
            is_explicitly_watched = False
            for w_path, is_recursive in watched_rules:
                if current_path == w_path:
                    is_watched_folder = True
                    is_explicitly_watched = True
                    break
                if is_recursive and current_path.startswith(w_path + '/'):
                    is_watched_folder = True
                    break
           
            # Mount Logic
            is_mount = (current_path in mounted_paths)

            # NEW: Resolve the physical path (handles Symlinks/Junctions for subfolders too)
            real_path = os.path.realpath(current_path).replace('\\', '/')

            dynamic_config[key] = {
                'display_name': folder_data['display_name'],
                'path': current_path,
                'real_path': real_path, # <--- NEW FIELD
                'relative_path': rel_path,
                'parent': parent_key,
                'children': [],
                'mtime': folder_data['mtime'],
                'is_watched': is_watched_folder,
                'is_explicitly_watched': is_explicitly_watched,
                'is_mount': is_mount
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
    
    # Whitelist approach: Only index valid media files
    valid_extensions = {
        '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif',  # Images
        '.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v', '.wmv', '.flv', '.mts', '.ts', # Videos
        '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac' # Audio
    }

    for folder_data in all_folders.values():
        folder_path = folder_data['path']
        if not os.path.isdir(folder_path): continue
        try:
            for name in os.listdir(folder_path):
                filepath = os.path.join(folder_path, name)
                
                # Check extension against whitelist
                _, ext = os.path.splitext(name)
                if os.path.isfile(filepath) and ext.lower() in valid_extensions:
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
    # debug if files_to_process: print(f"{Colors.YELLOW}DEBUG - File to process: {files_to_process}{Colors.RESET}")
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

    # SAFETY GUARD FOR DISCONNECTED DRIVES
    if to_delete:
        print(f"INFO: Detecting disconnected drives before cleanup...")
        
        # 1. Identify Offline Mounts
        # We fetch all configured mount points to check if their root is accessible
        mount_rows = conn.execute("SELECT path FROM mounted_folders").fetchall()
        offline_prefixes = []
        
        for row in mount_rows:
            m_path = row['path']
            # If the mount root itself is missing, assume the drive is offline.
            # note: os.path.exists returns False for broken symlinks/junctions
            if not os.path.exists(m_path):
                print(f"{Colors.YELLOW}WARN: Mount point seems offline: {m_path}{Colors.RESET}")
                offline_prefixes.append(m_path)

        # 2. Filter files to delete
        # Only delete files if they do NOT belong to an offline mount
        safe_to_delete = []
        protected_count = 0
        
        for path_to_remove in to_delete:
            is_protected = False
            for offline_root in offline_prefixes:
                # Check if file path starts with the offline root path
                if path_to_remove.startswith(offline_root):
                    is_protected = True
                    break
            
            if is_protected:
                protected_count += 1
            else:
                safe_to_delete.append(path_to_remove)

        if protected_count > 0:
            print(f"{Colors.YELLOW}PROTECTION ACTIVE: Skipped deletion of {protected_count} files because their source drive appears offline.{Colors.RESET}")

        # 3. Proceed with safe deletion
        if safe_to_delete:
            print(f"INFO: Removing {len(safe_to_delete)} obsolete file entries from the database...")
            
            paths_to_remove = [(p,) for p in safe_to_delete]
            conn.executemany("DELETE FROM files WHERE path = ?", paths_to_remove)
            
            # Clean AI Queue for validly deleted files
            std_paths_to_remove = [(get_standardized_path(p),) for p in safe_to_delete]
            conn.executemany("DELETE FROM ai_indexing_queue WHERE file_path = ?", std_paths_to_remove)
            
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

def cleanup_invalid_watched_folders(conn):
    """
    Checks if watched folders still exist on disk.
    [SAFE MODE]: If a folder is missing, we assumes it might be a disconnected drive
    and we DO NOT remove it automatically to prevent config loss.
    """
    try:
        rows = conn.execute("SELECT path FROM ai_watched_folders").fetchall()
        
        for row in rows:
            path = row['path']
            if not os.path.exists(path) or not os.path.isdir(path):
                # We just WARN the user, we do NOT delete the config.
                print(f"{Colors.YELLOW}WARN: Watched folder not found (Offline or Deleted): {path}")
                print(f"      Skipping AI checks for this folder. Config preserved.{Colors.RESET}")
                
    except Exception as e:
        print(f"ERROR checking watched folders: {e}")
        
def initialize_gallery_fast_no_db_check():
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

def initialize_gallery():
    print("INFO: Initializing gallery...")
    global FFPROBE_EXECUTABLE_PATH
    FFPROBE_EXECUTABLE_PATH = find_ffprobe_path()
    os.makedirs(THUMBNAIL_CACHE_DIR, exist_ok=True)
    os.makedirs(SQLITE_CACHE_DIR, exist_ok=True)
    
    with get_db_connection() as conn:
        try:
            init_db(conn) 
            # Cleanup invalid watched folders before full sync
            if ENABLE_AI_SEARCH:
                cleanup_invalid_watched_folders(conn)
            # Force full sync on every startup to clean external deletions
            print(f"{Colors.BLUE}INFO: Performing startup consistency check...{Colors.RESET}")
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

@app.route('/galleryout/api/compare_files', methods=['POST'])
def compare_files_api():
    data = request.json
    id_a = data.get('id_a')
    id_b = data.get('id_b')
    
    if not id_a or not id_b:
        return jsonify({'status': 'error', 'message': 'Missing file IDs'}), 400

    def get_flat_params(file_id):
        try:
            info = get_file_info_from_db(file_id)
            wf_json = extract_workflow(info['path'])
            if not wf_json: return {}
            
            # Reuse existing summary logic
            summary = generate_node_summary(wf_json)
            if not summary: return {}
            
            flat_params = {}
            for node in summary:
                node_type = node['type']
                for p in node['params']:
                    # Create a readable key like "KSampler > steps"
                    key = f"{node_type} > {p['name']}"
                    flat_params[key] = str(p['value'])
            return flat_params
        except:
            return {}

    try:
        params_a = get_flat_params(id_a)
        params_b = get_flat_params(id_b)
        
        # Identify all unique keys
        all_keys = sorted(list(set(params_a.keys()) | set(params_b.keys())))
        
        diff_table = []
        for key in all_keys:
            val_a = params_a.get(key, 'N/A')
            val_b = params_b.get(key, 'N/A')
            
            # Check difference (case insensitive)
            is_diff = str(val_a).lower() != str(val_b).lower()
            
            diff_table.append({
                'key': key,
                'val_a': val_a,
                'val_b': val_b,
                'is_diff': is_diff
            })
            
        # Sort: Differences at the top, then alphabetical
        diff_table.sort(key=lambda x: (not x['is_diff'], x['key']))
        
        return jsonify({'status': 'success', 'diff': diff_table})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
        

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

# Global dictionary to track active background jobs
# Structure: { 'job_id': {'status': 'processing', 'current': 0, 'total': 100, 'folder_key': '...'} }
rescan_jobs = {}

def background_rescan_worker(job_id, files_to_process):
    """
    Background worker that updates a global job status so the UI can poll for progress.
    """
    if not files_to_process: 
        rescan_jobs[job_id]['status'] = 'done'
        return

    print(f"INFO: [Background] Job {job_id}: Rescanning {len(files_to_process)} files...")
    
    try:
        total = len(files_to_process)
        rescan_jobs[job_id]['total'] = total
        
        with get_db_connection() as conn:
            processed_count = 0
            results = []
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
                futures = {executor.submit(process_single_file, path): path for path in files_to_process}
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                        
                        processed_count += 1
                        # UPDATE PROGRESS
                        rescan_jobs[job_id]['current'] = processed_count
                        
                    except Exception as e:
                        print(f"ERROR: Worker failed for a file: {e}")

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
                        is_favorite = CASE WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0 ELSE files.is_favorite END,
                        ai_caption = CASE WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL ELSE files.ai_caption END,
                        ai_embedding = CASE WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN NULL ELSE files.ai_embedding END,
                        ai_last_scanned = CASE WHEN ABS(files.mtime - excluded.mtime) > 0.1 THEN 0 ELSE files.ai_last_scanned END,
                        mtime = excluded.mtime
                """, results) 
                conn.commit()
                
        print(f"INFO: [Background] Job {job_id} finished.")
        rescan_jobs[job_id]['status'] = 'done'
        
    except Exception as e:
        print(f"CRITICAL ERROR in Background Rescan: {e}")
        rescan_jobs[job_id]['status'] = 'error'
        rescan_jobs[job_id]['error'] = str(e)
        
@app.route('/galleryout/rescan_folder', methods=['POST'])
def rescan_folder():
    data = request.json
    folder_key = data.get('folder_key')
    mode = data.get('mode', 'all')
    
    if not folder_key: return jsonify({'status': 'error', 'message': 'No folder provided.'}), 400
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Folder not found.'}), 404
    
    folder_path = folders[folder_key]['path']
    folder_name = folders[folder_key]['display_name']
    
    try:
        files_to_process = []
        with get_db_connection() as conn:
            query = "SELECT path, last_scanned FROM files WHERE path LIKE ?"
            rows = conn.execute(query, (folder_path + os.sep + '%',)).fetchall()
            
            folder_path_norm = os.path.normpath(folder_path)
            files_in_folder = [
                {'path': row['path'], 'last_scanned': row['last_scanned']} 
                for row in rows 
                if os.path.normpath(os.path.dirname(row['path'])) == folder_path_norm
            ]
            
            current_time = time.time()
            if mode == 'recent':
                cutoff_time = current_time - 3600
                files_to_process = [f['path'] for f in files_in_folder if (f['last_scanned'] or 0) < cutoff_time]
            else:
                files_to_process = [f['path'] for f in files_in_folder]
            
        if not files_to_process:
            return jsonify({'status': 'success', 'message': 'No files needed rescanning.', 'count': 0})
        
        # --- JOB CREATION ---
        job_id = str(uuid.uuid4())
        rescan_jobs[job_id] = {
            'status': 'processing', 
            'current': 0, 
            'total': len(files_to_process),
            'folder_key': folder_key,
            'folder_name': folder_name
        }
        
        # Start Worker with Job ID
        threading.Thread(target=background_rescan_worker, args=(job_id, files_to_process), daemon=True).start()
                
        return jsonify({
            'status': 'started', 
            'job_id': job_id,
            'total': len(files_to_process),
            'message': 'Background process started.'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/galleryout/check_rescan_status/<job_id>')
def check_rescan_status(job_id):
    job = rescan_jobs.get(job_id)
    if not job:
        return jsonify({'status': 'not_found'})
    
    # Return copy of job data
    return jsonify(job)
    
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

@app.route('/galleryout/mount_folder', methods=['POST'])
def mount_folder():
    data = request.json
    link_name_raw = data.get('link_name', '').strip()
    target_path_raw = data.get('target_path', '').strip()
    
    # Sanitize name
    link_name = re.sub(r'[\\/:*?"<>|]', '', link_name_raw)
    
    if not link_name or not target_path_raw:
        return jsonify({'status': 'error', 'message': 'Missing name or target path.'}), 400
        
    # Security: Normalize target path
    target_path = os.path.normpath(target_path_raw)
    
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        return jsonify({'status': 'error', 'message': f'Target path does not exist: {target_path}'}), 404
        
    # Construct link path inside BASE_OUTPUT_PATH
    link_full_path = os.path.join(BASE_OUTPUT_PATH, link_name)
    
    if os.path.exists(link_full_path):
        return jsonify({'status': 'error', 'message': 'A folder with this name already exists.'}), 409
        
    try:
        if os.name == 'nt':
            # --- WINDOWS ROBUST LOGIC ---
            
            # 1. Force Windows-style backslashes for cmd.exe compatibility
            # (Fixes issues with mixed slashes like Z:/path\folder)
            win_link = link_full_path.replace('/', '\\')
            win_target = target_path.replace('/', '\\')
            
            # Attempt 1: Junction (/J)
            # Ideal for local drives, does not require Admin usually.
            cmd_junction = f'mklink /J "{win_link}" "{win_target}"'
            
            # Use subprocess.run to capture the specific error message from Windows
            result = subprocess.run(cmd_junction, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                # Capture the actual error (e.g. "Local volumes are required...")
                err_junction = result.stderr.strip() or result.stdout.strip() or "Unknown Error"
                
                print(f"WARN: Junction failed ({err_junction}). Trying Symlink fallback...")
                
                # Attempt 2: Symbolic Link (/D)
                # Necessary for Network Shares, Virtual Drives, or Cross-Volume links.
                # NOTE: This usually requires Developer Mode enabled OR running ComfyUI as Administrator.
                cmd_symlink = f'mklink /D "{win_link}" "{win_target}"'
                result_sym = subprocess.run(cmd_symlink, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result_sym.returncode != 0:
                    err_sym = result_sym.stderr.strip() or result_sym.stdout.strip()
                    
                    # Create a detailed error message for the user
                    error_msg = (
                        f"Failed to create link.\n\n"
                        f"Attempt 1 (Junction): {err_junction}\n"
                        f"Attempt 2 (Symlink): {err_sym}\n\n"
                        f"TIP: If using Virtual Drives or Network Shares, try running ComfyUI as Administrator."
                    )
                    raise Exception(error_msg)
                    
        else:
            # LINUX/MAC: Standard symlink
            os.symlink(target_path, link_full_path)
            
        # Register in DB
        with get_db_connection() as conn:
            norm_link_path = os.path.normpath(link_full_path).replace('\\', '/')
            conn.execute("INSERT OR REPLACE INTO mounted_folders (path, target_source, created_at) VALUES (?, ?, ?)", 
                         (norm_link_path, target_path, time.time()))
            conn.commit()
            
        # Refresh Cache
        get_dynamic_folder_config(force_refresh=True)
        
        return jsonify({'status': 'success', 'message': f'Successfully linked "{link_name}".'})
        
    except Exception as e:
        print(f"Mount Error: {e}")
        # Clean up if partially created
        if os.path.exists(link_full_path):
            try: os.rmdir(link_full_path) 
            except: pass
            try: os.unlink(link_full_path)
            except: pass
            
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/galleryout/unmount_folder', methods=['POST'])
def unmount_folder():
    data = request.json
    folder_key = data.get('folder_key')
    
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status':'error', 'message':'Folder not found'}), 404
    
    folder_info = folders[folder_key]
    path_to_remove = folder_info['path']
    
    # Security Check: Ensure it is actually in the mounted_folders table
    # This prevents users from deleting real folders via this API
    is_safe_mount = False
    with get_db_connection() as conn:
        norm_path = os.path.normpath(path_to_remove).replace('\\', '/')
        row = conn.execute("SELECT path FROM mounted_folders WHERE path = ?", (norm_path,)).fetchone()
        if row: is_safe_mount = True
        
    if not is_safe_mount:
        return jsonify({'status':'error', 'message':'This folder is not a managed mount point. Cannot unmount.'}), 403
        
    try:
        # Remove the Link (Not the content)
        if os.name == 'nt':
            # On Windows, rmdir removes the Junction point safely without deleting content
            os.rmdir(path_to_remove)
        else:
            # On Linux/Mac, unlink removes the symlink
            os.unlink(path_to_remove)
            
        # Cleanup DB
        with get_db_connection() as conn:
            # 1. Remove from Mounts registry
            conn.execute("DELETE FROM mounted_folders WHERE path = ?", (norm_path,))
            
            # 2. Remove from AI Watch list (if present)
            conn.execute("DELETE FROM ai_watched_folders WHERE path = ?", (path_to_remove,))
            
            # 3. CRITICAL: Remove the file records associated with this path from the Gallery DB
            # We use LIKE to match the folder and everything inside it
            # Standardize path separator for SQL query just in case
            clean_path_for_query = path_to_remove + os.sep + '%'
            conn.execute("DELETE FROM files WHERE path LIKE ?", (clean_path_for_query,))
            
            # 4. Also clean pending AI jobs for these files
            # (We need to handle path separators carefully here, usually normalized in AI queue)
            std_path_prefix = path_to_remove.replace('\\', '/')
            conn.execute("DELETE FROM ai_indexing_queue WHERE file_path LIKE ?", (std_path_prefix + '/%',))
            
            conn.commit()
            
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder unmounted successfully.'})
        
    except Exception as e:
        print(f"Unmount Error: {e}")
        return jsonify({'status':'error', 'message':f"Error unmounting: {e}"}), 500

@app.route('/galleryout/api/browse_filesystem', methods=['POST'])
def browse_filesystem():
    data = request.json
    # Get path safely, handling None
    raw_path = data.get('path', '')
    if raw_path is None: raw_path = ''
    current_path = str(raw_path).strip()
    
    response_data = {
        'current_path': '',
        'parent_path': '',
        'folders': [],
        'error': None
    }

    # --- BLOCK 1: LIST DRIVES (WINDOWS) OR ROOT ---
    # If path is empty or 'Computer', list drives only and EXIT immediately.
    if not current_path or current_path == 'Computer':
        response_data['current_path'] = 'Computer'
        
        if os.name == 'nt':
            drives = []
            import string
            # Iterate from A to Z
            for letter in string.ascii_uppercase:
                drive_path = f'{letter}:\\'
                try:
                    # Use isdir which is specific for drives
                    # Fault-tolerant check inside its own try/except block
                    if os.path.isdir(drive_path):
                        drives.append({
                            'name': f'Drive ({letter}:)', 
                            'path': drive_path, 
                            'is_drive': True
                        })
                except Exception:
                    # If a specific drive hangs, is not ready, or errors, 
                    # skip it and continue to the next letter.
                    continue
            
            response_data['folders'] = drives
            # Return JSON immediately. Do not execute further code.
            return jsonify(response_data)
            
        else:
            # On Linux/Mac, root is simply '/'
            current_path = '/'

    # --- BLOCK 2: SCAN FOLDER CONTENT ---
    # We reach here only if browsing inside a specific drive or folder
    try:
        current_path = os.path.normpath(current_path)
        items = []
        
        # Scandir is faster and allows skipping unreadable files individually
        with os.scandir(current_path) as it:
            for entry in it:
                try:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        items.append({
                            'name': entry.name,
                            'path': entry.path,
                            'is_drive': False
                        })
                except Exception:
                    # Skip individual unreadable folders without breaking the list
                    continue
        
        items.sort(key=lambda x: x['name'].lower())
        response_data['folders'] = items
        response_data['current_path'] = current_path
        
        # Calculate "Up" button (Parent)
        parent = os.path.dirname(current_path)
        if parent == current_path: 
            # If at drive root (e.g. C:\), parent is Computer list
            if os.name == 'nt':
                parent = '' 
            else:
                parent = '' 
            
        response_data['parent_path'] = parent

    except Exception as e:
        # Catch errors accessing the specific folder (not the drives)
        response_data['error'] = f"Error accessing folder: {str(e)}"

    return jsonify(response_data)
    
   
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

@app.route('/galleryout/copy_batch', methods=['POST'])
def copy_batch():
    data = request.json
    file_ids = data.get('file_ids', [])
    dest_key = data.get('destination_folder')
    keep_favorites = data.get('keep_favorites', False)
    
    folders = get_dynamic_folder_config()
    
    if not all([file_ids, dest_key, dest_key in folders]):
        return jsonify({'status': 'error', 'message': 'Invalid data provided.'}), 400
    
    dest_path_raw = folders[dest_key]['path']
    copied_count = 0
    failed_files = []
    
    with get_db_connection() as conn:
        for file_id in file_ids:
            try:
                # 1. Fetch Source info
                file_info = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
                if not file_info: continue
                
                source_path = file_info['path']
                source_filename = file_info['name']
                
                if not os.path.exists(source_path):
                    failed_files.append(f"{source_filename} (not found)")
                    continue
                
                # 2. Determine Destination Path (Auto-rename logic)
                # Helper function _get_unique_filepath handles (1), (2) etc.
                final_dest_path = _get_unique_filepath(dest_path_raw, source_filename)
                final_filename = os.path.basename(final_dest_path)
                
                # 3. Physical Copy (Metadata preserved via copy2)
                shutil.copy2(source_path, final_dest_path)
                
                # 4. Create DB Record
                new_id = hashlib.md5(final_dest_path.encode()).hexdigest()
                new_mtime = time.time() # New file gets new import time
                
                # Logic for Favorites
                is_fav = file_info['is_favorite'] if keep_favorites else 0
                
                # Insert Copy
                # We copy AI data too because the image content is identical!
                conn.execute("""
                    INSERT INTO files (
                        id, path, mtime, name, type, duration, dimensions, has_workflow, 
                        size, is_favorite, last_scanned, workflow_files, workflow_prompt,
                        ai_last_scanned, ai_caption, ai_embedding, ai_error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_id, final_dest_path, new_mtime, final_filename, 
                    file_info['type'], file_info['duration'], file_info['dimensions'], 
                    file_info['has_workflow'], file_info['size'], 
                    is_fav, # User Choice
                    file_info['last_scanned'], 
                    file_info['workflow_files'], file_info['workflow_prompt'],
                    file_info['ai_last_scanned'], file_info['ai_caption'], file_info['ai_embedding'], file_info['ai_error']
                ))
                
                copied_count += 1
                
            except Exception as e:
                print(f"COPY ERROR: {e}")
                failed_files.append(source_filename)
                
        conn.commit()
        
    msg = f"Successfully copied {copied_count} files."
    status = 'success'
    if failed_files:
        status = 'partial_success'
        msg += f" Failed: {len(failed_files)}"
        
    return jsonify({'status': status, 'message': msg}) 
 
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
    
    # EXPLICITLY request 'ui' format to ensure Groups, Notes and Positions are preserved.
    # If we used 'api', the download would lack visual layout data.
    workflow_json = extract_workflow(filepath, target_type='ui')
    
    if workflow_json:
        base_name, _ = os.path.splitext(original_filename)
        new_filename = f"{base_name}.json"
        headers = {'Content-Disposition': f'attachment;filename="{new_filename}"'}
        return Response(workflow_json, mimetype='application/json', headers=headers)
    abort(404)

@app.route('/galleryout/node_summary/<string:file_id>')
def get_node_summary(file_id):
    try:
        # 1. Fetch basic info from DB
        file_info = get_file_info_from_db(file_id)
        filepath = file_info['path']
        db_dimensions = file_info.get('dimensions')
        
        # 2. Extract UI version for the Raw Node List (Always reliable)
        ui_json = extract_workflow(filepath, target_type='ui')
        if not ui_json:
            return jsonify({'status': 'error', 'message': 'Workflow not found for this file.'}), 404
            
        summary_data = generate_node_summary(ui_json)
        
        # 3. Extract API version for high-quality Metadata Dashboard
        api_json = extract_workflow(filepath, target_type='api')
        meta_data = {}
        
        try:
            # We prefer API format for real values (Seed, CFG, etc.)
            json_source = api_json if api_json else ui_json
            wf_data = json.loads(json_source)
            if isinstance(wf_data, list):
                wf_data = {str(i): n for i, n in enumerate(wf_data)}
            
            parser = ComfyMetadataParser(wf_data)
            parsed_meta = parser.parse()
            
            # --- STRICT VALIDATION LOGIC ---
            # We only show the Dashboard if we have a "Solid Set" of data.
            # Criteria: Must have a Positive Prompt AND at least 2 technical parameters (Seed, Model, Steps, etc.)
            # This prevents showing a "messy" or near-empty dashboard for complex/unsupported workflows.
            
            tech_count = 0
            if parsed_meta.get('seed'): tech_count += 1
            if parsed_meta.get('model'): tech_count += 1
            if parsed_meta.get('steps'): tech_count += 1
            if parsed_meta.get('sampler'): tech_count += 1
            
            has_prompt = len(parsed_meta.get('positive_prompt', '')) > 5
            
            # If data is solid, we populate meta_data for the frontend dashboard
            if has_prompt and tech_count >= 2:
                meta_data = parsed_meta
                # Ensure resolution is always present using DB fallback
                if not meta_data.get('width') or not meta_data.get('height'):
                    if db_dimensions and 'x' in db_dimensions:
                        w, h = db_dimensions.split('x')
                        meta_data['width'], meta_data['height'] = w.strip(), h.strip()
            else:
                # Data is too sparse or unreliable. 
                # We return empty meta to hide the dashboard and show only the Raw Node List.
                meta_data = {}
                
        except Exception as e:
            print(f"Metadata Validation Warning: {e}")
            meta_data = {}

        return jsonify({
            'status': 'success', 
            'summary': summary_data, # Raw Node List (Always shown)
            'meta': meta_data        # Dashboard Data (Only if valid/complete)
        })
        
    except Exception as e:
        print(f"ERROR generating node summary: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

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

# --- STORYBOARD (GRID SYSTEM) - FAST + SMART CORRUPTION DETECTION ---
@app.route('/galleryout/storyboard/<string:file_id>')
def get_storyboard(file_id):
    # 1. Validation
    has_ffmpeg = FFPROBE_EXECUTABLE_PATH is not None
    
    try:
        info = get_file_info_from_db(file_id)
        if info['type'] not in ['video', 'animated_image']:
            return jsonify({'status': 'error', 'message': 'Not a video or animated file'}), 400

        if info['type'] == 'video' and not has_ffmpeg:
             return jsonify({'status': 'error', 'message': 'FFmpeg not available'}), 501

        filepath = info['path']
        mtime = info['mtime']
        
        # 2. Cache Strategy
        file_hash = hashlib.md5((filepath + str(mtime)).encode()).hexdigest()
        cache_subdir = os.path.join(THUMBNAIL_CACHE_DIR, file_hash)
        
        # Return cached results immediately if available
        if os.path.exists(cache_subdir):
            cached_files = sorted(glob.glob(os.path.join(cache_subdir, "frame_*.jpg")))
            if len(cached_files) > 0:
                urls = [f"/galleryout/storyboard_frame/{file_hash}/{os.path.basename(f)}" for f in cached_files]
                return jsonify({'status': 'success', 'cached': True, 'frames': urls})

        os.makedirs(cache_subdir, exist_ok=True)

        # 3. Get Duration + FPS + Frame Count
        duration = 0
        fps = 0
        total_video_frames = 0
        
        if info['type'] == 'video' and has_ffmpeg:
            # Get duration, fps, and frame count in ONE call
            try:
                cmd_info = [
                    FFPROBE_EXECUTABLE_PATH, 
                    '-v', 'error', 
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=duration,r_frame_rate,nb_frames', 
                    '-of', 'csv=p=0', 
                    filepath
                ]
                res = subprocess.run(
                    cmd_info, 
                    capture_output=True, 
                    text=True, 
                    timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                if res.stdout.strip():
                    parts = res.stdout.strip().split(',')
                    
                    if len(parts) > 0 and parts[0]:
                        fps_str = parts[0]
                        if '/' in fps_str:
                            num, den = fps_str.split('/')
                            fps = float(num) / float(den)
                        else:
                            fps = float(fps_str)
                    
                    if len(parts) > 1 and parts[1]:
                        duration = float(parts[1])
                    
                    if len(parts) > 2 and parts[2]:
                        total_video_frames = int(parts[2])
                        
            except Exception as e:
                print(f"Info probe error: {e}")
            
            # Fallback: Try DB duration
            if duration <= 0 and info.get('duration'):
                try:
                    parts = info['duration'].split(':')
                    parts.reverse()
                    duration += float(parts[0])
                    if len(parts) > 1: duration += int(parts[1]) * 60
                    if len(parts) > 2: duration += int(parts[2]) * 3600
                except: 
                    pass
            
            # Fallback: Try format duration
            if duration <= 0:
                try:
                    cmd_dur2 = [
                        FFPROBE_EXECUTABLE_PATH, 
                        '-v', 'error', 
                        '-show_entries', 'format=duration', 
                        '-of', 'default=noprint_wrappers=1:nokey=1', 
                        filepath
                    ]
                    res2 = subprocess.run(
                        cmd_dur2, 
                        capture_output=True, 
                        text=True, 
                        timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    if res2.stdout.strip(): 
                        duration = float(res2.stdout.strip())
                except: 
                    pass
            
            # Calculate missing values
            if total_video_frames == 0 and duration > 0 and fps > 0:
                total_video_frames = int(duration * fps)
            elif fps == 0 and duration > 0 and total_video_frames > 0:
                fps = total_video_frames / duration
        
        # Final fallback
        if duration <= 0 and info['type'] == 'video': 
            duration = 60
        if fps <= 0 and info['type'] == 'video':
            fps = 25

        # 4. SMART CORRUPTION TEST - Test at 50% instead of end (faster + reliable)
        needs_transcode = False
        
        if info['type'] == 'video' and has_ffmpeg and duration > 15:
            print(f"🔍 Quick test...")
            
            ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
            ffmpeg_bin = os.path.join(os.path.dirname(FFPROBE_EXECUTABLE_PATH), ffmpeg_name)
            if not os.path.exists(ffmpeg_bin): 
                ffmpeg_bin = ffmpeg_name
            
            test_path = os.path.join(cache_subdir, "test.jpg")
            # Test at 50% - faster seek and still detects corruption
            test_timestamp = duration * 0.5
            
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            # Adaptive timeout based on duration
            test_timeout = min(20, max(8, int(duration / 100)))  # 8-20s range
            
            cmd_test = [
                ffmpeg_bin, '-y',
                '-ss', f"{test_timestamp:.3f}",
                '-i', filepath,
                '-frames:v', '1',
                '-vf', 'scale=-2:240:flags=fast_bilinear',
                '-q:v', '5',
                test_path
            ]
            
            try:
                subprocess.run(
                    cmd_test,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=test_timeout,
                    creationflags=creation_flags
                )
                
                if os.path.exists(test_path) and os.path.getsize(test_path) > 100:
                    print(f"✅ Healthy")
                    needs_transcode = False
                else:
                    print(f"⚠️ Corrupted!")
                    needs_transcode = True
                    
            except subprocess.TimeoutExpired:
                # Timeout on healthy files = just slow, not corrupted
                print(f"⏱️ Slow seek (normal for large files)")
                needs_transcode = False
            except Exception as e:
                print(f"⚠️ Corrupted: {e}")
                needs_transcode = True
                
            if os.path.exists(test_path):
                try: os.remove(test_path)
                except: pass

        # 5. TRANSCODING if needed
        source_for_extraction = filepath
        temp_transcoded = None
        
        if needs_transcode:
            print(f"🔧 Transcoding...")
            
            try:
                ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
                ffmpeg_bin = os.path.join(os.path.dirname(FFPROBE_EXECUTABLE_PATH), ffmpeg_name)
                if not os.path.exists(ffmpeg_bin): 
                    ffmpeg_bin = ffmpeg_name
                
                temp_transcoded = os.path.join(cache_subdir, f"temp_proxy_{uuid.uuid4().hex}.mp4")
                
                cmd_transcode = [
                    ffmpeg_bin, '-y',
                    '-i', filepath,
                    '-vf', 'scale=-2:480',
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '28',
                    '-an',
                    '-movflags', '+faststart',
                    temp_transcoded
                ]
                
                creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                
                subprocess.run(
                    cmd_transcode,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    creationflags=creation_flags
                )
                
                if os.path.exists(temp_transcoded) and os.path.getsize(temp_transcoded) > 1000:
                    print(f"✅ Transcoded")
                    source_for_extraction = temp_transcoded
                    
                    # Get corrected info
                    try:
                        cmd_info = [
                            FFPROBE_EXECUTABLE_PATH, 
                            '-v', 'error', 
                            '-select_streams', 'v:0',
                            '-show_entries', 'stream=duration,r_frame_rate,nb_frames', 
                            '-of', 'csv=p=0', 
                            temp_transcoded
                        ]
                        res = subprocess.run(
                            cmd_info, 
                            capture_output=True, 
                            text=True, 
                            timeout=2,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                        )
                        if res.stdout.strip():
                            parts = res.stdout.strip().split(',')
                            
                            if len(parts) > 0 and parts[0]:
                                fps_str = parts[0]
                                if '/' in fps_str:
                                    num, den = fps_str.split('/')
                                    fps = float(num) / float(den)
                                else:
                                    fps = float(fps_str)
                            
                            if len(parts) > 1 and parts[1]:
                                duration = float(parts[1])
                            
                            if len(parts) > 2 and parts[2]:
                                total_video_frames = int(parts[2])
                    except:
                        pass
                        
            except Exception as e:
                print(f"❌ Transcode failed: {e}")
                if temp_transcoded and os.path.exists(temp_transcoded):
                    try: os.remove(temp_transcoded)
                    except: pass
                temp_transcoded = None

        # 6. Worker Function (OPTIMIZED)
        def extract_and_save_frame(index, timestamp):
            out_filename = f"frame_{index:02d}.jpg"
            out_path = os.path.join(cache_subdir, out_filename)
            
            try:
                img = None
                actual_timestamp = timestamp
                actual_frame_number = None
                
                # A. Video Extraction
                if info['type'] == 'video' and has_ffmpeg:
                    actual_timestamp = timestamp
                    
                    if fps > 0:
                        actual_frame_number = int(timestamp * fps)
                    
                    ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
                    ffmpeg_bin = os.path.join(os.path.dirname(FFPROBE_EXECUTABLE_PATH), ffmpeg_name)
                    if not os.path.exists(ffmpeg_bin): 
                        ffmpeg_bin = ffmpeg_name 
                    
                    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    
                    # Fast extraction
                    cmd = [
                        ffmpeg_bin, '-y',
                        '-ss', f"{timestamp:.3f}",
                        '-i', source_for_extraction,
                        '-frames:v', '1',
                        '-vf', 'scale=-2:360:flags=fast_bilinear',
                        '-q:v', '4',
                        '-preset', 'ultrafast',
                        out_path
                    ]
                    
                    try:
                        subprocess.run(
                            cmd, 
                            check=True, 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL, 
                            timeout=8,
                            creationflags=creation_flags
                        )
                        
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                            img = Image.open(out_path)
                            
                    except Exception:
                        if os.path.exists(out_path):
                            try: os.remove(out_path)
                            except: pass
                        
                        # Slow seek fallback
                        cmd_slow = [
                            ffmpeg_bin, '-y',
                            '-i', source_for_extraction,
                            '-ss', f"{timestamp:.3f}",
                            '-frames:v', '1',
                            '-vf', 'scale=-2:360:flags=fast_bilinear',
                            '-q:v', '4',
                            out_path
                        ]
                        
                        try:
                            subprocess.run(
                                cmd_slow, 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL, 
                                timeout=40,
                                creationflags=creation_flags
                            )
                            
                            if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                                img = Image.open(out_path)
                        except:
                            pass

                # B. Animation Extraction
                elif info['type'] == 'animated_image':
                    with Image.open(filepath) as source_img:
                        is_anim = getattr(source_img, 'is_animated', False)
                        total_frames = source_img.n_frames if is_anim else 1
                        pct = index / 10.0
                        target_frame_idx = int(pct * (total_frames - 1))
                        source_img.seek(target_frame_idx)
                        img = source_img.copy().convert('RGB')
                        img.thumbnail((640, 360))
                        
                        actual_timestamp = None
                        actual_frame_number = target_frame_idx + 1

                # C. Professional Overlay
                if img:
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(img)
                    
                    # Calculate text
                    if actual_timestamp is None:
                        # Animation
                        with Image.open(filepath) as temp_img:
                            total_frames = temp_img.n_frames if getattr(temp_img, 'is_animated', False) else 1
                        time_str = f"#{actual_frame_number}/{total_frames}"
                    else:
                        # Video: timestamp + frame
                        display_ts = round(actual_timestamp)
                        m, s = int(display_ts // 60), int(display_ts % 60)
                        
                        if actual_frame_number is not None and total_video_frames > 0:
                            display_frame_number = actual_frame_number + 1
                            time_str = f"{m:02d}:{s:02d} | #{display_frame_number}/{total_video_frames}"
                        else:
                            time_str = f"{m:02d}:{s:02d}"
                    
                    # Font
                    font_size = 24
                    font = None
                    try: 
                        font = ImageFont.load_default(size=font_size)
                    except: 
                        font = ImageFont.load_default()

                    # Measure
                    left, top, right, bottom = draw.textbbox((0, 0), time_str, font=font)
                    txt_w = right - left
                    txt_h = bottom - top

                    # Box
                    pad_x = 6
                    pad_y = 4
                    box_w = txt_w + (pad_x * 2)
                    box_h = txt_h + (pad_y * 2)
                    
                    # Draw
                    draw.rectangle([0, 0, box_w, box_h], fill="black", outline=None)
                    draw.text((pad_x - left, pad_y - top), time_str, font=font, fill="#ffffff")
                    
                    # Save
                    img.save(out_path, quality=85)
                    img.close()
                    
                    return f"/galleryout/storyboard_frame/{file_hash}/{out_filename}"
                    
            except Exception as e:
                print(f"Worker error {index}: {e}")
                
            return None

        # 7. Parallel Execution
        timestamps = []
        
        if info['type'] == 'video':
            safe_end = max(0, duration - 0.1)
            # Generate 11 evenly spaced timestamps, but force the last one (index 10) to be the exact last frame
            base_timestamps = [(i, (safe_end / 10) * i) for i in range(11)]
            # Override the last timestamp to point to the very end (or last frame if frame count is known)
            if total_video_frames > 0 and fps > 0:
                # Use exact last frame position
                last_frame_timestamp = (total_video_frames - 1) / fps
                # Ensure it doesn't exceed duration
                last_frame_timestamp = min(last_frame_timestamp, duration - 0.001)
                base_timestamps[-1] = (10, last_frame_timestamp)
            else:
                # Fallback: use end of video minus a tiny epsilon
                base_timestamps[-1] = (10, duration - 0.001)
            timestamps = base_timestamps
        else:
            timestamps = [(i, 0) for i in range(11)]
        
        frame_urls = [None] * 11
        
        print(f"🎬 Extracting...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=11) as executor:
            futures = {executor.submit(extract_and_save_frame, i, ts): i for i, ts in timestamps}
            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                res = future.result()
                if res: 
                    frame_urls[idx] = res

        success_count = sum(1 for url in frame_urls if url is not None)
        print(f"✅ {success_count}/11")

        # Cleanup
        if temp_transcoded and os.path.exists(temp_transcoded):
            try:
                os.remove(temp_transcoded)
            except:
                pass

        final_urls = [url for url in frame_urls if url is not None]
        
        if not final_urls:
             return jsonify({'status': 'error', 'message': 'Extraction failed completely.'}), 500

        return jsonify({'status': 'success', 'cached': False, 'frames': final_urls})

    except Exception as e:
        print(f"Storyboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/galleryout/storyboard_frame/<string:file_hash>/<string:filename>')
def serve_storyboard_frame(file_hash, filename):
    safe_name = secure_filename(filename)
    directory = os.path.join(THUMBNAIL_CACHE_DIR, file_hash)
    return send_from_directory(directory, safe_name)
# Route to serve the cached frames

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
    Now includes Real Path resolution for mounted folders.
    """
    try:
        with get_db_connection() as conn:
            # Added 'path' to selection to resolve symlinks
            row = conn.execute("SELECT path, has_workflow, ai_caption, ai_last_scanned FROM files WHERE id = ?", (file_id,)).fetchone()
            
        if not row:
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
            
        # Resolve Real Path (Handles Windows Junctions and Linux Symlinks)
        internal_path = row['path']
        real_path_resolved = os.path.realpath(internal_path)
        
        # Check if they differ (ignore case on Windows for safety)
        is_different = False
        if os.name == 'nt':
            if internal_path.lower() != real_path_resolved.lower():
                is_different = True
        else:
            if internal_path != real_path_resolved:
                is_different = True
                
        return jsonify({
            'status': 'success',
            'has_workflow': bool(row['has_workflow']),
            'has_ai_caption': bool(row['ai_caption']),
            'ai_caption': row['ai_caption'] or "",
            'ai_last_scanned': row['ai_last_scanned'] or 0,
            # Send real_path only if it's actually different (a link)
            'real_path': real_path_resolved if is_different else None
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
