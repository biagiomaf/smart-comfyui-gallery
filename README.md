# SmartGallery for ComfyUI ✨
### Your lightweight, browser-based visual hub for ComfyUI outputs

**SmartGallery** is a fast, mobile-friendly web gallery that gives you
**complete control over your ComfyUI outputs** — even when ComfyUI is not running.

Browse, search, organize, and instantly recall the exact workflow behind every image or video,
from any device, on Windows, Linux, or Docker.

---

<p align="center">
  <img src="assets/gallery_from_pc_screen.png" alt="SmartGallery Interface" width="800">
</p>

<p align="center">
  <em>🎨 A beautiful, lightning-fast gallery that remembers the workflow behind every creation</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <a href="https://github.com/biagiomaf/smart-comfyui-gallery/stargazers">
    <img src="https://img.shields.io/github/stars/biagiomaf/smart-comfyui-gallery?style=social" alt="GitHub stars">
  </a>
</p>

---

## 🎯 Why SmartGallery?

If you use ComfyUI, you already know the pain:

- Thousands of generated files
- Forgotten workflows
- Generic filenames
- No easy way to browse from your phone
- No fast way to find *that* image again

**SmartGallery fixes all of this.**

It automatically links every generated file (PNG, JPG, MP4, WebP)
to its **exact workflow**, making your entire creative history searchable and explorable.

---

## ⚡ Key Features

- 📝 **$\color{red}{\text{(new)}}$** **Prompt Keywords Search**: Instantly find generations by searching for specific words inside your prompt. Supports multiple comma-separated keywords (e.g., "woman, kimono").

- 🧬 **$\color{red}{\text{(new)}}$** **Deep Workflow Search**: Search for generated images, videos, and animations based on the **filenames** inside the workflow (Models, LoRAs, Inputs). 
  *Supports multiple comma-separated keywords (e.g., "wan2.1, portrait.png").*

- 🏃‍♂️ **Blazing Fast**  
  SQLite database + smart caching = instant browsing, even with huge libraries

- 📱 **Mobile-First Experience**  
  Perfect UI on desktop, tablet, and smartphone
  
- 🔍 **Powerful Search**  
  Search by filename, prefix, extension, date range, or globally across folders

- 🔎 **Node Summary**  
  Instantly see model, seed, parameters, and source media used to generate each file

<p align="center">
  <img src="assets/node_summary_with_image.png" alt="Node Summary with source image" width="450"/>
</p>

- 📁 **Smart Organization**  
  Real-time folder browsing, sorting, filtering, and file management

- 📦 **Batch Operations**  
  Multi-select, ZIP download, range selection

- 🆕 **Universal Upload Magic**  
  Upload any ComfyUI-generated image or video and instantly discover its workflow

- 🔄 **Real-time Sync**  
  Background scanning with visual progress when new files are detected

- 🐳 **Docker Ready**  
  Run it anywhere, cleanly and reliably

---

## 🆕 What's New in Version 1.51?

Recent updates focus on search, performance, and usability.
Highlights:

### 📝 Powerful Prompt Text Search
Finding that one specific generation is now easier than ever. We've added a **Prompt Keywords** search that digs into the actual text used in your prompts.
*   **How it works:** It scans the workflow metadata for the text prompts you wrote.
*   **Multiple Keywords:** You can search for several words at once.
*   **Example:** You want to find all your previous tests involving a woman wearing a specific garment.
*   **Solution:** Just type `woman, kimono` in the Prompt Keywords field, and SmartGallery will filter all matching images, animations, and videos instantly!

### 🧬 Deep Workflow Search
We've added a powerful new way to find your creations. The **"Workflow Files"** search field digs inside the hidden metadata to find specific **filenames** used in the generation.

*   **How it works:** It searches specifically for the names of **Checkpoints, LoRAs, Upscalers, and Input Images** referenced in the nodes.
*   **Multiple Keywords:** You can search for multiple items at once by separating them with commas.
*   **Example:** You want to find images generated with the **Wan2.1** model that also used **portrait.png** as an input.
*   **Solution:** Just type `wan2.1, portrait.png` in the Workflow Files search, and SmartGallery will find matches containing both!
*   *(Note: This searches for filenames, not numeric parameters like Seed or CFG).*

