# SmartGallery Standalone Migration - Quick Reference

## TL;DR

**Status:** ✅ Ready to migrate (90% of code is already standalone)

**Complexity:** LOW - Mostly deletions, minimal changes

**Time:** 3-4 hours for MVP, 6-8 hours for production-ready

---

## What You're Removing (ComfyUI Integration Layer)

| File | Purpose | Lines | Action |
|------|---------|-------|--------|
| `__init__.py` | ComfyUI plugin entry point, subprocess launcher | 484 | DELETE |
| `js/galleryConfig.js` | ComfyUI sidebar dashboard | 814 | DELETE |
| `js/galleryConfig.css` | Sidebar styles | 819 | DELETE |
| `smart-comfyui-gallery.xml` | ComfyUI Manager metadata | ~20 | DELETE |

**Total lines removed:** ~2,137 lines  
**Core app affected:** 0 lines

---

## What You're Keeping (Standalone Core)

| File | Purpose | Changes |
|------|---------|---------|
| `smartgallery.py` | Flask app (3,500+ lines) | Minor cleanup (~20 lines) |
| `templates/index.html` | Frontend UI (2,700+ lines) | None |
| `static/galleryout/` | Static assets | None |
| `config.json` | Configuration | Simplify |
| `pyproject.toml` | Package metadata | Simplify |
| `LICENSE` | MIT License | None |
| `assets/` | Screenshots/docs | Update docs |

---

## Critical Code Changes

### 1. In `smartgallery.py` - Remove CORS (Line 850)

**Before:**
```python
CORS(app, resources={
    r"/smartgallery/*": {
        "origins": ["http://127.0.0.1:8000", "http://localhost:8000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

**After:**
```python
# CORS not needed for standalone version (single-origin)
```

---

### 2. In `smartgallery.py` - Remove Dashboard Routes (Lines 3223-3398)

**Delete these 5 routes:**
```python
@app.route('/smartgallery/stats')           # Line 3225
@app.route('/smartgallery/recent')          # Line 3282
@app.route('/smartgallery/sync_all')        # Line 3309
@app.route('/smartgallery/clear_cache')     # Line 3332
@app.route('/smartgallery/logs')            # Line 3372
```

**Impact:** None on gallery functionality (these were only for ComfyUI sidebar)

---

### 3. In `smartgallery.py` - Update Branding (Line 1, 3442)

**Before:**
```python
# Smart Gallery for ComfyUI
parser = argparse.ArgumentParser(description="Smart Gallery for ComfyUI")
parser.add_argument("--output-path", type=str, required=True, help="Path to ComfyUI's output directory.")
```

**After:**
```python
# SmartGallery - Standalone AI Media Gallery
parser = argparse.ArgumentParser(description="SmartGallery - Standalone Media Gallery")
parser.add_argument("--output-path", type=str, required=True, help="Path to your AI output directory.")
```

---

## New Files to Create

### 1. `requirements.txt`
```txt
Flask>=3.0.0
Pillow>=10.0.0
opencv-python>=4.8.0
tqdm>=4.66.0
```

**Note:** Removed `flask-cors` (not needed for standalone)

---

### 2. Updated `config.json.example`
```json
{
    "base_output_path": "/path/to/your/output",
    "base_input_path": "/path/to/your/input",
    "server_port": 8008,
    "ffprobe_manual_path": "",
    "enable_upload": true,
    "max_upload_size_mb": 100,
    "thumbnail_quality": 85
}
```

**Note:** Removed `"auto_detect_paths": true` (not applicable)

---

### 3. Updated `pyproject.toml`

**Remove this section:**
```toml
[tool.comfy]
PublisherId = "opj161"
DisplayName = "Smart Gallery"
```

**Update these fields:**
```toml
[project]
name = "smartgallery-standalone"
version = "2.0.0"
description = "Standalone AI image/video gallery with workflow metadata extraction"
```

---

## Git Commands

```bash
# 1. Create standalone branch
git checkout -b standalone

# 2. Remove integration files
git rm __init__.py
git rm -r js/
git rm smart-comfyui-gallery.xml
git commit -m "Remove ComfyUI integration layer"

# 3. Make code changes
# (Edit smartgallery.py, create requirements.txt, etc.)
git add -A
git commit -m "Clean up for standalone version"

# 4. Update documentation
# (Rewrite README.md, create INSTALLATION.md)
git add -A
git commit -m "Update documentation for standalone version"

# 5. Test and finalize
git commit -m "Standalone version ready for release"
git tag v2.0.0
```

---

## User-Facing Changes

### Installation

**Before (ComfyUI Plugin):**
```bash
# Install via ComfyUI Manager
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/smart-comfyui-gallery
# Restart ComfyUI
```

**After (Standalone):**
```bash
# Clone and install
git clone https://github.com/yourusername/smartgallery-standalone
cd smartgallery-standalone
pip install -r requirements.txt

# Configure
cp config.json.example config.json
# Edit config.json with your paths

