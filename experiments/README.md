# 🧪 Experimental Features
⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**
Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!

### 👀 Check back often!
 
This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!
**Successful experiments will be integrated into official releases** after thorough testing and community feedback.
---

## Current experiments: Version 1.54.6-beta (New Features)
### Files: `templates/index.html` + smartgallery.py 

**Last updated:** 29 January 2026

### Description  

### Thumbnail Grid Size Option in the new ⚙️Options Menu  
*   **Adjustable Thumbnail Size:** Users can choose between `Normal` (320px width) and `Compact` (220px width) thumbnail sizes.
*   **Persistent Preference:** The selected thumbnail size is saved in the browser's local storage, ensuring that the user's preference is remembered across sessions.
*   **Improved Information Density:** The `Compact` view allows more files to be displayed on screen simultaneously, making it easier to browse large collections.

#### **⚙️ Usability & Bandwidth Control (NEW)**
The gallery now provides advanced controls to manage video playback and bandwidth usage, especially crucial for servers with slow upload speeds.
*   **Options Menu:** A new **`⚙️ Options`** button is available next to the Shortcuts button (Desktop & Mobile).
*   **Video Autoplay Toggle:** This menu introduces a persistent, session-based setting: **`▶️ Video Autoplay`**.
    *   **Default:** Autoplay is **OFF** (Click-to-Play).
    *   **Function:** Disabling Autoplay saves bandwidth by preventing the browser from pre-buffering all videos in the grid.
*   **Keyboard Shortcut:** Toggle Autoplay state instantly by pressing the **`P`** key.
*   **Smart Interaction (Desktop):** When Autoplay is OFF, clicking the **small corner ▶️ icon** plays the video directly inside the thumbnail without launching the Lightbox. Clicking anywhere else on the thumbnail behaves normally (Selection/Lightbox).
*   **Smart Interaction (Mobile):** When Autoplay is OFF, tapping anywhere on the thumbnail opens the Lightbox (Click-to-Open).

#### **⚡ Focus Mode (Professional Workflow)**
Designed for production houses and power users who need maximum density and minimal distraction.
*   **Toggle:** Click the **`⚡ Focus Mode`** button in the header or press **`Q`**.
*   **Minimal UI:** Strips away metadata, buttons, and badges. Thumbnails remain at 100% quality/opacity.
*   **High-Visibility Selection:** Selected items "pop out" with a massive **High-Contrast Neon/White double border**, visible on any background.
*   **Workflow Shift:** In this mode, **Clicking an image toggles Selection** (for batch operations). To open the Lightbox, use the **`V`** shortcut.
*   **Persistent:** Remembers your preference between sessions.

#### **⌨️ Enhanced Keyboard & Help Interface**
*   **New Help Panel:** A redesigned, responsive **4-column cheat sheet** accessible via the **`? Shortcuts`** button or the **`?`** key.
*   **Standard Navigation:** Now documents OS-standard keys (`Home`, `End`, `PgUp`, `PgDn`, `Ctrl+Click`, `Shift+Click`).
*   **Cross-Platform:** Automatically detects MacOS and switches labels from `Ctrl` to `⌘` (Command) for a native experience.
*   **Accessible:** The Help button is now permanently visible in the desktop header for quick reference.

### 🎞️ Video Storyboard & Analysis - ffmpeg required 
*   **Quick Storyboard ('E'):** Hover over any video in the grid and press `E` to instantly open the storyboard. Focus is automatically preserved when closing, ensuring you never lose your spot.
*   **Grid Overview:** Instantly analyze video content with a clean **11-frame Grid (4-4-3 layout)** covering the entire duration from Start to the **True Last Frame**.
*   **Quality Awareness:** Includes a non-intrusive **Low-Res Warning (360p)** badge when zooming into frames, reminding users they are viewing a fast proxy, not the source resolution.
*   **Smart Hybrid Engine:** Uses a sophisticated backend that defaults to **Parallel Extraction** for speed, but automatically detects corrupt indices to switch to a **Safe Transcoding** mode.

#### **⚡ Advanced Workflow & Metadata Engine**
The gallery now features a high-performance, hybrid metadata extraction engine designed specifically for ComfyUI.
*   **Generation Dashboard:** A new, structured UI panel at the top of the Node Summary provides an "at-a-glance" view of the most important generation data (Real Seed, Model, Sampler, CFG, LoRAs).
*   **Deep Graph Tracing:** SmartGallery traces actual node connections (supporting both API and UI formats) to identify exact parameters, resolving linked values even if they come from separate "Seed Generator" or "Literal" nodes.
*   **Smart Prompt Cleaning:** Automatically strips LoRA tags, weights, and technical noise to provide a human-readable description while maintaining full raw data for advanced users.

