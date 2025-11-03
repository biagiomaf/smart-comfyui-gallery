# SmartGallery - Standalone AI Media Gallery
# Formerly: Smart Gallery for ComfyUI (now decoupled from ComfyUI)
# Author: Biagio Maffettone © 2025 — MIT License (free to use and modify)
#
# Version: 2.0.0 - Standalone Version (November 2025)
#
# MAJOR CHANGES (v2.0.0 - Standalone Release):
# - Decoupled from ComfyUI: Now runs as a standalone application
# - Removed ComfyUI integration layer (__init__.py, sidebar dashboard)
# - Enhanced configuration: Supports config.json + CLI arguments
# - Still fully compatible with ComfyUI-generated files and workflows
# - Removed CORS dependency (single-origin application)
# - Simplified deployment: Just Python + pip install
#
# FEATURES:
# - Browse and organize AI-generated images, videos, and audio files
# - Extract and display ComfyUI workflow metadata from any file
# - Advanced filtering: by type, date, dimensions, workflow parameters
# - Thumbnail generation and caching for fast browsing
# - SQLite database for efficient file indexing
# - File upload support with workflow extraction
# - Favorites and folder management
# - Lightbox viewer with keyboard navigation
#
# COMPATIBILITY:
# - Works with ANY ComfyUI-generated files (PNGs, videos with embedded workflows)
# - Can point to ComfyUI's output/input folders
# - No ComfyUI installation required
# - Workflow extraction is 100% independent
#
# GitHub: https://github.com/opj161/smart-comfyui-gallery (plugin version)
# GitHub: https://github.com/opj161/smartgallery-standalone (standalone version)
# Contact: biagiomaf@gmail.com

# CHANGES (v1.41.0):
# - CRITICAL PERFORMANCE: Added 5 database indices on files table (10-50x faster queries)
#   - idx_files_name: Fast name search (was O(n), now O(log n))
#   - idx_files_mtime: Fast date sorting
#   - idx_files_type: Fast type filtering
#   - idx_files_favorite: Fast favorite filtering
#   - idx_files_path: Fast folder filtering
# - CRITICAL PERFORMANCE: Implemented true SQL pagination with LIMIT/OFFSET
#   - Was: Load ALL matching files into memory, slice in Python (memory bloat)
#   - Now: Query only the requested page from database (90% memory reduction)
#   - Impact: Can handle millions of files without memory issues
# - Enhanced: load_more endpoint now queries database directly (no cache needed)
# - Technical: Separate COUNT query for total, paginated query for files
# - Breaking: Removed global gallery_view_cache (replaced with per-request queries)
#
# CHANGES (v1.40.7):
# - Fixed "Found 100 files" notification to show actual total count
# - Added visual results counter in header
# - Enhanced Load More button with remaining file count
# - load_more endpoint now returns total count
#
# CHANGES (v1.40.6):
# - CRITICAL FIX: Complete filter clearing system now works correctly
# - Issue: "Clear All" button didn't clear Tom-Select instances, only navigated
# - Root cause: Tom-Select instances created but never stored globally
# - Solution: Added global tomSelectInstances object to store all 5 instances
# - Fixed: "Clear All" button now programmatically clears all inputs + Tom-Select
# - Fixed: Individual pill removal now clears Tom-Select instances via .clear() API
# - Added: Automatic form submission after clearing (changes reach server)
# - Technical: Stored references during initialization, use Tom-Select API in clear functions
# - Impact: All filter clearing mechanisms now work as expected
#
# - Enhanced number inputs with monospace font and refined spinner controls
# - Improved arrow indicators between min/max ranges (larger, more visible)
# - Consistent 1.5rem spacing rhythm throughout filter panel
# - Color-coded range labels now bold (green for min, red for max)
# - Professional polish: All filter elements now have uniform visual language
#
# CHANGES (v1.40.3):
# - Enhanced Extensions and Prefixes multi-select dropdowns
# - Added 'remove_button' plugin for individual item removal
# - Set closeAfterSelect: false for better multi-select UX
# - Set maxOptions: null to show all available options
# - Improved placeholder visibility with hidePlaceholder: false
#
# CHANGES (v1.40.2):
# - FIXED: Workflow metadata dropdowns (Model, Sampler, Scheduler) now use Tom-Select
# - Previously these were plain HTML select elements, styling wasn't applied
# - Now initialized with Tom-Select after population for consistent modern UX
# - Applies all the enhanced dropdown styling from v1.40.1
#
# CHANGES (v1.40.1):
# - Enhanced filter panel styling with comprehensive Tom-Select dropdown theming
# - Improved text readability in dropdown menus (dark background, light text)
# - Added modern hover/focus states for all input fields and dropdowns
# - Styled multi-select pills with blue rounded badges
# - Enhanced visual feedback with smooth cubic-bezier transitions
# - Better accessibility with clear focus indicators and contrast
#
# BREAKING CHANGES (v1.40.0):
# - MAJOR REFACTOR: ComfyUIWorkflowParser now handles BOTH UI and API formats natively
# - Removed convert_ui_workflow_to_api_format() function (no longer needed)
# - Parser detects format automatically (checks for 'nodes' array = UI format)
# - Native UI format support: Uses links_map and widget_idx_map directly
# - 2-3x faster parsing (no conversion overhead)
# - Simpler architecture: Format-aware helper methods for all operations
# - extract_workflow_metadata() simplified: Passes raw workflow_data to parser
# - Debug stages updated: 01_raw → 02_parsed → 03_format_detection → 04_parser_input → 05_parser_output
#
# CHANGES (v1.39.4):
# - CRITICAL FIX: Debug mode now works with multiprocessing
# - Removed global DEBUG_WORKFLOW_DIR variable (caused worker process issues)
# - Debug directory now passed as parameter to worker processes
# - Debug files now properly created in output/workflow_debug/
# - All traversal methods now validate node types before operations
# - Improved error messages with format diagnostics
#
# CHANGES (v1.39.2):
# - Fixed parser bug where node_data validation prevented string assignment errors
# - Added comprehensive workflow extraction statistics after processing
# - Enhanced error reporting with parse error details and problematic file lists
#
# BREAKING CHANGES (v1.39.0):
# - Database schema upgraded to v22 (automatic migration from v21)
# - workflow_metadata table now supports multiple samplers per file
# - New ComfyUIWorkflowParser with graph-based workflow traversal
# - Query logic updated to use EXISTS subqueries (eliminates duplicate results)
# - New API endpoint: /workflow_samplers/<file_id> for detailed sampler inspection
#
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
import logging
from datetime import datetime
from flask import g, Flask, render_template, send_from_directory, abort, send_file, url_for, redirect, request, jsonify, Response, stream_with_context
# flask_cors removed - not needed for standalone version
from PIL import Image, ImageSequence
import colorsys
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
import concurrent.futures
from tqdm import tqdm
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


# ================================================================================
# WORKFLOW METADATA EXTRACTION - State-of-the-Art Implementation
# ================================================================================
# This section implements a robust, production-ready parser for ComfyUI workflows
# with multi-sampler support, advanced node tracing, and comprehensive error handling.
#
# Key Features:
# - Directed graph traversal (replaces flawed BFS with single-path backward trace)
# - Universal parameter getter (handles both direct values and Primitive node links)
# - Comprehensive node type support (researched from real-world workflows)
# - Granular extraction (each metadata field extracted independently)
# - Robust fallbacks (image dimensions from file if workflow parsing fails)
# - Database integrity validation (final type conversion pass)
# ================================================================================

# --- Comprehensive and Corrected Node Type Constants ---
# These lists are curated from analysis of real-world ComfyUI workflows

# Actual sampler nodes that perform sampling operations
SAMPLER_TYPES = [
    "KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced",
    "KSamplerEfficient", "DetailerForEach", "SamplerDPMPP_2M_SDE", "WanVideoSampler",
    "UltimateSDUpscale"  # Upscaling with diffusion refinement
]

# Model loader nodes (checkpoints, UNETs, diffusion models)
MODEL_LOADER_TYPES = [
    "CheckpointLoaderSimple", "CheckpointLoader", "Load Checkpoint", "UNETLoader",
    "Load Diffusion Model", "UnetLoaderGGUF", "DualCLIPLoader"
]

# Text encoding nodes for prompts
PROMPT_NODE_TYPES = [
    "CLIPTextEncode", "CLIP Text Encode (Prompt)", "TextEncodeQwenImageEditPlus",
    "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner"
]

# Scheduler nodes (provide scheduling algorithms)
SCHEDULER_NODE_TYPES = ["BasicScheduler", "KarrasScheduler", "ExponentialScheduler", "SgmUniformScheduler"]

# Sampler selection nodes (provide sampler names, not actual samplers)
SAMPLER_SELECT_NODE_TYPES = ["KSamplerSelect"]


