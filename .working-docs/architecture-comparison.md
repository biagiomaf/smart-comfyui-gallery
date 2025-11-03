# SmartGallery Architecture - Current vs Standalone

## Current Architecture (ComfyUI Plugin)

```
┌─────────────────────────────────────────────────────────────────┐
│                         ComfyUI Process                         │
│                          (Port 8000)                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  __init__.py (Plugin Entry Point)                        │  │
│  │  - Subprocess launcher                                   │  │
│  │  - Config API (aiohttp routes)                           │  │
│  │  - Auto-path detection (folder_paths)                    │  │
│  │  - SmartGalleryExtension (ComfyExtension)                │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │ subprocess.Popen()                            │
│                 ↓                                                │
└─────────────────┼────────────────────────────────────────────────┘
                  │
                  │ launches
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SmartGallery Process                          │
│                      (Port 8008)                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  smartgallery.py (Flask App)                             │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  /galleryout/* routes (Gallery)                     │ │  │
│  │  │  - Main gallery UI                                  │ │  │
│  │  │  - File browsing/upload                             │ │  │
│  │  │  - Workflow extraction                              │ │  │
│  │  │  - SQLite database                                  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  /smartgallery/* routes (Dashboard API)            │ │  │
│  │  │  - Stats endpoint                                  │ │  │
│  │  │  - Recent files                                    │ │  │
│  │  │  - Sync/clear cache                                │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  templates/index.html (Frontend)                         │  │
│  │  - Alpine.js SPA                                         │  │
│  │  - Calls /galleryout/* only                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         ↑
                         │ CORS requests
                         │ (port 8008 ← port 8000)
                         │
┌─────────────────────────────────────────────────────────────────┐
│                    ComfyUI Web UI                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  js/galleryConfig.js (Sidebar Tab)                       │  │
│  │  - Dashboard stats display                               │  │
│  │  - Config UI                                             │  │
│  │  - Recent files preview                                  │  │
│  │  - Calls /smartgallery/* API                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘


                    ComfyUI Integration Layer
                  ┌─────────────────────────────┐
                  │  __init__.py               │
                  │  js/galleryConfig.js       │
                  │  js/galleryConfig.css      │
                  │  smart-comfyui-gallery.xml │
                  │  CORS config               │
                  │  /smartgallery/* routes    │
                  └─────────────────────────────┘
```

---

## Standalone Architecture (After Migration)

```
┌─────────────────────────────────────────────────────────────────┐
│                   SmartGallery Process                          │
│                      (Port 8008)                                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  smartgallery.py (Flask App)                             │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  /galleryout/* routes (Gallery)                     │ │  │
│  │  │  - Main gallery UI                                  │ │  │
│  │  │  - File browsing/upload                             │ │  │
│  │  │  - Workflow extraction                              │ │  │
│  │  │  - SQLite database                                  │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  templates/index.html (Frontend)                         │  │
│  │  - Alpine.js SPA                                         │  │
│  │  - Calls /galleryout/* only                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Optional: templates/settings.html                       │  │
│  │  - Web-based configuration UI                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         ↑
                         │
                 ┌───────┴──────────┐
                 │                  │
          Direct execution    Or run as service
                 │                  │
          python smartgallery.py   systemd/Windows Service


         Executed directly by user
       ┌─────────────────────────┐
       │  Config Sources:       │
       │  1. config.json        │
       │  2. CLI arguments      │
       │  3. Environment vars   │
       └─────────────────────────┘
```

---

## File Structure Comparison

### Current (ComfyUI Plugin)
```
smart-comfyui-gallery/
├── __init__.py                    ← ❌ DELETE (ComfyUI integration)
├── smartgallery.py                ← ✅ KEEP (minor cleanup)
├── config.json                    ← ✅ KEEP (simplify)
├── config.json.example            ← ✅ KEEP (update)
├── templates/
│   └── index.html                 ← ✅ KEEP (no changes)
├── static/
│   └── galleryout/                ← ✅ KEEP (no changes)
├── js/
│   ├── galleryConfig.js           ← ❌ DELETE (sidebar dashboard)
│   └── galleryConfig.css          ← ❌ DELETE (sidebar styles)
├── pyproject.toml                 ← ✅ KEEP (simplify)
├── smart-comfyui-gallery.xml      ← ❌ DELETE (ComfyUI Manager)
├── README.md                      ← ✅ KEEP (rewrite)
├── LICENSE                        ← ✅ KEEP (no changes)
└── assets/                        ← ✅ KEEP (update screenshots)
```

### Standalone Version
```
smartgallery-standalone/
├── smartgallery.py                ← Core app (cleaned)
├── config.json.example            ← Configuration template
├── requirements.txt               ← NEW: Python dependencies
├── templates/
│   ├── index.html                 ← Gallery UI (unchanged)
│   └── settings.html              ← NEW (optional): Web config UI
├── static/
│   └── galleryout/                ← Static assets (unchanged)
├── pyproject.toml                 ← Simplified metadata
├── README.md                      ← Standalone documentation
├── INSTALLATION.md                ← NEW: Setup guide
├── LICENSE                        ← MIT License (unchanged)
├── docker/                        ← NEW (optional): Docker support
│   ├── Dockerfile
│   └── docker-compose.yml
└── service/                       ← NEW (optional): System services
    ├── smartgallery.service       ← Linux systemd
    └── smartgallery-install.bat   ← Windows service installer
```

---

## Data Flow Comparison

