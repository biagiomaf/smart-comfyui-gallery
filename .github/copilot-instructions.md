# SmartGallery - AI Coding Agent Instructions

## Project Overview

SmartGallery is a standalone Flask web application for browsing, organizing, and analyzing AI-generated media with ComfyUI workflow metadata extraction. It's a **single-file monolith** (`smartgallery.py` ~3400 lines) with an Alpine.js SPA frontend (`index.html` ~3700 lines).

**Key Architecture Pattern**: This is a **format-agnostic workflow parser** that reads ComfyUI workflows embedded in PNG/video metadata without requiring ComfyUI installation.

## Critical Architectural Decisions

### 1. Workflow Parser - The Core Innovation

The `ComfyUIWorkflowParser` class (lines 169-650) is the project's intellectual property:

- **Handles TWO workflow formats natively** (UI format with `nodes` array, API format with node_id dict)
- **Graph-based traversal** using `_find_source_node()` - NOT breadth-first search
- **Multi-sampler support** - extracts metadata for EACH sampler node independently
- Avoids flawed conversion overhead (removed `convert_ui_workflow_to_api_format()` in v1.40.0)

**When editing parser logic**:
```python
# CORRECT: Format-aware node access
if self.format == 'ui':
    # Use self.links_map (link_id -> (source_node_id, slot_idx))
    source_node = self._get_input_source_node(node, 'model')
else:  # API format
    # Use node['inputs'] directly
    source_node = node.get('inputs', {}).get('model')
```

### 2. Database Schema Evolution Pattern

Schema version in `DB_SCHEMA_VERSION = 22`. Migrations use **conditional ALTER TABLE** pattern:

```python
# Check if column exists before adding (idempotent migrations)
cursor.execute("PRAGMA table_info(files)")
columns = {col[1] for col in cursor.fetchall()}
if 'prompt_preview' not in columns:
    cursor.execute("ALTER TABLE files ADD COLUMN prompt_preview TEXT")
```

**Critical indices** (v1.41.0 performance fix):
- `idx_files_name`, `idx_files_mtime`, `idx_files_type`, `idx_files_favorite`, `idx_files_path`
- These enable O(log n) queries instead of O(n) table scans

### 3. Frontend State Management

Alpine.js stores (`Alpine.store('gallery')`) manage:
- **Folder tree state**: `folders`, `folderSort`, `folderSearchTerm`, `collapsedFolders`
- **Persistent UI preferences**: Saved to `localStorage` via `saveSortState()`
- **Reactive filtering**: `activeFilterPills` computed from form values

**Tom-Select Integration** (multi-select dropdowns):
```javascript
// ALWAYS store references for programmatic clearing
const tomSelectInstances = {};
tomSelectInstances.model = new TomSelect('#model-select', { /* config */ });

// Clear all instances when needed
Object.values(tomSelectInstances).forEach(ts => ts.clear());
```

## Developer Workflows

### Running the Application

```bash
# Standalone mode (no ComfyUI required)
python smartgallery.py --output-path "C:\path\to\media" --input-path "C:\path\to\workflows"

# With custom port
python smartgallery.py --port 8080

# Using config.json (preferred)
cp config.json.example config.json
# Edit config.json with your paths
python smartgallery.py
```

**First-time setup**: App auto-creates SQLite database and thumbnails on first sync.

### Debugging Workflow Extraction

Enable debug mode (line 876):
```python
DEBUG_WORKFLOW_EXTRACTION = True
```

Creates debug files in `output/workflow_debug/`:
- `01_raw.json` - Raw extracted JSON
- `02_parsed.json` - Parsed workflow data
- `03_format_detection.txt` - Detected format (UI vs API)
- `05_parser_output.json` - Final extracted metadata

**Common extraction failures**:
1. **No "nodes" or node dict** → Check if file has ComfyUI metadata at all
2. **Missing sampler metadata** → Verify parser node type lists (`SAMPLER_TYPES`, `MODEL_LOADER_TYPES`)
3. **Multiprocessing issues** → Debug dir must be passed to worker processes (fixed v1.39.4)

### Performance Optimization Patterns

**Database query pattern** (v1.41.0 - SQL pagination):
```python
# WRONG: Load all files into memory
all_files = db.execute("SELECT * FROM files WHERE ...").fetchall()
page = all_files[offset:offset+limit]  # Memory bloat!

# CORRECT: Database-level pagination
count = db.execute("SELECT COUNT(*) FROM files WHERE ...").fetchone()[0]
files = db.execute("SELECT * FROM files WHERE ... LIMIT ? OFFSET ?", 
                   (limit, offset)).fetchall()
```

