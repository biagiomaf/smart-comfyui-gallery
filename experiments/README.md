# 🧪 Experimental Features
⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**
Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!

### 👀 Check back often!
 
This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!
**Successful experiments will be integrated into official releases** after thorough testing and community feedback.
---

## Current experiments: Version 1.54.3-beta (New Features)
### Files: `templates/index.html` + smartgallery.py 

**Last updated:** 25 January 2026

### Description  

### 🎞️ Video Storyboard & Analysis - ffmpeg required 
*   **Quick Storyboard ('E'):** Hover over any video in the grid and press `E` to instantly open the storyboard. Focus is automatically preserved when closing, ensuring you never lose your spot.
*   **Grid Overview:** Instantly analyze video content with a clean **11-frame Grid (4-4-3 layout)** covering the entire duration from Start to the **True Last Frame**.
*   **Quality Awareness:** Includes a non-intrusive **Low-Res Warning (360p)** badge when zooming into frames, reminding users they are viewing a fast proxy, not the source resolution.
*   **Smart Hybrid Engine:** Uses a sophisticated backend that defaults to **Parallel Extraction** for speed, but automatically detects corrupt indices to switch to a **Safe Transcoding** mode.

### 📂 Advanced File Management
*   **Batch Copy:** Organize assets with precision. Now supports **Copy** with conflict resolution (auto-rename `file(1).png`).  

#### **⚡ Advanced Workflow & Metadata Engine**
The gallery now features a high-performance, hybrid metadata extraction engine designed specifically for ComfyUI.
*   **Generation Dashboard:** A new, structured UI panel at the top of the Node Summary provides an "at-a-glance" view of the most important generation data (Real Seed, Model, Sampler, CFG, LoRAs).
*   **Deep Graph Tracing:** SmartGallery traces actual node connections (supporting both API and UI formats) to identify exact parameters, resolving linked values even if they come from separate "Seed Generator" or "Literal" nodes.
*   **Smart Prompt Cleaning:** Automatically strips LoRA tags, weights, and technical noise to provide a human-readable description while maintaining full raw data for advanced users.

#### **🚀 Rapid Navigation & Shortcuts**
*   **"Hover-First" Interaction:** Speed up your workflow in Grid View. Shortcuts like **`N`** (Node Summary), **`V`** (View), **`F`** (Favorite), and **`Del`** (Quick Delete) now trigger immediately on the image under your mouse cursor. If the mouse is idle, they apply to the currently focused item.
*   **Smart "Move" Command:** Pressing **`M`** behaves intelligently:
    *   If you have a batch selected: It opens the Move panel for those files.
    *   If nothing is selected: It auto-selects the file under your cursor and opens the Move panel instantly.
*   **Redesigned Help:** Press **`?`** to view the new, organized 3-column shortcut cheat sheet.

#### **📂 Transparent Path & File Management**
*   **Mount Point Awareness:** The system distinguishes between logical gallery paths and real physical sources.
*   **Advanced Folder Info:** For mounted folders, symlinks, or Windows Junctions, the "Info" menu provides full transparency by displaying the exact physical location of the data on the server disk.
*   **Background Rescanning:** Heavy folder rescans are handled by non-blocking background workers with real-time progress polling, preventing timeouts on large directories.


### 📝 CHANGELOG.md

#### **[1.54.2-beta] - 2026-01-25**

**Added**
- **Generation Dashboard:** Added a high-fidelity summary panel at the top of the Node Summary to show Seed, Model, Steps, and Prompts at a glance.
- **Grid View Shortcuts:** Enabled `N` (Node Summary) and other action keys directly in Grid View via mouse hover.
- **Smart Move (`M`):** The Move shortcut now detects context: if no files are selected, it automatically selects the hovered item and opens the dialog.
- **Real Path Resolution:** New "Folder Info" tool that resolves and displays the physical path on disk (useful for Docker volumes and Symlinks).
- **Asynchronous Rescan:** Re-engineered the "Rescan Folder" feature to run in a background thread to avoid 502/Timeout errors on massive libraries.

**Changed**
- **Unified Shortcut Logic:** Completely rewrote input handling. **Mouse Hover** now strictly takes priority over **Keyboard Focus** for all actions. This fixes inconsistencies where shortcuts would target the wrong file after closing the Lightbox.
- **Help UI Overhaul:** Redesigned the Keyboard Shortcuts (`?`) overlay into a clean, responsive 3-column layout (Global, Grid, Lightbox).
- **Hybrid Parser:** Integrated `ComfyMetadataParser` to support both API-format and UI-format JSON metadata simultaneously for better accuracy.

**Fixed**
- **KSampler Data Alignment:** Fixed a critical parsing issue in Node Summary where the missing `control_after_generate` field caused values (Steps, CFG, Sampler) to shift and display incorrectly.
- **Focus Loss Bug:** Fixed an issue where the `V` key became unresponsive after returning to the grid until the mouse was moved.
- **Resolution Display:** Fixed an issue where linked resolutions appeared as node IDs (e.g., "41,0") instead of actual dimensions.
- **JSON List Crash:** Fixed a critical backend error when parsing non-standard JSON structures in certain workflows.


This release contains new beta features for the current production version (v1.54).  


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
