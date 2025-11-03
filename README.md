# SmartGallery - Standalone AI Media Gallery ✨# SmartGallery for ComfyUI ✨

### Your Visual Hub with Universal Workflow Recall, Upload Magic & Intelligent Organization

<p align="center">

  <img src="assets/gallery_from_pc_screen.png" alt="SmartGallery Interface" width="800"><p align="center">

</p>  <img src="assets/gallery_from_pc_screen.png" alt="SmartGallery Interface" width="800">

</p>

<p align="center">

  <em>🎨 Browse, organize, and analyze your AI-generated media with powerful workflow extraction</em><p align="center">

</p>  <img src="assets/smartgallery-3.jpg" alt="SmartGallery Interface" width="800">

</p>

<p align="center">

  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a><p align="center">

  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">  <em>🎨 Beautiful, lightning-fast gallery that remembers the exact workflow behind every single creation</em>

  <img src="https://img.shields.io/badge/Version-2.0.0-green.svg" alt="Version"></p>

</p>

<p align="center">

---  <img src="assets/node_summary.png" alt="Node Summary" width="500">

</p>

## 🎯 What is SmartGallery?<p align="center">

  <em>🔍 Instant workflow insights - Node Summary</em>

**SmartGallery** is a standalone web application for browsing, organizing, and analyzing AI-generated images and videos. It specializes in **extracting and displaying ComfyUI workflow metadata** from your media files, making it easy to:</p>



- 📁 Browse thousands of AI-generated files with lightning-fast performance<p align="center">

- 🔍 **Extract workflow metadata** from any ComfyUI-generated file (PNG, video, etc.)  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>

- 🎨 View generation parameters: models, prompts, samplers, CFG, steps, seeds  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">

- 🔎 Advanced filtering by type, date, dimensions, and workflow parameters  <a href="https://github.com/opj161/smart-comfyui-gallery/stargazers"><img src="https://img.shields.io/github/stars/opj161/smart-comfyui-gallery?style=social" alt="GitHub stars"></a>

- ⭐ Organize with favorites and folder management</p>

- 📤 Upload files from anywhere and instantly see their workflows

- 🖼️ Beautiful lightbox viewer with zoom and keyboard navigation---



### 🚀 New in Version 2.0.0 (Standalone Release)## 🆕 What's New in Version 1.50?



- **✅ Fully Decoupled**: No longer requires ComfyUI installation- 🎨 **Optimal UX Gallery Cards**: Revolutionary new card design for a cleaner, more intuitive browsing experience

- **✅ Flexible Configuration**: Use `config.json` or command-line arguments  - **Prompt Preview First**: See the actual prompt used to create each image at a glance (truncated to 2 lines)

- **✅ Still Compatible**: Works perfectly with ComfyUI-generated files  - **Smart Information Hierarchy**: Prompts are now the primary info, filename becomes secondary subtitle

- **✅ Simplified Deployment**: Just Python + pip install  - **Declarative Selection**: Click the top-right checkbox to select files without opening the lightbox

- **✅ Universal**: Can point to any folder with AI-generated media  - **Compact Actions**: Favorite button always visible, secondary actions (Download, Delete, Node Summary) hidden in a clean kebab menu (⋮)

  - **Sampler Badges Enhanced**: Hover over workflow badges to see all sampler names used in multi-sampler workflows

---  

- 🚀 **Backend Performance**: Pre-calculated prompt previews and sampler names stored in database for instant display

## 🎯 Key Features  - Automatic migration adds new columns to existing databases safely

  - Zero performance impact - all metadata extracted during existing sync operations

### 🔍 **Workflow Extraction (100% Independent)**  - Works seamlessly with workflow metadata filtering and deep-linking



The workflow parser extracts ComfyUI metadata from **any file** with embedded workflow JSON:### Previous Updates (v1.36-v1.40)

- ✅ PNG files with ComfyUI workflows- 🔗 **Deep-Linking**: Share direct links to any file with intelligent pagination and filter-aware navigation