**Thumbnail generation**: Uses `multiprocessing.Pool` with `MAX_PARALLEL_WORKERS` (default: all cores)
- Set to `1` for debugging to avoid process spawn issues
- Set to `4-8` for production to balance CPU/memory

### Testing Workflow Changes

1. **Create test files** with embedded workflows (use ComfyUI's Save Image node)
2. **Clear database** to force re-extraction: `rm .sqlite_cache/gallery_cache.sqlite`
3. **Enable debug mode** and check `workflow_debug/` output
4. **Verify SQL queries** using `EXPLAIN QUERY PLAN` for performance

## Project-Specific Conventions

### Code Organization

- **No modules/packages** - Single `smartgallery.py` file for portability
- **Flask routes after helpers** - All utility functions defined before `@app.route` decorators
- **Alpine.js components** - Use `x-data="componentName()"` pattern, NOT global functions
- **CSS in `<style>` tag** - No external stylesheets (self-contained deployment)

### Naming Conventions

```python
# Database columns: snake_case
file_id, sampler_name, positive_prompt

# Flask routes: lowercase with underscores
@app.route('/galleryout/view/<folder_key>')

# Alpine.js properties: camelCase
isLightboxOpen, currentFolderKey, activeFilterPills

# CSS classes: kebab-case with BEM-like structure
.gallery-item, .filter-panel-header, .lightbox-sampler-panel
```

### Error Handling Philosophy

**Fail gracefully for metadata extraction**:
```python
try:
    sampler_name = self._extract_sampler_details(node)
except Exception as e:
    logging.warning(f"Failed to extract sampler: {e}")
    sampler_name = None  # Continue processing other fields
```

**Fail fast for critical paths** (database, file operations):
```python
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")
```

## Integration Points

### ComfyUI Workflow Embedding

SmartGallery reads workflows from:
1. **PNG tEXt chunks** - `workflow` and `prompt` keys
2. **Video metadata** - MP4 comment atom (requires `ffprobe`)
3. **Direct JSON files** - Fallback for testing

### External Dependencies

- **FFmpeg/ffprobe**: Optional but recommended for video metadata and thumbnails
- **SQLite**: Bundled with Python, no external setup needed
- **Tom-Select**: CDN-loaded (multi-select dropdowns)
- **Alpine.js**: CDN-loaded (reactive UI framework)

### Browser Compatibility

- **Modern browsers only** (ES6+, CSS Grid, Intersection Observer API)
- **Mobile responsive** - Sidebar collapses, bottom sheet filters
- **No IE11 support** - Uses `async/await`, `fetch`, template literals

## Known Limitations & Gotchas

1. **Workflow format detection** - Assumes `nodes` array = UI format. Custom formats may fail.
2. **Multiprocessing on Windows** - Requires `if __name__ == '__main__'` guard
3. **Large galleries (>10K files)** - Initial sync can take 5-10 minutes, use progress overlay
4. **SQLite locking** - Single-writer limitation, avoid concurrent uploads from multiple clients
5. **Tom-Select state** - Must store instances globally for programmatic clearing (v1.40.6 fix)

## Common Tasks

### Adding a New Filter

1. Add HTML input in filter panel (`index.html` line ~1850)
2. Add Alpine.js reactive property: `filters.myFilter`
3. Update `_build_filter_conditions()` in `smartgallery.py` (~line 1603)
4. Add to `activeFilterPills` computed property for visual feedback

### Adding Workflow Metadata Fields

1. Update `ComfyUIWorkflowParser._extract_parameters()` (~line 605)
2. Add database column via schema migration in `init_db()`
3. Add to `workflow_metadata` table INSERT query (~line 1380)
4. Update filter UI if filterable

### Changing Thumbnail Generation

Edit `create_thumbnail()` function (~line 1238):
- Images: Pillow resize with `LANCZOS` filter
- Videos: ffmpeg extract first frame + resize
- Animated GIFs: Extract first frame, convert to WebP

## Version History Context

- **v1.39.0**: Multi-sampler support (schema v22)
- **v1.40.0**: Native UI/API format support (removed conversion)
- **v1.41.0**: SQL pagination (removed in-memory cache)
- **v1.50.0**: Prompt-first card design, enhanced UX

When editing code, check version-specific comments for rationale behind breaking changes.
