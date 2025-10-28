# Smart Gallery for ComfyUI
# Author: Biagio Maffettone © 2025 — MIT License (free to use and modify)
#
# Version: 1.33 - October 28, 2025
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
import threading
from flask import Flask, render_template, send_from_directory, abort, send_file, url_for, redirect, request, jsonify, Response
from PIL import Image, ImageSequence
import colorsys
from werkzeug.utils import secure_filename


# --- USER CONFIGURATION ---
# Adjust the parameters in this section to customize the gallery.
#
# IMPORTANT:
# - Even on Windows, always use forward slashes ( / ) in paths, 
#   not backslashes ( \ ), to ensure compatibility.

# - It is strongly recommended to have ffmpeg installed, since some features depend on it.

# --- CACHE AND FOLDER NAMES ---
# Constants are now defined and loaded into app.config in the main block.

# --- HELPER FUNCTIONS (DEFINED FIRST) ---
def path_to_key(relative_path):
    if not relative_path: return '_root_'
    return base64.urlsafe_b64encode(relative_path.replace(os.sep, '/').encode()).decode()

def key_to_path(key):
    if key == '_root_': return ''
    try:
        return base64.urlsafe_b64decode(key.encode()).decode().replace('/', os.sep)
    except Exception as e:
        print(f"ERROR: Failed to decode key '{key}': {e}")
        return None

# --- DERIVED SETTINGS ---
DB_SCHEMA_VERSION = 21  # Schema version is static and can remain global

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)