🌐 **Global search across all folders**

📅 **Date range filtering**

🚀 **Optimized UI for large libraries**

👉 See [CHANGELOG.md](CHANGELOG.md) for full details.


<div align="center">
  <img src="assets/gallery_from_mobile_screen.png" alt="Mobile View" width="300">
  <img src="assets/node_summary.png" alt="Node Summary" width="350"/>
</div>
<p align="center">
  <em>📱 Perfect mobile experience</em>
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
# Windows Command Prompt: call venv\Scripts\activate.bat
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Your Paths

You have **two easy options** to configure SmartGallery:

#### 🅰️ Option A: Environment Variables (recommended)
Create a startup script to keep your settings organized.

Perfect if you want to keep your settings separate or run multiple configurations.

**Windows:**
Create a file named start_gallery.bat inside the smart-comfyui-gallery folder with the following content:
```cmd
@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
REM Path to your ComfyUI Output folder (Where images are generated)
set "BASE_OUTPUT_PATH=C:/ComfyUI/output"
REM Path to your ComfyUI Input folder (For source media in Node Summary)
set "BASE_INPUT_PATH=C:/ComfyUI/input"
REM Where SmartGallery stores the SQLite Database and Thumbnails Cache
set "BASE_SMARTGALLERY_PATH=C:/ComfyUI/output"
REM Path to ffprobe.exe (ffmpeg required for extracting workflows from video files)
set "FFPROBE_MANUAL_PATH=C:/ffmpeg/bin/ffprobe.exe"
set SERVER_PORT=8189
REM Leave MAX_PARALLEL_WORKERS empty to use all CPU cores (recommended)
set "MAX_PARALLEL_WORKERS="
python smartgallery.py
```

**Linux/Mac:**
Create a file named start_gallery.sh with the following content:
```bash
#!/bin/bash
source venv/bin/activate
# Path to your ComfyUI Output folder (Where images are generated)
export BASE_OUTPUT_PATH="$HOME/ComfyUI/output"
# Path to your ComfyUI Input folder (For source media in Node Summary)
export BASE_INPUT_PATH="$HOME/ComfyUI/input"
# Where SmartGallery stores the SQLite Database and Thumbnails Cache
export BASE_SMARTGALLERY_PATH="$HOME/ComfyUI/output"
# Path to ffprobe executable (Required for extracting workflows from video files)
export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
# The port where SmartGallery will run
export SERVER_PORT=8189
# Leave empty to use all CPU cores, or set a number (e.g., 4) to limit usage
export MAX_PARALLEL_WORKERS=""
python smartgallery.py
```
Then make it executable and run it:
```bash
chmod +x start_gallery.sh
./start_gallery.sh
```

> 💡 **Tip**: See the complete configuration guide at the top of `smartgallery.py` for all available settings and detailed examples!

#### 🅱️ Option B: Direct File Edit 

Open `smartgallery.py` and find the **USER CONFIGURATION** section. A detailed guide is included at the top of the file. Update just the paths after the commas:
```python
# Find this section and change ONLY the values after the commas:
BASE_OUTPUT_PATH = os.environ.get('BASE_OUTPUT_PATH', 'C:/ComfyUI/output')
BASE_INPUT_PATH = os.environ.get('BASE_INPUT_PATH', 'C:/ComfyUI/input')
BASE_SMARTGALLERY_PATH = os.environ.get('BASE_SMARTGALLERY_PATH', BASE_OUTPUT_PATH) # DB & Cache location
FFPROBE_MANUAL_PATH = os.environ.get('FFPROBE_MANUAL_PATH', "C:/ffmpeg/bin/ffprobe.exe")
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8189))
```

> 💡 **Important**: Always use forward slashes (`/`) even on Windows! If your paths contain spaces, use quotes.

