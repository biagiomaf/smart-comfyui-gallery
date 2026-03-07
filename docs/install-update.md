# SmartGallery - Installation & Update  
## Windows, macOS, Linux, Docker

<details>
<summary><strong>Select your platform</strong></summary>

Each quick install shows **only the relevant steps for that platform**.

---

<details>
<summary><strong>Windows (Python)</strong></summary>

### 1. Install

**Option A: Using Git (Recommended)**
```bat
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
```

**Option B: No Git (Manual Download)**

Download the latest **Source code (zip)** from [**Releases**](https://github.com/biagiomaf/smart-comfyui-gallery/releases/latest), extract it, and open a terminal inside the folder.

**Then, setup the environment:**
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run (Best Practice)

Create a new file named `run_smartgallery.bat` inside the folder and paste this content.

**⚠️ IMPORTANT:** Replace the example paths with your real paths. Use forward slashes `/` even on Windows.
```bat
@echo off
cd /d %~dp0
call venv\Scripts\activate.bat

:: --- CONFIGURATION ---
:: REPLACE these paths with your actual folders.
:: NOTE: Use forward slashes (/) for paths (e.g., C:/ComfyUI/output)

set "BASE_OUTPUT_PATH=C:/Path/To/ComfyUI/output"
set "BASE_INPUT_PATH=C:/Path/To/ComfyUI/input"
set "BASE_SMARTGALLERY_PATH=C:/Path/To/ComfyUI/output"

:: If ffmpeg is not in your system PATH, point to ffprobe.exe here:
set "FFPROBE_MANUAL_PATH=C:/Path/To/ffmpeg/bin/ffprobe.exe"
set SERVER_PORT=8189

:: --- START ---
python smartgallery.py
pause
```

Double-click `run_smartgallery.bat` to start.

### 3. How to Update

If you installed via Git:
```bat
cd smart-comfyui-gallery
git pull
venv\Scripts\activate
pip install -r requirements.txt
```

If you downloaded the ZIP: Download the new version, extract it, and copy your `run_smartgallery.bat` into the new folder.

</details>

---

<details>
<summary><strong>macOS (Python)</strong></summary>

### 1. Install

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
```

**Option B: No Git (Manual Download)**

Download the latest **Source code (tar.gz)** from [**Releases**](https://github.com/biagiomaf/smart-comfyui-gallery/releases/latest), extract it, and open a terminal inside the folder.

**Then, setup the environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run (Best Practice)

Create a file named `run_smartgallery.sh`, make it executable (`chmod +x run_smartgallery.sh`), and paste this content:
```bash
#!/bin/bash
source venv/bin/activate

# Increase open files limit (fix for "Too many open files" on macOS)
ulimit -n 4096

# --- CONFIGURATION ---
# REPLACE these paths with your actual folders.
export BASE_OUTPUT_PATH="$HOME/ComfyUI/output"
export BASE_INPUT_PATH="$HOME/ComfyUI/input"
export BASE_SMARTGALLERY_PATH="$HOME/ComfyUI/output"

# Ensure ffprobe is installed (brew install ffmpeg)
export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
export SERVER_PORT=8189

# --- START ---
python smartgallery.py
```

Run it with: `./run_smartgallery.sh`

### 3. How to Update

If you installed via Git:
```bash
cd smart-comfyui-gallery
git pull
source venv/bin/activate
pip install -r requirements.txt
```

If you downloaded the tar.gz: Download the new version, extract it, and copy your `run_smartgallery.sh` into the new folder.

</details>

---

<details>
<summary><strong>Linux (Python)</strong></summary>

### 1. Install

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
```

**Option B: No Git**

Download **Source code** from [**Releases**](https://github.com/biagiomaf/smart-comfyui-gallery/releases/latest).

**Then, setup the environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run (Best Practice)

Create a file named `run_smartgallery.sh`, make it executable (`chmod +x run_smartgallery.sh`), and paste this content:
```bash
#!/bin/bash
source venv/bin/activate

# --- CONFIGURATION ---
# REPLACE these paths with your actual folders.
export BASE_OUTPUT_PATH="$HOME/ComfyUI/output"
export BASE_INPUT_PATH="$HOME/ComfyUI/input"
export BASE_SMARTGALLERY_PATH="$HOME/ComfyUI/output"
export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
export SERVER_PORT=8189

# --- START ---
python smartgallery.py
```

Run it with: `./run_smartgallery.sh`

### 3. How to Update

If you installed via Git:
```bash
cd smart-comfyui-gallery
git pull
source venv/bin/activate
pip install -r requirements.txt
```

If you downloaded the source code manually: Download the new version, extract it, and copy your `run_smartgallery.sh` into the new folder.

</details>

---

<details>
<summary><strong>Docker</strong></summary>

### 1. Run

Replace the paths on the left side of the `:` with your actual host paths.
```bash
docker run \
  --name smartgallery \
  -v /your/host/output:/mnt/output \
  -v /your/host/input:/mnt/input \
  -v /your/host/SmartGallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e BASE_INPUT_PATH=/mnt/input \
  -e BASE_SMARTGALLERY_PATH=/mnt/SmartGallery \
  -p 8189:8189 \
  -e WANTED_UID=`id -u` \
  -e WANTED_GID=`id -g` \
  mmartial/smart-comfyui-gallery
```

### 2. How to Update
```bash
# 1. Pull the latest image
docker pull mmartial/smart-comfyui-gallery

# 2. Stop and remove the old container
docker stop smartgallery && docker rm smartgallery

# 3. Run the 'docker run' command again (see above)
```

### 🐳 Docker Deployment 

Want to run SmartGallery in a containerized environment? We've got you covered!

> 🎖️ **Special Thanks**: A huge shout-out to **[Martial Michel](https://github.com/mmartial)** for orchestrating the Docker support and contributing to the core application logic.

Docker deployment provides isolation, easier deployment, and consistent environments across different systems. However, it requires some familiarity with Docker concepts.

**🗄️ Pre-built images**

Pre-built images are available on DockerHub at [mmartial/smart-comfyui-gallery](https://hub.docker.com/r/mmartial/smart-comfyui-gallery) and Unraid's Community Apps. 

![../assets/smart-comfyui-gallery-unraidCA.png](../assets/smart-comfyui-gallery-unraidCA.png)

**Full Docker guide:** 👉 [DOCKER_HELP.md](DOCKER_HELP.md)

</details>


## ComfyUI Plugin

<details>
<summary><strong>Run as a ComfyUI custom_nodes Plugin</strong></summary>
This repository can run **inside ComfyUI** as a `custom_nodes`:

- No separate web server port (no `8189`)
- The UI is served by ComfyUI at `http://127.0.0.1:8188/galleryout/view/_root_`
- The Gallery tab appears in the ComfyUI sidebar as **Gallery**

### 1) Install the plugin

1. Go to your ComfyUI `custom_nodes` folder.
2. Clone (or symlink) this repository into `custom_nodes/`.

Example (Linux/macOS):
```bash
cd /path/to/ComfyUI/custom_nodes
git clone <THIS_REPO_URL> smart-comfyui-gallery
```

### 2) Install Python dependencies (ComfyUI venv)

Install the dependencies into the same Python environment used by ComfyUI:
```bash
cd /path/to/ComfyUI
./.venv/bin/pip install -r custom_nodes/smart-comfyui-gallery/requirements.txt
```

### 3) Restart ComfyUI

Restart ComfyUI so it can load the plugin.

### 4) Open SmartGallery

- From the ComfyUI sidebar: **Gallery**
- Or directly: `http://127.0.0.1:8188/galleryout/view/_root_`

### Notes

- The plugin automatically uses ComfyUI paths for `output` and `input` (no need to set `BASE_OUTPUT_PATH` / `BASE_INPUT_PATH`).
- On first launch, SmartGallery will initialize its database and may scan your output folder.

</details>