#### **🚀 Rapid Navigation**
*   **"Hover-First" Interaction:** Speed up your workflow in Grid View. Shortcuts like **`N`** (Node Summary), **`V`** (View), **`F`** (Favorite), and **`Del`** (Quick Delete) now trigger immediately on the image under your mouse cursor.
*   **Smart "Move" Command:** Pressing **`M`** behaves intelligently:
    *   If you have a batch selected: It opens the Move panel for those files.
    *   If nothing is selected: It auto-selects the file under your cursor and opens the Move panel instantly.

#### **📂 Transparent Path & File Management**
*   **Mount Point Awareness:** The system distinguishes between logical gallery paths and real physical sources.
*   **Advanced Folder Info:** For mounted folders, symlinks, or Windows Junctions, the "Info" menu provides full transparency by displaying the exact physical location of the data on the server disk.
*   **Background Rescanning:** Heavy folder rescans are handled by non-blocking background workers with real-time progress polling.


### 📝 CHANGELOG.md

#### **[1.54.6-beta] - 2026-01-29**

**Added**
*   **Thumbnail Grid Size:** Added a new toggle in the Options menu (`⚙️`) allowing users to switch between **Normal** and **Compact** view on desktop. This preference is saved automatically.

#### **[1.54.5-beta] - 2026-01-27**

**Added**
- **Options Menu & Autoplay Toggle:** New persistent **`⚙️ Options`** menu (Desktop/Mobile) to manage core gallery settings.
- **Video Autoplay Control:** Introduced a session-based toggle to explicitly enable/disable video autoplay in the grid. (Default: **OFF** to save bandwidth).
- **'P' Shortcut:** Added the **`P`** key shortcut to quickly toggle the Video Autoplay setting.
- **Dynamic UX for Videos:**
    - On **Desktop**, when Autoplay is OFF, a small **▶️ icon** appears in the corner. Clicking it plays the video **in-grid** for quick preview.
    - On **Mobile**, the thumbnail is fully clickable to open the Lightbox (Click-to-Open).
- **Visual Feedback:** Added a full-screen loader (`loader-overlay`) to prevent interaction during the necessary page reload after changing the Autoplay setting.

#### **[1.54.4-beta] - 2026-01-26**

**Added**
- **Focus Mode:** A new streamlined view for professionals. Hides UI clutter and changes click behavior to "Select Only" for rapid batching. Accessible via the **`⚡`** button or **`Q`** key.
- **Shortcuts Button:** Added a dedicated `? Shortcuts` button in the desktop header.
- **Platform Detection:** The Shortcuts panel now automatically displays `⌘` symbols for Mac users and `Ctrl` for Windows/Linux.

**Changed**
- **Header Layout:** Reorganized the top bar to group tools (`Shortcuts`, `Focus Mode`, `AI Manager`) on the right side for better desktop usability.


#### **[1.54.3-beta] - 2026-01-25**

**Added**
- **Generation Dashboard:** Added a high-fidelity summary panel at the top of the Node Summary to show Seed, Model, Steps, and Prompts at a glance.
- **Grid View Shortcuts:** Enabled `N` (Node Summary) and other action keys directly in Grid View via mouse hover.
- **Smart Move (`M`):** The Move shortcut now detects context: if no files are selected, it automatically selects the hovered item and opens the dialog.
- **Real Path Resolution:** New "Folder Info" tool that resolves and displays the physical path on disk (useful for Docker volumes and Symlinks).
- **Asynchronous Rescan:** Re-engineered the "Rescan Folder" feature to run in a background thread to avoid 502/Timeout errors on massive libraries.

**Changed**
- **Unified Shortcut Logic:** Completely rewrote input handling. **Mouse Hover** now strictly takes priority over **Keyboard Focus** for all actions. This fixes inconsistencies where shortcuts would target the wrong file after closing the Lightbox.
- **Help UI Overhaul:** Redesigned the Keyboard Shortcuts (`?`) overlay into a clean, responsive layout.
- **Hybrid Parser:** Integrated `ComfyMetadataParser` to support both API-format and UI-format JSON metadata simultaneously for better accuracy.

**Fixed**
- **KSampler Data Alignment:** Fixed a critical parsing issue in Node Summary where the missing `control_after_generate` field caused values (Steps, CFG, Sampler) to shift and display incorrectly.
- **Focus Loss Bug:** Fixed an issue where the `V` key became unresponsive after returning to the grid until the mouse was moved.
- **Resolution Display:** Fixed an issue where linked resolutions appeared as node IDs (e.g., "41,0") instead of actual dimensions.


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