> 📹 **FFmpeg Note**: Recommended for extracting workflows from MP4 files. Download from [ffmpeg.org](https://ffmpeg.org/) if needed. Common locations:
> - Windows: `C:/ffmpeg/bin/ffprobe.exe` or `C:/Program Files/ffmpeg/bin/ffprobe.exe`
> - Linux: `/usr/bin/ffprobe` or `/usr/local/bin/ffprobe`
> - Mac: `/usr/local/bin/ffprobe` or `/opt/homebrew/bin/ffprobe`

### Step 4: Launch & Enjoy

Visit **`http://127.0.0.1:8189/galleryout`** and watch the magic happen!

> **⏱️ First Run**: The initial launch scans your files and generates thumbnails. Thanks to parallel processing, this is now incredibly fast (seconds to a few minutes depending on your collection size). After that? Lightning fast! ⚡

---


## 🐳 Docker Deployment (Advanced Users)

Want to run SmartGallery in a containerized environment? We've got you covered!

> 🎖️ **Special Thanks**: A huge shout-out to **[Martial Michel](https://github.com/mmartial)** for orchestrating the Docker support and contributing significant improvements to the core application logic.

> **Note for Windows Users**: The standard installation (Steps 1-4 above) is much simpler and works perfectly on Windows! Docker is completely optional and mainly useful for Linux servers or advanced deployment scenarios.

Docker deployment provides isolation, easier deployment, and consistent environments across different systems. However, it requires some familiarity with Docker concepts.

**🗄️ Pre-built images**

Pre-built images are available on DockerHub at [mmartial/smart-comfyui-gallery](https://hub.docker.com/r/mmartial/smart-comfyui-gallery) and Unraid's Community Apps. 

![assets/smart-comfyui-gallery-unraidCA.png](assets/smart-comfyui-gallery-unraidCA.png)

Example `docker run` command:

```bash
# Adapt the mounts and WANTED_UID/WANTED_GID variables to match your system
docker run \
  --name smartgallery \
  -v /comfyui-nvidia/basedir/output:/mnt/output \
  -v /comfyui-nvidia/basedir/input:/mnt/input \
  -v /comfyui-nvidia/SmartGallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e BASE_INPUT_PATH=/mnt/input \
  -e BASE_SMARTGALLERY_PATH=/mnt/SmartGallery \
  -p 8189:8189 \
  -e WANTED_UID=`id -u` \
  -e WANTED_GID=`id -g` \
  mmartial/smart-comfyui-gallery
```

> **Note**: The `id -u` and `id -g` commands return the user and group IDs of the current user, respectively. This ensures that the container runs with the same permissions as the host user, which is important for file permissions and access to mounted volumes.

A [compose.yaml](compose.yaml) file is provided for ease of use. You can use it to obtain the published image and run the container with the following command after placing it in a directory of your choice and adapting the paths and environment variables to match your system:
```bash
docker compose up -d
```

See the following section's "All available environment variables" for a list of all available environment variables.

**📚 [Complete Docker Setup Guide →](DOCKER_HELP.md)**

Our comprehensive Docker guide covers:
- 🏗️ Building the Docker image
- 🚀 Running with Docker Compose (recommended for beginners)
- ⚙️ Using Makefile (For advanced control and automation)
- 🔐 Understanding permissions and volume mapping
- 🛠️ Troubleshooting common Docker issues
- 📋 All available environment variables


---
## 🌐 Reverse Proxy Setup

Running behind Nginx or Apache? Point your proxy to:
```
http://127.0.0.1:8189/galleryout
```

**Example Nginx configuration:**
```nginx
location /gallery/ {
    proxy_pass http://127.0.0.1:8189/galleryout/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

---
## 🚀 Coming Soon: Announcing the AI Features (Optional)

SmartGallery is designed to stay **lightweight by default**.

Advanced AI-powered features will be provided soon by a **separate optional component**:

### **SmartGallery AI Service (Optional)**

> 🔌 A dedicated service, completely independent from the SmartGallery core.

### 🧠 AI Search (Coming Soon)

Search your gallery by **describing what you remember** — not filenames.

Examples:
```text
"cyberpunk portrait with neon lights"
"dark fantasy illustration"
"portrait with red background"
No manual tagging.
No heavy dependencies in the core.
No cloud. Fully local and private.
```
⚠️ Important
SmartGallery works perfectly without AI
The AI Service is optional, local and free!
It runs in a separate Docker container or Python environment.
If you don't install it, nothing changes.

**The AI Service is currently under development and not released yet.**

[ SmartGallery Core (lightweight)]  --->  [ SmartGallery AI Service (Optional)- docker / separate environment]
                    
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

## 🔥 License

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
