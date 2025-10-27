# Smart Gallery for ComfyUI
# Author: Biagio Maffettone © 2025 — MIT License (free to use and modify)
#
# Version: 1.31 - October 27, 2025
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
import glob
import sys
import subprocess
import base64
from flask import Flask, render_template, send_from_directory, abort, send_file, url_for, redirect, request, jsonify, Response
from PIL import Image, ImageSequence
import colorsys
from werkzeug.utils import secure_filename
import concurrent.futures
from tqdm import tqdm


# --- USER CONFIGURATION ---
# Adjust the parameters in this section to customize the gallery.
#
# IMPORTANT:
# - Even on Windows, always use forward slashes ( / ) in paths, 
#   not backslashes ( \ ), to ensure compatibility.

# - It is strongly recommended to have ffmpeg installed, since some features depend on it.

# Path to the ComfyUI 'output' folder.
BASE_OUTPUT_PATH = os.environ.get('BASE_OUTPUT_PATH', 'C:/sm/Data/Packages/ComfyUI/output')

# Path to the ComfyUI 'input' folder (used for locating .json workflows).
BASE_INPUT_PATH = os.environ.get('BASE_INPUT_PATH', 'C:/sm/Data/Packages/ComfyUI/input')

BASE_SMARTGALLERY_PATH = os.environ.get('BASE_SMARTGALLERY_PATH', 'C:/Temp/SmartGallery')

# Path to the ffmpeg utility "ffprobe.exe" (Windows). 
# On Linux, adjust the filename accordingly. 
# This is required for extracting workflows from .mp4 files.  
# NOTE: Having a full ffmpeg installation is highly recommended.
FFPROBE_MANUAL_PATH = os.environ.get('FFPROBE_MANUAL_PATH', "C:/omgp10/ffmpeg2/bin/ffprobe.exe")
# - Even on Windows, always use forward slashes ( / ) in paths, 
#   not backslashes ( \ ), to ensure compatibility.

# Port on which the gallery web server will run. 
# Must be different from the ComfyUI port.  
# Note: the gallery does not require ComfyUI to be running; it works independently.
SERVER_PORT = os.environ.get('SERVER_PORT', 8189)

# Width (in pixels) of the generated thumbnails.
THUMBNAIL_WIDTH = os.environ.get('THUMBNAIL_WIDTH', 300)

# Assumed frame rate for animated WebP files.  
# Many tools, including ComfyUI, generate WebP animations at ~16 FPS.  
# Adjust this value if your WebPs use a different frame rate,  
# so that animation durations are calculated correctly.
WEBP_ANIMATED_FPS = os.environ.get('WEBP_ANIMATED_FPS', 16.0)

# Maximum number of files to load initially before showing a "Load more" button.  
# Use a very large number (e.g., 9999999) for "infinite" loading.
PAGE_SIZE = os.environ.get('PAGE_SIZE', 100)

# Names of special folders (e.g., 'video', 'audio').  
# These folders will appear in the menu only if they exist inside BASE_OUTPUT_PATH.  
# Leave as-is if unsure.
SPECIAL_FOLDERS = ['video', 'audio']

# Number of files to process at once during database sync. 
# Higher values use more memory but may be faster. Lower this if you run out of memory.
BATCH_SIZE = os.environ.get('BATCH_SIZE', 500)

# Number of parallel processes to use for thumbnail and metadata generation.
# - Set to None to use all available CPU cores (fastest, but uses more CPU).
# - Set to 1 to disable parallel processing (slowest, like in the previous versions).
# - Set to a specific number of cores (e.g., 4) to limit CPU usage on a multi-core machine.
MAX_PARALLEL_WORKERS = os.environ.get('MAX_PARALLEL_WORKERS', None)

# ------- END OF USER CONFIGURATION -------


