# 🧪 Experimental Features
⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**
Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!

### 👀 Check back often!

This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!
**Successful experiments will be integrated into official releases** after thorough testing and community feedback.
---

## Current experiments: Version 1.52.2 Beta
### Files: `templates/index.html` + smartgallery.py 

**Last updated:** 05 January 2026

### Seamless Infinite Scrolling
Browsing large galleries is now smoother and faster.
- **Auto-Loading:** Images automatically load as you scroll down, eliminating the need to repeatedly click "Load More".
- **High Performance:** Powered by the modern `IntersectionObserver` API, it ensures efficient memory usage and battery life on both Desktop and Mobile devices.

### UI/UX Modernization and lot of new features

This **beta release** introduces a comprehensive overhaul of the frontend interface, focusing on responsiveness, state management, and visual consistency.

- Modernized Design System: Implemented a unified "Glass/Dark" theme using CSS variables and backdrop-filters. The interface now features improved contrast ratios and reduced visual noise to focus on asset visualization.
- Mobile-First Architecture: The layout now fully adapts to mobile viewports. Key improvements include a collapsible navigation sidebar with independent internal scrolling and a responsive grid system for thumbnails.
- Asynchronous Modal System: Replaced native browser blocking calls (alert, confirm, prompt) with custom, non-blocking "Smart Dialogs". These modals use Javascript Promises (async/await) to maintain application flow and visual consistency.
- Contextual Action Bar: Batch operations (Delete, Move, Indexing) are now handled via a floating action bar that appears contextually upon selection, maximizing screen real estate.
- State Persistence: Improved notification system handling across page reloads using sessionStorage to ensure feedback visibility during file operations.

### Recursive Search & Smart Filter Persistence

The filtering system has been significantly upgraded to support recursive directory traversal and persistent search sessions during navigation.
Key Enhancements:
- Recursive Search Mode: A new "Include Subfolders" toggle is available in Search. When enabled, the gallery will scan the entire directory tree starting from the current folder, allowing you to find files regardless of their depth.
- Smart Navigation: Navigating between folders while filters are active no longer resets your search. Apply your current search filters to the newly selected folder.
- Dynamic Filter Discovery: Dropdown menus for File Extensions and Filename Prefixes now update dynamically via AJAX. If you toggle "Include Subfolders," the filters immediately reflect all file types found throughout the entire sub-tree without a page reload.
- Intelligent UI & UX:

### Real-time Transcoding Bridge (ProRes / `.mov` support)

This feature introduces a **real-time transcoding pipeline** that allows SmartGallery to preview **ProRes `.mov` files directly in the browser**.
This is especially useful for:
-  **macOS users**
-  Video creators exporting **ProRes** from Final Cut Pro, DaVinci Resolve, or Premiere
-  Anyone working with **high-quality `.mov` files** that browsers normally can't play

**How it works:**
- When SmartGallery detects a `.mov` file (commonly ProRes)
- It automatically launches ffmpeg in the background
- The video is **transcoded on-the-fly** into a browser-friendly **H.264 stream**
- A new `/stream/` route pipes ffmpeg output **directly to the HTML5 video player**
- ✅ No intermediate files, no manual conversion!
**Requirements:**
- `ffmpeg` must be installed on your system
- `ffprobe` path must be correctly configured:
```env
  FFPROBE_MANUAL_PATH=/path/to/ffprobe
```

---

### The rest of the New Features:

- **Automatic refresh** the current folder. Set a silent auto-refresh timer to detect new files in background, no longer manual refreshing.
- Full Resizable and hide the left sidebar (directory tree)
- Keyboard shortcut `C` - copies image workflow to clipboard for pasting in ComfyUI (Ctrl+V)

---

## How to install and test this beta version:

**⚠️ IMPORTANT:**
- This version may be unstable
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

