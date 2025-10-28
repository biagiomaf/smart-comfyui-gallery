# SmartGallery for ComfyUI ✨
### Your Visual Hub with Universal Workflow Recall, Upload Magic & Intelligent Organization

<p align="center">
  <img src="assets/gallery_from_pc_screen.png" alt="SmartGallery Interface" width="800">
</p>

<p align="center">
  <img src="assets/smartgallery-3.jpg" alt="SmartGallery Interface" width="800">
</p>

<p align="center">
  <em>🎨 Beautiful, lightning-fast gallery that remembers the exact workflow behind every single creation</em>
</p>

<p align="center">
  <img src="assets/node_summary.png" alt="Node Summary" width="500">
</p>
<p align="center">
  <em>🔍 Instant workflow insights - Node Summary</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <a href="https://github.com/biagiomaf/smart-comfyui-gallery/stargazers"><img src="https://img.shields.io/github/stars/biagiomaf/smart-comfyui-gallery?style=social" alt="GitHub stars"></a>
</p>

---

## 🆕 What's New in Version 1.31?

- ⚡ Parallel processing: Initial scan now 10-20x faster (minutes → seconds)
- 🔍 **Smart Folder Navigation**: Expandable sidebar with real-time search and bi-directional sorting (A-Z, Z-A, newest, oldest)
- 🖼️ **Enhanced Gallery Sorting**: Toggle thumbnail sorting by date or name with visual indicators
- 🔎 **Advanced Lightbox**: Zoom with mouse wheel, persistent zoom levels, percentage display, rename and quick delete
- ⚡ **Real-time Sync**: Silent background checks with visual progress overlay when new files are detected
- 📝 **Smart Workflow Names**: Downloaded workflows now match your image filenames

---

## 🚀 The Problem Every ComfyUI User Faces

You've just created the most stunning AI image or video of your life. It's perfect. Absolutely perfect.

**But wait... what workflow did you use?** 😱

Hours later, you're desperately trying to recreate that magic, clicking through endless nodes, tweaking parameters, and pulling your hair out because you can't remember the exact recipe that made it work.

**Plus, what about those amazing AI images someone shared with you? Or that perfect generation you saved from Discord?** You want to know the workflow, but you can't load it into your gallery...

**This stops now.**

---

## 🎯 What Makes SmartGallery Revolutionary

SmartGallery isn't just another image viewer. It's a **time machine for your creativity** that automatically links every single file you've ever generated to its exact workflow—whether it's PNG, JPG, MP4, or WebP.

### ⚡ Key Features That Will Transform Your Workflow

- 🏃‍♂️ **Blazing Fast**: SQLite database + smart caching = instant loading even with thousands of files
- 📱 **Mobile Perfect**: Gorgeous interface that works flawlessly on any device
- 🔍 **Node Summary Magic**: See model, seed, and key parameters at a glance
- 📁 **Smart Organization** 🆕: Expandable sidebar with real-time search, bi-directional sorting (name/date), and intuitive folder management
- 🖼️ **Enhanced Gallery View** 🆕: Sort thumbnails by date or name with instant toggle between ascending/descending order
- 🔎 **Advanced Lightbox** 🆕: Zoom with mouse wheel, persistent zoom levels across images, and quick delete functionality
- 🆕 **Universal Upload Magic**: Upload ANY ComfyUI-generated image/video from your PC or phone and instantly discover its workflow!
- 🔄 **Real-time Sync** 🆕: Silent background checks with visual progress overlay when new files are detected
- 🔧 **Standalone Power**: Works independently—manage your gallery even when ComfyUI is off
- ⚡ **2-File Installation**: Just two files to transform your entire workflow

### 🔥 Upload & Discover Feature

**Game-changing addition!** You can upload images and videos from anywhere:

- 📤 **Drag & Drop Upload**: From your PC, phone, or any device
- 🔍 **Instant Workflow Detection**: Automatically extracts and displays the original ComfyUI workflow (if available)
- 🌍 **Community Sharing**: Someone shared an amazing creation? Upload it and see exactly how they made it!
- 💾 **Expand Your Collection**: Add AI art from other sources to your organized gallery
- 🔄 **Cross-Platform Sync**: Upload from mobile, manage from desktop—seamlessly

<div align="center">
  <img src="assets/gallery_from_mobile_screen.png" alt="Mobile View" width="300"">