- ✅ Videos (MP4, WebM, MKV) with workflow metadata- 🎯 **Advanced Filtering**: Tom-Select dropdowns, workflow metadata filters (model, sampler, scheduler, CFG, steps, dimensions)

- ✅ Files from other machines- � **Real-time Sync**: Server-Sent Events with progress overlay for non-blocking folder synchronization

- ✅ Files uploaded via Discord/web- 🐛 **Stability Fixes**: Flask context management, streaming fixes, filter clearing improvements

- ✅ Files from any ComfyUI installation

### Earlier Updates (v1.30-v1.35)

**No ComfyUI installation required!** The parser reads embedded JSON metadata directly from files.- ⚡ **10-20x Faster Sync**: Parallel processing with all CPU cores for blazing fast database updates

- ✏️ **File Rename**: Rename files directly from the lightbox with validation

### 📊 **Advanced Gallery Features**- 💾 **Persistent UI State**: Folder expansion, sort preferences, and sidebar state remembered across sessions

- 🔍 **Smart Folder Navigation**: Expandable sidebar with real-time search and bi-directional sorting

- **Lightning-Fast Database**: SQLite with optimized indices for instant queries- 🖼️ **Enhanced Gallery Sorting**: Toggle thumbnail sorting by date or name with visual indicators

- **Smart Thumbnails**: Automatic generation and caching- 🔎 **Advanced Lightbox**: Zoom with mouse wheel, persistent zoom levels, percentage display, and quick delete

- **Rich Filtering**: Filter by type, date range, dimensions, workflow parameters

- **Model/Sampler Search**: Find files by specific models, samplers, or schedulers---

- **Prompt Search**: Search within positive/negative prompts

- **Favorites System**: Mark and filter your best generations## 🚀 The Problem Every ComfyUI User Faces

- **Folder Management**: Expandable sidebar with search and sorting

- **Batch Operations**: Select multiple files for batch actionsYou've just created the most stunning AI image or video of your life. It's perfect. Absolutely perfect.



### 🎨 **Modern UI/UX****But wait... what workflow did you use?** 😱



- **Prompt-First Cards**: See generation prompts at a glanceHours later, you're desperately trying to recreate that magic, clicking through endless nodes, tweaking parameters, and pulling your hair out because you can't remember the exact recipe that made it work.

- **Lightbox Viewer**: Full-screen viewing with zoom and keyboard navigation

- **Responsive Design**: Works on desktop, tablet, and mobile**Plus, what about those amazing AI images someone shared with you? Or that perfect generation you saved from Discord?** You want to know the workflow, but you can't load it into your gallery...

- **Dark Theme**: Easy on the eyes for long browsing sessions

- **Real-time Updates**: Automatic detection of new files**This stops now.**



------



## 📦 Installation## 🎯 What Makes SmartGallery Revolutionary



### PrerequisitesSmartGallery isn't just another image viewer. It's a **time machine for your creativity** that automatically links every single file you've ever generated to its exact workflow—whether it's PNG, JPG, MP4, or WebP.



- **Python 3.9+** installed on your system### ⚡ Key Features That Will Transform Your Workflow

- **FFmpeg** (optional, but recommended for video support)

- 🏃‍♂️ **Blazing Fast**: SQLite database + smart caching = instant loading even with thousands of files

### Quick Start- 📱 **Mobile Perfect**: Gorgeous interface that works flawlessly on any device

- 🔍 **Node Summary Magic**: See model, seed, and key parameters at a glance

#### 1. Clone the repository- 🎨 **Prompt-First Design** 🆕: See the actual prompt used to create each image directly in the gallery card

```bash- 🎯 **Intuitive Selection** 🆕: Separate selection from viewing with clean top-right checkboxes

git clone https://github.com/opj161/smartgallery-standalone.git- 📋 **Kebab Menus** 🆕: Organized secondary actions (Download, Delete, Node Summary) in compact dropdown menus

cd smartgallery-standalone- 📁 **Smart Organization**: Expandable sidebar with real-time search, bi-directional sorting (name/date), and intuitive folder management

```- 🖼️ **Enhanced Gallery View**: Sort thumbnails by date or name with instant toggle between ascending/descending order

