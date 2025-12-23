# 🧪 Experimental Features

⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**

Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!

## 👀 Check back often!

This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!

**Successful experiments will be integrated into official releases** after thorough testing and community feedback.

---

## Current experiments

### Files: `templates/index.html` + smartgallery.py - ProRes .mov support

### 🎥 Real-time Transcoding Bridge (ProRes / `.mov` support)
**Last updated:** 23 December 2025

**What is this?**  
This experimental feature introduces a **real-time transcoding pipeline** that allows SmartGallery to preview **ProRes `.mov` files directly in the browser**.

This is especially useful for:
- 🍎 **macOS users**
- 🎬 Video creators exporting **ProRes** from Final Cut Pro, DaVinci Resolve, or Premiere
- 🖥️ Anyone working with **high-quality `.mov` files** that browsers normally can’t play

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

** All the New features:**
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