# 🧪 Experimental Features
⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**
Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!

### 👀 Check back often!
 
This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!
**Successful experiments will be integrated into official releases** after thorough testing and community feedback.
---

## Current experiments: Version 1.54.2-beta (New Features)
### Files: `templates/index.html` + smartgallery.py 

**Last updated:** 20 January 2026

### Description  

### 🎞️ Video Storyboard & Analysis - ffmpeg required 
*   **Quick Storyboard ('E'):** Hover over any video in the grid and press `E` to instantly open the storyboard. Focus is automatically preserved when closing, ensuring you never lose your spot.
*   **Grid Overview:** Instantly analyze video content with a clean **11-frame Grid (4-4-3 layout)** covering the entire duration from Start to the **True Last Frame**.
*   **Quality Awareness:** Includes a non-intrusive **Low-Res Warning (360p)** badge when zooming into frames, reminding users they are viewing a fast proxy, not the source resolution.
*   **Smart Hybrid Engine:** Uses a sophisticated backend that defaults to **Parallel Extraction** for speed, but automatically detects corrupt indices to switch to a **Safe Transcoding** mode.

### 📂 Advanced File Management
*   **Batch Copy:** Organize assets with precision. Now supports **Copy** with conflict resolution (auto-rename `file(1).png`).  

This release contains new beta features for the current production version (v1.54).  

---

## Model Management (NEW!)

Toggle between Images and Models view to manage your AI model library:

### Features
- 📊 View Checkpoints, Diffusion Models, LoRAs, and Embeddings
- 🔍 CivitAI Integration - Fetch metadata, trigger words, and tags
- 📝 Display model information: Name, Size, Triggers, Tags
- ⚡ Fast scanning with incremental updates

### Usage
1. Click the **Models** toggle in the sidebar
2. Select models with checkboxes
3. Click "🔍 Fetch CivitAI Metadata" to enrich model data

---

## How to install and test this beta version:

**⚠️ IMPORTANT:**
This beta version is a candidate for the next official release (v1.55).  
- Always backup your original file before testing

1. **Backup your current file:**
```bash
copy templates\index.html templates\index.html.backup
copy smartgallery.py smartgallery.py.backup
```
2. **Replace with experimental version:**
```bash
copy experiments\templates\index.html templates\index.html
copy experiments\smartgallery.py smartgallery.py
```
3. Restart the application and enjoy (...and test) the new features
4. **If something breaks - restore original:**
```bash
copy templates\index.html.backup templates\index.html
copy smartgallery.py.backup smartgallery.py
```

**For Docker Users**
- the process to use this beta version is to use the **make build_exp** which will provide a smartgallery:exp image

---

## We need you Feedback
**Everything works?** → Let us know, so we can officially realease this beta experimental version. Leave a message in the discussion area of this repo. 
Your feedback helps make these features stable for everyone. Thank you for testing! 🙏

**Found a bug?** → Open an issue with details  