- 🔎 **Advanced Lightbox**: Zoom with mouse wheel, persistent zoom levels across images, and quick delete functionality

#### 2. Install dependencies- 🆕 **Universal Upload Magic**: Upload ANY ComfyUI-generated image/video from your PC or phone and instantly discover its workflow!

```bash- 🔄 **Real-time Sync**: Silent background checks with visual progress overlay when new files are detected

pip install -r requirements.txt- 🔧 **Standalone Power**: Works independently—manage your gallery even when ComfyUI is off

```- ⚡ **2-File Installation**: Just two files to transform your entire workflow



#### 3. Configure paths### 🔥 Upload & Discover Feature



**Option A: Using config.json (Recommended)****Game-changing addition!** You can upload images and videos from anywhere:

```bash

cp config.json.example config.json- 📤 **Drag & Drop Upload**: From your PC, phone, or any device

# Edit config.json with your paths- 🔍 **Instant Workflow Detection**: Automatically extracts and displays the original ComfyUI workflow (if available)

```- 🌍 **Community Sharing**: Someone shared an amazing creation? Upload it and see exactly how they made it!

- 💾 **Expand Your Collection**: Add AI art from other sources to your organized gallery

Example `config.json`:- 🔄 **Cross-Platform Sync**: Upload from mobile, manage from desktop—seamlessly

```json

{<div align="center">

    "base_output_path": "C:/MyAI/output",  <img src="assets/gallery_from_mobile_screen.png" alt="Mobile View" width="300"">

    "base_input_path": "C:/MyAI/input",</div>

    "server_port": 8008,<p align="center">

    "enable_upload": true,  <em>📱 Perfect mobile experience - now with upload!</em>

    "max_upload_size_mb": 100,</p>

    "thumbnail_quality": 85

}---

```

## 🎮 Installation

**Option B: Using command-line arguments**

```bash### Method 1: Using ComfyUI Manager (Recommended)

python smartgallery.py --output-path /path/to/output --input-path /path/to/input1.  Open ComfyUI Manager.

```2.  Click `Install Custom Nodes`.

3.  Search for `SmartGallery`.

#### 4. Run the application4.  Click `Install`, and restart ComfyUI.

```bash

python smartgallery.pyThe gallery will start automatically in the background with ComfyUI.

```

### Method 2: Manual Installation

#### 5. Open in browser

Navigate to: **http://localhost:8008/galleryout/**1.  Navigate to your ComfyUI `custom_nodes` directory:

    ```bash

---    cd /path/to/your/ComfyUI/custom_nodes/

    ```

## 🎯 Usage Examples2.  Clone this repository:

```bash

### Using with ComfyUI Foldersgit clone https://github.com/opj161/smart-comfyui-gallery

```

SmartGallery can point directly to your ComfyUI output/input folders:3.  Install the required dependencies into your ComfyUI environment:

```bash

```json# Navigate into the new folder