# Thread-safe caches with locks for concurrent access
gallery_view_cache = []
gallery_view_cache_lock = threading.Lock()
folder_config_cache = None
folder_config_cache_lock = threading.Lock()


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
        # Use hash to get a consistent color for the same node type
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
    Analizza un workflow JSON, estrae i dettagli dei nodi attivi e li restituisce
    in un formato strutturato (lista di dizionari).
    """
    try:
        workflow_data = json.loads(workflow_json_string)
    except json.JSONDecodeError:
        return None # Errore di parsing

    active_workflow = filter_enabled_nodes(workflow_data)
    nodes = active_workflow.get('nodes', [])
    if not nodes:
        return []

    # Ordina i nodi per categoria logica e poi per ID
    sorted_nodes = sorted(nodes, key=lambda n: (
        NODE_CATEGORIES_ORDER.index(NODE_CATEGORIES.get(n.get('type'), 'others')),
        n.get('id', 0)
    ))
    
    summary_list = []
    for node in sorted_nodes:
        node_type = node.get('type', 'Unknown')
        
        # Estrai i parametri
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
    manual_path = app.config.get("FFPROBE_MANUAL_PATH", "")
    if manual_path and os.path.isfile(manual_path):
        try:
            subprocess.run([manual_path, "-version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            return manual_path
        except Exception as e:
            print(f"WARNING: Manual ffprobe path '{manual_path}' is invalid: {e}")
    base_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    try:
        result = subprocess.run([base_name, "-version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        return base_name
    except Exception as e:
        print(f"WARNING: ffprobe not found in PATH: {e}")
    print("WARNING: ffprobe not found. Video metadata analysis will be disabled.")
    return None

def _validate_and_get_workflow(json_string):
    try:
        data = json.loads(json_string)
        workflow_data = data.get('workflow', data.get('prompt', data))
        if isinstance(workflow_data, dict) and 'nodes' in workflow_data: return json.dumps(workflow_data)
    except Exception as e:
        print(f"DEBUG: Failed to validate workflow JSON: {e}")
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
    except Exception as e:
        print(f"DEBUG: Error scanning bytes for workflow: {e}")
    return None

def extract_workflow(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    video_exts = app.config.get('VIDEO_EXTENSIONS', ['.mp4', '.mkv', '.webm', '.mov', '.avi'])
    
    if ext in video_exts:
        ffprobe_path = app.config.get("FFPROBE_EXECUTABLE_PATH")
        if ffprobe_path:
            try:
                cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                data = json.loads(result.stdout)
                if 'format' in data and 'tags' in data['format']:
                    for value in data['format']['tags'].values():
                        if isinstance(value, str) and value.strip().startswith('{'):
                            workflow = _validate_and_get_workflow(value)
                            if workflow: return workflow
            except Exception as e:
                print(f"DEBUG: Error extracting workflow from video metadata: {e}")
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
        except Exception as e:
            print(f"DEBUG: Error extracting workflow from image metadata: {e}")

    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        json_str = _scan_bytes_for_workflow(content)
        if json_str:
            workflow = _validate_and_get_workflow(json_str)
            if workflow: return workflow
    except Exception as e:
        print(f"DEBUG: Error scanning file content for workflow: {e}")

    try:
        base_filename = os.path.basename(filepath)
        search_pattern = os.path.join(app.config['BASE_INPUT_PATH_WORKFLOW'], f"{base_filename}*.json")
        json_files = glob.glob(search_pattern)
        if json_files:
            latest = max(json_files, key=os.path.getmtime)
            with open(latest, 'r', encoding='utf-8') as f:
                workflow = _validate_and_get_workflow(f.read())
                if workflow: return workflow
    except Exception as e:
        print(f"DEBUG: Error searching for workflow log file: {e}")
                
    return None

def is_webp_animated(filepath):
    try:
        with Image.open(filepath) as img: return getattr(img, 'is_animated', False)
    except Exception as e:
        print(f"DEBUG: Error checking if WebP is animated: {e}")
        return False

def format_duration(seconds):
    if not seconds or seconds < 0: return ""
    m, s = divmod(int(seconds), 60); h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def analyze_file_metadata(filepath):
    details = {'type': 'unknown', 'duration': '', 'dimensions': '', 'has_workflow': 0}
    ext_lower = os.path.splitext(filepath)[1].lower()
    
    # Use centralized extension configuration
    image_exts = app.config.get('IMAGE_EXTENSIONS', ['.png', '.jpg', '.jpeg'])
    animated_exts = app.config.get('ANIMATED_IMAGE_EXTENSIONS', ['.gif', '.webp'])
    video_exts = app.config.get('VIDEO_EXTENSIONS', ['.mp4', '.webm', '.mov'])
    audio_exts = app.config.get('AUDIO_EXTENSIONS', ['.mp3', '.wav', '.ogg', '.flac'])
    
    if ext_lower in image_exts:
        details['type'] = 'image'
    elif ext_lower in animated_exts:
        details['type'] = 'animated_image'
    elif ext_lower in video_exts:
        details['type'] = 'video'
    elif ext_lower in audio_exts:
        details['type'] = 'audio'
    
    # Special handling for WebP (can be static or animated)
    if details['type'] == 'animated_image' and ext_lower == '.webp':
        details['type'] = 'animated_image' if is_webp_animated(filepath) else 'image'
    
    if 'image' in details['type']:
        try:
            with Image.open(filepath) as img: details['dimensions'] = f"{img.width}x{img.height}"
        except Exception as e:
            print(f"DEBUG: Error getting image dimensions for {filepath}: {e}")
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
        except Exception as e:
            print(f"DEBUG: Error analyzing video metadata for {filepath}: {e}")
    elif details['type'] == 'animated_image':
        try:
            with Image.open(filepath) as img:
                if getattr(img, 'is_animated', False):
                    if ext_lower == '.gif': total_duration_sec = sum(frame.info.get('duration', 100) for frame in ImageSequence.Iterator(img)) / 1000
                    elif ext_lower == '.webp': total_duration_sec = getattr(img, 'n_frames', 1) / app.config['WEBP_ANIMATED_FPS']
        except Exception as e:
            print(f"DEBUG: Error analyzing animated image duration for {filepath}: {e}")
    if total_duration_sec > 0: details['duration'] = format_duration(total_duration_sec)
    return details

def create_thumbnail(filepath, file_hash, file_type):
    thumbnail_cache_dir = app.config['THUMBNAIL_CACHE_DIR']
    if file_type in ['image', 'animated_image']:
        try:
            with Image.open(filepath) as img:
                fmt = 'gif' if img.format == 'GIF' else 'webp' if img.format == 'WEBP' else 'jpeg'
                cache_path = os.path.join(thumbnail_cache_dir, f"{file_hash}.{fmt}")
                if file_type == 'animated_image' and getattr(img, 'is_animated', False):
                    frames = [fr.copy() for fr in ImageSequence.Iterator(img)]
                    if frames:
                        for frame in frames: frame.thumbnail((app.config['THUMBNAIL_WIDTH'], app.config['THUMBNAIL_WIDTH'] * 2), Image.Resampling.LANCZOS)
                        processed_frames = [frame.convert('RGBA').convert('RGB') for frame in frames]
                        if processed_frames:
                            processed_frames[0].save(cache_path, save_all=True, append_images=processed_frames[1:], duration=img.info.get('duration', 100), loop=img.info.get('loop', 0), optimize=True)
                else:
                    img.thumbnail((app.config['THUMBNAIL_WIDTH'], app.config['THUMBNAIL_WIDTH'] * 2), Image.Resampling.LANCZOS)
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
                cache_path = os.path.join(thumbnail_cache_dir, f"{file_hash}.jpeg")
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img.thumbnail((app.config['THUMBNAIL_WIDTH'], app.config['THUMBNAIL_WIDTH'] * 2), Image.Resampling.LANCZOS)
                img.save(cache_path, 'JPEG', quality=80)
                return cache_path
        except Exception as e: print(f"ERROR (OpenCV): Could not create thumbnail for {os.path.basename(filepath)}: {e}")
    return None

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE_FILE'])
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
    
    with folder_config_cache_lock:
        if folder_config_cache is not None and not force_refresh:
            return folder_config_cache

        print("INFO: Refreshing folder configuration by scanning directory tree...")

    base_path_normalized = os.path.normpath(app.config['BASE_OUTPUT_PATH']).replace('\\', '/')
    
    try:
        root_mtime = os.path.getmtime(app.config['BASE_OUTPUT_PATH'])
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
        for dirpath, dirnames, _ in os.walk(app.config['BASE_OUTPUT_PATH']):
            dirnames[:] = [d for d in dirnames if d not in [app.config['THUMBNAIL_CACHE_FOLDER_NAME'], app.config['SQLITE_CACHE_FOLDER_NAME']]]
            for dirname in dirnames:
                full_path = os.path.normpath(os.path.join(dirpath, dirname)).replace('\\', '/')
                relative_path = os.path.relpath(full_path, app.config['BASE_OUTPUT_PATH']).replace('\\', '/')
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
        print(f"WARNING: The base directory '{app.config['BASE_OUTPUT_PATH']}' was not found.")
    
        folder_config_cache = dynamic_config
        return dynamic_config
    
def full_sync_database(conn):
    print("INFO: Starting full file scan...")
    all_folders = get_dynamic_folder_config(force_refresh=True)
    start_time = time.time()
    db_files = {row['path']: row['mtime'] for row in conn.execute('SELECT path, mtime FROM files').fetchall()}
    disk_files = {}
    for folder_data in all_folders.values():
        folder_path = folder_data['path']
        if not os.path.isdir(folder_path): continue
        for name in os.listdir(folder_path):
            filepath = os.path.join(folder_path, name)
            if os.path.isfile(filepath) and os.path.splitext(name)[1].lower() not in ['.json', '.sqlite']:
                disk_files[filepath] = os.path.getmtime(filepath)
    to_add = set(disk_files) - set(db_files)
    to_delete = set(db_files) - set(disk_files)
    to_check = set(disk_files) & set(db_files)
    to_update = {path for path in to_check if disk_files.get(path, 0) > db_files.get(path, 0)}
    files_to_process = to_add.union(to_update)
    if files_to_process:
        print(f"INFO: Analyzing {len(files_to_process)} new or modified files...")
        data_to_upsert = []
        for p in files_to_process:
            metadata = analyze_file_metadata(p)
            file_hash = hashlib.md5((p + str(disk_files[p])).encode()).hexdigest()
            if not glob.glob(os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*")):
                create_thumbnail(p, file_hash, metadata['type'])
            data_to_upsert.append((hashlib.md5(p.encode()).hexdigest(), p, disk_files[p], os.path.basename(p), *metadata.values()))
        if data_to_upsert: conn.executemany("INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data_to_upsert)
    if to_delete:
        print(f"INFO: Removing {len(to_delete)} obsolete files...")
        conn.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in to_delete])
    conn.commit()
    print(f"INFO: Full scan completed in {time.time() - start_time:.2f} seconds.")

def sync_folder_on_demand(folder_path):
    yield f"data: {json.dumps({'message': 'Checking folder for changes...', 'current': 0, 'total': 1})}\n\n"
    
    try:
        with get_db_connection() as conn:
            # Use centralized extension configuration
            valid_extensions = set(app.config.get('ALL_MEDIA_EXTENSIONS', []))
            disk_files = {}
            
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
            files_to_update = {path for path in (disk_filepaths & db_filepaths) if disk_files[path] > db_files[path]}
            
            if not files_to_add and not files_to_update and not files_to_delete:
                yield f"data: {json.dumps({'message': 'Folder is up-to-date.', 'status': 'no_changes', 'current': 1, 'total': 1})}\n\n"
                return

            files_to_process = list(files_to_add.union(files_to_update))
            total_files_to_process = len(files_to_process)
            
            if total_files_to_process > 0:
                yield f"data: {json.dumps({'message': f'Found {total_files_to_process} new/modified files...', 'current': 0, 'total': total_files_to_process})}\n\n"
                time.sleep(1)

                data_to_upsert = []
                for i, path in enumerate(files_to_process):
                    progress_data = {'message': f'Processing: {os.path.basename(path)}', 'current': i + 1, 'total': total_files_to_process }
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    
                    metadata = analyze_file_metadata(path)
                    file_hash = hashlib.md5((path + str(disk_files[path])).encode()).hexdigest()
                    if not glob.glob(os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*")): 
                        create_thumbnail(path, file_hash, metadata['type'])
                    
                    data_to_upsert.append((hashlib.md5(path.encode()).hexdigest(), path, disk_files[path], os.path.basename(path), *metadata.values()))
                
                if data_to_upsert: 
                    conn.executemany("INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data_to_upsert)

            if files_to_delete:
                paths_to_delete_list = list(files_to_delete)
                placeholders = ','.join('?' * len(paths_to_delete_list))
                conn.execute(f"DELETE FROM files WHERE path IN ({placeholders})", paths_to_delete_list)

            conn.commit()
            yield f"data: {json.dumps({'message': 'Sync complete. Reloading...', 'status': 'reloading', 'current': total_files_to_process, 'total': total_files_to_process})}\n\n"

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

def initialize_gallery(flask_app):
    """Initializes the gallery by setting up derived paths and the database."""
    # Now that BASE_OUTPUT_PATH etc. are in app.config, we can derive the rest.
    flask_app.config['BASE_INPUT_PATH_WORKFLOW'] = os.path.join(flask_app.config['BASE_INPUT_PATH'], flask_app.config['WORKFLOW_FOLDER_NAME'])
    flask_app.config['THUMBNAIL_CACHE_DIR'] = os.path.join(flask_app.config['BASE_OUTPUT_PATH'], flask_app.config['THUMBNAIL_CACHE_FOLDER_NAME'])
    flask_app.config['SQLITE_CACHE_DIR'] = os.path.join(flask_app.config['BASE_OUTPUT_PATH'], flask_app.config['SQLITE_CACHE_FOLDER_NAME'])
    flask_app.config['DATABASE_FILE'] = os.path.join(flask_app.config['SQLITE_CACHE_DIR'], flask_app.config['DATABASE_FILENAME'])
    
    protected_keys = {path_to_key(f) for f in flask_app.config['SPECIAL_FOLDERS']}
    protected_keys.add('_root_')
    flask_app.config['PROTECTED_FOLDER_KEYS'] = protected_keys

    print("INFO: Initializing gallery...")
    flask_app.config['FFPROBE_EXECUTABLE_PATH'] = find_ffprobe_path()
    os.makedirs(flask_app.config['THUMBNAIL_CACHE_DIR'], exist_ok=True)
    os.makedirs(flask_app.config['SQLITE_CACHE_DIR'], exist_ok=True)
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
    global gallery_view_cache  # Module-level cache shared across requests (thread-safe via lock)
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
    
    # Thread-safe update of gallery_view_cache
    with gallery_view_cache_lock:
        gallery_view_cache = all_files_filtered
        initial_files = gallery_view_cache[:app.config['PAGE_SIZE']]
        total_files_count = len(gallery_view_cache)
    
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
                           total_files=total_files_count, 
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
                           protected_folder_keys=list(app.config['PROTECTED_FOLDER_KEYS']))

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
    if folder_key in app.config['PROTECTED_FOLDER_KEYS']: return jsonify({'status': 'error', 'message': 'This folder cannot be renamed.'}), 403
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
    if folder_key in app.config['PROTECTED_FOLDER_KEYS']: return jsonify({'status': 'error', 'message': 'This folder cannot be deleted.'}), 403
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
    
    # Validate input
    if offset < 0:
        return jsonify(files=[])
    
    # Thread-safe access to gallery_view_cache
    with gallery_view_cache_lock:
        if offset >= len(gallery_view_cache):
            return jsonify(files=[])
        return jsonify(files=gallery_view_cache[offset:offset + app.config['PAGE_SIZE']])

def get_file_info_from_db(file_id, column='*'):
    try:
        with get_db_connection() as conn:
            row = conn.execute(f"SELECT {column} FROM files WHERE id = ?", (file_id,)).fetchone()
        if not row: abort(404)
        return dict(row) if column == '*' else row[0]
    except sqlite3.Error as e:
        print(f"ERROR: Database error in get_file_info_from_db for file_id {file_id}: {e}")
        abort(500)

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
        files_to_delete = conn.execute(f"SELECT id, path, mtime FROM files WHERE id IN ({placeholders})", file_ids).fetchall()
        ids_to_remove_from_db = []
        for row in files_to_delete:
            try:
                if os.path.exists(row['path']): 
                    os.remove(row['path'])
                
                # Clean up orphaned thumbnail
                file_hash = hashlib.md5((row['path'] + str(row['mtime'])).encode()).hexdigest()
                thumbnail_pattern = os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*")
                for thumbnail_path in glob.glob(thumbnail_pattern):
                    try:
                        os.remove(thumbnail_path)
                    except Exception as e:
                        print(f"WARNING: Could not remove thumbnail {thumbnail_path}: {e}")
                
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
        file_info = conn.execute("SELECT path, mtime FROM files WHERE id = ?", (file_id,)).fetchone()
        if not file_info:
            return jsonify({'status': 'success', 'message': 'File already deleted from database.'})
        
        filepath = file_info['path']
        mtime = file_info['mtime']
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            # If file doesn't exist on disk, we still proceed to remove the DB entry, which is the desired state.
        except OSError as e:
            # A real OS error occurred (e.g., permissions).
            print(f"ERROR: Could not delete file {filepath} from disk: {e}")
            return jsonify({'status': 'error', 'message': f'Could not delete file from disk: {e}'}), 500

        # Clean up orphaned thumbnail
        file_hash = hashlib.md5((filepath + str(mtime)).encode()).hexdigest()
        try:
            thumbnail_pattern = os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*")
            for thumbnail_path in glob.glob(thumbnail_pattern):
                os.remove(thumbnail_path)
                print(f"INFO: Removed orphaned thumbnail: {os.path.basename(thumbnail_path)}")
        except Exception as e:
            print(f"WARNING: Could not remove thumbnail for {filepath}: {e}")

        # Whether the file was deleted now or was already gone, we clean up the DB.
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'File deleted successfully.'})

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
    existing_thumbnails = glob.glob(os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*"))
    if existing_thumbnails: return send_file(existing_thumbnails[0])
    print(f"WARN: Thumbnail not found for {os.path.basename(filepath)}, generating...")
    cache_path = create_thumbnail(filepath, file_hash, info['type'])
    if cache_path and os.path.exists(cache_path): return send_file(cache_path)
    return "Thumbnail generation failed", 404

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Smart Gallery for ComfyUI")
    parser.add_argument("--output-path", type=str, required=True, help="Path to ComfyUI's output directory.")
    parser.add_argument("--input-path", type=str, required=True, help="Path to ComfyUI's input directory.")
    parser.add_argument("--port", type=int, default=8008, help="Port for the gallery web server.")
    parser.add_argument("--ffprobe-path", type=str, default="", help="Manual path to the ffprobe executable.")

    args = parser.parse_args()

    # --- Populate Flask app config from arguments ---
    app.config['BASE_OUTPUT_PATH'] = args.output_path
    app.config['BASE_INPUT_PATH'] = args.input_path
    app.config['SERVER_PORT'] = args.port
    app.config['FFPROBE_MANUAL_PATH'] = args.ffprobe_path

    # --- Set other static configuration values ---
    app.config['THUMBNAIL_WIDTH'] = 300
    app.config['WEBP_ANIMATED_FPS'] = 16.0
    app.config['PAGE_SIZE'] = 100
    app.config['SPECIAL_FOLDERS'] = ['video', 'audio']
    
    # --- Define valid file extensions (centralized) ---
    app.config['VIDEO_EXTENSIONS'] = ['.mp4', '.mkv', '.webm', '.mov', '.avi']
    app.config['IMAGE_EXTENSIONS'] = ['.png', '.jpg', '.jpeg']
    app.config['ANIMATED_IMAGE_EXTENSIONS'] = ['.gif', '.webp']
    app.config['AUDIO_EXTENSIONS'] = ['.mp3', '.wav', '.ogg', '.flac']
    app.config['ALL_MEDIA_EXTENSIONS'] = (
        app.config['VIDEO_EXTENSIONS'] + 
        app.config['IMAGE_EXTENSIONS'] + 
        app.config['ANIMATED_IMAGE_EXTENSIONS'] + 
        app.config['AUDIO_EXTENSIONS']
    )
    
    # --- Set constants for cache/folder names ---
    app.config['THUMBNAIL_CACHE_FOLDER_NAME'] = '.thumbnails_cache'
    app.config['SQLITE_CACHE_FOLDER_NAME'] = '.sqlite_cache'
    app.config['DATABASE_FILENAME'] = 'gallery_cache.sqlite'
    app.config['WORKFLOW_FOLDER_NAME'] = 'workflow_logs_success'

    if not os.path.isdir(app.config['BASE_OUTPUT_PATH']) or not os.path.isdir(app.config['BASE_INPUT_PATH']):
        print(f"ERROR: One or more paths are invalid. Please check your configuration.\nOutput: {app.config['BASE_OUTPUT_PATH']}\nInput: {app.config['BASE_INPUT_PATH']}")
        sys.exit(1)

    # Initialize derived paths and database
    initialize_gallery(app)

    print(f"SmartGallery started! Open: http://127.0.0.1:{app.config['SERVER_PORT']}/galleryout/")
    app.run(host='0.0.0.0', port=app.config['SERVER_PORT'], debug=False)