</div>
<p align="center">
  <em>📱 Perfect mobile experience - now with upload!</em>
</p>

---

## 🎮 Installation: Ridiculously Simple

### Step 1: Get the Code
```bash
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
```

### Step 2: Quick Setup
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Your Paths

Open `smartgallery.py` and find the **User Configuration** section. Just update these paths to match your setup:
```python
# 🎯 Point to your ComfyUI folders
BASE_OUTPUT_PATH = 'C:/your/path/to/ComfyUI/output'
BASE_INPUT_PATH = 'C:/your/path/to/ComfyUI/input'

# 🔧 Optional: FFmpeg path (for video workflow extraction)
FFPROBE_MANUAL_PATH = "C:/path/to/ffprobe.exe"

# 🌐 Choose your port (different from ComfyUI)
SERVER_PORT = 8189
```

> **💡 Pro Tip**: Use forward slashes (`/`) even on Windows for best compatibility!

> **📹 Note**: FFmpeg installation is recommended for complete workflow discovery from MP4 files. Download from [ffmpeg.org](https://ffmpeg.org/) if needed.

### Step 4: Launch & Enjoy
```bash
python smartgallery.py
```

Visit **`http://127.0.0.1:8189/galleryout`** and watch the magic happen!

> **⏱️ First Run**: The initial launch takes a few minutes as SmartGallery builds your database and generates thumbnails. After that? Lightning fast!

---

## 🔄 Updates Are Just a Reinstall

### Step 1: Delete Your Old Install
SmartGallery is self-contained; delete or archive your old versions without worry.

### Step 2: Reinstall Fresh!
Download the newest version, complete your fresh installation, and enjoy!

---

## 🆕 How to Use the Upload Feature

### 🖱️ Desktop Upload
1. **Drag & Drop**: Simply drag images/videos directly into the gallery
2. **Upload Button**: Click the upload button and select files
3. **Instant Analysis**: SmartGallery automatically scans for embedded workflows
4. **Organize**: Uploaded files appear in your gallery with full workflow info (if available)

### 📱 Mobile Upload
1. **Touch Upload**: Tap the upload button on mobile
2. **Camera/Gallery**: Choose from camera roll or take new photos
3. **Seamless Integration**: Uploads integrate perfectly with your existing gallery

### 🔍 Workflow Detection
- **Automatic**: Works with any ComfyUI-generated image/video containing metadata
- **Intelligent**: Recognizes various metadata formats and embedding methods
- **Visual Feedback**: Clear indicators show when workflows are detected
- **Fallback**: Files without workflows still get organized beautifully

---

## 🛠️ Advanced Configuration

Want to customize your experience? Here are the key settings you can tweak:

| Setting | Description | Default |
|---------|-------------|---------|
| `THUMBNAIL_WIDTH` | Thumbnail size in pixels | `300` |
| `PAGE_SIZE` | Files to load initially | `100` |
| `WEBP_ANIMATED_FPS` | Frame rate for WebP animations | `16.0` |
| `SPECIAL_FOLDERS` | Custom folder names in menu | `['video', 'audio']` |
| `MAX_UPLOAD_SIZE` | Maximum file size for uploads | `100MB` |

---

## 🌐 Reverse Proxy Setup

Running behind Nginx or Apache? Point your proxy to:
```
http://127.0.0.1:8189/galleryout
```

---

## 🤝 Join the Community

### Found a Bug? Have an Idea?
**[➡️ Open an Issue](../../issues)** - I read every single one!

### Want to Contribute?
1. Fork the repo
2. Create your feature branch (`git checkout -b amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin amazing-feature`)
5. Open a Pull Request

Let's build something incredible together! 🚀

---

## 🔥 License & Disclaimer

SmartGallery is released under the **MIT License** - see [LICENSE](LICENSE) for details.

This software is provided "as is" without warranty. Use responsibly and in compliance with applicable laws.

---

## ❤️ Show Some Love

If SmartGallery has transformed your ComfyUI workflow, **please give it a ⭐ star!** 

It takes 2 seconds but means the world to me and helps other creators discover this tool.

**[⭐ Star this repo now!](https://github.com/biagiomaf/smart-comfyui-gallery/stargazers)**

---

<p align="center">
  <em>Made with ❤️ for the ComfyUI community</em>
</p>