{cd smart-comfyui-gallery

    "base_output_path": "C:/ComfyUI/output",# Install dependencies

    "base_input_path": "C:/ComfyUI/input",pip install -e .

    "server_port": 8008```

}4.  **Restart ComfyUI.**

```

The gallery will start automatically in the background. You can access it at **`http://127.0.0.1:8008/galleryout/`** (or your configured port).

Then run: `python smartgallery.py`

---

### Using with Any Folder

## 🆕 How to Use the Upload Feature

Point to any folder with AI-generated files:

### 🖱️ Desktop Upload

```bash1. **Drag & Drop**: Simply drag images/videos directly into the gallery

python smartgallery.py --output-path D:/MyAIArt --input-path D:/MyAIWorkflows2. **Upload Button**: Click the upload button and select files

```3. **Instant Analysis**: SmartGallery automatically scans for embedded workflows

4. **Organize**: Uploaded files appear in your gallery with full workflow info (if available)

### Custom Port

### 📱 Mobile Upload

```bash1. **Touch Upload**: Tap the upload button on mobile

python smartgallery.py --port 90002. **Camera/Gallery**: Choose from camera roll or take new photos

```3. **Seamless Integration**: Uploads integrate perfectly with your existing gallery



### Full CLI Options### 🔍 Workflow Detection

- **Automatic**: Works with any ComfyUI-generated image/video containing metadata

```bash- **Intelligent**: Recognizes various metadata formats and embedding methods

python smartgallery.py --help- **Visual Feedback**: Clear indicators show when workflows are detected

```- **Fallback**: Files without workflows still get organized beautifully



Available arguments:---

- `--config` - Path to config file (default: config.json)

- `--output-path` - Output directory (overrides config)## 🛠️ Configuration

- `--input-path` - Input directory (overrides config)

- `--port` - Server port (overrides config)SmartGallery now features a **dedicated configuration interface** accessible from ComfyUI's sidebar! 🎉

- `--ffprobe-path` - Path to ffprobe executable

### Quick Start

---1. Open ComfyUI

2. Click the **Gallery Config** icon (🖼️) in the left sidebar

## 🔧 Configuration Options3. Configure paths, port, and features through the intuitive UI

4. Click **Save Configuration**

All options can be set in `config.json`:5. Restart gallery server if prompted



| Option | Type | Default | Description |### Configuration Options

|--------|------|---------|-------------|- **📁 Path Detection**: Auto-detect from ComfyUI or specify manually

| `base_output_path` | string | *required* | Path to your AI output directory |- **🌐 Server Port**: Configure gallery server port (default: 8008)

| `base_input_path` | string | *required* | Path to your input/workflow directory |- **✨ Features**: Enable/disable uploads, set size limits, adjust thumbnail quality

| `server_port` | int | 8008 | Web server port |- **⚙️ Advanced**: FFprobe path for video workflow extraction

| `enable_upload` | bool | true | Enable file upload through web UI |

| `max_upload_size_mb` | int | 100 | Maximum upload file size (MB) |> **💡 Pro Tip**: The new sidebar configuration provides real-time validation, detailed error messages, and one-click gallery restart!

| `thumbnail_quality` | int | 85 | JPEG quality for thumbnails (1-100) |

| `ffprobe_manual_path` | string | "" | Manual path to ffprobe (if not in PATH) |> **� Detailed Documentation**: See [CONFIGURATION.md](CONFIGURATION.md) for complete configuration guide, API documentation, and troubleshooting.



---### Legacy Settings Panel (Deprecated)

The old ComfyUI settings panel integration is deprecated but still functional for backward compatibility. Please migrate to the new sidebar tab for the best experience.

## 📖 How It Works

**Important:** You must **restart the gallery server** (or ComfyUI) for configuration changes to take effect.

### Workflow Extraction

> **📹 FFmpeg Note**: For complete workflow discovery from MP4 files, ensure FFmpeg is installed. Download from [ffmpeg.org](https://ffmpeg.org/) if needed.

SmartGallery extracts ComfyUI workflow metadata using a **graph-based parser**:

---

1. **Read File**: Loads PNG/video file bytes

2. **Extract JSON**: Searches for embedded workflow JSON in metadata## 🌐 Reverse Proxy Setup

3. **Parse Workflow**: Analyzes the node graph (UI or API format)

4. **Trace Samplers**: Follows node connections to find samplersRunning behind Nginx or Apache? Point your proxy to:

5. **Extract Metadata**: Pulls out models, prompts, parameters, etc.```

http://127.0.0.1:8189/galleryout

**Key Point**: This works on **any file** with ComfyUI metadata, regardless of where it came from.```



### Database Structure---



- **SQLite Database**: Stores file metadata and workflow information## 🤝 Join the Community

- **Fast Indices**: Optimized for instant queries on name, date, type, etc.

- **Smart Caching**: Thumbnails cached for fast loading### Found a Bug? Have an Idea?

- **Auto-Sync**: Detects new files and updates database automatically**[➡️ Open an Issue](../../issues)** - I read every single one!



### File Organization### Want to Contribute?

1. Fork the repo

```2. Create your feature branch (`git checkout -b amazing-feature`)

your-ai-folder/3. Commit your changes (`git commit -m 'Add amazing feature'`)

├── image1.png (with workflow)4. Push to the branch (`git push origin amazing-feature`)

├── video1.mp4 (with workflow)5. Open a Pull Request

├── subfolder/

│   └── image2.pngLet's build something incredible together! 🚀

└── .sqlite_cache/

    ├── gallery_cache.sqlite (database)---

    └── .thumbnails_cache/ (thumbnail cache)

```## 🔥 License & Disclaimer



---SmartGallery is released under the **MIT License** - see [LICENSE](LICENSE) for details.



## 🎨 Gallery Features in DetailThis software is provided "as is" without warranty. Use responsibly and in compliance with applicable laws.



### Filtering---



- **By Type**: Images, videos, animated images, audio## ❤️ Show Some Love

- **By Date**: Date range picker with min/max

- **By Dimensions**: Width/height rangesIf SmartGallery has transformed your ComfyUI workflow, **please give it a ⭐ star!** 

- **By Workflow**:

  - Model namesIt takes 2 seconds but means the world to me and helps other creators discover this tool.

  - Sampler/scheduler

  - CFG scale range**[⭐ Star this repo now!](https://github.com/opj161/smart-comfyui-gallery/stargazers)**

  - Steps range

  - Seed search---

- **By Prompt**: Search in positive/negative prompts

<p align="center">

### Sorting  <em>Made with ❤️ for the ComfyUI community</em>

</p>
- **By Date**: Newest/oldest first
- **By Name**: A-Z or Z-A

### Batch Operations

- Select multiple files
- Batch download
- Batch delete
- Batch favorite/unfavorite

### Lightbox Viewer

- **Full-Screen View**: Click any thumbnail
- **Keyboard Navigation**: Arrow keys, Esc to close
- **Mouse Zoom**: Scroll wheel to zoom in/out
- **Workflow View**: See full generation parameters
- **Node Summary**: Quick overview of key parameters

---

## 🚀 Advanced Usage

### Running as a Service (Linux)

Create `/etc/systemd/system/smartgallery.service`:

```ini
[Unit]
Description=SmartGallery AI Media Gallery
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/smartgallery-standalone
ExecStart=/usr/bin/python3 /path/to/smartgallery-standalone/smartgallery.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable smartgallery
sudo systemctl start smartgallery
```

### Docker Support (Coming Soon)

A Docker image will be available in a future release.

### Environment Variables (Optional)

Set environment variables for configuration:
```bash
export SMARTGALLERY_OUTPUT=/path/to/output
export SMARTGALLERY_INPUT=/path/to/input
export SMARTGALLERY_PORT=8008
python smartgallery.py
```

---

## 🛠️ Troubleshooting

### "Paths not provided" error
Make sure you either:
- Create `config.json` with paths, OR
- Use `--output-path` and `--input-path` CLI arguments

### Videos not showing thumbnails
Install FFmpeg and make sure `ffprobe` is in your system PATH, or set `ffprobe_manual_path` in config.json.

### Database not updating
The gallery auto-syncs every few minutes. To force a sync, restart the application.

### High memory usage
Reduce `BATCH_SIZE` in `smartgallery.py` (line ~816) if processing many files.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Original ComfyUI Plugin Version**: [smart-comfyui-gallery](https://github.com/opj161/smart-comfyui-gallery)
- **ComfyUI Community**: For the amazing AI generation platform
- **Contributors**: Thanks to everyone who helped improve this project

---

## 📧 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/opj161/smartgallery-standalone/issues)
- **Email**: biagiomaf@gmail.com
- **Original Project**: [smart-comfyui-gallery](https://github.com/opj161/smart-comfyui-gallery)

---

## 🔗 Related Projects

- **ComfyUI**: [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **Original Plugin Version**: [smart-comfyui-gallery](https://github.com/opj161/smart-comfyui-gallery)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/opj161">Biagio Maffettone</a>
</p>
