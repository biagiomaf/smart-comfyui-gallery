# 🐳 SmartGallery Docker Deployment Guide

This guide covers everything you need to know to run SmartGallery in a Docker container.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Method 1: Docker Compose (Recommended for beginners)](#method-1-docker-compose-recommended)
- [Method 2: Makefile (Power Users)](#method-2-makefile-power-users)
- [Understanding Docker Permissions](#understanding-docker-permissions)
- [Environment Variables Reference](#environment-variables-reference)
- [Docker Volumes Explained](#docker-volumes-explained)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Prerequisites

Before you begin, ensure you have:

- **Docker installed**:
  - **Linux**: Docker Engine ([installation guide](https://docs.docker.com/engine/install/))
  - **Windows/Mac**: Docker Desktop ([download](https://www.docker.com/products/docker-desktop/))
- **Basic Docker knowledge**: Understanding of containers, images, and volumes
- **Your ComfyUI output and input folders path** ready
- **Sufficient disk space** for Docker images and volumes

> **⚠️ Important**: Docker on Windows adds complexity. The standard Python installation is recommended for Windows users unless you specifically need containerization.

---

## Quick Start

For those who just want to get started quickly:
```bash
# 1. Clone the repository
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery

# 2. Build the Docker image
docker build -t smartgallery:latest .

# 3. Edit compose.yaml with your paths (see below)
nano compose.yaml  # or use your favorite editor
# if building your own image, replace mmartial/smart-comfyui-gallery:latest with smartgallery:latest

# 4. Start the container
docker compose up -d

# 5. Access the gallery
# Open http://localhost:8189/galleryout in your browser
```

---

## Method 1: Docker Compose (Recommended)

Docker Compose is the easiest way to run SmartGallery in Docker.

### Step 1: Build the Docker Image

From the project directory:
```bash
docker build -t smartgallery:latest .
```

This creates a Docker image named `smartgallery:latest` containing:
- Python 3.12
- All required dependencies
- FFmpeg (with ffprobe for video workflow extraction)
- Pre-configured environment

**Build time**: ~2-5 minutes depending on your internet connection.

### Step 2: Configure `compose.yaml`

Open `compose.yaml` in your favorite text editor and adjust the configuration:
```yaml
services:
  comfy-smartgallery:
    image: smartgallery:latest
    container_name: comfy-smartgallery
    ports:
      - 8189:8189
    volumes:
      # CHANGE THESE PATHS TO MATCH YOUR SYSTEM
      - /path/to/your/ComfyUI/output:/mnt/output
      - /path/to/your/ComfyUI/input:/mnt/input
      - /path/to/your/SmartGallery:/mnt/SmartGallery
    restart: unless-stopped
    environment:
      # Container paths (DO NOT CHANGE)
      - BASE_OUTPUT_PATH=/mnt/output
      - BASE_INPUT_PATH=/mnt/input
      - BASE_SMARTGALLERY_PATH=/mnt/SmartGallery
      # File permissions (CHANGE TO YOUR UID/GID)
      - WANTED_UID=1000
      - WANTED_GID=1000
```

#### What to Change:

**1. Volume Paths (Required)**

Replace these with your actual paths:
```yaml
volumes:
  # Your ComfyUI output folder
  - /home/username/ComfyUI/output:/mnt/output
  # Your ComfyUI input folder
  - /home/username/ComfyUI/input:/mnt/input
  
  # Where SmartGallery stores database/cache (can be anywhere)
  - /home/username/SmartGallery_Data:/mnt/SmartGallery
```

**Linux Examples:**
```yaml
- /home/john/ComfyUI/output:/mnt/output
- /home/john/ComfyUI/input:/mnt/input
- /home/john/SmartGallery:/mnt/SmartGallery
```

**Windows Examples (using WSL paths):**
```yaml
- /mnt/c/Users/YourName/ComfyUI/output:/mnt/output
- /mnt/c/Users/YourName/ComfyUI/input:/mnt/input
- /mnt/c/Users/YourName/SmartGallery:/mnt/SmartGallery
```

**Mac Examples:**
```yaml
- /Users/yourname/ComfyUI/output:/mnt/output
- /Users/yourname/ComfyUI/input:/mnt/input
- /Users/yourname/SmartGallery:/mnt/SmartGallery
```

**2. User Permissions (Linux/Mac Only)**

Find your user ID and group ID:
```bash
id -u  # Your User ID (UID)
id -g  # Your Group ID (GID)
```

Update in `compose.yaml`:
```yaml
environment:
  - WANTED_UID=1000  # Replace with your UID
  - WANTED_GID=1000  # Replace with your GID
```

> **Windows Users**: Leave these as `1000` (default values work fine on Windows).

**3. Optional: Change Port**

Only if port 8189 is already in use:
```yaml
ports:
  - 8190:8189  # Maps host port 8190 to container port 8189
```

### Step 3: Start the Container
```bash
docker compose up -d
```

The `-d` flag runs it in detached mode (background).

**What happens:**
1. Container starts with name `comfy-smartgallery`
2. Mounts your specified volumes
3. Adjusts internal user permissions to match your UID/GID
4. Starts SmartGallery web server
5. Makes it accessible at `http://localhost:8189/galleryout`

### Step 4: Verify It's Running

**Check container status:**
```bash
docker ps
```

You should see `comfy-smartgallery` in the list.

**View logs:**
```bash
docker compose logs -f
```

Press `Ctrl+C` to stop following logs.

**Access the gallery:**
Open your browser and navigate to:
```
http://localhost:8189/galleryout
```

### Managing the Container

**Stop the container:**
```bash
docker compose down
```

**Restart the container:**
```bash
docker compose restart
```

**View live logs:**
```bash
docker compose logs -f comfy-smartgallery
```

**Update after code changes:**
```bash
docker compose down
docker build -t smartgallery:latest .
docker compose up -d
```

---

## Method 2: Makefile (Power Users)

The Makefile provides more control and is ideal for developers or advanced users.

### Step 1: Configure the Makefile

Open `Makefile` and adjust these variables:
```makefile
# === CHANGE THESE VALUES ===

# Your actual paths on the host system
BASE_OUTPUT_PATH_REAL=/home/username/ComfyUI/output
BASE_INPUT_PATH_REAL=/home/username/ComfyUI/input
BASE_SMARTGALLERY_PATH_REAL=/home/username/SmartGallery

# Your user permissions (use: id -u and id -g)
WANTED_UID=1000
WANTED_GID=1000

# === OPTIONAL CUSTOMIZATIONS ===

# Port to expose
EXPOSED_PORT=8189

# SmartGallery settings
THUMBNAIL_WIDTH=300
PAGE_SIZE=100
BATCH_SIZE=500

# === DO NOT CHANGE (container internal paths) ===
BASE_OUTPUT_PATH=/mnt/output
BASE_INPUT_PATH=/mnt/input
BASE_SMARTGALLERY_PATH=/mnt/SmartGallery
```

### Step 2: Build the Image
```bash
make build
```

This builds the Docker image with detailed logging. The build log is saved to `smartgallery.log`.

### Step 3: Run the Container
```bash
make run
```

This starts the container with all your configured settings.

### Step 4: Manage the Container

**Stop and remove:**
```bash
make kill
```

**Remove buildx builder (if needed):**
```bash
make buildx_rm
```

### Makefile Commands Reference

| Command | Description |
|---------|-------------|
| `make build` | Build the Docker image with logging |
| `make run` | Start the container with configured settings |
| `make kill` | Stop and remove the container |
| `make buildx_rm` | Remove the buildx builder |

---

## Understanding Docker Permissions

SmartGallery's Docker setup uses a **two-user system** to handle Linux file permissions correctly.

### Why Permissions Matter

When Docker creates files inside a container, they're owned by the container's user (typically UID 1000 or root). This can cause problems:

❌ **Without proper UID/GID mapping:**
- Files created by the container are owned by a different user on your host
- You can't edit or delete files created by SmartGallery
- SmartGallery might not be able to read your ComfyUI files

✅ **With proper UID/GID mapping:**
- Files created inside the container match your host user
- Full read/write access from both container and host
- No permission errors

### The Two-User System

SmartGallery uses two users to achieve this:

1. **`smartgallerytoo`** (UID 1025)
   - Initial user that starts the container
   - Adjusts the `smartgallery` user's UID/GID
   - Restarts the script as `smartgallery`

2. **`smartgallery`** (UID adjustable)
   - Actual user running SmartGallery
   - UID/GID is changed to match your `WANTED_UID`/`WANTED_GID`
   - All files are created with your host user's permissions

### How It Works

The `docker_init.bash` script automatically:

1. Checks if running as `smartgallerytoo` (initial startup)
2. Uses `sudo` to modify `smartgallery` user's UID/GID
3. Changes ownership of `/home/smartgallery` directory
4. Saves environment variables
5. Restarts the script as the `smartgallery` user
6. Verifies UID/GID match the expected values
7. Starts SmartGallery application

### Setting Your UID/GID

**On Linux/Mac:**
```bash
# Find your UID and GID
id -u  # Example output: 1000
id -g  # Example output: 1000

# Use these values in compose.yaml or Makefile
WANTED_UID=1000
WANTED_GID=1000
```

**On Windows:**

Windows handles Docker permissions differently. Use the default values:
```yaml
WANTED_UID=1000
WANTED_GID=1000
```

---

## Environment Variables Reference

All SmartGallery configuration can be set via environment variables in `compose.yaml`:

### Core Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BASE_OUTPUT_PATH` | ComfyUI output folder (container path) | Required | `/mnt/output` |
| `BASE_INPUT_PATH` | ComfyUI input folder (container path) | Required | `/mnt/input` |
| `BASE_SMARTGALLERY_PATH` | Database/cache location (container path) | Same as output | `/mnt/SmartGallery` |
| `FFPROBE_MANUAL_PATH` | Path to ffprobe executable | `/usr/bin/ffprobe` | `/usr/bin/ffprobe` |
| `SERVER_PORT` | Web server port inside container | `8189` | `8189` |

### Gallery Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `THUMBNAIL_WIDTH` | Thumbnail width in pixels | `300` | `300` |
| `PAGE_SIZE` | Files to load initially | `100` | `100` |
| `WEBP_ANIMATED_FPS` | WebP animation frame rate | `16.0` | `16.0` |
| `BATCH_SIZE` | Database sync batch size | `500` | `500` |

### Performance

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MAX_PARALLEL_WORKERS` | CPU cores for processing | `""` (all cores) | `4` or `""` |

**Options for `MAX_PARALLEL_WORKERS`:**
- `""` (empty string): Use all available CPU cores (fastest)
- `1`: Single-threaded processing (slowest, lowest CPU usage)
- `4`: Use 4 CPU cores (balanced)

### Docker-Specific

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `WANTED_UID` | Host user ID for file permissions | `1000` | `1000` |
| `WANTED_GID` | Host group ID for file permissions | `1000` | `1000` |

### Adding Custom Environment Variables

In `compose.yaml`:
```yaml
environment:
  - BASE_OUTPUT_PATH=/mnt/output
  - BASE_INPUT_PATH=/mnt/input
  - BASE_SMARTGALLERY_PATH=/mnt/SmartGallery
  - THUMBNAIL_WIDTH=400
  - PAGE_SIZE=200
  - MAX_PARALLEL_WORKERS=4
  - WANTED_UID=1000
  - WANTED_GID=1000
```

---

## Docker Volumes Explained

Docker volumes map folders from your host system into the container.

### Volume Configuration
```yaml
volumes:
  - /host/path:/container/path
```

**Left side (before `:`)**: Path on your host computer  
**Right side (after `:`)**: Path inside the container

### SmartGallery Volumes
```yaml
volumes:
  - /home/user/ComfyUI/output:/mnt/output
  - /home/user/ComfyUI/input:/mnt/input
  - /home/user/SmartGallery:/mnt/SmartGallery
```

**First Volume** (`/mnt/output`):
- Your ComfyUI generated files
- Images, videos, workflows
- SmartGallery reads from here
- Can be read-only if desired: `/path/to/output:/mnt/output:ro`

**Second Volume** (`/mnt/input`):
- Your ComfyUI input folder (source images, videos, audio)
- Required for the Node Summary to display source media
- SmartGallery reads from here
- Can be read-only if desired: `/path/to/input:/mnt/input:ro`

**Third Volume** (`/mnt/SmartGallery`):
- SmartGallery's working directory
- SQLite database
- Thumbnail cache
- ZIP downloads
- Needs read-write access

### Volume Best Practices

✅ **Do:**
- Use absolute paths: `/home/user/...`
- Ensure folders exist before starting container
- Keep SmartGallery data separate from ComfyUI output
- Use descriptive folder names: `SmartGallery_Data`

❌ **Don't:**
- Use relative paths: `../ComfyUI/output` (won't work)
- Mount the same folder to multiple paths
- Store SmartGallery data inside ComfyUI output folder

### Checking Volume Contents

**From host:**
```bash
ls -la /home/user/SmartGallery
```

**From inside container:**
```bash
docker exec -it comfy-smartgallery ls -la /mnt/SmartGallery
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker compose logs comfy-smartgallery
```

**Common issues:**

1. **Port already in use:**
```
   Error: bind: address already in use
```
   **Solution**: Change the port in `compose.yaml`:
```yaml
   ports:
     - 8190:8189  # Use 8190 instead
```

2. **Volume path doesn't exist:**
```
   Error: invalid mount config
```
   **Solution**: Create the folders first:
```bash
   mkdir -p /home/user/ComfyUI/output
   mkdir -p /home/user/SmartGallery
```

3. **Image not found:**
```
   Error: No such image: smartgallery:latest
```
   **Solution**: Build the image first:
```bash
   docker build -t smartgallery:latest .
```

### Permission Denied Errors

**Symptom**: Container can't read ComfyUI files or write database.

**Check your UID/GID:**
```bash
id -u  # Should match WANTED_UID
id -g  # Should match WANTED_GID
```

**Verify volume permissions:**
```bash
ls -la /home/user/ComfyUI/output
ls -la /home/user/SmartGallery
```

**Fix permissions:**
```bash
# Make folders accessible
chmod 755 /home/user/ComfyUI/output
chmod 755 /home/user/SmartGallery

# Change ownership (if needed)
sudo chown -R $(id -u):$(id -g) /home/user/SmartGallery
```

**Update UID/GID in compose.yaml:**
```yaml
environment:
  - WANTED_UID=1000  # Your actual UID
  - WANTED_GID=1000  # Your actual GID
```

Then restart:
```bash
docker compose down
docker compose up -d
```

### Can't Access Gallery

**Check if container is running:**
```bash
docker ps
```

**Check if port is accessible:**
```bash
curl http://localhost:8189/galleryout
```

**Check firewall (Linux):**
```bash
sudo ufw allow 8189
```

**Try different browser or incognito mode** (clears cache).

### Database or Thumbnail Issues

**Reset SmartGallery data:**
```bash
# Stop container
docker compose down

# Delete SmartGallery data (not ComfyUI files!)
rm -rf /home/user/SmartGallery/*

# Start container (will rebuild database)
docker compose up -d
```

### Container Exits Immediately

**View exit logs:**
```bash
docker compose logs comfy-smartgallery
```

**Common causes:**
- Missing or incorrect `BASE_OUTPUT_PATH`
- UID/GID mismatch causing permission errors
- Python dependency issues

**Try running interactively:**
```bash
docker run -it --rm \
  -v /path/to/output:/mnt/output \
  -v /path/to/smartgallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e WANTED_UID=1000 \
  -e WANTED_GID=1000 \
  smartgallery:latest \
  /bin/bash
```

This drops you into a shell inside the container for debugging.

### Rebuild After Code Changes
```bash
# Stop container
docker compose down

# Rebuild image
docker build -t smartgallery:latest .

# Start container
docker compose up -d

# Check logs
docker compose logs -f
```

### Still Having Issues?

1. **Check the main troubleshooting section** in [README.md](README.md#-troubleshooting)
2. **Open an issue** on GitHub with:
   - Your `docker compose logs` output
   - Your `compose.yaml` configuration (remove sensitive paths)
   - Operating system and Docker version
   - Steps to reproduce the problem

---

## Advanced Topics

### Running Multiple Instances

To run multiple SmartGallery instances (e.g., for different ComfyUI installations):

**1. Create separate compose files:**

`compose-instance1.yaml`:
```yaml
services:
  smartgallery-instance1:
    image: smartgallery:latest
    container_name: smartgallery-instance1
    ports:
      - 8189:8189
    volumes:
      - /path/to/comfyui1/output:/mnt/output
      - /path/to/comfyui1/input:/mnt/input
      - /path/to/smartgallery1:/mnt/SmartGallery
    environment:
      - BASE_OUTPUT_PATH=/mnt/output
      - BASE_INPUT_PATH=/mnt/input
      - BASE_SMARTGALLERY_PATH=/mnt/SmartGallery
      - WANTED_UID=1000
      - WANTED_GID=1000
```

`compose-instance2.yaml`:
```yaml
services:
  smartgallery-instance2:
    image: smartgallery:latest
    container_name: smartgallery-instance2
    ports:
      - 8190:8189  # Different port!
    volumes:
      - /path/to/comfyui2/output:/mnt/output
      - /path/to/comfyui2/input:/mnt/input
      - /path/to/smartgallery2:/mnt/SmartGallery
    environment:
      - BASE_OUTPUT_PATH=/mnt/output
      - BASE_INPUT_PATH=/mnt/input
      - BASE_SMARTGALLERY_PATH=/mnt/SmartGallery
      - WANTED_UID=1000
      - WANTED_GID=1000
```

**2. Start both:**
```bash
docker compose -f compose-instance1.yaml up -d
docker compose -f compose-instance2.yaml up -d
```

**3. Access:**
- Instance 1: `http://localhost:8189/galleryout`
- Instance 2: `http://localhost:8190/galleryout`

### Using Docker Run Instead of Compose

If you prefer `docker run` over compose:
```bash
docker run -d \
  --name smartgallery \
  -p 8189:8189 \
  -v /home/user/ComfyUI/output:/mnt/output \
  -v /home/user/ComfyUI/input:/mnt/input \
  -v /home/user/SmartGallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e BASE_INPUT_PATH=/mnt/input \
  -e BASE_SMARTGALLERY_PATH=/mnt/SmartGallery \
  -e WANTED_UID=1000 \
  -e WANTED_GID=1000 \
  --restart unless-stopped \
  smartgallery:latest
```

### Read-Only Output Volume

If you want to prevent SmartGallery from modifying your ComfyUI outputs:
```yaml
volumes:
  - /path/to/output:/mnt/output:ro  # :ro = read-only
  - /path/to/input:/mnt/input:ro  # :ro = read-only
  - /path/to/smartgallery:/mnt/SmartGallery
```

### Custom Network Configuration

To run SmartGallery on a custom Docker network:
```yaml
services:
  comfy-smartgallery:
    image: smartgallery:latest
    networks:
      - comfyui_network
    # ... rest of configuration ...

networks:
  comfyui_network:
    external: true
```

### Resource Limits

Limit CPU and memory usage:
```yaml
services:
  comfy-smartgallery:
    image: smartgallery:latest
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Health Checks

Add a health check to monitor container status:
```yaml
services:
  comfy-smartgallery:
    image: smartgallery:latest
    # ... other config ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8189/galleryout"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Need More Help?

- **Main README**: [README.md](README.md)
- **Report Issues**: [GitHub Issues](../../issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

<p align="center">
  <em>Made with ❤️ for the ComfyUI community</em>
</p>