# Run
python smartgallery.py
# Open http://localhost:8008/galleryout/
```

---

### Configuration

**Before (ComfyUI Plugin):**
- Auto-detects ComfyUI paths via `folder_paths` API
- Configure via ComfyUI sidebar tab
- Subprocess management automatic

**After (Standalone):**
- Manual path configuration in `config.json`
- Or override via CLI arguments
- Direct execution by user

---

## Feature Parity Matrix

| Feature | ComfyUI Plugin | Standalone | Status |
|---------|----------------|------------|--------|
| Gallery browsing | ✅ | ✅ | **Identical** |
| File upload | ✅ | ✅ | **Identical** |
| Workflow extraction | ✅ | ✅ | **Identical** |
| Filtering/search | ✅ | ✅ | **Identical** |
| Lightbox viewer | ✅ | ✅ | **Identical** |
| Database caching | ✅ | ✅ | **Identical** |
| Thumbnail generation | ✅ | ✅ | **Identical** |
| Batch operations | ✅ | ✅ | **Identical** |
| Folder management | ✅ | ✅ | **Identical** |
| ComfyUI sidebar | ✅ | ❌ | **Removed** (ComfyUI-only) |
| Auto-path detection | ✅ | ❌ | **Removed** (manual config) |
| Subprocess launcher | ✅ | ❌ | **Removed** (direct exec) |

---

## Testing Checklist

### Basic Functionality
- [ ] Server starts without errors
- [ ] Gallery loads at `http://localhost:8008/galleryout/`
- [ ] Files display correctly
- [ ] Thumbnails generate properly
- [ ] Lightbox opens and navigates
- [ ] Search/filter works
- [ ] Upload accepts files

### Workflow Extraction
- [ ] Workflow metadata extracted from ComfyUI PNGs
- [ ] Workflow metadata extracted from videos
- [ ] Node summary displays correctly
- [ ] Multi-sampler workflows parse correctly
- [ ] Files without workflows handled gracefully

### Configuration
- [ ] `config.json` paths respected
- [ ] CLI arguments override config.json
- [ ] Invalid paths show clear error messages
- [ ] Port configuration works
- [ ] FFprobe path configuration works

### Performance
- [ ] Large galleries (1000+ files) load quickly
- [ ] Pagination works correctly
- [ ] Database sync completes without errors
- [ ] Thumbnail cache rebuilds successfully

### Cross-Platform
- [ ] Windows: Paths with backslashes work
- [ ] Linux: Paths with forward slashes work
- [ ] macOS: Paths work correctly
- [ ] FFprobe detection works on all platforms

---

## Rollback Plan

If something goes wrong:

```bash
# Return to main branch
git checkout main

# Or delete standalone branch
git branch -D standalone

# Original ComfyUI plugin remains unchanged
```

**No risk to the main branch.** The standalone branch is completely independent.

---

## Deployment Options

### Option 1: Simple Python Script
```bash
python smartgallery.py --output-path /path/to/output --input-path /path/to/input
```

### Option 2: With Config File
```bash
# Edit config.json first
python smartgallery.py
```

### Option 3: As System Service (Linux)
```bash
sudo cp service/smartgallery.service /etc/systemd/system/
sudo systemctl enable smartgallery
sudo systemctl start smartgallery
```

### Option 4: Docker Container
```bash
docker-compose up -d
```

### Option 5: Standalone Executable (PyInstaller)
```bash
# Build executable
pyinstaller smartgallery.spec

# Distribute
dist/smartgallery.exe  # Windows
dist/smartgallery      # Linux/macOS
```

---

## Support Two Versions

### Recommended Branch Strategy

```
main (ComfyUI plugin)
  └── standalone (independent fork)
```

**Cherry-pick strategy:**
- Core feature updates → Cherry-pick to both branches
- UI updates → Cherry-pick to both branches
- Integration-specific → main only
- Standalone-specific → standalone only

**Maintenance:**
```bash
# On main branch: Add new gallery feature
git checkout main
# ... make changes ...
git commit -m "Add new filtering feature"

# Cherry-pick to standalone
git checkout standalone
git cherry-pick <commit-hash>
# Resolve any conflicts (usually none)
git push
```

---

## FAQ

**Q: Will the standalone version work with ComfyUI-generated files?**  
A: ✅ YES. The workflow extraction system is 100% independent. It works with ANY file that has ComfyUI workflow JSON embedded (PNG metadata, video metadata, etc.).

**Q: Do I need ComfyUI installed to run standalone version?**  
A: ❌ NO. Zero ComfyUI dependencies. Just Python + Flask + Pillow.

**Q: Will my database/cache from the ComfyUI plugin work with standalone?**  
A: ✅ YES. Same database schema, same cache structure. 100% compatible.

**Q: Can I run both versions simultaneously?**  
A: ⚠️ NOT RECOMMENDED on same paths. They share the same database file, which could cause conflicts. Use different output directories or run one at a time.

**Q: What about updates to the main ComfyUI plugin?**  
A: Cherry-pick feature updates to standalone branch. Integration-specific updates stay on main branch.

**Q: Will the standalone version be maintained?**  
A: Depends on community interest. If there's demand, it can be maintained alongside the plugin version.

---

## Resources

- **Detailed Analysis:** `standalone-migration-analysis.md`
- **Architecture Diagrams:** `architecture-comparison.md`
- **Original Project:** https://github.com/opj161/smart-comfyui-gallery
- **Flask Documentation:** https://flask.palletsprojects.com/
- **Alpine.js Documentation:** https://alpinejs.dev/

---

## Next Steps

1. **Read full analysis:** `standalone-migration-analysis.md`
2. **Review architecture:** `architecture-comparison.md`
3. **Create branch:** `git checkout -b standalone`
4. **Start migration:** Follow Phase 1-4 in detailed analysis
5. **Test thoroughly:** Use testing checklist above
6. **Deploy:** Choose deployment option that fits your needs

---

## Summary

Creating a standalone version is:
- ✅ **Straightforward** - Clear separation already exists
- ✅ **Low-risk** - No changes to core functionality
- ✅ **Quick** - 3-4 hours for MVP
- ✅ **Beneficial** - Broader audience, simpler deployment

The codebase architecture makes this migration exceptionally clean. Most work is **deletions**, not refactoring.

**Recommendation:** Proceed with confidence. The standalone version will be a cleaner, more accessible product for non-ComfyUI users.