# --- CACHE AND FOLDER NAMES ---
THUMBNAIL_CACHE_FOLDER_NAME = '.thumbnails_cache'
SQLITE_CACHE_FOLDER_NAME = '.sqlite_cache'
DATABASE_FILENAME = 'gallery_cache.sqlite'
WORKFLOW_FOLDER_NAME = 'workflow_logs_success'

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
DB_SCHEMA_VERSION = 21
BASE_INPUT_PATH_WORKFLOW = os.path.join(BASE_SMARTGALLERY_PATH, WORKFLOW_FOLDER_NAME)
THUMBNAIL_CACHE_DIR = os.path.join(BASE_SMARTGALLERY_PATH, THUMBNAIL_CACHE_FOLDER_NAME)
SQLITE_CACHE_DIR = os.path.join(BASE_SMARTGALLERY_PATH, SQLITE_CACHE_FOLDER_NAME)
DATABASE_FILE = os.path.join(SQLITE_CACHE_DIR, DATABASE_FILENAME)
PROTECTED_FOLDER_KEYS = {path_to_key(f) for f in SPECIAL_FOLDERS}
PROTECTED_FOLDER_KEYS.add('_root_')


# ---- Set variables ----
print("BASE_OUTPUT_PATH: ", BASE_OUTPUT_PATH)
print("BASE_INPUT_PATH: ", BASE_INPUT_PATH)
print("BASE_SMARTGALLERY_PATH: ", BASE_SMARTGALLERY_PATH)
print("THUMBNAIL_WIDTH: ", THUMBNAIL_WIDTH)
print("WEBP_ANIMATED_FPS: ", WEBP_ANIMATED_FPS)
print("PAGE_SIZE: ", PAGE_SIZE)
print("BATCH_SIZE: ", BATCH_SIZE)
print("MAX_PARALLEL_WORKERS: ", MAX_PARALLEL_WORKERS)
print("FFPROBE_MANUAL_PATH: ", FFPROBE_MANUAL_PATH)
print("SERVER_PORT: ", SERVER_PORT)
print("BASE_INPUT_PATH_WORKFLOW: ", BASE_INPUT_PATH_WORKFLOW)
print("THUMBNAIL_CACHE_DIR: ", THUMBNAIL_CACHE_DIR)
print("SQLITE_CACHE_DIR: ", SQLITE_CACHE_DIR)
print("DATABASE_FILE: ", DATABASE_FILE)
print("PROTECTED_FOLDER_KEYS: ", PROTECTED_FOLDER_KEYS)


# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)
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
    "PreviewImage": "output", "SaveImage": "output"
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
    Analyzes a workflow JSON, extracts details of active nodes, and returns them
    in a structured format (list of dictionaries).
    """
    try:
        workflow_data = json.loads(workflow_json_string)
    except json.JSONDecodeError:
        return None # Parsing error

    active_workflow = filter_enabled_nodes(workflow_data)
    nodes = active_workflow.get('nodes', [])
    if not nodes:
        return []

    # Sort nodes by logical category and then by ID
    sorted_nodes = sorted(nodes, key=lambda n: (
        NODE_CATEGORIES_ORDER.index(NODE_CATEGORIES.get(n.get('type'), 'others')),
        n.get('id', 0)
    ))
    
    summary_list = []
    for node in sorted_nodes:
        node_type = node.get('type', 'Unknown')
        
        # Extract parameters
        params_list = []
        widgets_values = node.get('widgets_values', [])
        param_names_list = NODE_PARAM_NAMES.get(node_type, [])
        
        for i, value in enumerate(widgets_values):
            param_name = param_names_list[i] if i < len(param_names_list) else f"param_{i+1}"
            params_list.append({"name": param_name, "value": value})

        summary_list.append({
            "id": node.get('id', 'N/A'),
            "type": node_type,
            "category": NODE_CATEGORIES.get(node_type, 'others'),
            "color": get_node_color(node_type),
            "params": params_list
        })
        
    return summary_list


# --- ALL UTILITY AND HELPER FUNCTIONS ARE DEFINED HERE, BEFORE ANY ROUTES ---

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
        workflow_data = data.get('workflow', data.get('prompt', data))
        if isinstance(workflow_data, dict) and 'nodes' in workflow_data: return json.dumps(workflow_data)
    except Exception: pass
    return None

def _scan_bytes_for_workflow(content_bytes):
    open_braces, start_index = 0, -1
    try:
        stream_str = content_bytes.decode('utf-8', errors='ignore')
        first_brace = stream_str.find('{')
        if first_brace == -1: return None
        stream_subset = stream_str[first_brace:]
        for i, char in enumerate(stream_subset):
            if char == '{':
                if start_index == -1: start_index = i
                open_braces += 1
            elif char == '}':
                if start_index != -1: open_braces -= 1
            if start_index != -1 and open_braces == 0:
                candidate = stream_subset[start_index : i + 1]
                json.loads(candidate)
                return candidate
    except Exception:
        return None
    return None

def extract_workflow(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    video_exts = ['.mp4', '.mkv', '.webm', '.mov', '.avi']
    
    if ext in video_exts:
        if FFPROBE_EXECUTABLE_PATH:
            try:
                cmd = [FFPROBE_EXECUTABLE_PATH, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                data = json.loads(result.stdout)
                if 'format' in data and 'tags' in data['format']:
                    for value in data['format']['tags'].values():
                        if isinstance(value, str) and value.strip().startswith('{'):
                            workflow = _validate_and_get_workflow(value)
                            if workflow: return workflow
            except Exception: pass
    else:
        try:
            with Image.open(filepath) as img:
                workflow_str = img.info.get('workflow') or img.info.get('prompt')
                if workflow_str:
                    workflow = _validate_and_get_workflow(workflow_str)
                    if workflow: return workflow
                exif_data = img.info.get('exif')
                if exif_data and isinstance(exif_data, bytes):
                    json_str = _scan_bytes_for_workflow(exif_data)
                    if json_str:
                        workflow = _validate_and_get_workflow(json_str)
                        if workflow: return workflow
        except Exception: pass

    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        json_str = _scan_bytes_for_workflow(content)
        if json_str:
            workflow = _validate_and_get_workflow(json_str)
            if workflow: return workflow
    except Exception: pass

    try:
        base_filename = os.path.basename(filepath)
        search_pattern = os.path.join(BASE_INPUT_PATH_WORKFLOW, f"{base_filename}*.json")
        json_files = glob.glob(search_pattern)
        if json_files:
            latest = max(json_files, key=os.path.getmtime)
            with open(latest, 'r', encoding='utf-8') as f:
                workflow = _validate_and_get_workflow(f.read())
                if workflow: return workflow
    except Exception: pass
                
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
        
        return (
            file_id, filepath, mtime, os.path.basename(filepath),
            metadata['type'], metadata['duration'], metadata['dimensions'], metadata['has_workflow']
        )
    except Exception as e:
        print(f"ERROR: Failed to process file {os.path.basename(filepath)} in worker: {e}")
        return None

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn=None):
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE, mtime REAL NOT NULL,
            name TEXT NOT NULL, type TEXT, duration TEXT, dimensions TEXT,
            has_workflow INTEGER, is_favorite INTEGER DEFAULT 0
        )
    ''')
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
            dirnames[:] = [d for d in dirnames if d not in [THUMBNAIL_CACHE_FOLDER_NAME, SQLITE_CACHE_FOLDER_NAME]]
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
                conn.executemany(
                    "INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    batch
                )
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
                    conn.executemany("INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data_to_upsert)

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
    try:
        if not os.path.isdir(folder_path): return None, [], []
        for filename in os.listdir(folder_path):
            if os.path.isfile(os.path.join(folder_path, filename)):
                ext = os.path.splitext(filename)[1]
                if ext and ext.lower() not in ['.json', '.sqlite']: extensions.add(ext.lstrip('.').lower())
                if '_' in filename: prefixes.add(filename.split('_')[0])
    except Exception as e: print(f"ERROR: Could not scan folder '{folder_path}': {e}")
    return None, sorted(list(extensions)), sorted(list(prefixes))

def initialize_gallery():
    print("INFO: Initializing gallery...")
    global FFPROBE_EXECUTABLE_PATH
    FFPROBE_EXECUTABLE_PATH = find_ffprobe_path()
    os.makedirs(THUMBNAIL_CACHE_DIR, exist_ok=True)
    os.makedirs(SQLITE_CACHE_DIR, exist_ok=True)
    with get_db_connection() as conn:
        try:
            stored_version = conn.execute('PRAGMA user_version').fetchone()[0]
        except sqlite3.DatabaseError: stored_version = 0
        if stored_version < DB_SCHEMA_VERSION:
            print(f"INFO: DB version outdated ({stored_version} < {DB_SCHEMA_VERSION}). Rebuilding database...")
            conn.execute('DROP TABLE IF EXISTS files')
            init_db(conn)
            full_sync_database(conn)
            conn.execute(f'PRAGMA user_version = {DB_SCHEMA_VERSION}')
            conn.commit()
            print("INFO: Rebuild complete.")
        else:
            print(f"INFO: DB version ({stored_version}) is up to date. Starting normally.")


# --- FLASK ROUTES ---
@app.route('/galleryout/')
@app.route('/')
def gallery_redirect_base():
    return redirect(url_for('gallery_view', folder_key='_root_'))

@app.route('/galleryout/sync_status/<string:folder_key>')
def sync_status(folder_key):
    folders = get_dynamic_folder_config()
    if folder_key not in folders:
        abort(404)
    folder_path = folders[folder_key]['path']
    return Response(sync_folder_on_demand(folder_path), mimetype='text/event-stream')

@app.route('/galleryout/view/<string:folder_key>')
def gallery_view(folder_key):
    global gallery_view_cache
    folders = get_dynamic_folder_config(force_refresh=True)
    if folder_key not in folders:
        return redirect(url_for('gallery_view', folder_key='_root_'))
    
    current_folder_info = folders[folder_key]
    folder_path = current_folder_info['path']
    
    with get_db_connection() as conn:
        conditions, params = [], []
        conditions.append("path LIKE ?")
        params.append(folder_path + os.sep + '%')
        
        sort_by = 'name' if request.args.get('sort_by') == 'name' else 'mtime'
        sort_order = 'asc' if request.args.get('sort_order', 'desc').lower() == 'asc' else 'desc'

        search_term = request.args.get('search', '').strip()
        if search_term:
            conditions.append("name LIKE ?")
            params.append(f"%{search_term}%")
        if request.args.get('favorites', 'false').lower() == 'true':
            conditions.append("is_favorite = 1")

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
        query = f"SELECT * FROM files WHERE {' AND '.join(conditions)} ORDER BY {sort_by} {sort_direction}"
        
        all_files_raw = conn.execute(query, params).fetchall()
        
    folder_path_norm = os.path.normpath(folder_path)
    all_files_filtered = [dict(row) for row in all_files_raw if os.path.normpath(os.path.dirname(row['path'])) == folder_path_norm]
    gallery_view_cache = all_files_filtered
    initial_files = gallery_view_cache[:PAGE_SIZE]
    _, extensions, prefixes = scan_folder_and_extract_options(folder_path)
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
                           folders=folders,
                           current_folder_key=folder_key, 
                           current_folder_info=current_folder_info,
                           breadcrumbs=breadcrumbs,
                           ancestor_keys=list(ancestor_keys),
                           available_extensions=extensions, 
                           available_prefixes=prefixes,
                           selected_extensions=request.args.getlist('extension'), 
                           selected_prefixes=request.args.getlist('prefix'),
                           show_favorites=request.args.get('favorites', 'false').lower() == 'true', 
                           protected_folder_keys=list(PROTECTED_FOLDER_KEYS))

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
                           
@app.route('/galleryout/create_folder', methods=['POST'])
def create_folder():
    data = request.json
    parent_key = data.get('parent_key', '_root_')
    folder_name = re.sub(r'[^a-zA-Z0-9_-]', '', data.get('folder_name', '')).strip()
    if not folder_name: return jsonify({'status': 'error', 'message': 'Invalid folder name provided.'}), 400
    folders = get_dynamic_folder_config()
    if parent_key not in folders: return jsonify({'status': 'error', 'message': 'Parent folder not found.'}), 404
    parent_path = folders[parent_key]['path']
    new_folder_path = os.path.join(parent_path, folder_name)
    if os.path.exists(new_folder_path): return jsonify({'status': 'error', 'message': 'A folder with this name already exists here.'}), 400
    try:
        os.makedirs(new_folder_path)
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder created successfully.'})
    except Exception as e: return jsonify({'status': 'error', 'message': f'Error creating folder: {e}'}), 500

@app.route('/galleryout/rename_folder/<string:folder_key>', methods=['POST'])
def rename_folder(folder_key):
    if folder_key in PROTECTED_FOLDER_KEYS: return jsonify({'status': 'error', 'message': 'This folder cannot be renamed.'}), 403
    new_name = re.sub(r'[^a-zA-Z0-9_-]', '', request.json.get('new_name', '')).strip()
    if not new_name: return jsonify({'status': 'error', 'message': 'Invalid name.'}), 400
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
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filepath = os.path.join(destination_folder, filename)
    while os.path.exists(new_filepath):
        new_filename = f"{base}({counter}){ext}"
        new_filepath = os.path.join(destination_folder, new_filename)
        counter += 1
    return new_filepath

@app.route('/galleryout/move_batch', methods=['POST'])
def move_batch():
    data = request.json
    file_ids, dest_key = data.get('file_ids', []), data.get('destination_folder')
    folders = get_dynamic_folder_config()
    if not all([file_ids, dest_key, dest_key in folders]):
        return jsonify({'status': 'error', 'message': 'Invalid data provided.'}), 400
    moved_count, renamed_count, failed_files, dest_path_folder = 0, 0, [], folders[dest_key]['path']
    with get_db_connection() as conn:
        for file_id in file_ids:
            source_path = None
            try:
                file_info = conn.execute("SELECT path, name FROM files WHERE id = ?", (file_id,)).fetchone()
                if not file_info:
                    failed_files.append(f"ID {file_id} not found in DB")
                    continue
                source_path, source_filename = file_info['path'], file_info['name']
                if not os.path.exists(source_path):
                    failed_files.append(f"{source_filename} (not found on disk)")
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    continue
                final_dest_path = _get_unique_filepath(dest_path_folder, source_filename)
                final_filename = os.path.basename(final_dest_path)
                if final_filename != source_filename: renamed_count += 1
                shutil.move(source_path, final_dest_path)
                new_id = hashlib.md5(final_dest_path.encode()).hexdigest()
                conn.execute("UPDATE files SET id = ?, path = ?, name = ? WHERE id = ?", (new_id, final_dest_path, final_filename, file_id))
                moved_count += 1
            except Exception as e:
                filename_for_error = os.path.basename(source_path) if source_path else f"ID {file_id}"
                failed_files.append(filename_for_error)
                print(f"ERROR: Failed to move file {filename_for_error}. Reason: {e}")
                continue
        conn.commit()
    message = f"Successfully moved {moved_count} file(s)."
    if renamed_count > 0: message += f" {renamed_count} were renamed to avoid conflicts."
    if failed_files: message += f" Failed to move {len(failed_files)} file(s)."
    return jsonify({'status': 'partial_success' if failed_files else 'success', 'message': message})

@app.route('/galleryout/delete_batch', methods=['POST'])
def delete_batch():
    file_ids = request.json.get('file_ids', [])
    if not file_ids: return jsonify({'status': 'error', 'message': 'No files selected.'}), 400
    deleted_count, failed_files = 0, []
    with get_db_connection() as conn:
        placeholders = ','.join('?' * len(file_ids))
        files_to_delete = conn.execute(f"SELECT id, path FROM files WHERE id IN ({placeholders})", file_ids).fetchall()
        ids_to_remove_from_db = []
        for row in files_to_delete:
            try:
                if os.path.exists(row['path']): os.remove(row['path'])
                ids_to_remove_from_db.append(row['id'])
                deleted_count += 1
            except Exception as e: 
                failed_files.append(os.path.basename(row['path']))
                print(f"ERROR: Could not delete {row['path']}: {e}")
        if ids_to_remove_from_db:
            db_placeholders = ','.join('?' * len(ids_to_remove_from_db))
            conn.execute(f"DELETE FROM files WHERE id IN ({db_placeholders})", ids_to_remove_from_db)
            conn.commit()
    message = f'Successfully deleted {deleted_count} files.'
    if failed_files: message += f" Failed to delete {len(failed_files)} files."
    return jsonify({'status': 'partial_success' if failed_files else 'success', 'message': message})

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
                os.remove(filepath)
            # If file doesn't exist on disk, we still proceed to remove the DB entry, which is the desired state.
        except OSError as e:
            # A real OS error occurred (e.g., permissions).
            print(f"ERROR: Could not delete file {filepath} from disk: {e}")
            return jsonify({'status': 'error', 'message': f'Could not delete file from disk: {e}'}), 500

        # Whether the file was deleted now or was already gone, we clean up the DB.
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'File deleted successfully.'})

# --- NEW FEATURE: RENAME FILE ---
@app.route('/galleryout/rename_file/<string:file_id>', methods=['POST'])
def rename_file(file_id):
    data = request.json
    new_name = data.get('new_name', '').strip()

    # Basic validation for the new name
    if not new_name or len(new_name) > 250:
        return jsonify({'status': 'error', 'message': 'The provided filename is invalid or too long.'}), 400
    if re.search(r'[\\/:"*?<>|]', new_name):
        return jsonify({'status': 'error', 'message': 'Filename contains invalid characters.'}), 400

    try:
        with get_db_connection() as conn:
            file_info = conn.execute("SELECT path, name FROM files WHERE id = ?", (file_id,)).fetchone()
            if not file_info:
                return jsonify({'status': 'error', 'message': 'File not found in the database.'}), 404

            old_path = file_info['path']
            old_name = file_info['name']
            
            # Preserve the original extension
            _, old_ext = os.path.splitext(old_name)
            new_name_base, new_ext = os.path.splitext(new_name)
            if not new_ext: # If user didn't provide an extension, use the old one
                final_new_name = new_name + old_ext
            else:
                final_new_name = new_name

            if final_new_name == old_name:
                return jsonify({'status': 'error', 'message': 'The new name is the same as the old one.'}), 400

            file_dir = os.path.dirname(old_path)
            new_path = os.path.join(file_dir, final_new_name)

            if os.path.exists(new_path):
                return jsonify({'status': 'error', 'message': f'A file named "{final_new_name}" already exists in this folder.'}), 409

            # Perform the rename and database update
            os.rename(old_path, new_path)
            new_id = hashlib.md5(new_path.encode()).hexdigest()
            conn.execute("UPDATE files SET id = ?, path = ?, name = ? WHERE id = ?", (new_id, new_path, final_new_name, file_id))
            conn.commit()

            return jsonify({
                'status': 'success',
                'message': 'File renamed successfully.',
                'new_name': final_new_name,
                'new_id': new_id
            })

    except OSError as e:
        print(f"ERROR: OS error during file rename for {file_id}: {e}")
        return jsonify({'status': 'error', 'message': f'A system error occurred during rename: {e}'}), 500
    except Exception as e:
        print(f"ERROR: Generic error during file rename for {file_id}: {e}")
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {e}'}), 500

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

if __name__ == '__main__':
    initialize_gallery()
    print(f"Gallery started! Open: http://127.0.0.1:{SERVER_PORT}/galleryout/")
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)