class ComfyUIWorkflowParser:
    """
    State-of-the-art parser for ComfyUI workflow metadata with native UI format support.
    
    Architecture:
    - Treats workflow as a Directed Acyclic Graph (DAG)
    - Uses single-path backward tracing for each input (not BFS)
    - Extracts metadata for each sampler node independently
    - Handles complex workflows with Primitive nodes, LoRA chains, and multiple samplers
    - Supports BOTH UI Workflow format and API/Prompt format natively
    
    Design Principles:
    - Fail gracefully: Missing one field doesn't prevent extraction of others
    - Comprehensive: Supports all known ComfyUI node variations
    - Robust: Validates and converts types before database insertion
    - Format-agnostic: Works with UI and API formats without conversion overhead
    """
    
    def __init__(self, workflow_data: Dict[str, Any], file_path: Path):
        """
        Initialize parser with workflow data in either UI or API format.
        
        Args:
            workflow_data: ComfyUI workflow in UI format (has 'nodes' array) or API format (node_id -> node_data dict)
            file_path: Path to the image/video file (for dimension fallback)
        """
        self.file_path = file_path
        
        # Detect format and normalize data structures
        if isinstance(workflow_data, dict) and 'nodes' in workflow_data and isinstance(workflow_data.get('nodes'), list):
            # UI Format
            self.format = 'ui'
            self.nodes_by_id = {str(n['id']): n for n in workflow_data['nodes'] if isinstance(n, dict)}
            self.links_map = self._build_link_map(workflow_data.get('links', []))
            self.widget_map = workflow_data.get('widget_idx_map', {})
        else:
            # API Format
            self.format = 'api'
            self.nodes_by_id = workflow_data
            self.links_map = None
            self.widget_map = None
            
            # Ensure all nodes have their ID embedded (for easier access in API format)
            for node_id, node_data in self.nodes_by_id.items():
                if isinstance(node_data, dict):
                    node_data['id'] = node_id
    
    def _build_link_map(self, links_list: List) -> Dict[int, Tuple[str, int]]:
        """
        Builds a lookup map for UI format links.
        
        Args:
            links_list: List of links from UI workflow format
                       Each link: [link_id, source_node_id, source_slot, target_node_id, target_slot, type]
        
        Returns:
            Dict mapping link_id -> (source_node_id, source_output_slot)
        """
        link_map = {}
        for link in links_list:
            if isinstance(link, list) and len(link) >= 3:
                link_id = link[0]
                source_node_id = str(link[1])
                source_output_slot = link[2]
                link_map[link_id] = (source_node_id, source_output_slot)
        return link_map
    
    def _get_node_type(self, node: Dict[str, Any]) -> Optional[str]:
        """
        Gets the node type in a format-agnostic way.
        
        Args:
            node: Node dict (UI or API format)
        
        Returns:
            Node type string or None
        """
        if not isinstance(node, dict):
            return None
        
        if self.format == 'ui':
            return node.get('type')
        else:
            return node.get('class_type')
    
    def _get_input_source_node(self, node: Dict[str, Any], input_name: str) -> Optional[Dict[str, Any]]:
        """
        Finds the source node for a given input connection in a format-agnostic way.
        
        Args:
            node: Current node
            input_name: Name of the input to trace (e.g., 'model', 'positive')
        
        Returns:
            Source node dict or None if not connected
        """
        if not isinstance(node, dict):
            return None
        
        if self.format == 'ui':
            # UI Format: Find input by name in inputs array, then look up link
            for input_def in node.get('inputs', []):
                if isinstance(input_def, dict) and input_def.get('name') == input_name:
                    link_id = input_def.get('link')
                    if link_id is not None and link_id in self.links_map:
                        source_node_id, _ = self.links_map[link_id]
                        return self.nodes_by_id.get(source_node_id)
            return None
        else:
            # API Format: Input is either a direct value or [node_id, slot]
            link_data = node.get('inputs', {}).get(input_name)
            if isinstance(link_data, list) and len(link_data) >= 1:
                source_node_id = str(link_data[0])
                return self.nodes_by_id.get(source_node_id)
            return None
    
    def _get_widget_value(self, node: Dict[str, Any], param_name: str) -> Any:
        """
        Gets a widget parameter value in a format-agnostic way.
        
        Args:
            node: Node dict
            param_name: Parameter name (e.g., 'seed', 'steps', 'cfg')
        
        Returns:
            Parameter value or None
        """
        if not isinstance(node, dict):
            return None
        
        if self.format == 'ui':
            # UI Format: Use widget_idx_map to find value in widgets_values array
            node_id = str(node.get('id', ''))
            widgets_values = node.get('widgets_values', [])
            
            # Try widget_idx_map first (most reliable)
            if node_id in self.widget_map and isinstance(self.widget_map[node_id], dict):
                param_index = self.widget_map[node_id].get(param_name)
                if param_index is not None and isinstance(param_index, int) and param_index < len(widgets_values):
                    return widgets_values[param_index]
            
            # Fallback: Use hardcoded parameter positions for known node types
            node_type = node.get('type', '')
            if node_type in ["KSampler", "KSamplerAdvanced"]:
                param_map = {
                    "seed": 0,
                    "control_after_generate": 1,
                    "steps": 2,
                    "cfg": 3,
                    "sampler_name": 4,
                    "scheduler": 5,
                    "denoise": 6
                }
                idx = param_map.get(param_name)
                if idx is not None and idx < len(widgets_values):
                    return widgets_values[idx]
            elif node_type == "CLIPTextEncode" and param_name == "text" and len(widgets_values) > 0:
                return widgets_values[0]
            elif node_type == "CheckpointLoaderSimple" and param_name == "ckpt_name" and len(widgets_values) > 0:
                return widgets_values[0]
            elif node_type in ["EmptyLatentImage", "EmptySD3LatentImage"]:
                param_map = {"width": 0, "height": 1, "batch_size": 2}
                idx = param_map.get(param_name)
                if idx is not None and idx < len(widgets_values):
                    return widgets_values[idx]
            elif node_type == "DualCLIPLoader":
                param_map = {"clip_name1": 0, "clip_name2": 1, "type": 2}
                idx = param_map.get(param_name)
                if idx is not None and idx < len(widgets_values):
                    return widgets_values[idx]
            elif node_type == "UNETLoader" and param_name == "unet_name" and len(widgets_values) > 0:
                return widgets_values[0]
            
            return None
        else:
            # API Format: Direct lookup in inputs dict
            val = node.get('inputs', {}).get(param_name)
            # Only return if it's a direct value (not a connection)
            if val is not None and not isinstance(val, list):
                return val
            return None

    def parse(self) -> List[Dict[str, Any]]:
        """
        Main entry point: Finds all samplers and processes them.
        
        Returns:
            List of sampler metadata dictionaries (one per sampler node found)
        """
        sampler_nodes = self._find_sampler_nodes()
        if not sampler_nodes:
            return []
        
        parsed_samplers = [self._process_sampler(node) for node in sampler_nodes]
        return [data for data in parsed_samplers if data is not None]

    def _find_sampler_nodes(self) -> List[Dict[str, Any]]:
        """
        Finds all nodes that perform actual sampling operations.
        Excludes helper nodes like KSamplerSelect (which only provide sampler names).
        
        Returns:
            List of sampler node dicts, sorted by ID (heuristic for workflow order)
        """
        nodes = [
            node for node in self.nodes_by_id.values()
            if isinstance(node, dict) and self._get_node_type(node) in SAMPLER_TYPES
        ]
        return sorted(nodes, key=lambda n: int(n.get('id', 0)))

    def _process_sampler(self, sampler_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Orchestrates extraction of all metadata for a single sampler.
        Each extraction method is independent to maximize data recovery.
        
        Returns:
            Complete metadata dict with all fields, or None if critical failure
        """
        try:
            # Extract each piece of metadata independently
            sampler_name, scheduler = self._extract_sampler_details(sampler_node)
            model_name = self._extract_model(sampler_node)
            pos_prompts, neg_prompts = self._extract_prompts(sampler_node)
            width, height = self._extract_dimensions(sampler_node)
            params = self._extract_parameters(sampler_node)

            # Assemble complete metadata record
            sampler_data = {
                "model_name": model_name,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "positive_prompt": "\n---\n".join(pos_prompts),  # Multi-prompt support
                "negative_prompt": "\n---\n".join(neg_prompts),
                "width": width,
                "height": height,
                **params  # cfg, steps
            }
            
            # Final type conversion pass to ensure database integrity
            for key, type_converter in [("cfg", float), ("steps", int), ("width", int), ("height", int)]:
                if key in sampler_data and sampler_data[key] is not None:
                    try:
                        sampler_data[key] = type_converter(sampler_data[key])
                    except (ValueError, TypeError):
                        sampler_data[key] = None
            
            return sampler_data
            
        except Exception as e:
            logging.debug(f"Failed to process sampler node {sampler_node.get('id')}: {e}")
            return None

    def _find_source_node(self, start_node_id: str, input_name: str, 
                          stop_at_types: Optional[List[str]] = None, max_hops=20) -> Optional[Dict[str, Any]]:
        """
        Traces a single input connection backwards through the graph.
        This is the core traversal algorithm - single-path, not BFS.
        
        Args:
            start_node_id: Node to start tracing from
            input_name: Name of input to trace (e.g., 'model', 'positive', 'latent_image')
            stop_at_types: Optional list of target node types to stop at
            max_hops: Maximum depth to prevent infinite loops
        
        Returns:
            The ultimate source node for this input, or None if not found
        """
        current_node_id = start_node_id
        
        for _ in range(max_hops):
            node = self.nodes_by_id.get(str(current_node_id))
            
            # Validation: Ensure node exists and is a dict
            if not node or not isinstance(node, dict):
                return None
            
            # Check if we found a target node type
            node_type = self._get_node_type(node)
            if stop_at_types and node_type in stop_at_types:
                return node

            # Get the source node for this input (format-agnostic)
            source_node = self._get_input_source_node(node, input_name)
            
            # If no source (direct value or not connected), we're at the end
            if source_node is None:
                return node
            
            # Continue tracing
            current_node_id = str(source_node.get('id', ''))
            if not current_node_id:
                return node
        
        return None

    def _get_widget_or_input_value(self, node: Optional[Dict[str, Any]], param_name: str) -> Any:
        """
        Universal value getter: retrieves parameter whether it's a direct widget value
        or linked from a Primitive node.
        
        This is critical for advanced workflows where users use Primitive nodes
        to make parameters dynamic or reusable.
        
        Args:
            node: Node to extract value from
            param_name: Parameter name (e.g., 'sampler_name', 'cfg', 'steps')
        
        Returns:
            The actual value (str, int, float) or None
        """
        if not node or not isinstance(node, dict):
            return None
        
        try:
            # Try to get direct widget value first
            val = self._get_widget_value(node, param_name)
            if val is not None:
                return val
            
            # For API format, also check for Primitive node connections
            if self.format == 'api':
                input_val = node.get("inputs", {}).get(param_name)
                # Check if it's a link to a Primitive node
                if isinstance(input_val, list) and len(input_val) >= 1:
                    source_node = self.nodes_by_id.get(str(input_val[0]))
                    if isinstance(source_node, dict):
                        source_type = self._get_node_type(source_node)
                        if source_type and source_type.startswith("Primitive"):
                            # Extract value from Primitive node
                            return source_node.get("inputs", {}).get("value")
        except Exception:
            pass
        
        return None

    def _extract_sampler_details(self, sampler_node: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts sampler_name and scheduler, handling both direct values and linked nodes.
        
        Returns:
            Tuple of (sampler_name, scheduler)
        """
        # Try direct values first
        sampler_name = self._get_widget_or_input_value(sampler_node, "sampler_name")
        scheduler = self._get_widget_or_input_value(sampler_node, "scheduler")

        # If sampler_name not found, check for KSamplerSelect node
        if sampler_name is None:
            sampler_source = self._find_source_node(sampler_node["id"], "sampler", SAMPLER_SELECT_NODE_TYPES)
            sampler_name = self._get_widget_or_input_value(sampler_source, "sampler_name")
        
        # If scheduler not found, check for scheduler nodes (sigmas input)
        if scheduler is None:
            scheduler_source = self._find_source_node(sampler_node["id"], "sigmas", SCHEDULER_NODE_TYPES)
            scheduler = self._get_widget_or_input_value(scheduler_source, "scheduler")
            
        return sampler_name, scheduler

    def _extract_model(self, sampler_node: Dict[str, Any]) -> Optional[str]:
        """
        Traces the model input to find the checkpoint/UNET loader.
        Handles LoRA chains by continuing to trace through them.
        
        Returns:
            Model name (without extension) or None
        """
        model_node = self._find_source_node(sampler_node["id"], "model", MODEL_LOADER_TYPES)
        if model_node:
            # Try all known model name parameters
            model_name = (
                self._get_widget_or_input_value(model_node, "ckpt_name") or
                self._get_widget_or_input_value(model_node, "unet_name") or
                self._get_widget_or_input_value(model_node, "model_name") or
                self._get_widget_or_input_value(model_node, "clip_name1")
            )
            if isinstance(model_name, str):
                # Clean up: remove path and extension
                return os.path.splitext(os.path.basename(model_name))[0]
        return None

    def _extract_prompts(self, sampler_node: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Extracts positive and negative prompts by tracing conditioning inputs.
        
        Returns:
            Tuple of (positive_prompts_list, negative_prompts_list)
        """
        pos_prompts, neg_prompts = [], []
        
        # Trace positive conditioning
        pos_node = self._find_source_node(sampler_node["id"], "positive", PROMPT_NODE_TYPES)
        pos_text = self._get_widget_or_input_value(pos_node, "text")
        if isinstance(pos_text, str) and pos_text.strip():
            pos_prompts.append(pos_text)

        # Trace negative conditioning
        neg_node = self._find_source_node(sampler_node["id"], "negative", PROMPT_NODE_TYPES)
        neg_text = self._get_widget_or_input_value(neg_node, "text")
        if isinstance(neg_text, str) and neg_text.strip():
            neg_prompts.append(neg_text)
        
        return pos_prompts, neg_prompts

    def _extract_parameters(self, sampler_node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts numeric parameters (cfg, steps) from sampler or linked nodes.
        
        Returns:
            Dict with 'cfg' and 'steps' keys
        """
        params = {
            "cfg": self._get_widget_or_input_value(sampler_node, "cfg"),
            "steps": self._get_widget_or_input_value(sampler_node, "steps"),
        }
        
        # Fallback: steps might be on the scheduler node
        if params["steps"] is None:
            scheduler_source = self._find_source_node(sampler_node["id"], "sigmas", SCHEDULER_NODE_TYPES)
            params["steps"] = self._get_widget_or_input_value(scheduler_source, "steps")
        
        return params

    def _extract_dimensions(self, sampler_node: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
        """
        Extracts output dimensions from latent generator nodes or image file.
        Includes fallback to read actual image dimensions if workflow parsing fails.
        
        Returns:
            Tuple of (width, height)
        """
        width, height = None, None
        
        # Trace latent_image input to find dimension source
        latent_node = self._find_source_node(sampler_node["id"], "latent_image")
        if latent_node:
            node_type = self._get_node_type(latent_node)
            
            # Check for known dimension-providing nodes
            if node_type in ["EmptyLatentImage", "EmptySD3LatentImage"]:
                width = self._get_widget_or_input_value(latent_node, "width")
                height = self._get_widget_or_input_value(latent_node, "height")
            elif node_type == "WanImageToVideo":
                width = self._get_widget_or_input_value(latent_node, "width")
                height = self._get_widget_or_input_value(latent_node, "height")

        # Fallback: read dimensions directly from image file
        if Image and self.file_path and (width is None or height is None):
            if self.file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                try:
                    with Image.open(self.file_path) as img:
                        width, height = img.size
                except Exception:
                    pass
        
        return width, height


def debug_save_workflow_stage(file_path: Path, stage: str, data: Any, format_info: str = "", debug_dir: str = None):
    """
    Debug helper to save workflow data at different processing stages.
    
    Args:
        file_path: Original image/video file path
        stage: Stage name (e.g., 'raw', 'parsed', 'api_format', 'filtered')
        data: Data to save (will be JSON-ified)
        format_info: Additional format information to include in filename
        debug_dir: Debug directory path (required when debugging is enabled)
    """
    if not debug_dir:
        return
    
    try:
        # Create subfolder for this file
        file_basename = os.path.splitext(file_path.name)[0]
        file_debug_dir = os.path.join(debug_dir, file_basename)
        os.makedirs(file_debug_dir, exist_ok=True)
        
        # Create filename with stage and format info
        if format_info:
            debug_filename = f"{stage}_{format_info}.json"
        else:
            debug_filename = f"{stage}.json"
        
        debug_file = os.path.join(file_debug_dir, debug_filename)
        
        # Save data as formatted JSON
        with open(debug_file, 'w', encoding='utf-8') as f:
            if isinstance(data, str):
                # If data is already a string, try to parse and re-format it
                try:
                    parsed = json.loads(data)
                    json.dump(parsed, f, indent=2, ensure_ascii=False)
                except:
                    f.write(data)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Also save a summary text file
        summary_file = os.path.join(file_debug_dir, f"{stage}_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Stage: {stage}\n")
            f.write(f"Format: {format_info}\n")
            f.write(f"Data type: {type(data).__name__}\n")
            if isinstance(data, dict):
                f.write(f"Keys: {list(data.keys())[:20]}\n")
                f.write(f"Total keys: {len(data)}\n")
                # Sample a few values
                f.write("\nSample entries:\n")
                for i, (k, v) in enumerate(list(data.items())[:3]):
                    f.write(f"  {k}: {type(v).__name__}")
                    if isinstance(v, dict):
                        f.write(f" with keys {list(v.keys())[:5]}")
                    f.write("\n")
            elif isinstance(data, list):
                f.write(f"Length: {len(data)}\n")
            elif isinstance(data, str):
                f.write(f"Length: {len(data)} chars\n")
                f.write(f"Preview: {data[:200]}...\n")
    
    except Exception as e:
        logging.debug(f"Failed to save debug workflow stage: {e}")


def extract_workflow_metadata(workflow_str: str, file_path: Path, debug_dir: str = None) -> List[Dict[str, Any]]:
    """
    High-level entry point for workflow metadata extraction.
    
    Parses a ComfyUI workflow JSON string and returns metadata for all samplers.
    Uses hybrid parser that supports both API/Prompt format and UI Workflow format natively.
    
    Args:
        workflow_str: JSON string of workflow data
        file_path: Path to the image/video file (for dimension fallback)
        debug_dir: Optional debug directory for saving workflow stages
    
    Returns:
        List of sampler metadata dictionaries (one per sampler node found)
        Empty list if parsing fails or no samplers found
    """
    if not workflow_str:
        return []
    
    try:
        # DEBUG: Save raw workflow string
        debug_save_workflow_stage(file_path, "01_raw", workflow_str, "string", debug_dir)
        
        # Parse JSON string
        workflow_data = json.loads(workflow_str)
        
        # DEBUG: Save parsed JSON
        debug_save_workflow_stage(file_path, "02_parsed", workflow_data, "json_object", debug_dir)
        
        # Format Detection - Parser supports both formats natively
        detected_format = "unknown"
        parser_data = None
        
        if isinstance(workflow_data, dict):
            # Strategy 1: Check for nested 'prompt' or 'Prompt' key
            if 'prompt' in workflow_data and isinstance(workflow_data['prompt'], dict):
                parser_data = workflow_data['prompt']
                detected_format = "nested_prompt_api"
            elif 'Prompt' in workflow_data and isinstance(workflow_data['Prompt'], dict):
                parser_data = workflow_data['Prompt']
                detected_format = "nested_Prompt_api"
            
            # Strategy 2: Check for UI Workflow format (has 'nodes' array)
            elif 'nodes' in workflow_data and isinstance(workflow_data.get('nodes'), list):
                # UI format - check for embedded API first
                if 'extra' in workflow_data and isinstance(workflow_data['extra'], dict):
                    if 'prompt' in workflow_data['extra'] and isinstance(workflow_data['extra']['prompt'], dict):
                        parser_data = workflow_data['extra']['prompt']
                        detected_format = "ui_with_embedded_api"
                
                # No embedded API - use UI format directly (hybrid parser handles this!)
                if parser_data is None:
                    parser_data = workflow_data
                    detected_format = "ui_native"
            
            # Strategy 3: Assume root is already API format
            elif workflow_data:
                # Validate it looks like API format (dict of node_id -> node_data with 'class_type')
                sample_values = [v for v in list(workflow_data.values())[:3] if isinstance(v, dict)]
                if sample_values and all('class_type' in v for v in sample_values):
                    parser_data = workflow_data
                    detected_format = "direct_api"
        
        # DEBUG: Save format detection results
        debug_save_workflow_stage(file_path, "03_format_detection", 
                                {
                                    "detected_format": detected_format,
                                    "workflow_data_type": type(workflow_data).__name__,
                                    "workflow_data_keys": list(workflow_data.keys())[:20] if isinstance(workflow_data, dict) else None,
                                    "parser_data_found": parser_data is not None,
                                    "parser_will_use": "ui_native" if (parser_data and 'nodes' in parser_data) else "api_format"
                                }, 
                                detected_format, debug_dir)
        
        # Validation: Ensure we have valid parser data
        if parser_data is None:
            logging.debug(f"Could not detect valid workflow format for {file_path.name}")
            return []
        
        # DEBUG: Save data that will be passed to parser
        debug_save_workflow_stage(file_path, "04_parser_input", parser_data, detected_format, debug_dir)
        
        # Parse with hybrid parser (handles both UI and API formats)
        parser = ComfyUIWorkflowParser(parser_data, file_path)
        result = parser.parse()
        
        # DEBUG: Save parser results
        debug_save_workflow_stage(file_path, "05_parser_output", 
                                {
                                    "format_used": parser.format,
                                    "samplers_found": len(result),
                                    "metadata": result
                                }, 
                                f"{parser.format}_{len(result)}_samplers", debug_dir)
        
        return result
        
    except (json.JSONDecodeError, TypeError) as e:
        logging.warning(f" Could not parse workflow JSON for {file_path.name}: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in workflow metadata extraction for {file_path.name}: {e}")
        logging.error("Traceback:", exc_info=True)
        return []


# --- USER CONFIGURATION ---
# Adjust the parameters in this section to customize the gallery.
#
# IMPORTANT:
# - Even on Windows, always use forward slashes ( / ) in paths, 
#   not backslashes ( \ ), to ensure compatibility.

# - It is strongly recommended to have ffmpeg installed, since some features depend on it.

# Number of files to process at once during database sync. 
# Higher values use more memory but may be faster. Lower this if you run out of memory.
BATCH_SIZE = 500

# Number of parallel processes to use for thumbnail and metadata generation.
# - Set to None to use all available CPU cores (fastest, but uses more CPU).
# - Set to 1 to disable parallel processing (slowest, like in previous versions).
# - Set to a specific number of cores (e.g., 4) to limit CPU usage on a multi-core machine.
MAX_PARALLEL_WORKERS = None

# Number of files to display per page in the gallery view
FILES_PER_PAGE = 100

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
        logging.error(f"Failed to decode key '{key}': {e}")
        return None

# --- DERIVED SETTINGS ---
DB_SCHEMA_VERSION = 22  # Schema version is static and can remain global

# --- DEBUG CONFIGURATION ---
# Set to True to enable workflow debugging (saves extracted workflows to disk)
DEBUG_WORKFLOW_EXTRACTION = True  # Change to True to enable debugging

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)

# CORS not needed for standalone version (single-origin application)
# All requests come from the same server (localhost:8008)

# Set default configuration values (will be overridden by CLI args in __main__)
# These MUST be set before any routes are accessed
app.config.setdefault('PAGE_SIZE', 100)
app.config.setdefault('THUMBNAIL_WIDTH', 300)
app.config.setdefault('WEBP_ANIMATED_FPS', 16.0)
app.config.setdefault('THUMBNAIL_CACHE_FOLDER_NAME', '.thumbnails_cache')
app.config.setdefault('SQLITE_CACHE_FOLDER_NAME', '.sqlite_cache')
app.config.setdefault('DATABASE_FILENAME', 'gallery_cache.sqlite')
app.config.setdefault('WORKFLOW_FOLDER_NAME', 'workflow_logs_success')
app.config.setdefault('VIDEO_EXTENSIONS', ['.mp4', '.mkv', '.webm', '.mov', '.avi'])
app.config.setdefault('IMAGE_EXTENSIONS', ['.png', '.jpg', '.jpeg'])
app.config.setdefault('ANIMATED_IMAGE_EXTENSIONS', ['.gif', '.webp'])
app.config.setdefault('AUDIO_EXTENSIONS', ['.mp3', '.wav', '.ogg', '.flac'])
app.config.setdefault('SPECIAL_FOLDERS', ['video', 'audio'])

# Set placeholder paths (will be properly set in initialize_gallery)
app.config.setdefault('BASE_OUTPUT_PATH', '')
app.config.setdefault('BASE_INPUT_PATH', '')
app.config.setdefault('DATABASE_FILE', '')
app.config.setdefault('THUMBNAIL_CACHE_DIR', '')
app.config.setdefault('SQLITE_CACHE_DIR', '')
app.config.setdefault('BASE_INPUT_PATH_WORKFLOW', '')
app.config.setdefault('PROTECTED_FOLDER_KEYS', set())

app.config['ALL_MEDIA_EXTENSIONS'] = (
    app.config.get('VIDEO_EXTENSIONS', []) + 
    app.config.get('IMAGE_EXTENSIONS', []) + 
    app.config.get('ANIMATED_IMAGE_EXTENSIONS', []) + 
    app.config.get('AUDIO_EXTENSIONS', [])
)

# Thread-safe caches with locks for concurrent access
# Note: gallery_view_cache removed in v1.41.0 - using SQL pagination instead
folder_config_cache = None
folder_config_cache_lock = threading.Lock()

# --- Enhanced In-Memory Cache for Filter Options ---
_filter_options_cache = {}
_cache_lock = threading.Lock()
CACHE_DURATION_SECONDS = 300  # 5 minutes

class CacheEntry:
    """Simple cache entry with timestamp and data."""
    def __init__(self, data):
        self.data = data
        self.timestamp = time.time()
        self.hits = 0
    
    def is_expired(self, max_age_seconds):
        """Check if cache entry is older than max_age_seconds."""
        return (time.time() - self.timestamp) > max_age_seconds
    
    def record_hit(self):
        """Record a cache hit for statistics."""
        self.hits += 1
        return self.data

def get_cache_stats():
    """Return cache statistics for monitoring."""
    with _cache_lock:
        # Calculate hits from CacheEntry objects
        total_hits = 0
        for entry in _filter_options_cache.values():
            if isinstance(entry, dict) and 'data' in entry:
                # Old dict-based cache format doesn't track hits (backward compatibility)
                pass
            elif hasattr(entry, 'hits'):
                # New CacheEntry format with hit tracking
                total_hits += entry.hits
        
        stats = {
            'filter_options': {
                'entries': len(_filter_options_cache),
                'hits': total_hits
            },
            'folder_config': {
                'cached': folder_config_cache is not None
            }
        }
    return stats

# Request counter for stats
request_counter = {'count': 0, 'lock': threading.Lock()}

# --- PERFORMANCE MONITORING ---
# Track request timing for performance analysis
request_timing_log = {'requests': [], 'lock': threading.Lock()}

def log_request_timing(endpoint, duration_ms):
    """Log request timing for performance monitoring."""
    with request_timing_log['lock']:
        request_timing_log['requests'].append({
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
        # Keep only last 1000 requests to prevent memory bloat
        if len(request_timing_log['requests']) > 1000:
            request_timing_log['requests'] = request_timing_log['requests'][-1000:]

# --- INITIALIZATION GUARD DECORATOR (Issue #5) ---
from functools import wraps

def require_initialization(f):
    """Decorator to ensure initialize_gallery() was called before accessing route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if DATABASE_FILE is properly initialized (not empty placeholder)
        db_file = app.config.get('DATABASE_FILE', '')
        if not db_file or db_file.strip() == '':
            return jsonify({
                'error': 'Gallery not initialized',
                'message': 'initialize_gallery() must be called before accessing routes'
            }), 503  # Service Unavailable
        
        # Performance timing
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            log_request_timing(f.__name__, duration_ms)
            if duration_ms > 1000:  # Log slow requests (>1s)
                logging.warning(f"Slow request: {f.__name__} took {duration_ms:.2f}ms")
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logging.error(f"Request {f.__name__} failed after {duration_ms:.2f}ms: {e}")
            raise
    return decorated_function


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
            logging.warning(f" Manual ffprobe path '{manual_path}' is invalid: {e}")
    base_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    try:
        result = subprocess.run([base_name, "-version"], capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        return base_name
    except Exception as e:
        logging.warning(f"ffprobe not found in PATH: {e}")
    logging.warning("ffprobe not found. Video metadata analysis will be disabled.")
    return None

def _validate_and_get_workflow(json_string):
    """
    Validates and extracts workflow data from JSON string.
    Handles both Workflow and Prompt/API formats by returning whichever is valid.
    """
    try:
        data = json.loads(json_string)
        
        # Try to get workflow data from nested structure first
        # Check for 'workflow' key (capitalized or lowercase)
        workflow_data = data.get('workflow') or data.get('Workflow') or data.get('prompt') or data.get('Prompt')
        
        # If we got nested data, use that, otherwise use root
        if workflow_data is None:
            workflow_data = data
        
        # Check if it's workflow format (has 'nodes' array)
        if isinstance(workflow_data, dict) and 'nodes' in workflow_data and isinstance(workflow_data['nodes'], list):
            # Valid workflow format - return as-is
            return json.dumps(workflow_data)
        
        # For API/Prompt format, return the data as-is without conversion
        # The metadata extraction will handle it differently
        if isinstance(workflow_data, dict) and workflow_data:
            # Check if it looks like API format (has dict with node data)
            # Just validate it's not empty and return it
            return json.dumps(data)
        
        return None
    except json.JSONDecodeError as e:
        logging.debug(f"Invalid JSON in workflow: {e}")
        return None
    except Exception as e:
        logging.debug(f"Failed to validate workflow JSON: {e}")
        logging.debug("Traceback:", exc_info=True)
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
        logging.debug(f"Error scanning bytes for workflow: {e}")
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
                logging.debug(f"Error extracting workflow from video metadata: {e}")
    else:
        try:
            with Image.open(filepath) as img:
                # Check for both lowercase and capitalized keys (PNG metadata can vary)
                workflow_str = (img.info.get('workflow') or img.info.get('Workflow') or 
                               img.info.get('prompt') or img.info.get('Prompt'))
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
            logging.debug(f"Error extracting workflow from image metadata: {e}")

    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        json_str = _scan_bytes_for_workflow(content)
        if json_str:
            workflow = _validate_and_get_workflow(json_str)
            if workflow: return workflow
    except Exception as e:
        logging.debug(f"Error scanning file content for workflow: {e}")

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
        logging.debug(f"Error searching for workflow log file: {e}")
                
    return None


def is_webp_animated(filepath):
    try:
        with Image.open(filepath) as img: return getattr(img, 'is_animated', False)
    except Exception as e:
        logging.debug(f"Error checking if WebP is animated: {e}")
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
            logging.debug(f"Error getting image dimensions for {filepath}: {e}")
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
            logging.debug(f"Error analyzing video metadata for {filepath}: {e}")
    elif details['type'] == 'animated_image':
        try:
            with Image.open(filepath) as img:
                if getattr(img, 'is_animated', False):
                    if ext_lower == '.gif': total_duration_sec = sum(frame.info.get('duration', 100) for frame in ImageSequence.Iterator(img)) / 1000
                    elif ext_lower == '.webp': total_duration_sec = getattr(img, 'n_frames', 1) / app.config['WEBP_ANIMATED_FPS']
        except Exception as e:
            logging.debug(f"Error analyzing animated image duration for {filepath}: {e}")
    if total_duration_sec > 0: details['duration'] = format_duration(total_duration_sec)
    return details

def create_thumbnail(filepath, file_hash, file_type):
    """Create thumbnail for image or video file (optimized)."""
    thumbnail_cache_dir = app.config['THUMBNAIL_CACHE_DIR']
    thumbnail_width = app.config['THUMBNAIL_WIDTH']
    thumbnail_height = thumbnail_width * 2
    
    if file_type in ('image', 'animated_image'):
        try:
            with Image.open(filepath) as img:
                fmt = 'gif' if img.format == 'GIF' else 'webp' if img.format == 'WEBP' else 'jpeg'
                cache_path = os.path.join(thumbnail_cache_dir, f"{file_hash}.{fmt}")
                
                if file_type == 'animated_image' and getattr(img, 'is_animated', False):
                    frames = [fr.copy() for fr in ImageSequence.Iterator(img)]
                    if frames:
                        # Resize all frames
                        for frame in frames: 
                            frame.thumbnail((thumbnail_width, thumbnail_height), Image.Resampling.LANCZOS)
                        
                        # Convert to RGB
                        processed_frames = [frame.convert('RGBA').convert('RGB') for frame in frames]
                        if processed_frames:
                            processed_frames[0].save(
                                cache_path, save_all=True, append_images=processed_frames[1:], 
                                duration=img.info.get('duration', 100), 
                                loop=img.info.get('loop', 0), 
                                optimize=True
                            )
                else:
                    img.thumbnail((thumbnail_width, thumbnail_height), Image.Resampling.LANCZOS)
                    if img.mode != 'RGB': 
                        img = img.convert('RGB')
                    img.save(cache_path, 'JPEG', quality=85)
                return cache_path
        except Exception as e: 
            logging.error(f"Pillow: Could not create thumbnail for {os.path.basename(filepath)}: {e}")
            
    elif file_type == 'video':
        try:
            cap = cv2.VideoCapture(filepath)
            success, frame = cap.read()
            cap.release()
            if success:
                cache_path = os.path.join(thumbnail_cache_dir, f"{file_hash}.jpeg")
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img.thumbnail((thumbnail_width, thumbnail_height), Image.Resampling.LANCZOS)
                img.save(cache_path, 'JPEG', quality=80)
                return cache_path
        except Exception as e: 
            logging.error(f"OpenCV: Could not create thumbnail for {os.path.basename(filepath)}: {e}")
    return None

def process_single_file(filepath, thumbnail_cache_dir, thumbnail_width, video_exts, image_exts, animated_exts, audio_exts, webp_animated_fps, base_input_path_workflow, debug_dir=None):
    """
    Worker function to perform all heavy processing for a single file.
    Designed to be run in a parallel process pool.
    
    This function is adapted to work with multiprocessing by accepting all necessary
    configuration values as parameters instead of relying on app.config.
    
    Args:
        debug_dir: Optional debug directory for workflow extraction debugging
    """
    try:
        mtime = os.path.getmtime(filepath)
        
        # Analyze metadata (inline version to avoid app.config dependency)
        details = {'type': 'unknown', 'duration': '', 'dimensions': '', 'has_workflow': 0}
        ext_lower = os.path.splitext(filepath)[1].lower()
        
        if ext_lower in image_exts:
            details['type'] = 'image'
        elif ext_lower in animated_exts:
            details['type'] = 'animated_image'
        elif ext_lower in video_exts:
            details['type'] = 'video'
        elif ext_lower in audio_exts:
            details['type'] = 'audio'
        
        # Special handling for WebP
        if details['type'] == 'animated_image' and ext_lower == '.webp':
            try:
                with Image.open(filepath) as img:
                    details['type'] = 'animated_image' if getattr(img, 'is_animated', False) else 'image'
            except:
                pass
        
        # Get dimensions
        if 'image' in details['type']:
            try:
                with Image.open(filepath) as img:
                    details['dimensions'] = f"{img.width}x{img.height}"
            except:
                pass
        
        # Check for workflow (simplified version)
        # Note: We do a simple check here. Full extraction is expensive and done later if needed.
        workflow_found = False
        try:
            if ext_lower not in video_exts:
                with Image.open(filepath) as img:
                    # Check for both lowercase and capitalized keys (PNG metadata can vary)
                    if (img.info.get('workflow') or img.info.get('Workflow') or 
                        img.info.get('prompt') or img.info.get('Prompt')):
                        workflow_found = True
        except:
            pass
        
        if not workflow_found:
            # Check for workflow log file
            try:
                base_filename = os.path.basename(filepath)
                search_pattern = os.path.join(base_input_path_workflow, f"{base_filename}*.json")
                if glob.glob(search_pattern):
                    workflow_found = True
            except:
                pass
        
        details['has_workflow'] = 1 if workflow_found else 0
        
        # Get duration for video/animated
        total_duration_sec = 0
        if details['type'] == 'video':
            try:
                cap = cv2.VideoCapture(filepath)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if fps > 0 and count > 0:
                        total_duration_sec = count / fps
                    details['dimensions'] = f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                    cap.release()
            except:
                pass
        elif details['type'] == 'animated_image':
            try:
                with Image.open(filepath) as img:
                    if getattr(img, 'is_animated', False):
                        if ext_lower == '.gif':
                            total_duration_sec = sum(frame.info.get('duration', 100) for frame in ImageSequence.Iterator(img)) / 1000
                        elif ext_lower == '.webp':
                            total_duration_sec = getattr(img, 'n_frames', 1) / webp_animated_fps
            except:
                pass
        
        if total_duration_sec > 0:
            m, s = divmod(int(total_duration_sec), 60)
            h, m = divmod(m, 60)
            details['duration'] = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        
        # Create thumbnail
        file_hash_for_thumbnail = hashlib.md5((filepath + str(mtime)).encode()).hexdigest()
        
        if not glob.glob(os.path.join(thumbnail_cache_dir, f"{file_hash_for_thumbnail}.*")):
            # Inline thumbnail creation
            file_type = details['type']
            if file_type in ['image', 'animated_image']:
                try:
                    with Image.open(filepath) as img:
                        fmt = 'gif' if img.format == 'GIF' else 'webp' if img.format == 'WEBP' else 'jpeg'
                        cache_path = os.path.join(thumbnail_cache_dir, f"{file_hash_for_thumbnail}.{fmt}")
                        if file_type == 'animated_image' and getattr(img, 'is_animated', False):
                            frames = [fr.copy() for fr in ImageSequence.Iterator(img)]
                            if frames:
                                for frame in frames:
                                    frame.thumbnail((thumbnail_width, thumbnail_width * 2), Image.Resampling.LANCZOS)
                                processed_frames = [frame.convert('RGBA').convert('RGB') for frame in frames]
                                if processed_frames:
                                    processed_frames[0].save(cache_path, save_all=True, append_images=processed_frames[1:], 
                                                           duration=img.info.get('duration', 100), loop=img.info.get('loop', 0), optimize=True)
                        else:
                            img.thumbnail((thumbnail_width, thumbnail_width * 2), Image.Resampling.LANCZOS)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            img.save(cache_path, 'JPEG', quality=85)
                except:
                    pass
            elif file_type == 'video':
                try:
                    cap = cv2.VideoCapture(filepath)
                    success, frame = cap.read()
                    cap.release()
                    if success:
                        cache_path = os.path.join(thumbnail_cache_dir, f"{file_hash_for_thumbnail}.jpeg")
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)
                        img.thumbnail((thumbnail_width, thumbnail_width * 2), Image.Resampling.LANCZOS)
                        img.save(cache_path, 'JPEG', quality=80)
                except:
                    pass
        
        file_id = hashlib.md5(filepath.encode()).hexdigest()
        
        # Extract workflow metadata if workflow is present
        # Returns a LIST of sampler metadata dicts (one per sampler node found)
        workflow_metadata_list = []
        extraction_status = {
            'has_workflow': details['has_workflow'],
            'workflow_extracted': False,
            'metadata_extracted': False,
            'sampler_count': 0,
            'parse_error': None
        }
        
        if details['has_workflow']:
            try:
                workflow_json = extract_workflow(filepath)
                if workflow_json:
                    extraction_status['workflow_extracted'] = True
                    # Pass Path object for dimension fallback and debug directory
                    workflow_metadata_list = extract_workflow_metadata(workflow_json, Path(filepath), debug_dir)
                    if workflow_metadata_list:
                        extraction_status['metadata_extracted'] = True
                        extraction_status['sampler_count'] = len(workflow_metadata_list)
            except Exception as e:
                extraction_status['parse_error'] = str(e)

        # --- NEW: Logic for Prompt Preview and Sampler Names ---
        prompt_preview = None
        sampler_names = ""
        try:
            if workflow_metadata_list:
                # For prompt preview, take the positive prompt from the first sampler
                first_sampler = workflow_metadata_list[0]
                if first_sampler and first_sampler.get('positive_prompt'):
                    preview_text = str(first_sampler.get('positive_prompt') or '').strip()
                    if len(preview_text) > 150:
                        prompt_preview = preview_text[:150] + '...'
                    else:
                        prompt_preview = preview_text

                # For sampler names, collect all unique names (optimized: no need for list())
                unique_samplers = sorted({s.get('sampler_name') for s in workflow_metadata_list if s and s.get('sampler_name')})
                sampler_names = ', '.join(unique_samplers)
        except Exception:
            # Keep defaults if anything goes wrong
            prompt_preview = prompt_preview
            sampler_names = sampler_names
        # --- End of New Logic ---

        return (
            file_id, filepath, mtime, os.path.basename(filepath),
            details['type'], details['duration'], details['dimensions'], details['has_workflow'],
            workflow_metadata_list,  # Returns LIST of metadata dicts (one per sampler)
            extraction_status,  # Statistics for reporting
            prompt_preview,  # NEW return value
            sampler_names    # NEW return value
        )
    except Exception as e:
        logging.error(f"Failed to process file {os.path.basename(filepath)} in worker: {e}")
        return None

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        db_file = app.config.get('DATABASE_FILE', '')
        
        # Enhanced validation (Issue #4)
        if not db_file or db_file.strip() == '':
            raise RuntimeError("Gallery not initialized - DATABASE_FILE not configured. Call initialize_gallery() first.")
        
        # Verify it's an absolute path
        if not os.path.isabs(db_file):
            raise RuntimeError(f"DATABASE_FILE must be an absolute path, got: {db_file}")
        
        # Ensure parent directory exists
        db_dir = os.path.dirname(db_file)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logging.info(f"Created database directory: {db_dir}")
            except (OSError, PermissionError) as e:
                raise RuntimeError(f"Cannot create database directory {db_dir}: {e}")
        
        # Open database connection with optimizations
        g.db = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES, timeout=30.0)
        g.db.row_factory = sqlite3.Row
        
        # Enable performance optimizations
        cursor = g.db.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache (negative means KB)
        cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
        cursor.close()
        
    return g.db

def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def build_metadata_filter_subquery(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    Build an EXISTS subquery for filtering files by workflow metadata.
    
    This prevents duplicate file results when multiple samplers match filters.
    The subquery returns TRUE if ANY sampler in the file matches ALL filter criteria.
    
    Args:
        filters: Dict with keys: model, sampler, scheduler, cfg_min, cfg_max, 
                steps_min, steps_max, width_min, width_max, height_min, height_max
    
    Returns:
        Tuple of (subquery_sql_string, [params_list])
    """
    conditions: List[str] = []
    params: List[Any] = []
    
    # Exact string matches
    if filters.get('model'):
        conditions.append("wm.model_name = ?")
        params.append(filters['model'])
    
    if filters.get('sampler'):
        conditions.append("wm.sampler_name = ?")
        params.append(filters['sampler'])
    
    if filters.get('scheduler'):
        conditions.append("wm.scheduler = ?")
        params.append(filters['scheduler'])
    
    # Numeric range filters
    if filters.get('cfg_min') is not None:
        conditions.append("wm.cfg >= ?")
        params.append(float(filters['cfg_min']))
    
    if filters.get('cfg_max') is not None:
        conditions.append("wm.cfg <= ?")
        params.append(float(filters['cfg_max']))
    
    if filters.get('steps_min') is not None:
        conditions.append("wm.steps >= ?")
        params.append(int(filters['steps_min']))
    
    if filters.get('steps_max') is not None:
        conditions.append("wm.steps <= ?")
        params.append(int(filters['steps_max']))
    
    if filters.get('width_min') is not None:
        conditions.append("wm.width >= ?")
        params.append(int(filters['width_min']))
    
    if filters.get('width_max') is not None:
        conditions.append("wm.width <= ?")
        params.append(int(filters['width_max']))
    
    if filters.get('height_min') is not None:
        conditions.append("wm.height >= ?")
        params.append(int(filters['height_min']))
    
    if filters.get('height_max') is not None:
        conditions.append("wm.height <= ?")
        params.append(int(filters['height_max']))
    
    # Build EXISTS subquery
    if conditions:
        where_clause = " AND ".join(conditions)
        subquery = f"EXISTS (SELECT 1 FROM workflow_metadata wm WHERE wm.file_id = f.id AND {where_clause})"
        return (subquery, params)
    else:
        return ("", [])

def _build_filter_conditions(args) -> Tuple[List[str], List[Any]]:
    """
    Builds a list of SQL conditions and parameters based on request arguments.
    This centralizes the filtering logic for gallery_view and load_more.

    Args:
        args: A dictionary-like object containing request arguments (e.g., request.args).

    Returns:
        A tuple of (conditions_list, params_list).
    """
    conditions: List[str] = []
    params: List[Any] = []

    # Gather workflow metadata filters
    metadata_filters: Dict[str, Any] = {}
    if args.get('filter_model', '').strip():
        metadata_filters['model'] = args.get('filter_model').strip()
    if args.get('filter_sampler', '').strip():
        metadata_filters['sampler'] = args.get('filter_sampler').strip()
    if args.get('filter_scheduler', '').strip():
        metadata_filters['scheduler'] = args.get('filter_scheduler').strip()
    if args.get('filter_cfg_min', type=float) is not None:
        metadata_filters['cfg_min'] = args.get('filter_cfg_min', type=float)
    if args.get('filter_cfg_max', type=float) is not None:
        metadata_filters['cfg_max'] = args.get('filter_cfg_max', type=float)
    if args.get('filter_steps_min', type=int) is not None:
        metadata_filters['steps_min'] = args.get('filter_steps_min', type=int)
    if args.get('filter_steps_max', type=int) is not None:
        metadata_filters['steps_max'] = args.get('filter_steps_max', type=int)
    if args.get('filter_width_min', type=int) is not None:
        metadata_filters['width_min'] = args.get('filter_width_min', type=int)
    if args.get('filter_width_max', type=int) is not None:
        metadata_filters['width_max'] = args.get('filter_width_max', type=int)
    if args.get('filter_height_min', type=int) is not None:
        metadata_filters['height_min'] = args.get('filter_height_min', type=int)
    if args.get('filter_height_max', type=int) is not None:
        metadata_filters['height_max'] = args.get('filter_height_max', type=int)

    # Build EXISTS subquery for metadata filters
    if metadata_filters:
        subquery_sql, subquery_params = build_metadata_filter_subquery(metadata_filters)
        if subquery_sql:
            conditions.append(subquery_sql)
            params.extend(subquery_params)

    search_term = args.get('search', '').strip()
    if search_term:
        conditions.append("f.name LIKE ?")
        params.append(f"%{search_term}%")
    
    if args.get('favorites', 'false').lower() == 'true':
        conditions.append("f.is_favorite = 1")

    selected_prefixes = args.getlist('prefix')
    if selected_prefixes:
        prefix_conditions = [f"f.name LIKE ?" for p in selected_prefixes if p.strip()]
        if prefix_conditions:
            conditions.append(f"({' OR '.join(prefix_conditions)})")
            params.extend([f"{p.strip()}_%" for p in selected_prefixes if p.strip()])

    selected_extensions = args.getlist('extension')
    if selected_extensions:
        ext_conditions = [f"f.name LIKE ?" for ext in selected_extensions if ext.strip()]
        if ext_conditions:
            conditions.append(f"({' OR '.join(ext_conditions)})")
            params.extend([f"%.{ext.lstrip('.').lower()}" for ext in selected_extensions if ext.strip()])

    return conditions, params

def init_db(conn=None):
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE, mtime REAL NOT NULL,
            name TEXT NOT NULL, type TEXT, duration TEXT, dimensions TEXT,
            has_workflow INTEGER, is_favorite INTEGER DEFAULT 0,
            prompt_preview TEXT, sampler_names TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS workflow_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            sampler_index INTEGER DEFAULT 0,
            model_name TEXT,
            sampler_name TEXT,
            scheduler TEXT,
            cfg REAL,
            steps INTEGER,
            positive_prompt TEXT,
            negative_prompt TEXT,
            width INTEGER,
            height INTEGER,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        )
    ''')
    # Create indices for efficient filtering
    # Workflow metadata indices
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_file_sampler ON workflow_metadata(file_id, sampler_index)')  # Prevent duplicate samplers
    conn.execute('CREATE INDEX IF NOT EXISTS idx_model_name ON workflow_metadata(model_name)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_sampler_name ON workflow_metadata(sampler_name)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_scheduler ON workflow_metadata(scheduler)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_cfg ON workflow_metadata(cfg)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_steps ON workflow_metadata(steps)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_width ON workflow_metadata(width)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_height ON workflow_metadata(height)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_file_id ON workflow_metadata(file_id)')  # Performance: EXISTS subquery optimization
    
    # Files table indices (CRITICAL PERFORMANCE - v1.41.0)
    # These enable fast search, sort, and filter operations
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_name ON files(name)')  # Fast name search
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_mtime ON files(mtime DESC)')  # Fast date sorting
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_type ON files(type)')  # Fast type filtering
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_favorite ON files(is_favorite)')  # Fast favorite filtering
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)')  # Fast folder filtering
    
    conn.commit()
    if close_conn: conn.close()
    
def get_dynamic_folder_config(force_refresh=False):
    """Get folder configuration with caching (optimized)."""
    global folder_config_cache
    
    with folder_config_cache_lock:
        # Check cache first
        if folder_config_cache is not None and not force_refresh:
            return folder_config_cache

        logging.info("Refreshing folder configuration by scanning directory tree...")
        
        # CRITICAL: All folder scanning must happen inside the lock to prevent race conditions
        base_path = app.config['BASE_OUTPUT_PATH']
        
        # Validation: Ensure BASE_OUTPUT_PATH is initialized (fixes Issue #2)
        if not base_path or base_path.strip() == '':
            logging.error("BASE_OUTPUT_PATH is not initialized. Call initialize_gallery() first.")
            return {'_root_': {
                'display_name': 'Main',
                'path': '',
                'relative_path': '',
                'parent': None,
                'children': [],
                'mtime': time.time()
            }}
        
        base_path_normalized = os.path.normpath(base_path).replace('\\', '/')
        
        try:
            root_mtime = os.path.getmtime(base_path)
        except (OSError, PermissionError) as e:
            logging.warning(f"Could not get mtime for base path: {e}")
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

        # Optimization: Pre-compile exclusion set
        excluded_dirs = {app.config['THUMBNAIL_CACHE_FOLDER_NAME'], app.config['SQLITE_CACHE_FOLDER_NAME']}
        
        try:
            all_folders = {}
            for dirpath, dirnames, _ in os.walk(base_path):
                # Filter out excluded directories in-place (more efficient)
                dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
                for dirname in dirnames:
                    full_path = os.path.normpath(os.path.join(dirpath, dirname)).replace('\\', '/')
                    relative_path = os.path.relpath(full_path, base_path).replace('\\', '/')
                    try:
                        mtime = os.path.getmtime(full_path)
                    except (OSError, PermissionError) as e:
                        logging.warning(f"Could not get mtime for {full_path}: {e}")
                        mtime = time.time()
                    
                    all_folders[relative_path] = {
                        'full_path': full_path,
                        'display_name': dirname,
                        'mtime': mtime
                    }

            # Sort by depth (number of path separators)
            sorted_paths = sorted(all_folders.keys(), key=lambda x: x.count('/'))

            for rel_path in sorted_paths:
                folder_data = all_folders[rel_path]
                key = path_to_key(rel_path)
                parent_rel_path = os.path.dirname(rel_path).replace('\\', '/')
                parent_key = '_root_' if parent_rel_path in ('.', '') else path_to_key(parent_rel_path)

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
        except (FileNotFoundError, OSError, PermissionError) as e:
            logging.warning(f" Error scanning directory '{base_path}': {e}")
        
        # Update cache atomically before releasing lock
        folder_config_cache = dynamic_config
        return dynamic_config
    
def full_sync_database(conn):
    logging.info(" Starting full file scan...")
    start_time = time.time()

    all_folders = get_dynamic_folder_config(force_refresh=True)
    db_files = {row['path']: row['mtime'] for row in conn.execute('SELECT path, mtime FROM files').fetchall()}
    
    disk_files = {}
    logging.info(" Scanning directories on disk...")
    for folder_data in all_folders.values():
        folder_path = folder_data['path']
        if not os.path.isdir(folder_path): 
            continue
        try:
            for name in os.listdir(folder_path):
                filepath = os.path.join(folder_path, name)
                if os.path.isfile(filepath) and os.path.splitext(name)[1].lower() not in ['.json', '.sqlite']:
                    disk_files[filepath] = os.path.getmtime(filepath)
        except OSError as e:
            logging.warning(f" Could not access folder {folder_path}: {e}")
            
    db_paths = set(db_files.keys())
    disk_paths = set(disk_files.keys())
    
    to_delete = db_paths - disk_paths
    to_add = disk_paths - db_paths
    to_check = disk_paths & db_paths
    to_update = {path for path in to_check if int(disk_files.get(path, 0)) > int(db_files.get(path, 0))}
    
    files_to_process = list(to_add.union(to_update))
    
    if files_to_process:
        logging.info(f"Processing {len(files_to_process)} files in parallel using up to {MAX_PARALLEL_WORKERS or 'all'} CPU cores...")
        
        # Gather config values for worker processes
        thumbnail_cache_dir = app.config['THUMBNAIL_CACHE_DIR']
        thumbnail_width = app.config['THUMBNAIL_WIDTH']
        video_exts = app.config['VIDEO_EXTENSIONS']
        image_exts = app.config['IMAGE_EXTENSIONS']
        animated_exts = app.config['ANIMATED_IMAGE_EXTENSIONS']
        audio_exts = app.config['AUDIO_EXTENSIONS']
        webp_animated_fps = app.config['WEBP_ANIMATED_FPS']
        base_input_path_workflow = app.config['BASE_INPUT_PATH_WORKFLOW']
        
        # Set up debug directory if debugging enabled
        debug_dir = None
        if DEBUG_WORKFLOW_EXTRACTION:
            debug_dir = os.path.join(app.config['BASE_OUTPUT_PATH'], 'workflow_debug')
            os.makedirs(debug_dir, exist_ok=True)
        
        results = []
        stats = {
            'total_processed': 0,
            'failed_files': 0,
            'files_with_workflows': 0,
            'workflows_extracted': 0,
            'workflows_not_extracted': 0,
            'metadata_extracted': 0,
            'metadata_failed': 0,
            'total_samplers': 0,
            'parse_errors': [],
            'files_without_metadata': []
        }
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
            # Submit all jobs to the pool
            futures = {
                executor.submit(
                    process_single_file, path, thumbnail_cache_dir, thumbnail_width,
                    video_exts, image_exts, animated_exts, audio_exts, webp_animated_fps,
                    base_input_path_workflow, debug_dir
                ): path for path in files_to_process
            }
            
            # Create the progress bar with the correct total
            with tqdm(total=len(files_to_process), desc="Processing files", unit="file") as pbar:
                # Iterate over the jobs as they are COMPLETED
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
                        stats['total_processed'] += 1
                        
                        # Collect statistics from extraction_status (10th element)
                        if len(result) >= 10:
                            extraction_status = result[9]
                            if extraction_status['has_workflow']:
                                stats['files_with_workflows'] += 1
                                
                                if extraction_status['workflow_extracted']:
                                    stats['workflows_extracted'] += 1
                                else:
                                    stats['workflows_not_extracted'] += 1
                                
                                if extraction_status['metadata_extracted']:
                                    stats['metadata_extracted'] += 1
                                    stats['total_samplers'] += extraction_status['sampler_count']
                                else:
                                    stats['metadata_failed'] += 1
                                    if extraction_status['workflow_extracted']:
                                        # Workflow extracted but no metadata found
                                        stats['files_without_metadata'].append(result[3])  # filename
                                
                                if extraction_status['parse_error']:
                                    stats['parse_errors'].append({
                                        'file': result[3],
                                        'error': extraction_status['parse_error']
                                    })
                    else:
                        stats['failed_files'] += 1
                    # Update the bar by 1 step for each completed job
                    pbar.update(1)

        # Log comprehensive statistics
        logging.info("="*80)
        logging.info("WORKFLOW METADATA EXTRACTION STATISTICS")
        logging.info("="*80)
        logging.info(f"Total files processed:              {stats['total_processed']}")
        logging.info(f"Files that failed to process:       {stats['failed_files']}")
        logging.info("\nWorkflow Detection:")
        logging.info(f"  Files with embedded workflows:    {stats['files_with_workflows']}")
        logging.info(f"  Workflows successfully extracted: {stats['workflows_extracted']}")
        logging.info(f"  Workflows that couldn't be read:  {stats['workflows_not_extracted']}")
        logging.info("\nMetadata Extraction:")
        logging.info(f"  Files with metadata extracted:    {stats['metadata_extracted']}")
        logging.info(f"  Files with no metadata found:     {stats['metadata_failed']}")
        logging.info(f"  Total samplers found:             {stats['total_samplers']}")
        
        if stats['metadata_extracted'] > 0:
            avg_samplers = stats['total_samplers'] / stats['metadata_extracted']
            logging.info(f"  Average samplers per workflow:    {avg_samplers:.2f}")
        
        # Show parse errors (limit to first 10)
        if stats['parse_errors']:
            logging.info(f"\nParse Errors ({len(stats['parse_errors'])} total):")
            for i, error_info in enumerate(stats['parse_errors'][:10]):
                logging.info(f"  {i+1}. {error_info['file']}: {error_info['error'][:80]}")
            if len(stats['parse_errors']) > 10:
                logging.info(f"  ... and {len(stats['parse_errors']) - 10} more")
        
        # Show files where workflow was found but no metadata extracted (limit to first 10)
        if stats['files_without_metadata']:
            logging.info(f"\nFiles with workflows but no metadata extracted ({len(stats['files_without_metadata'])} total):")
            for i, filename in enumerate(stats['files_without_metadata'][:10]):
                logging.info(f"  {i+1}. {filename}")
            if len(stats['files_without_metadata']) > 10:
                logging.info(f"  ... and {len(stats['files_without_metadata']) - 10} more")
        
        logging.info("="*80 + "\n")

        if results:
            print(f"INFO: Inserting {len(results)} processed records into the database...")
            files_data = []
            metadata_data = []
            file_ids_with_metadata = set()
            
            for result in results:
                # result now has 12 elements: (id, path, mtime, name, type, duration, dimensions, has_workflow, workflow_metadata_list, extraction_status, prompt_preview, sampler_names)
                file_id = result[0]
                # Build file tuple: first 8 standard fields + prompt_preview and sampler_names (positions 10 and 11)
                file_tuple = result[:8] + tuple(result[10:12])
                workflow_metadata_list = result[8]  # 9th element is LIST of metadata dicts
                
                files_data.append(file_tuple)
                
                # Process each sampler's metadata
                if workflow_metadata_list and isinstance(workflow_metadata_list, list):
                    file_ids_with_metadata.add(file_id)
                    for sampler_index, sampler_meta in enumerate(workflow_metadata_list):
                        metadata_data.append((
                            file_id,
                            sampler_index,
                            sampler_meta.get('model_name'),
                            sampler_meta.get('sampler_name'),
                            sampler_meta.get('scheduler'),
                            sampler_meta.get('cfg'),
                            sampler_meta.get('steps'),
                            sampler_meta.get('positive_prompt'),
                            sampler_meta.get('negative_prompt'),
                            sampler_meta.get('width'),
                            sampler_meta.get('height')
                        ))
            
            # Insert files in batches
            for i in range(0, len(files_data), BATCH_SIZE):
                batch = files_data[i:i + BATCH_SIZE]
                conn.executemany(
                    "INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow, prompt_preview, sampler_names) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    batch
                )
                conn.commit()
            
            # For workflow metadata, use DELETE-then-INSERT pattern to handle variable sampler counts
            if metadata_data:
                print(f"INFO: Updating workflow metadata for {len(file_ids_with_metadata)} files ({len(metadata_data)} total samplers)...")
                
                # Delete old metadata for files being updated
                if file_ids_with_metadata:
                    placeholders = ','.join(['?'] * len(file_ids_with_metadata))
                    conn.execute(f"DELETE FROM workflow_metadata WHERE file_id IN ({placeholders})", list(file_ids_with_metadata))
                    conn.commit()
                
                # Insert new metadata in batches
                for i in range(0, len(metadata_data), BATCH_SIZE):
                    batch = metadata_data[i:i + BATCH_SIZE]
                    conn.executemany(
                        "INSERT INTO workflow_metadata (file_id, sampler_index, model_name, sampler_name, scheduler, cfg, steps, positive_prompt, negative_prompt, width, height) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        batch
                    )
                    conn.commit()

    if to_delete:
        print(f"INFO: Removing {len(to_delete)} obsolete file entries from the database...")
        conn.executemany("DELETE FROM files WHERE path = ?", [(p,) for p in to_delete])
        conn.commit()

    print(f"INFO: Full scan completed in {time.time() - start_time:.2f} seconds.")

def sync_folder_internal(folder_path):
    """Non-generator version for internal synchronization (Issue #8 fix)."""
    try:
        conn = get_db()
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
            return  # Nothing to do
            
        files_to_process = list(files_to_add.union(files_to_update))
            
        if files_to_process:
            data_to_upsert = []
            metadata_to_upsert = []
            file_ids_with_metadata = set()
            
            for path in files_to_process:
                metadata = analyze_file_metadata(path)
                file_hash = hashlib.md5((path + str(disk_files[path])).encode()).hexdigest()
                if not glob.glob(os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*")): 
                    create_thumbnail(path, file_hash, metadata['type'])
                
                file_id = hashlib.md5(path.encode()).hexdigest()

                # --- NEW: Extract preview data here as well ---
                prompt_preview = None
                sampler_names = ""
                workflow_meta_list = []
                if metadata['has_workflow']:
                    try:
                        workflow_json = extract_workflow(path)
                        if workflow_json:
                            workflow_meta_list = extract_workflow_metadata(workflow_json, Path(path))
                            if workflow_meta_list:
                                first_sampler = workflow_meta_list[0]
                                if first_sampler and first_sampler.get('positive_prompt'):
                                    preview_text = str(first_sampler.get('positive_prompt') or '').strip()
                                    prompt_preview = (preview_text[:150] + '...') if len(preview_text) > 150 else preview_text
                                unique_samplers = sorted(list({s.get('sampler_name') for s in workflow_meta_list if s and s.get('sampler_name')}))
                                sampler_names = ', '.join(unique_samplers)
                    except Exception as e:
                        logging.debug(f"Error extracting workflow metadata for {os.path.basename(path)}: {e}")
                # --- End new logic ---

                data_to_upsert.append((file_id, path, disk_files[path], os.path.basename(path), metadata['type'], metadata['duration'], metadata['dimensions'], metadata['has_workflow'], prompt_preview, sampler_names))
                
                # Extract workflow metadata if present (returns LIST of sampler metadata)
                if metadata['has_workflow']:
                    try:
                        workflow_json = extract_workflow(path)
                        if workflow_json:
                            workflow_meta_list = extract_workflow_metadata(workflow_json, Path(path))
                            if workflow_meta_list and isinstance(workflow_meta_list, list):
                                file_ids_with_metadata.add(file_id)
                                for sampler_index, sampler_meta in enumerate(workflow_meta_list):
                                    metadata_to_upsert.append((
                                        file_id,
                                        sampler_index,
                                        sampler_meta.get('model_name'),
                                        sampler_meta.get('sampler_name'),
                                        sampler_meta.get('scheduler'),
                                        sampler_meta.get('cfg'),
                                        sampler_meta.get('steps'),
                                        sampler_meta.get('positive_prompt'),
                                        sampler_meta.get('negative_prompt'),
                                        sampler_meta.get('width'),
                                        sampler_meta.get('height')
                                    ))
                    except Exception as e:
                        logging.debug(f"Error extracting workflow metadata for {os.path.basename(path)}: {e}")
                
            if data_to_upsert: 
                conn.executemany("INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow, prompt_preview, sampler_names) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data_to_upsert)
            
            # Use DELETE-then-INSERT pattern for metadata (handles variable sampler counts)
            if metadata_to_upsert:
                # Delete old metadata for updated files
                if file_ids_with_metadata:
                    placeholders = ','.join(['?'] * len(file_ids_with_metadata))
                    conn.execute(f"DELETE FROM workflow_metadata WHERE file_id IN ({placeholders})", list(file_ids_with_metadata))
                
                # Insert new metadata
                conn.executemany("INSERT INTO workflow_metadata (file_id, sampler_index, model_name, sampler_name, scheduler, cfg, steps, positive_prompt, negative_prompt, width, height) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", metadata_to_upsert)

        if files_to_delete:
            paths_to_delete_list = list(files_to_delete)
            placeholders = ','.join('?' * len(paths_to_delete_list))
            conn.execute(f"DELETE FROM files WHERE path IN ({placeholders})", paths_to_delete_list)

        conn.commit()
    except Exception as e:
        logging.error(f"sync_folder_internal failed for {folder_path}: {e}")

def sync_folder_on_demand(folder_path):
    yield f"data: {json.dumps({'message': 'Checking folder for changes...', 'current': 0, 'total': 1})}\n\n"
    
    try:
        conn = get_db()
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
        files_to_update = {path for path in (disk_filepaths & db_filepaths) if int(disk_files[path]) > int(db_files[path])}
            
        if not files_to_add and not files_to_update and not files_to_delete:
            yield f"data: {json.dumps({'message': 'Folder is up-to-date.', 'status': 'no_changes', 'current': 1, 'total': 1})}\n\n"
            return

        files_to_process = list(files_to_add.union(files_to_update))
        total_files = len(files_to_process)
            
        if total_files > 0:
            yield f"data: {json.dumps({'message': f'Found {total_files} new/modified files. Processing...', 'current': 0, 'total': total_files})}\n\n"
                
            # Gather config values for worker processes
            thumbnail_cache_dir = app.config['THUMBNAIL_CACHE_DIR']
            thumbnail_width = app.config['THUMBNAIL_WIDTH']
            video_exts = app.config['VIDEO_EXTENSIONS']
            image_exts = app.config['IMAGE_EXTENSIONS']
            animated_exts = app.config['ANIMATED_IMAGE_EXTENSIONS']
            audio_exts = app.config['AUDIO_EXTENSIONS']
            webp_animated_fps = app.config['WEBP_ANIMATED_FPS']
            base_input_path_workflow = app.config['BASE_INPUT_PATH_WORKFLOW']
                
            data_to_upsert = []
            processed_count = 0

            with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
                futures = {
                    executor.submit(
                        process_single_file, path, thumbnail_cache_dir, thumbnail_width,
                        video_exts, image_exts, animated_exts, audio_exts, webp_animated_fps,
                        base_input_path_workflow
                    ): path for path in files_to_process
                }
                    
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
                files_data = []
                metadata_data = []
                
                for result in data_to_upsert:
                    # result now has 12 elements: (id, path, mtime, name, type, duration, dimensions, has_workflow, workflow_metadata_list, extraction_status, prompt_preview, sampler_names)
                    file_id = result[0]
                    # First 8 + prompt_preview + sampler_names
                    file_tuple = result[:8] + tuple(result[10:12])
                    workflow_metadata = result[8]  # 9th element is metadata dict/list or None
                    
                    files_data.append(file_tuple)
                    
                    if workflow_metadata:
                        # If workflow_metadata is a list, insert each sampler; otherwise treat as single
                        if isinstance(workflow_metadata, list):
                            for sampler_index, sampler_meta in enumerate(workflow_metadata):
                                metadata_data.append((
                                    file_id,
                                    sampler_index,
                                    sampler_meta.get('model_name'),
                                    sampler_meta.get('sampler_name'),
                                    sampler_meta.get('scheduler'),
                                    sampler_meta.get('cfg'),
                                    sampler_meta.get('steps'),
                                    sampler_meta.get('positive_prompt'),
                                    sampler_meta.get('negative_prompt'),
                                    sampler_meta.get('width'),
                                    sampler_meta.get('height')
                                ))
                        elif isinstance(workflow_metadata, dict):
                            metadata_data.append((
                                file_id,
                                0,
                                workflow_metadata.get('model_name'),
                                workflow_metadata.get('sampler_name'),
                                workflow_metadata.get('scheduler'),
                                workflow_metadata.get('cfg'),
                                workflow_metadata.get('steps'),
                                workflow_metadata.get('positive_prompt'),
                                workflow_metadata.get('negative_prompt'),
                                workflow_metadata.get('width'),
                                workflow_metadata.get('height')
                            ))

                conn.executemany("INSERT OR REPLACE INTO files (id, path, mtime, name, type, duration, dimensions, has_workflow, prompt_preview, sampler_names) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", files_data)
                
                if metadata_data:
                    # DELETE old metadata for these files then insert to handle variable sampler counts
                    file_ids = {m[0] for m in metadata_data}
                    if file_ids:
                        placeholders = ','.join(['?'] * len(file_ids))
                        conn.execute(f"DELETE FROM workflow_metadata WHERE file_id IN ({placeholders})", list(file_ids))
                    conn.executemany("INSERT INTO workflow_metadata (file_id, sampler_index, model_name, sampler_name, scheduler, cfg, steps, positive_prompt, negative_prompt, width, height) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", metadata_data)

        if files_to_delete:
            conn.executemany("DELETE FROM files WHERE path IN (?)", [(p,) for p in files_to_delete])

        conn.commit()
        yield f"data: {json.dumps({'message': 'Sync complete. Reloading...', 'status': 'reloading', 'current': total_files, 'total': total_files})}\n\n"

    except Exception as e:
        error_message = f"Error during sync: {e}"
        logging.error(error_message)
        yield f"data: {json.dumps({'message': error_message, 'current': 1, 'total': 1, 'error': True})}\n\n"

def scan_folder_and_extract_options(folder_path):
    """Scan folder for file extensions and prefixes (optimized)."""
    extensions, prefixes = set(), set()
    try:
        if not os.path.isdir(folder_path): 
            return None, [], []
        
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1]
                if ext and ext.lower() not in ('.json', '.sqlite'):
                    extensions.add(ext.lstrip('.').lower())
                if '_' in filename: 
                    prefixes.add(filename.split('_', 1)[0])  # Only split once
    except Exception as e: 
        logging.error(f"Could not scan folder '{folder_path}': {e}")
    
    return None, sorted(extensions), sorted(prefixes)  # sorted() works on sets directly

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

    # Print debug status message if enabled
    if DEBUG_WORKFLOW_EXTRACTION:
        debug_path = os.path.join(flask_app.config['BASE_OUTPUT_PATH'], 'workflow_debug')
        print(f"INFO: Workflow debugging ENABLED - will save to {debug_path}")
        logging.info(" Each file will have a subfolder with workflow data at each processing stage")
    
    # Setup logging
    log_dir = os.path.join(flask_app.config['BASE_OUTPUT_PATH'], 'smartgallery_logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'gallery_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    flask_app.logger.setLevel(logging.INFO)
    flask_app.config['LOG_FILE'] = log_file

    logging.info(" Initializing gallery...")
    logging.info("SmartGallery initialization started")
    flask_app.config['FFPROBE_EXECUTABLE_PATH'] = find_ffprobe_path()
    os.makedirs(flask_app.config['THUMBNAIL_CACHE_DIR'], exist_ok=True)
    os.makedirs(flask_app.config['SQLITE_CACHE_DIR'], exist_ok=True)
    
    # Register teardown handler for database connections
    flask_app.teardown_appcontext(close_db)
    
    # Wrap database initialization in app context (required for g object access during startup)
    with flask_app.app_context():
        conn = get_db()

        # --- NEW: Schema Migration Logic ---
        try:
            cursor = conn.execute("PRAGMA table_info(files)")
            columns = [row['name'] for row in cursor.fetchall()]
            if 'prompt_preview' not in columns:
                logging.info(" Migrating database schema: Adding 'prompt_preview' column to files table.")
                conn.execute("ALTER TABLE files ADD COLUMN prompt_preview TEXT")
            if 'sampler_names' not in columns:
                logging.info(" Migrating database schema: Adding 'sampler_names' column to files table.")
                conn.execute("ALTER TABLE files ADD COLUMN sampler_names TEXT")
            conn.commit()
        except sqlite3.DatabaseError:
            # If the files table does not exist yet or PRAGMA failed, ensure init_db will create it later
            pass

        try:
            stored_version = conn.execute('PRAGMA user_version').fetchone()[0]
        except sqlite3.DatabaseError: stored_version = 0
        if stored_version < DB_SCHEMA_VERSION:
            print(f"INFO: DB version outdated ({stored_version} < {DB_SCHEMA_VERSION}). Starting migration...")
            logging.info(f"DB version outdated ({stored_version} < {DB_SCHEMA_VERSION}). Starting migration...")
            
            # v21 → v22 migration: workflow_metadata PRIMARY KEY change
            if stored_version == 21 and DB_SCHEMA_VERSION == 22:
                try:
                    # Step 1: Backup old workflow_metadata table
                    logging.info(" Backing up workflow_metadata table...")
                    conn.execute('DROP TABLE IF EXISTS workflow_metadata_backup')
                    conn.execute('CREATE TABLE workflow_metadata_backup AS SELECT * FROM workflow_metadata')
                    
                    # Step 2: Drop old table and recreate with new schema
                    logging.info(" Recreating workflow_metadata with new schema...")
                    conn.execute('DROP TABLE workflow_metadata')
                    init_db(conn)  # Creates new schema with AUTOINCREMENT id
                    
                    # Step 3: Migrate existing data (all as sampler_index=0)
                    logging.info(" Migrating existing workflow metadata...")
                    conn.execute('''
                        INSERT INTO workflow_metadata 
                        (file_id, sampler_index, model_name, sampler_name, scheduler, cfg, steps, 
                         positive_prompt, negative_prompt, width, height)
                        SELECT file_id, 0, model_name, sampler_name, scheduler, cfg, steps,
                               positive_prompt, negative_prompt, width, height
                        FROM workflow_metadata_backup
                    ''')
                    
                    # Step 4: Update schema version
                    conn.execute(f'PRAGMA user_version = {DB_SCHEMA_VERSION}')
                    conn.commit()
                    
                    # Step 5: Clean up backup table
                    conn.execute('DROP TABLE workflow_metadata_backup')
                    conn.commit()
                    
                    logging.info(" Migration complete. Triggering full rescan to extract multi-sampler metadata...")
                    logging.info("Schema migration v21→v22 complete. Starting full rescan.")
                    full_sync_database(conn)
                    logging.info(" Rescan complete.")
                    logging.info("Full rescan after migration complete")
                    
                except Exception as e:
                    logging.error(f"Migration failed: {e}. Rolling back...")
                    logging.error(f"Migration failed: {e}", exc_info=True)
                    conn.rollback()
                    # Attempt rollback: restore from backup if exists
                    try:
                        conn.execute('DROP TABLE IF EXISTS workflow_metadata')
                        conn.execute('CREATE TABLE workflow_metadata AS SELECT * FROM workflow_metadata_backup')
                        conn.execute('DROP TABLE workflow_metadata_backup')
                        conn.commit()
                        logging.info(" Rollback successful. Old schema restored.")
                        logging.info("Rollback successful. Old schema restored.")
                    except Exception as rollback_error:
                        print(f"CRITICAL: Rollback failed: {rollback_error}")
                        logging.critical(f"Rollback failed: {rollback_error}", exc_info=True)
                    raise
            else:
                # For other version transitions, fall back to full rebuild
                logging.info(" Performing full database rebuild...")
                conn.execute('DROP TABLE IF EXISTS files')
                conn.execute('DROP TABLE IF EXISTS workflow_metadata')
                init_db(conn)
                full_sync_database(conn)
                conn.execute(f'PRAGMA user_version = {DB_SCHEMA_VERSION}')
                conn.commit()
                logging.info(" Rebuild complete.")
                logging.info("Database rebuild complete")
        else:
            print(f"INFO: DB version ({stored_version}) is up to date. Starting normally.")
            logging.info(f"DB version ({stored_version}) is up to date")


# --- FLASK ROUTES ---
@app.route('/galleryout/')
@app.route('/')
def gallery_redirect_base():
    return redirect(url_for('gallery_view', folder_key='_root_'))

@app.route('/galleryout/sync_status/<string:folder_key>')
@require_initialization
def sync_status(folder_key):
    folders = get_dynamic_folder_config()
    if folder_key not in folders:
        abort(404)
    folder_path = folders[folder_key]['path']
    return Response(stream_with_context(sync_folder_on_demand(folder_path)), mimetype='text/event-stream')

@app.route('/galleryout/view/<string:folder_key>')
@require_initialization
def gallery_view(folder_key):
    # Note: gallery_view_cache removed in v1.41.0 - using SQL pagination instead
    folders = get_dynamic_folder_config(force_refresh=True)
    if folder_key not in folders:
        return redirect(url_for('gallery_view', folder_key='_root_'))
    
    current_folder_info = folders[folder_key]
    folder_path = current_folder_info['path']
    
    # Get page number from query parameters
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    offset = (page - 1) * FILES_PER_PAGE
    
    conn = get_db()
    
    # Base conditions for this view (scoping to the current folder)
    conditions = ["f.path LIKE ?"]
    params = [folder_path + os.sep + '%']
    
    # Get all filter conditions from the centralized helper function
    filter_conditions, filter_params = _build_filter_conditions(request.args)
    conditions.extend(filter_conditions)
    params.extend(filter_params)
    
    sort_by = 'name' if request.args.get('sort_by') == 'name' else 'mtime'
    sort_order = 'asc' if request.args.get('sort_order', 'desc').lower() == 'asc' else 'desc'
    
    sort_direction = "ASC" if sort_order == 'asc' else "DESC"
    
    # TRUE SQL PAGINATION (v1.41.0) - Query only needed rows, not all results
    # Step 1: Get total count for pagination UI
    count_query = f"""
        SELECT COUNT(DISTINCT f.id) as total
        FROM files f 
        WHERE {' AND '.join(conditions)}
    """
    total_count_row = conn.execute(count_query, params).fetchone()
    total_files_count = total_count_row['total'] if total_count_row else 0
    
    # Step 2: Get only the page of files we need (with LIMIT/OFFSET)
    query_paginated = f"""
        SELECT f.*,
               COALESCE((SELECT COUNT(DISTINCT wm.sampler_index) 
                         FROM workflow_metadata wm 
                         WHERE wm.file_id = f.id), 0) as sampler_count
        FROM files f 
        WHERE {' AND '.join(conditions)} 
        ORDER BY f.{sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    
    # Add pagination params
    paginated_params = params + [FILES_PER_PAGE, offset]
    page_files_raw = conn.execute(query_paginated, paginated_params).fetchall()
    
    folder_path_norm = os.path.normpath(folder_path)
    initial_files = [dict(row) for row in page_files_raw if os.path.normpath(os.path.dirname(row['path'])) == folder_path_norm]
    
    # TRUE SQL PAGINATION (v1.41.0): No more global cache needed!
    # load_more endpoint now queries database directly with same filters
    # This eliminates memory bloat from caching large result sets
    
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
                           initial_page=page,
                           files_per_page=FILES_PER_PAGE,
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
@require_initialization
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
    # Issue #8 fix: Use non-generator sync function for internal use
    if success_count > 0: sync_folder_internal(destination_path)
    if errors: return jsonify({'status': 'partial_success', 'message': f'Successfully uploaded {success_count} files. The following files failed: {", ".join(errors.keys())}'}), 207
    return jsonify({'status': 'success', 'message': f'Successfully uploaded {success_count} files.'})
                           
@app.route('/galleryout/create_folder', methods=['POST'])
@require_initialization
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
@require_initialization
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
        # Issue #9 fix: Perform filesystem operation BEFORE database transaction
        # This ensures DB is only updated if the rename succeeds
        os.rename(old_path, new_path)
        
        # Now update the database to reflect the new paths
        conn = get_db()
        old_path_like = old_path + os.sep + '%'
        files_to_update = conn.execute("SELECT id, path FROM files WHERE path LIKE ?", (old_path_like,)).fetchall()
        update_data = []
        for row in files_to_update:
            new_file_path = row['path'].replace(old_path, new_path, 1)
            new_id = hashlib.md5(new_file_path.encode()).hexdigest()
            update_data.append((new_id, new_file_path, row['id']))
            
        if update_data: 
            conn.executemany("UPDATE files SET id = ?, path = ? WHERE id = ?", update_data)
        conn.commit()
        
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder renamed.'})
    except (OSError, PermissionError) as e:
        # If rename failed, database was never updated - no rollback needed
        return jsonify({'status': 'error', 'message': f'Error renaming folder: {e}'}), 500
    except Exception as e:
        # If DB update failed after successful rename, try to rollback the rename
        try:
            if os.path.exists(new_path):
                os.rename(new_path, old_path)  # Attempt to undo the rename
                return jsonify({'status': 'error', 'message': f'Database update failed, rename reverted: {e}'}), 500
        except Exception as rollback_error:
            return jsonify({'status': 'error', 'message': f'Critical: Folder renamed but DB update failed and rollback failed: {e}. Manual intervention required.'}), 500
        return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500

@app.route('/galleryout/delete_folder/<string:folder_key>', methods=['POST'])
@require_initialization
def delete_folder(folder_key):
    if folder_key in app.config['PROTECTED_FOLDER_KEYS']: return jsonify({'status': 'error', 'message': 'This folder cannot be deleted.'}), 403
    folders = get_dynamic_folder_config()
    if folder_key not in folders: return jsonify({'status': 'error', 'message': 'Folder not found.'}), 404
    try:
        folder_path = folders[folder_key]['path']
        conn = get_db()
        conn.execute("DELETE FROM files WHERE path LIKE ?", (folder_path + os.sep + '%',))
        conn.commit()
        shutil.rmtree(folder_path)
        get_dynamic_folder_config(force_refresh=True)
        return jsonify({'status': 'success', 'message': 'Folder deleted.'})
    except Exception as e: return jsonify({'status': 'error', 'message': f'Error: {e}'}), 500

@app.route('/galleryout/filter_options')
@require_initialization
def filter_options():
    """
    Returns unique values for filterable metadata, with caching.
    NOTE: This endpoint no longer returns models as they are handled by a separate search API.
    """
    global _filter_options_cache
    
    with _cache_lock:
        cache_entry = _filter_options_cache.get('options')
        if cache_entry and (time.time() - cache_entry['timestamp']) < CACHE_DURATION_SECONDS:
            logging.info(" Serving filter options from cache.")
            return jsonify(cache_entry['data'])

    # --- If cache is invalid, proceed with database query ---
    logging.info(" Cache miss or expired. Querying DB for filter options.")
    
    try:
        conn = get_db()
        
        # --- RESTORE: Query models (pre-loaded + cached) ---
        models_raw = conn.execute("""
            SELECT model_name, COUNT(DISTINCT file_id) as file_count
            FROM workflow_metadata
            WHERE model_name IS NOT NULL AND model_name != ''
            GROUP BY model_name
            ORDER BY file_count DESC, model_name
        """).fetchall()
        
        samplers_raw = conn.execute("""
            SELECT sampler_name, COUNT(DISTINCT file_id) as file_count 
            FROM workflow_metadata 
            WHERE sampler_name IS NOT NULL AND sampler_name != '' 
            GROUP BY sampler_name 
            ORDER BY file_count DESC, sampler_name
        """).fetchall()
        
        schedulers_raw = conn.execute("""
            SELECT scheduler, COUNT(DISTINCT file_id) as file_count 
            FROM workflow_metadata 
            WHERE scheduler IS NOT NULL AND scheduler != '' 
            GROUP BY scheduler 
            ORDER BY file_count DESC, scheduler
        """).fetchall()
        
        # Safely extract and normalize values
        models = [{'value': row['model_name'], 'count': row['file_count']} for row in models_raw if row['model_name']]
        samplers = [{'value': row['sampler_name'], 'count': row['file_count']} for row in samplers_raw if row['sampler_name']]
        schedulers = [{'value': row['scheduler'], 'count': row['file_count']} for row in schedulers_raw if row['scheduler']]

        # (Ranges are cheap to query, so they are not part of this cache optimization focus but are included)
        cfg_range = conn.execute("SELECT MIN(cfg) as min_cfg, MAX(cfg) as max_cfg FROM workflow_metadata WHERE cfg IS NOT NULL").fetchone()
        steps_range = conn.execute("SELECT MIN(steps) as min_steps, MAX(steps) as max_steps FROM workflow_metadata WHERE steps IS NOT NULL").fetchone()
        dimensions_range = conn.execute("SELECT MIN(width) as min_width, MAX(width) as max_width, MIN(height) as min_height, MAX(height) as max_height FROM workflow_metadata WHERE width IS NOT NULL AND height IS NOT NULL").fetchone()

        response_data = {
            'status': 'success',
                'options': {
                'models': models,
                'samplers': samplers,
                'schedulers': schedulers,
                'cfg_range': {'min': cfg_range['min_cfg'], 'max': cfg_range['max_cfg']} if cfg_range else None,
                'steps_range': {'min': steps_range['min_steps'], 'max': steps_range['max_steps']} if steps_range else None,
                'width_range': {'min': dimensions_range['min_width'], 'max': dimensions_range['max_width']} if dimensions_range else None,
                'height_range': {'min': dimensions_range['min_height'], 'max': dimensions_range['max_height']} if dimensions_range else None
            }
        }
        
        # Update cache
        with _cache_lock:
            _filter_options_cache['options'] = {
                'timestamp': time.time(),
                'data': response_data
            }
        
        print(f"INFO: filter_options returning {len(samplers)} samplers, {len(schedulers)} schedulers.")
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"filter_options failed: {e}")
        # Return error but with empty arrays so frontend doesn't break
        return jsonify({
            'status': 'error', 'message': str(e),
            'options': {'models': [], 'samplers': [], 'schedulers': []}
        }), 500



@app.route('/galleryout/workflow_samplers/<string:file_id>')
@require_initialization
def workflow_samplers(file_id):
    """
    Returns all sampler metadata for a specific file.
    Used for detailed workflow inspection in the frontend.
    """
    try:
        conn = get_db()
        
        # Verify file exists
        file_exists = conn.execute("SELECT 1 FROM files WHERE id = ?", (file_id,)).fetchone()
        if not file_exists:
            return jsonify({
                'status': 'error',
                'message': 'File not found'
            }), 404
        
        # Get all samplers for this file, ordered by sampler_index
        samplers_raw = conn.execute("""
            SELECT * FROM workflow_metadata 
            WHERE file_id = ? 
            ORDER BY sampler_index
        """, (file_id,)).fetchall()
        
        samplers = []
        for row in samplers_raw:
            samplers.append({
                'sampler_index': row['sampler_index'],
                'model_name': row['model_name'],
                'sampler_name': row['sampler_name'],
                'scheduler': row['scheduler'],
                'cfg': float(row['cfg']) if row['cfg'] is not None else None,
                'steps': int(row['steps']) if row['steps'] is not None else None,
                'positive_prompt': row['positive_prompt'],
                'negative_prompt': row['negative_prompt'],
                'width': int(row['width']) if row['width'] is not None else None,
                'height': int(row['height']) if row['height'] is not None else None
            })
        
        return jsonify({
            'status': 'success',
            'file_id': file_id,
            'sampler_count': len(samplers),
            'samplers': samplers
        })
        
    except Exception as e:
        logging.error(f"workflow_samplers endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e),
            'sampler_count': 0,
            'samplers': []
        }), 500


@app.route('/galleryout/health')
def health_check():
    """
    Health check endpoint for monitoring application status.
    Returns database connection status and basic statistics.
    """
    try:
        # Check database connectivity
        conn = get_db()
        file_count = conn.execute("SELECT COUNT(*) as count FROM files").fetchone()['count']
        workflow_count = conn.execute("SELECT COUNT(DISTINCT file_id) as count FROM workflow_metadata").fetchone()['count']
        
        # Get cache stats
        cache_stats = get_cache_stats()
        
        # Get recent performance stats
        with request_timing_log['lock']:
            recent_requests = request_timing_log['requests'][-10:]
            avg_response_time = sum(r['duration_ms'] for r in recent_requests) / len(recent_requests) if recent_requests else 0
        
        return jsonify({
            'status': 'healthy',
            'database': {
                'connected': True,
                'total_files': file_count,
                'files_with_workflow': workflow_count
            },
            'cache': cache_stats,
            'performance': {
                'avg_response_time_ms': round(avg_response_time, 2),
                'recent_requests': len(recent_requests)
            }
        })
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/galleryout/stats')
@require_initialization
def get_stats():
    """
    Performance and statistics endpoint for monitoring.
    Provides detailed information about the gallery state.
    """
    try:
        conn = get_db()
        
        # File statistics
        file_stats = conn.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                SUM(CASE WHEN has_workflow = 1 THEN 1 ELSE 0 END) as with_workflow,
                SUM(CASE WHEN is_favorite = 1 THEN 1 ELSE 0 END) as favorites
            FROM files
            GROUP BY type
        """).fetchall()
        
        # Workflow statistics
        workflow_stats = conn.execute("""
            SELECT 
                COUNT(DISTINCT file_id) as total_files,
                COUNT(*) as total_samplers,
                COUNT(DISTINCT model_name) as unique_models,
                COUNT(DISTINCT sampler_name) as unique_samplers,
                COUNT(DISTINCT scheduler) as unique_schedulers
            FROM workflow_metadata
        """).fetchone()
        
        # Performance timing stats
        with request_timing_log['lock']:
            all_requests = request_timing_log['requests']
            if all_requests:
                durations = [r['duration_ms'] for r in all_requests]
                timing_stats = {
                    'total_requests': len(all_requests),
                    'avg_ms': round(sum(durations) / len(durations), 2),
                    'min_ms': round(min(durations), 2),
                    'max_ms': round(max(durations), 2),
                    'p95_ms': round(sorted(durations)[int(len(durations) * 0.95)], 2) if len(durations) > 20 else None
                }
            else:
                timing_stats = {'total_requests': 0}
        
        return jsonify({
            'status': 'success',
            'files': [dict(row) for row in file_stats],
            'workflows': dict(workflow_stats) if workflow_stats else {},
            'performance': timing_stats,
            'cache': get_cache_stats()
        })
        
    except Exception as e:
        logging.error(f"Stats endpoint failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/galleryout/load_more')
@require_initialization
def load_more():
    """
    Load more files with TRUE SQL PAGINATION (v1.41.0)
    Queries only the requested page from database instead of caching all results.
    """
    page = request.args.get('page', 2, type=int)
    folder_key = request.args.get('folder_key', '_root_')
    
    # Validate input
    if page < 1:
        return jsonify(files=[], total=0)
    
    # Get folder configuration
    folders = get_dynamic_folder_config()
    if folder_key not in folders:
        return jsonify(files=[], total=0)
    
    current_folder_info = folders[folder_key]
    folder_path = current_folder_info['path']
    
    offset = (page - 1) * FILES_PER_PAGE
    
    # Rebuild query with same filters as gallery_view
    conn = get_db()

    # Base conditions for this view (scoping to the current folder)
    conditions = ["f.path LIKE ?"]
    params = [folder_path + os.sep + '%']

    # Get all filter conditions from the centralized helper function
    filter_conditions, filter_params = _build_filter_conditions(request.args)
    conditions.extend(filter_conditions)
    params.extend(filter_params)

    sort_by = 'name' if request.args.get('sort_by') == 'name' else 'mtime'
    sort_order = 'asc' if request.args.get('sort_order', 'desc').lower() == 'asc' else 'desc'

    sort_direction = "ASC" if sort_order == 'asc' else "DESC"
    
    # Get total count
    count_query = f"""
        SELECT COUNT(DISTINCT f.id) as total
        FROM files f 
        WHERE {' AND '.join(conditions)}
    """
    total_count_row = conn.execute(count_query, params).fetchone()
    total_count = total_count_row['total'] if total_count_row else 0
    
    if offset >= total_count:
        return jsonify(files=[], total=total_count)
    
    # Get only the requested page
    query_paginated = f"""
        SELECT f.*,
               COALESCE((SELECT COUNT(DISTINCT wm.sampler_index) 
                         FROM workflow_metadata wm 
                         WHERE wm.file_id = f.id), 0) as sampler_count
        FROM files f 
        WHERE {' AND '.join(conditions)} 
        ORDER BY f.{sort_by} {sort_direction}
        LIMIT ? OFFSET ?
    """
    
    paginated_params = params + [FILES_PER_PAGE, offset]
    page_files_raw = conn.execute(query_paginated, paginated_params).fetchall()
    
    folder_path_norm = os.path.normpath(folder_path)
    files_to_return = [dict(row) for row in page_files_raw if os.path.normpath(os.path.dirname(row['path'])) == folder_path_norm]
    
    return jsonify(files=files_to_return, total=total_count)

@app.route('/galleryout/file_location/<string:file_id>')
@require_initialization
def file_location(file_id):
    """
    Finds which folder and page a specific file_id belongs on,
    respecting current filter and sort parameters.
    """
    conn = get_db()
    
    # First, find the file's folder by getting its path
    file_info = conn.execute("SELECT path FROM files WHERE id = ?", (file_id,)).fetchone()
    
    if not file_info:
        return jsonify({"status": "error", "message": "File not found"}), 404
    
    file_path = file_info['path']
    file_dir = os.path.dirname(file_path)
    
    # Find the folder key for this directory
    folders = get_dynamic_folder_config()
    folder_key = None
    for key, folder_data in folders.items():
        if os.path.normpath(folder_data['path']) == os.path.normpath(file_dir):
            folder_key = key
            break
    
    if not folder_key:
        return jsonify({"status": "error", "message": "Folder not found for file"}), 404
    
    # Re-apply the same filter/sort logic from gallery_view
    # This is crucial for calculating the correct index.
    search_term = request.args.get('search', '').strip()
    selected_extensions = request.args.getlist('extension')
    selected_prefixes = request.args.getlist('prefix')
    show_favorites = request.args.get('favorites', 'false').lower() == 'true'
    sort_by = 'name' if request.args.get('sort_by') == 'name' else 'mtime'
    sort_order = 'asc' if request.args.get('sort_order', 'desc').lower() == 'asc' else 'desc'
    
    sort_direction = "ASC" if sort_order == 'asc' else "DESC"
    
    conditions = ["f.path LIKE ?"]
    params = [file_dir + os.sep + '%']
    
    # Gather workflow metadata filters
    metadata_filters = {}
    if request.args.get('filter_model', '').strip():
        metadata_filters['model'] = request.args.get('filter_model').strip()
    if request.args.get('filter_sampler', '').strip():
        metadata_filters['sampler'] = request.args.get('filter_sampler').strip()
    if request.args.get('filter_scheduler', '').strip():
        metadata_filters['scheduler'] = request.args.get('filter_scheduler').strip()
    if request.args.get('filter_cfg_min', type=float) is not None:
        metadata_filters['cfg_min'] = request.args.get('filter_cfg_min', type=float)
    if request.args.get('filter_cfg_max', type=float) is not None:
        metadata_filters['cfg_max'] = request.args.get('filter_cfg_max', type=float)
    if request.args.get('filter_steps_min', type=int) is not None:
        metadata_filters['steps_min'] = request.args.get('filter_steps_min', type=int)
    if request.args.get('filter_steps_max', type=int) is not None:
        metadata_filters['steps_max'] = request.args.get('filter_steps_max', type=int)
    if request.args.get('filter_width_min', type=int) is not None:
        metadata_filters['width_min'] = request.args.get('filter_width_min', type=int)
    if request.args.get('filter_width_max', type=int) is not None:
        metadata_filters['width_max'] = request.args.get('filter_width_max', type=int)
    if request.args.get('filter_height_min', type=int) is not None:
        metadata_filters['height_min'] = request.args.get('filter_height_min', type=int)
    if request.args.get('filter_height_max', type=int) is not None:
        metadata_filters['height_max'] = request.args.get('filter_height_max', type=int)
    
    # Build EXISTS subquery for metadata filters
    if metadata_filters:
        subquery_sql, subquery_params = build_metadata_filter_subquery(metadata_filters)
        if subquery_sql:
            conditions.append(subquery_sql)
            params.extend(subquery_params)
    
    if search_term:
        conditions.append("f.name LIKE ?")
        params.append(f"%{search_term}%")
    
    if show_favorites:
        conditions.append("f.is_favorite = 1")
    
    if selected_prefixes:
        prefix_conditions = [f"f.name LIKE ?" for p in selected_prefixes if p.strip()]
        params.extend([f"{p.strip()}_%" for p in selected_prefixes if p.strip()])
        if prefix_conditions:
            conditions.append(f"({' OR '.join(prefix_conditions)})")
    
    if selected_extensions:
        ext_conditions = [f"f.name LIKE ?" for ext in selected_extensions if ext.strip()]
        params.extend([f"%.{ext.lstrip('.').lower()}" for ext in selected_extensions if ext.strip()])
        if ext_conditions:
            conditions.append(f"({' OR '.join(ext_conditions)})")
    
    # Get all file IDs in the folder, with filters and sorting applied (EXISTS subquery, no JOIN)
    query = f"SELECT id FROM files f WHERE {' AND '.join(conditions)} ORDER BY f.{sort_by} {sort_direction}"
    
    all_files_in_view = conn.execute(query, params).fetchall()
    
    all_ids_in_view = [row['id'] for row in all_files_in_view]
    
    try:
        index_in_view = all_ids_in_view.index(file_id)
        page = (index_in_view // FILES_PER_PAGE) + 1
        
        return jsonify({
            "status": "success",
            "folder_key": folder_key,
            "page": page
        })
    except ValueError:
        return jsonify({
            "status": "error", 
            "message": "File exists but is hidden by current filters."
        }), 404

def get_file_info_from_db(file_id, column='*'):
    try:
        conn = get_db()
        row = conn.execute(f"SELECT {column} FROM files WHERE id = ?", (file_id,)).fetchone()
        if not row: abort(404)
        return dict(row) if column == '*' else row[0]
    except sqlite3.Error as e:
        logging.error(f"Database error in get_file_info_from_db for file_id {file_id}: {e}")
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
@require_initialization
def move_batch():
    data = request.json
    file_ids, dest_key = data.get('file_ids', []), data.get('destination_folder')
    folders = get_dynamic_folder_config()
    if not all([file_ids, dest_key, dest_key in folders]):
        return jsonify({'status': 'error', 'message': 'Invalid data provided.'}), 400
    moved_count, renamed_count, failed_files, dest_path_folder = 0, 0, [], folders[dest_key]['path']
    
    conn = get_db()
    for file_id in file_ids:
        source_path = None
        savepoint = None
        try:
            # Create a savepoint for atomic rollback (Issue #6)
            savepoint = f"move_{file_id}"
            conn.execute(f"SAVEPOINT {savepoint}")
                
            file_info = conn.execute("SELECT path, name FROM files WHERE id = ?", (file_id,)).fetchone()
            if not file_info:
                failed_files.append(f"ID {file_id} not found in DB")
                conn.execute(f"RELEASE SAVEPOINT {savepoint}")
                continue
            source_path, source_filename = file_info['path'], file_info['name']
            if not os.path.exists(source_path):
                failed_files.append(f"{source_filename} (not found on disk)")
                conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                conn.execute(f"RELEASE SAVEPOINT {savepoint}")
                continue
                
            final_dest_path = _get_unique_filepath(dest_path_folder, source_filename)
            final_filename = os.path.basename(final_dest_path)
            if final_filename != source_filename: renamed_count += 1
                
            # CRITICAL: Perform file operation BEFORE DB commit
            shutil.move(source_path, final_dest_path)
                
            # Only update DB after successful file move
            new_id = hashlib.md5(final_dest_path.encode()).hexdigest()
            conn.execute("UPDATE files SET id = ?, path = ?, name = ? WHERE id = ?", (new_id, final_dest_path, final_filename, file_id))
            conn.execute(f"RELEASE SAVEPOINT {savepoint}")
            moved_count += 1
        except Exception as e:
            # Rollback database changes if file operation failed
            if savepoint:
                try:
                    conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    conn.execute(f"RELEASE SAVEPOINT {savepoint}")
                except Exception as rb_error:
                    logging.error(f"Failed to rollback savepoint: {rb_error}")
                
            filename_for_error = os.path.basename(source_path) if source_path else f"ID {file_id}"
            failed_files.append(filename_for_error)
            logging.error(f"Failed to move file {filename_for_error}. Reason: {e}")
            continue
    conn.commit()
    
    message = f"Successfully moved {moved_count} file(s)."
    if renamed_count > 0: message += f" {renamed_count} were renamed to avoid conflicts."
    if failed_files: message += f" Failed to move {len(failed_files)} file(s)."
    return jsonify({'status': 'partial_success' if failed_files else 'success', 'message': message})

@app.route('/galleryout/delete_batch', methods=['POST'])
@require_initialization
def delete_batch():
    file_ids = request.json.get('file_ids', [])
    if not file_ids: return jsonify({'status': 'error', 'message': 'No files selected.'}), 400
    deleted_count, failed_files = 0, []
    conn = get_db()
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
                    logging.warning(f" Could not remove thumbnail {thumbnail_path}: {e}")
                
            ids_to_remove_from_db.append(row['id'])
            deleted_count += 1
        except Exception as e: 
            failed_files.append(os.path.basename(row['path']))
            logging.error(f"Could not delete {row['path']}: {e}")
    if ids_to_remove_from_db:
        db_placeholders = ','.join('?' * len(ids_to_remove_from_db))
        conn.execute(f"DELETE FROM files WHERE id IN ({db_placeholders})", ids_to_remove_from_db)
        conn.commit()
    message = f'Successfully deleted {deleted_count} files.'
    if failed_files: message += f" Failed to delete {len(failed_files)} files."
    return jsonify({'status': 'partial_success' if failed_files else 'success', 'message': message})

@app.route('/galleryout/favorite_batch', methods=['POST'])
@require_initialization
def favorite_batch():
    data = request.json
    file_ids, status = data.get('file_ids', []), data.get('status', False)
    if not file_ids: return jsonify({'status': 'error', 'message': 'No files selected'}), 400
    conn = get_db()
    placeholders = ','.join('?' * len(file_ids))
    conn.execute(f"UPDATE files SET is_favorite = ? WHERE id IN ({placeholders})", [1 if status else 0] + file_ids)
    conn.commit()
    return jsonify({'status': 'success', 'message': f"Updated favorites for {len(file_ids)} files."})

@app.route('/galleryout/toggle_favorite/<string:file_id>', methods=['POST'])
@require_initialization
def toggle_favorite(file_id):
    conn = get_db()
    current = conn.execute("SELECT is_favorite FROM files WHERE id = ?", (file_id,)).fetchone()
    if not current: abort(404)
    new_status = 1 - current['is_favorite']
    conn.execute("UPDATE files SET is_favorite = ? WHERE id = ?", (new_status, file_id))
    conn.commit()
    return jsonify({'status': 'success', 'is_favorite': bool(new_status)})

# --- NEW FEATURE: RENAME FILE ---
@app.route('/galleryout/rename_file/<string:file_id>', methods=['POST'])
@require_initialization
def rename_file(file_id):
    data = request.json
    new_name = data.get('new_name', '').strip()

    # Basic validation for the new name
    if not new_name or len(new_name) > 250:
        return jsonify({'status': 'error', 'message': 'The provided filename is invalid or too long.'}), 400
    if re.search(r'[\\/:"*?<>|]', new_name):
        return jsonify({'status': 'error', 'message': 'Filename contains invalid characters.'}), 400

    try:
        conn = get_db()
        file_info = conn.execute("SELECT path, name FROM files WHERE id = ?", (file_id,)).fetchone()
        if not file_info:
            return jsonify({'status': 'error', 'message': 'File not found in the database.'}), 404

        old_path = file_info['path']
        old_name = file_info['name']
            
        # Preserve the original extension
        _, old_ext = os.path.splitext(old_name)
        new_name_base, new_ext = os.path.splitext(new_name)
        if not new_ext:  # If user didn't provide an extension, use the old one
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
        logging.error(f"OS error during file rename for {file_id}: {e}")
        return jsonify({'status': 'error', 'message': f'A system error occurred during rename: {e}'}), 500
    except Exception as e:
        logging.error(f"Generic error during file rename for {file_id}: {e}")
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {e}'}), 500

# --- FIX: ROBUST DELETE ROUTE ---
@app.route('/galleryout/delete/<string:file_id>', methods=['POST'])
@require_initialization
def delete_file(file_id):
    conn = get_db()
    file_info = conn.execute("SELECT path, mtime FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_info:
        return jsonify({'status': 'success', 'message': 'File already deleted from database.'})
        
    filepath = file_info['path']
    mtime = file_info['mtime']
        
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        # If file doesn't exist on disk, we still proceed to remove the DB entry, which is the desired state.
    except (OSError, PermissionError) as e:
        # A real OS error occurred (e.g., permissions). Issue #7: Catch both OSError and PermissionError
        logging.error(f"Could not delete file {filepath} from disk: {e}")
        return jsonify({'status': 'error', 'message': f'Could not delete file from disk: {e}'}), 500

    # Clean up orphaned thumbnail
    file_hash = hashlib.md5((filepath + str(mtime)).encode()).hexdigest()
    try:
        thumbnail_pattern = os.path.join(app.config['THUMBNAIL_CACHE_DIR'], f"{file_hash}.*")
        for thumbnail_path in glob.glob(thumbnail_pattern):
            os.remove(thumbnail_path)
            print(f"INFO: Removed orphaned thumbnail: {os.path.basename(thumbnail_path)}")
    except Exception as e:
        logging.warning(f" Could not remove thumbnail for {filepath}: {e}")

    # Whether the file was deleted now or was already gone, we clean up the DB.
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    return jsonify({'status': 'success', 'message': 'File deleted successfully.'})

@app.route('/galleryout/file/<string:file_id>')
@require_initialization
def serve_file(file_id):
    filepath = get_file_info_from_db(file_id, 'path')
    if filepath.lower().endswith('.webp'): return send_file(filepath, mimetype='image/webp')
    return send_file(filepath)

@app.route('/galleryout/download/<string:file_id>')
@require_initialization
def download_file(file_id):
    filepath = get_file_info_from_db(file_id, 'path')
    return send_file(filepath, as_attachment=True)

@app.route('/galleryout/workflow/<string:file_id>')
@require_initialization
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
@require_initialization
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
@require_initialization
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


# --- DASHBOARD API ROUTES REMOVED ---
# The following routes were removed as they were only used by the ComfyUI sidebar:
# - /smartgallery/stats (gallery statistics)
# - /smartgallery/recent (recent files)
# - /smartgallery/sync_all (full sync trigger)
# - /smartgallery/clear_cache (cache clearing)
# - /smartgallery/logs (log viewer)
#
# For standalone usage, all functionality is accessible directly through the
# main gallery interface at /galleryout/


# Request counter middleware
@app.before_request
def count_request():
    """Increment request counter for stats"""
    with request_counter['lock']:
        request_counter['count'] += 1


# --- Error Handlers (Flask Best Practices) ---
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Convert HTTP exceptions to JSON responses for API endpoints."""
    response = {
        "status": "error",
        "code": e.code,
        "name": e.name,
        "message": e.description
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_generic_exception(e):
    """Catch unexpected errors, log full traceback, and return safe JSON response."""
    import traceback
    # Log the full traceback for debugging
    app.logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
    
    # Return generic error to client (don't expose internal details)
    response = {
        "status": "error",
        "code": 500,
        "name": "Internal Server Error",
        "message": "An unexpected error occurred. Check server logs for details."
    }
    return jsonify(response), 500


if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description="SmartGallery - Standalone AI Media Gallery")
    parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file (default: config.json)")
    parser.add_argument("--output-path", type=str, help="Path to your AI output directory (overrides config.json)")
    parser.add_argument("--input-path", type=str, help="Path to your input directory (overrides config.json)")
    parser.add_argument("--port", type=int, help="Port for the gallery web server (overrides config.json)")
    parser.add_argument("--ffprobe-path", type=str, help="Manual path to the ffprobe executable (overrides config.json)")

    args = parser.parse_args()

    # Load configuration from config.json if it exists
    config_data = {}
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"✓ Loaded configuration from: {args.config}")
        except Exception as e:
            logging.warning(f" Failed to load config file '{args.config}': {e}")
            print("Continuing with command-line arguments only...")
    else:
        if args.config != "config.json":  # Only warn if non-default config was specified
            logging.warning(f" Config file '{args.config}' not found")
        print("Using command-line arguments only...")

    # Merge config: CLI args override config.json
    output_path = args.output_path or config_data.get('base_output_path')
    input_path = args.input_path or config_data.get('base_input_path')
    server_port = args.port or config_data.get('server_port', 8008)
    ffprobe_path = args.ffprobe_path or config_data.get('ffprobe_manual_path', '')

    # Validate required paths
    if not output_path or not input_path:
        print("\nERROR: Required paths not provided!")
        print("\nYou must provide paths either via:")
        print("  1. Command line: --output-path and --input-path")
        print("  2. Config file: Create config.json with base_output_path and base_input_path")
        print("\nExample config.json:")
        print('{')
        print('    "base_output_path": "/path/to/your/output",')
        print('    "base_input_path": "/path/to/your/input",')
        print('    "server_port": 8008')
        print('}')
        print("\nSee config.json.example for more options.")
        sys.exit(1)

    if not os.path.isdir(output_path):
        print(f"\nERROR: Output path does not exist or is not a directory: {output_path}")
        sys.exit(1)
    
    if not os.path.isdir(input_path):
        print(f"\nERROR: Input path does not exist or is not a directory: {input_path}")
        sys.exit(1)

    # --- Populate Flask app config from merged configuration ---
    app.config['BASE_OUTPUT_PATH'] = output_path
    app.config['BASE_INPUT_PATH'] = input_path
    app.config['SERVER_PORT'] = server_port
    app.config['FFPROBE_MANUAL_PATH'] = ffprobe_path
    
    # Apply additional config options if present
    if 'thumbnail_quality' in config_data:
        app.config['THUMBNAIL_QUALITY'] = config_data['thumbnail_quality']
    if 'enable_upload' in config_data:
        app.config['ENABLE_UPLOAD'] = config_data['enable_upload']
    if 'max_upload_size_mb' in config_data:
        app.config['MAX_UPLOAD_SIZE_MB'] = config_data['max_upload_size_mb']
    
    # Update ALL_MEDIA_EXTENSIONS after potential config updates
    app.config['ALL_MEDIA_EXTENSIONS'] = (
        app.config['VIDEO_EXTENSIONS'] + 
        app.config['IMAGE_EXTENSIONS'] + 
        app.config['ANIMATED_IMAGE_EXTENSIONS'] + 
        app.config['AUDIO_EXTENSIONS']
    )

    # Initialize derived paths and database
    initialize_gallery(app)

    print("\n" + "="*60)
    print("SmartGallery - Standalone AI Media Gallery")
    print("="*60)
    print(f"Output Path: {output_path}")
    print(f"Input Path:  {input_path}")
    print(f"Server Port: {server_port}")
    print(f"\n✓ SmartGallery is running!")
    print(f"✓ Open in browser: http://127.0.0.1:{server_port}/galleryout/")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=server_port, debug=False)
