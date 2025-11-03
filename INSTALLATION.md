# SmartGallery - Installation Guide

This guide provides detailed installation instructions for SmartGallery on Windows, Linux, and macOS.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Advanced Setup](#advanced-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python 3.9 or higher**
  - Check version: `python --version` or `python3 --version`
  - Download from: [python.org](https://www.python.org/downloads/)

### Recommended

- **FFmpeg** (for video thumbnail generation and metadata extraction)
  - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)
  - Linux: `sudo apt install ffmpeg` (Debian/Ubuntu) or `sudo dnf install ffmpeg` (Fedora)
  - macOS: `brew install ffmpeg`

---

## Windows Installation

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```powershell
   python --version
   ```

### Step 2: Install Git (Optional)

If you want to clone the repository:
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer with default options

### Step 3: Get SmartGallery

**Option A: Using Git**
```powershell
git clone https://github.com/opj161/smartgallery-standalone.git
cd smartgallery-standalone
```

**Option B: Download ZIP**
1. Go to the GitHub repository
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Open PowerShell/Command Prompt in the extracted folder

### Step 4: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

If you get an error about `pip` not found, try:
```powershell
python -m pip install -r requirements.txt
```

### Step 5: Install FFmpeg (Recommended)

**Option A: Using Winget (Windows 11/10)**
```powershell
winget install FFmpeg
```

**Option B: Manual Installation**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the ZIP file
3. Add the `bin` folder to your system PATH, OR
4. Note the path to `ffprobe.exe` for config.json

### Step 6: Configure

Create `config.json`:
```powershell
Copy-Item config.json.example config.json
notepad config.json
```

Edit the paths (use forward slashes or double backslashes):
```json
{
    "base_output_path": "C:/Users/YourName/ComfyUI/output",
    "base_input_path": "C:/Users/YourName/ComfyUI/input",
    "server_port": 8008,
    "ffprobe_manual_path": "C:/FFmpeg/bin/ffprobe.exe"
}
```

### Step 7: Run

```powershell
python smartgallery.py
```

Open browser: **http://localhost:8008/galleryout/**

---

## Linux Installation

### Step 1: Install Python

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
```

Verify:
```bash
python3 --version
```

### Step 2: Install FFmpeg

**Debian/Ubuntu:**
```bash
sudo apt install ffmpeg
```

**Fedora/RHEL:**
```bash
sudo dnf install ffmpeg
```

**Arch Linux:**
```bash
sudo pacman -S ffmpeg
```

### Step 3: Get SmartGallery

```bash
git clone https://github.com/opj161/smartgallery-standalone.git
cd smartgallery-standalone
```

### Step 4: Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure

```bash
cp config.json.example config.json
nano config.json  # or use your preferred editor
```

Example config:
```json
{
    "base_output_path": "/home/yourname/ai/output",
    "base_input_path": "/home/yourname/ai/input",
    "server_port": 8008
}
```

### Step 7: Run

```bash
python3 smartgallery.py
```

Open browser: **http://localhost:8008/galleryout/**

### Optional: Run as System Service

See [Advanced Setup](#running-as-systemd-service) below.

---

## macOS Installation

### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python

```bash
brew install python
```

Verify:
```bash
python3 --version
```

### Step 3: Install FFmpeg

```bash
brew install ffmpeg
```

### Step 4: Get SmartGallery

```bash
git clone https://github.com/opj161/smartgallery-standalone.git
cd smartgallery-standalone
```

### Step 5: Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Configure

```bash
cp config.json.example config.json
nano config.json  # or open -e config.json
```

Example config:
```json
{
    "base_output_path": "/Users/yourname/AI/output",
    "base_input_path": "/Users/yourname/AI/input",
    "server_port": 8008
}
```

### Step 8: Run

```bash
python3 smartgallery.py
```

Open browser: **http://localhost:8008/galleryout/**

---

## Configuration

### config.json Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `base_output_path` | string | Yes | Path to your AI output directory |
| `base_input_path` | string | Yes | Path to your input/workflow directory |
| `server_port` | integer | No | Server port (default: 8008) |
| `enable_upload` | boolean | No | Allow file uploads (default: true) |
| `max_upload_size_mb` | integer | No | Max upload size in MB (default: 100) |
| `thumbnail_quality` | integer | No | JPEG quality 1-100 (default: 85) |
| `ffprobe_manual_path` | string | No | Manual path to ffprobe executable |

### Path Formats

**Windows:**
- Forward slashes: `"C:/Users/Name/folder"`
- Double backslashes: `"C:\\Users\\Name\\folder"`

**Linux/macOS:**
- Standard: `"/home/username/folder"`
- Tilde expansion NOT supported, use full paths

### Using with ComfyUI

Point to your ComfyUI folders:
```json
{
    "base_output_path": "C:/ComfyUI/output",
    "base_input_path": "C:/ComfyUI/input"
}
```

### Standalone Usage

Point to any folder:
```json
{
    "base_output_path": "D:/MyAIArt",
    "base_input_path": "D:/Prompts"
}
```

---

## Running the Application

### Standard Run

```bash
python smartgallery.py
```

### With Config File

```bash
python smartgallery.py --config my-config.json
```

### Override Config with CLI Args

```bash
python smartgallery.py --output-path /other/path --port 9000
```

### Command-Line Only (No Config File)

```bash
python smartgallery.py --output-path /path/to/output --input-path /path/to/input
```

### Run in Background (Linux/macOS)

```bash
nohup python3 smartgallery.py > smartgallery.log 2>&1 &
```

Stop with:
```bash
pkill -f smartgallery.py
```

---

## Advanced Setup

### Running as systemd Service (Linux)

1. Create service file:
```bash
sudo nano /etc/systemd/system/smartgallery.service
```

2. Add content:
```ini
[Unit]
Description=SmartGallery AI Media Gallery
After=network.target

[Service]
Type=simple
User=youruser
Group=yourgroup
WorkingDirectory=/home/youruser/smartgallery-standalone
ExecStart=/home/youruser/smartgallery-standalone/venv/bin/python smartgallery.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartgallery
sudo systemctl start smartgallery
```

4. Check status:
```bash
sudo systemctl status smartgallery
```

5. View logs:
```bash
sudo journalctl -u smartgallery -f
```

### Run on Startup (Windows)

**Option A: Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: "When I log on"
4. Action: "Start a program"
5. Program: `python.exe`
6. Arguments: `C:\path\to\smartgallery.py`
7. Start in: `C:\path\to\smartgallery-standalone\`

**Option B: Startup Folder**
1. Create a batch file `start-smartgallery.bat`:
```batch
@echo off
cd /d C:\path\to\smartgallery-standalone
python smartgallery.py
```
2. Save to: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`

### Reverse Proxy (nginx)

For running behind nginx:

```nginx
server {
    listen 80;
    server_name smartgallery.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Python not found

**Windows:**
- Reinstall Python, check "Add to PATH"
- Or use full path: `C:\Python39\python.exe smartgallery.py`

**Linux/macOS:**
- Use `python3` instead of `python`

### pip not found

Try:
```bash
python -m pip install -r requirements.txt
```

### Permission denied (Linux)

```bash
chmod +x smartgallery.py
python3 smartgallery.py
```

### Port already in use

Change port in config.json or use CLI:
```bash
python smartgallery.py --port 9000
```

### FFprobe not found

**Option 1: Add to PATH**
- Windows: Add FFmpeg bin folder to System PATH
- Linux/macOS: FFmpeg from package manager should be in PATH

**Option 2: Manual path in config**
```json
{
    "ffprobe_manual_path": "C:/FFmpeg/bin/ffprobe.exe"
}
```

### Videos show as broken

1. Make sure FFmpeg is installed
2. Check ffprobe path: `ffprobe -version`
3. Set `ffprobe_manual_path` in config.json if needed

### Database errors

Delete the database and let it rebuild:
```bash
rm -rf output/.sqlite_cache/
python smartgallery.py
```

### High memory usage

Edit `smartgallery.py` line ~816:
```python
BATCH_SIZE = 100  # Reduce from 500
```

### Slow performance

1. Check database indices: Should auto-create on first run
2. Reduce thumbnail quality in config.json
3. Clear thumbnail cache and rebuild

---

## Getting Help

- **GitHub Issues**: [smartgallery-standalone/issues](https://github.com/opj161/smartgallery-standalone/issues)
- **Email**: biagiomaf@gmail.com
- **Original Project**: [smart-comfyui-gallery](https://github.com/opj161/smart-comfyui-gallery)

---

## Next Steps

After installation:
1. Open **http://localhost:8008/galleryout/**
2. Wait for initial database sync (first run only)
3. Explore filtering options
4. Upload test files to verify workflow extraction
5. Customize config.json to your preferences

Enjoy browsing your AI creations! 🎨
