# 🧪 Experimental Features
⚠️ **WARNING: EXPERIMENTAL AND POTENTIALLY UNSTABLE CODE**
Files in this folder are under active development and **may contain bugs or break functionality**. Use at your own risk!

### 👀 Check back often!

This folder is updated regularly with new experimental features. If you're interested in testing cutting-edge functionality, **check this folder frequently** for updates!
**Successful experiments will be integrated into official releases** after thorough testing and community feedback.
---

## Current experiments: Version 1.53.1 Beta (Hotfix)
### Files: `templates/index.html` + smartgallery.py 

**Last updated:** 09 January 2026

### Description
This release contains critical fixes and workflow improvements for the current production version (v1.53).  
It addresses specific issues reported by macOS users and restores some beloved UI shortcuts.  
**🛠️ Critical Bug Fixes**  
- MacOS Metadata Stability: Fixed a critical issue on macOS where Favorites and AI metadata were failing to save or appearing to reset upon page reload.  
This was caused by microsecond precision differences in file timestamps between the OS and the Database.  
The system now tolerates negligible timing variations (floating point precision fix).

**⚡ UI & Workflow Improvements**  
- "Hover-to-Favorite" Restored: You can now toggle favorites by simply hovering your mouse over an image and pressing F. Clicking to focus the item is no longer required, restoring the faster workflow from previous versions.  
- New Filter Shortcut: Added the T shortcut to quickly toggle the Filters Panel.  
Pressing T will toggle the visibility of the search/filter bar.  
It automatically scrolls the page to the top to ensure the panel is immediately visible and accessible.  
- Help Menu Updated: The Keyboard Shortcuts legend (?) has been updated to include the new commands.

## How to install and test this beta version:

**⚠️ IMPORTANT:**
This version is a candidate for the next stable patch (1.53.1).  
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