### Current (ComfyUI Plugin)
```
User opens ComfyUI
    ↓
__init__.py loads
    ↓
Auto-detects paths (folder_paths API)
    ↓
Launches smartgallery.py subprocess
    ↓
Flask app starts on port 8008
    ↓
User opens http://localhost:8008/galleryout/
    ↓
Frontend (index.html) loads
    ↓
Makes API calls to /galleryout/*
    ↓
Gallery displays files from ComfyUI's output folder

Sidebar Dashboard:
    User clicks "Gallery" tab in ComfyUI
        ↓
    js/galleryConfig.js loads
        ↓
    Makes CORS requests to http://localhost:8008/smartgallery/*
        ↓
    Displays stats, recent files, config UI
```

### Standalone Version
```
User configures config.json (one-time)
    ↓
User runs: python smartgallery.py
    ↓
Flask app starts on port 8008
    ↓
User opens http://localhost:8008/galleryout/
    ↓
Frontend (index.html) loads
    ↓
Makes API calls to /galleryout/*
    ↓
Gallery displays files from configured output folder

Optional Settings UI:
    User clicks "Settings" in gallery
        ↓
    templates/settings.html loads
        ↓
    Makes API calls to /galleryout/save_settings
        ↓
    Updates config.json
        ↓
    User restarts app for changes to take effect
```

---

## Dependency Graph

### Current (ComfyUI Plugin)

```
__init__.py
├── Requires: ComfyUI
│   ├── server.PromptServer
│   ├── folder_paths
│   ├── comfy_api.latest
│   └── aiohttp
└── Launches: smartgallery.py

smartgallery.py
├── Requires: Standard Python
│   ├── Flask
│   ├── flask-cors (for sidebar)
│   ├── Pillow
│   ├── opencv-python
│   └── tqdm
└── Serves: templates/index.html

templates/index.html
├── Requires: CDN Libraries
│   ├── Alpine.js
│   └── Tom-Select
└── Calls: /galleryout/* routes

js/galleryConfig.js
├── Requires: ComfyUI
│   ├── /scripts/app.js
│   └── /scripts/api.js
└── Calls: /smartgallery/* routes (CORS)
```

### Standalone Version

```
smartgallery.py
├── Requires: Standard Python
│   ├── Flask
│   ├── Pillow
│   ├── opencv-python
│   └── tqdm
└── Serves: templates/index.html

templates/index.html
├── Requires: CDN Libraries
│   ├── Alpine.js
│   └── Tom-Select
└── Calls: /galleryout/* routes

config.json
└── Read by: smartgallery.py
```

**Note:** NO external dependencies. Everything is self-contained.

---

## Workflow Metadata Extraction (Both Versions)

**Important:** The workflow extraction system is **100% independent** of ComfyUI.

```
┌─────────────────────────────────────────────────────────────┐
│  ComfyUIWorkflowParser (in smartgallery.py)                 │
│                                                              │
│  Input: PNG/MP4/WebP file with embedded JSON metadata       │
│         ↓                                                    │
│  1. Read file bytes                                         │
│  2. Search for JSON workflow in metadata                    │
│  3. Parse workflow structure (UI or API format)             │
│  4. Trace node graph to find samplers                       │
│  5. Extract metadata:                                       │
│     - Model name                                            │
│     - Positive/negative prompts                             │
│     - Sampler/scheduler                                     │
│     - CFG, steps, seed                                      │
│     - Dimensions                                            │
│         ↓                                                    │
│  Output: Structured metadata dictionary                     │
│                                                              │
│  Works with files from:                                     │
│  ✅ ComfyUI (generated directly)                            │
│  ✅ Uploaded from other machines                            │
│  ✅ Received via Discord/web                                │
│  ✅ Any tool that embeds ComfyUI workflow JSON              │
└─────────────────────────────────────────────────────────────┘
```

**This parser has ZERO dependencies on ComfyUI being installed or running.**

---

## Migration Checklist

### Files to Delete
- [ ] `__init__.py`
- [ ] `js/galleryConfig.js`
- [ ] `js/galleryConfig.css`
- [ ] `smart-comfyui-gallery.xml`

### Files to Modify
- [ ] `smartgallery.py`
  - [ ] Remove CORS config
  - [ ] Delete/comment `/smartgallery/*` routes
  - [ ] Update branding/comments
  - [ ] (Optional) Enhance CLI args

- [ ] `config.json.example`
  - [ ] Remove `auto_detect_paths` option
  - [ ] Add usage instructions

- [ ] `pyproject.toml`
  - [ ] Remove `[tool.comfy]` section
  - [ ] Update project name/description

- [ ] `README.md`
  - [ ] Rewrite for standalone usage
  - [ ] Update installation instructions
  - [ ] Update feature list

### Files to Create
- [ ] `requirements.txt`
- [ ] `INSTALLATION.md`
- [ ] (Optional) `templates/settings.html`
- [ ] (Optional) `docker/Dockerfile`
- [ ] (Optional) `service/smartgallery.service`

### Testing
- [ ] Fresh install in clean Python environment
- [ ] Test gallery browsing
- [ ] Test file upload
- [ ] Test workflow extraction
- [ ] Test filtering/search
- [ ] Test configuration methods
- [ ] Cross-platform testing (Windows/Linux/macOS)

---

## Summary

**Key Insight:** The architecture is already 90% standalone. The main app (`smartgallery.py` + `templates/index.html`) is a self-contained Flask application. The ComfyUI integration is a **thin wrapper** that:

1. Launches the app as a subprocess
2. Provides a sidebar dashboard
3. Auto-detects paths

Removing this wrapper creates a **fully standalone** application with:
- ✅ Same features
- ✅ Same UI
- ✅ Same workflow extraction
- ✅ Zero ComfyUI dependencies
- ✅ Direct execution model

**Effort:** Low (mostly deletions)  
**Risk:** Minimal (no core logic changes)  
**Benefit:** High (broader audience, simpler deployment)
