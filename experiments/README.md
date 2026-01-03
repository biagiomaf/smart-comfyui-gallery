# 🧪 Experimental Features
⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**
Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!
## 👀 Check back often!
This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!
**Successful experiments will be integrated into official releases** after thorough testing and community feedback.
---
## Current experiments
### Files: `templates/index.html` + smartgallery.py 

### 📂 Recursive Search & Smart Filter Persistence

**Last updated:** 24 December 2025

**What is this?**  

The filtering system has been significantly upgraded to support recursive directory traversal and persistent search sessions during navigation.
Key Enhancements:
- Recursive Search Mode: A new "Include Subfolders" toggle is available in Search. When enabled, the gallery will scan the entire directory tree starting from the current folder, allowing you to find files regardless of their depth.
- Smart Navigation Modal: Navigating between folders while filters are active no longer resets your search. A new stylized modal allows you to:
- Keep Filters & Navigate: Apply your current search terms, extensions, and date ranges to the newly selected folder.
- Reset & Browse: Clear filters and browse the target folder in its default state.
- Dynamic Filter Discovery: Dropdown menus for File Extensions and Filename Prefixes now update dynamically via AJAX. If you toggle "Include Subfolders," the filters immediately reflect all file types found throughout the entire sub-tree without a page reload.
- Intelligent UI & UX:
- Context-Aware: The recursive option is automatically managed based on search scope (e.g., disabled during Global Search as it is already implicit).
- Keyboard Accessible: The navigation modal supports immediate keyboard confirmation (Focus on "Keep Filters"), optimized for large desktop screens.


### 🎥 Real-time Transcoding Bridge (ProRes / `.mov` support)

This experimental feature introduces a **real-time transcoding pipeline** that allows SmartGallery to preview **ProRes `.mov` files directly in the browser**.
This is especially useful for:
- 🍎 **macOS users**
- 🎬 Video creators exporting **ProRes** from Final Cut Pro, DaVinci Resolve, or Premiere
- 🖥️ Anyone working with **high-quality `.mov` files** that browsers normally can't play

**How it works:**
- When SmartGallery detects a `.mov` file (commonly ProRes)
- It automatically launches **ffmpeg in the background**
- The video is **transcoded on-the-fly** into a browser-friendly **H.264 stream**
- A new `/stream/` route pipes ffmpeg output **directly to the HTML5 video player**
- ✅ No intermediate files, no manual conversion
**Requirements:**
- `ffmpeg` must be installed on your system
- `ffprobe` path must be correctly configured:
```env
  FFPROBE_MANUAL_PATH=/path/to/ffprobe
```
---
**All the New features:**
- 🎥 Real-time Transcoding Bridge (ProRes / `.mov` support)
- ✨ Automatic auto-refresh of current folder
- 📏 Resizable left sidebar (directory tree)
- ⌨️ Keyboard shortcut `C` - copies image workflow to clipboard for pasting in ComfyUI (Ctrl+V)
**⚠️ IMPORTANT:**
- This version **may be unstable**
- **Always backup** your original file before testing
- If something **doesn't work or breaks**, please:
  1. **Restore the original file** immediately
  2. **Open an issue** on GitHub describing the problem
  3. Include your browser and OS information
**How to test:**
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
3. Restart the application and test the new features
4. **If something breaks - restore original:**
```bash
copy templates\index.html.backup templates\index.html
copy smartgallery.py.backup smartgallery.py
```
## Feedback
**Found a bug?** → Open an issue with details  
**Everything works?** → Let us know too!
Your feedback helps make these features stable for everyone. Thank you for testing! 🙏
