# Advanced Storage, NAS & Multi-Drive Setup Guide

SmartGallery works out of the box when pointed directly at ComfyUI's `output` folder. However, once your library grows to **tens of thousands of assets (40K–100K+ files)**—or when you want to store media on a **NAS, external drive, or another computer on your LAN**—separating SmartGallery's root, cache database, and ComfyUI's active `output` folder gives you major performance, stability, and organizational benefits.

This guide explains how to design, configure, and maintain an advanced multi-drive or network storage layout across **Windows, macOS, Linux, and Docker**.

---

## Table of Contents

1. [Why Separate SmartGallery from ComfyUI's `output` Folder?](#1-why-separate-smartgallery-from-comfyuis-output-folder)
2. [The Recommended 4-Variable Architecture](#2-the-recommended-4-variable-architecture)
3. [Configuration Examples (Windows, Linux/macOS, Docker)](#3-configuration-examples-windows-linuxmacos-docker)
4. [Mounting External & Network Drives (`🔗 Mount Folder`)](#4-mounting-external--network-drives--mount-folder)
5. [Windows Symlinks, Developer Mode & the `Z:\` UAC Trap](#5-windows-symlinks-developer-mode--the-z-uac-trap)
6. [Real-World LAN Setup: Windows GPU Host + Mac Storage & Browser](#6-real-world-lan-setup-windows-gpu-host--mac-storage--browser)
7. [Migrating an Existing 50K+ Library Without Losing DAM Data](#7-migrating-an-existing-50k-library-without-losing-dam-data)
8. [Rules for Moving, Renaming & Creating Subfolders](#8-rules-for-moving-renaming--creating-subfolders)
9. [Performance Tips for Large Libraries (50K–100K+ Files)](#9-performance-tips-for-large-libraries-50k100k-files)
10. [Troubleshooting & FAQ](#10-troubleshooting--faq)

---

## 1. Why Separate SmartGallery from ComfyUI's `output` Folder?

When you keep everything inside ComfyUI's `output` directory, three bottlenecks eventually appear as your library grows:

1. **ComfyUI's Asset Scanner Overhead:**
   ComfyUI's built-in asset scanner checks its `output` directory very frequently (every few seconds). If 49K–100K+ archived images and videos live inside `ComfyUI/output`—or if you place a symlink to a 50K+ archive *inside* `ComfyUI/output`—ComfyUI may repeatedly walk that massive tree.
2. **Keeping SQLite & Thumbnails on Fast Local Storage:**
   Media files can sit on a large mechanical HDD or network NAS, while SmartGallery's database (`.sqlite_cache`) and `.thumbnails_cache` should always live on a **fast local NVMe/SSD** (`BASE_SMARTGALLERY_PATH`). That way, scrolling, searching, filtering, rating, and opening collections remain instantaneous regardless of where the source files are stored.
3. **Never Put SQLite WAL Databases on Network Shares (SMB / NFS):**
   SmartGallery runs SQLite in **WAL mode** (`PRAGMA journal_mode=WAL`) so multiple threads, Exhibition Portals, and AI workers can access it concurrently. Network filesystems (SMB/CIFS, NFS) do not reliably support the shared-memory locking required by SQLite `-shm`/`-wal` files, which can cause `database is locked` errors or database corruption. Keeping `BASE_SMARTGALLERY_PATH` on a local drive eliminates this risk completely.

---

## 2. The Recommended 4-Variable Architecture

Instead of pointing `BASE_OUTPUT_PATH` directly at `ComfyUI/output`, create a **neutral empty root folder** for SmartGallery (for example, `E:/SG_ROOT`), keep ComfyUI writing to its own local `output` folder, keep SmartGallery's database/cache in its own fast local folder (`E:/SG_DATABASE`), and mount both `ComfyUI/output` and your archive drive inside `SG_ROOT`:

```text
E:/SG_ROOT/                     <-- BASE_OUTPUT_PATH (neutral SmartGallery root)
 ├── ComfyUI_Output/  (🔗 link) --> E:/ComfyUI/output/        (local SSD: live ComfyUI renders)
 └── Archive/         (🔗 link) --> Z:/COMFYUI_ARCHIVE/       (NAS / external / network share, or D:/Archive)

E:/SG_DATABASE/                 <-- BASE_SMARTGALLERY_PATH (fast local SSD: DB + thumbnails)
E:/ComfyUI/models/              <-- BASE_MODELS_PATH (explicitly set for LoRA Synergy & Matchmaker)
E:/ComfyUI/input/               <-- BASE_INPUT_PATH  (explicitly set for Node Summary & Remix)
```

### What Lives Where

| Variable | Recommended Location | What It Stores / Controls |
| :--- | :--- | :--- |
| **`BASE_OUTPUT_PATH`** | Neutral local folder (`E:/SG_ROOT`) | Root gallery directory scanned by SmartGallery (`followlinks=True`). Holds your normal folders and `🔗` mount links. |
| **`BASE_SMARTGALLERY_PATH`** | Fast local SSD (`E:/SG_DATABASE`) | Service folders: `.sqlite_cache`, `.thumbnails_cache`, `.clean_cache`, `.zip_downloads`, `.collection_notes`, `.imported_workflows`, `.omniquery`. |
| **`BASE_MODELS_PATH`** | ComfyUI models dir (`E:/ComfyUI/models`) | Used by **LoRA Synergy**, `.civitai.info`/`.metadata.json` trigger mining, LoRA preview thumbnails, and **Matchmaker** (`loras`, `checkpoints`, `unet`). |
| **`BASE_INPUT_PATH`** | ComfyUI input dir (`E:/ComfyUI/input`) | Used by **Node Summary** to display source images/videos and by **Remix Workflow** to upload new input media to ComfyUI. |

### Why Setting `BASE_MODELS_PATH` and `BASE_INPUT_PATH` Explicitly Matters
In `smartgallery.py`, if `BASE_MODELS_PATH` is not set via environment variable, it defaults to:
```text
<parent folder of BASE_OUTPUT_PATH>/models
```
When `BASE_OUTPUT_PATH` is `E:/ComfyUI/output`, that default conveniently resolves to `E:/ComfyUI/models`.
However, once you change `BASE_OUTPUT_PATH` to `E:/SG_ROOT`, the default would look for `E:/models` (which doesn't exist), silently disabling LoRA Synergy previews and Matchmaker!

Setting `BASE_MODELS_PATH` and `BASE_INPUT_PATH` explicitly ensures **all ComfyUI integrations continue working 100%** regardless of where `SG_ROOT` and `SG_DATABASE` live.

> **Custom Model Paths (Stability Matrix / `extra_model_paths.yaml`):**
> If your checkpoints, LoRAs, or UNET models are split across different folders, you can also override `LORAS_PATH`, `CHECKPOINTS_PATH`, and `UNET_PATH` individually as environment variables.

---

## 3. Configuration Examples (Windows, Linux/macOS, Docker)

Always use **forward slashes (`/`)** in environment variable paths—even on Windows—and wrap paths containing spaces in double quotes.

### Windows (Command Prompt `.bat`)
```bat
@echo off
call venv\Scripts\activate.bat

set "BASE_OUTPUT_PATH=E:/SG_ROOT"
set "BASE_SMARTGALLERY_PATH=E:/SG_DATABASE"
set "BASE_MODELS_PATH=E:/ComfyUI/models"
set "BASE_INPUT_PATH=E:/ComfyUI/input"

set "COMFYUI_SERVER_URL=http://127.0.0.1:8188"
set "FFPROBE_MANUAL_PATH=C:/ffmpeg/bin/ffprobe.exe"
set SERVER_PORT=8189

REM Optional: Safe Trash instead of permanent delete (keep on same drive if possible)
REM set "DELETE_TO=E:/SG_Trash"

python smartgallery.py
```

### Windows (PowerShell `.ps1`)
```powershell
venv\Scripts\Activate.ps1

$env:BASE_OUTPUT_PATH="E:/SG_ROOT"
$env:BASE_SMARTGALLERY_PATH="E:/SG_DATABASE"
$env:BASE_MODELS_PATH="E:/ComfyUI/models"
$env:BASE_INPUT_PATH="E:/ComfyUI/input"

$env:COMFYUI_SERVER_URL="http://127.0.0.1:8188"
$env:FFPROBE_MANUAL_PATH="C:/ffmpeg/bin/ffprobe.exe"
$env:SERVER_PORT="8189"

python smartgallery.py
```

### Linux / macOS (`bash` / `zsh`)
```bash
#!/usr/bin/env bash
source venv/bin/activate

export BASE_OUTPUT_PATH="$HOME/sg_root"
export BASE_SMARTGALLERY_PATH="$HOME/sg_database"
export BASE_MODELS_PATH="$HOME/ComfyUI/models"
export BASE_INPUT_PATH="$HOME/ComfyUI/input"

export COMFYUI_SERVER_URL="http://127.0.0.1:8188"
export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
export SERVER_PORT=8189

python3 smartgallery.py
```

### Docker (`docker-compose.yml`)
In Docker, bind-mount your fast local SSD folder to `/app/sg_database`, and mount your media folders directly under `/app/sg_root/...`:

```yaml
services:
  smartgallery:
    image: smartgallery:latest
    ports:
      - "8189:8189"
    environment:
      - BASE_OUTPUT_PATH=/app/sg_root
      - BASE_SMARTGALLERY_PATH=/app/sg_database
      - BASE_MODELS_PATH=/app/comfy_models
      - BASE_INPUT_PATH=/app/comfy_input
      - COMFYUI_SERVER_URL=http://host.docker.internal:8188
      - SERVER_PORT=8189
    volumes:
      # Fast local SSD for SQLite & thumbnails
      - /local/ssd/sg_database:/app/sg_database
      # Live ComfyUI output + Archive mounted into SG_ROOT
      - /local/ssd/comfyui/output:/app/sg_root/ComfyUI_Output
      - /mnt/nas/comfyui_archive:/app/sg_root/Archive
      # ComfyUI models (read-only is fine) & input
      - /local/ssd/comfyui/models:/app/comfy_models:ro
      - /local/ssd/comfyui/input:/app/comfy_input
```

> **Docker Warning for NAS Bind Mounts:**
> If your NAS share `/mnt/nas/comfyui_archive` is temporarily unmounted on the host when the Docker container starts, Docker will see an empty directory at `/app/sg_root/Archive`—and unlike SG's internal `mounted_folders` links, Docker bind mounts aren't registered in `mounted_folders`, so `full_sync_database()` could think those files were deleted. Ensure your NAS mount is active before starting the container (e.g., via systemd `RequiresMountsFor=` or `autofs`).

---

## 4. Mounting External & Network Drives (`🔗 Mount Folder`)

Inside SmartGallery's sidebar, the **🔗 (Link External Folder)** button lets you attach folders from other drives or network shares directly under `BASE_OUTPUT_PATH` (`SG_ROOT`).

### Why You Should Always Use SG's Mount UI (Instead of Manual Symlinks)
When you mount a folder through SmartGallery's UI:
1. SmartGallery creates the OS link (`mklink /J` or `mklink /D` on Windows, `os.symlink` on Linux/macOS) inside `BASE_OUTPUT_PATH`.
2. It registers the link path in the **`mounted_folders`** SQLite table.
3. **Offline-Drive Protection:** On every startup, `full_sync_database()` checks every registered mount in `mounted_folders`. If a network drive (`Z:\`) or external USB drive is disconnected or sleeping (`os.path.exists(mount_path) == False`), SmartGallery prints:
   ```text
   WARN: Mount point seems offline: E:/SG_ROOT/Archive
   PROTECTION ACTIVE: Skipped deletion of 49210 files because their source drive appears offline.
   ```
   Your favorites, collections, ratings, comments, and AI captions stay 100% safe until the drive is reconnected!

If you create symlinks/junctions manually in a terminal outside SG, they are **not** in `mounted_folders`, so an offline drive at startup would cause SmartGallery to remove those entries from the DB.

### Important: Do NOT Mount the Archive Inside ComfyUI's `output` Folder
If your goal is to prevent ComfyUI's built-in asset scanner from scanning your archive, **do not** leave `BASE_OUTPUT_PATH=E:/ComfyUI/output` and mount `Z:/COMFYUI_ARCHIVE` inside it. Because `mount_folder` creates the link inside `BASE_OUTPUT_PATH`, the link would sit at `E:/ComfyUI/output/Archive`, where ComfyUI's scanner may follow it. Always use a separate neutral `BASE_OUTPUT_PATH` (such as `E:/SG_ROOT`).

---

## 5. Windows Symlinks, Developer Mode & the `Z:\` UAC Trap

When creating a mount on Windows, `smartgallery.py` tries two native link types in order:
1. **NTFS Junction (`mklink /J`):** Works on local NTFS drives (`C:\`, `D:\`, `E:\`) without Administrator privileges.
2. **Directory Symbolic Link (`mklink /D`):** Automatically used as fallback when `mklink /J` fails—which is **always required for network drives (`Z:\`), SMB/UNC paths, and certain virtual drives** (*"Local volumes are required to complete the operation"*).

### Question: Do I Have to Run SmartGallery as Administrator Every Time?
**No.** Windows only checks symlink-creation privileges **once** at the moment the `mklink /D` link is created. Once the symlink exists in `E:/SG_ROOT`, normal (non-elevated) SmartGallery can read, browse, thumbnail, and scan through it permanently.

### ⚠️ The Classic Windows UAC + Mapped Network Drive (`Z:\`) Trap
In Windows, mapped network drive letters (`Z:\`) are scoped to your **standard (non-elevated) user session**. When UAC is enabled and you right-click **"Run as Administrator"**, Windows creates a separate elevated security token—and in that elevated session, **`Z:\` often does not exist at all!** Attempting to browse or mount `Z:\` from an elevated SmartGallery prompt frequently fails with:
```text
Target path does not exist: Z:\COMFYUI_ARCHIVE
```

### ✅ The Best Solution: Enable Windows Developer Mode
Enabling **Developer Mode** allows your standard (non-admin) Windows user to create `mklink /D` symbolic links directly—keeping SmartGallery in the exact same user session that already sees `Z:\`:

- **Windows 10:** `Settings` → `Update & Security` → `For developers` → Turn **Developer Mode** **ON**
- **Windows 11:** `Settings` → `System` → `For developers` → Turn **Developer Mode** **ON**

After enabling Developer Mode:
1. Start SmartGallery **normally** (do *not* run as Administrator).
2. Click `🔗` in the sidebar, select `Z:\COMFYUI_ARCHIVE`, give it a name (e.g., `Archive`), and click **Create Link**.

*(If a corporate IT policy prevents enabling Developer Mode, you can map the network share inside the elevated session or mount via UNC/admin once, then run SG normally afterwards.)*

---

## 6. Real-World LAN Setup: Windows GPU Host + Mac Storage & Browser

A popular multi-machine workflow looks like this:
- **Windows 10/11 PC (GPU Host):** Runs ComfyUI (`:8188`) and SmartGallery (`:8189`), has a fast local SSD (`E:`) for `SG_DATABASE` and live ComfyUI `output`.
- **Mac (or Dedicated NAS) on the Same LAN:** Stores the large media archive and acts as the daily viewing/management client via Firefox/Safari/Chrome.

### Step-by-Step Setup

1. **On the Mac (or NAS):**
   - Enable SMB File Sharing (*System Settings → General → Sharing → File Sharing* on macOS) and share your archive folder (e.g., `COMFYUI_ARCHIVE`).
2. **On the Windows PC:**
   - Map the Mac/NAS SMB share as a persistent drive letter (e.g., `Z:\` → `\\YourMacName\COMFYUI_ARCHIVE`, checking *"Reconnect at sign-in"*).
   - Enable **Windows Developer Mode** (see [Section 5](#5-windows-symlinks-developer-mode--the-z-uac-trap)).
   - Configure your SmartGallery startup script with the [4-Variable Architecture](#2-the-recommended-4-variable-architecture):
     - `BASE_OUTPUT_PATH=E:/SG_ROOT`
     - `BASE_SMARTGALLERY_PATH=E:/SG_DATABASE`
     - `BASE_MODELS_PATH=E:/ComfyUI/models`
     - `BASE_INPUT_PATH=E:/ComfyUI/input`
     - `COMFYUI_SERVER_URL=http://127.0.0.1:8188`
3. **Mount Inside SmartGallery:**
   - Start SmartGallery on the Windows PC, click `🔗`, mount `E:/ComfyUI/output` as `ComfyUI_Output`, and mount `Z:/COMFYUI_ARCHIVE` as `Archive`.
4. **Access from Firefox on Your Mac:**
   - Look at the Windows SmartGallery console output on startup—it automatically detects and prints your LAN address:
     ```text
     👉 Local Access:   http://127.0.0.1:8189/galleryout/
     👉 Network Access: http://192.168.1.50:8189/galleryout/
     ```
   - Open `http://192.168.1.50:8189/galleryout/` on your Mac.
   - Features like **Remix Workflow**, **ComfyUI Queue Deck**, and **LoRA Synergy** are relayed cleanly through SmartGallery's backend proxy (`/galleryout/api/comfy_proxy/...`) to `http://127.0.0.1:8188` on the Windows PC—no CORS issues and no need to expose ComfyUI directly if you don't want to!

---

## 7. Migrating an Existing 50K+ Library Without Losing DAM Data

SmartGallery identifies every asset in SQLite by `id = md5(path)`.
If you already have an existing database with favorites, collections, status tags, ratings, comments, or AI captions and want to move your archive out of `E:/ComfyUI/output` onto `Z:/COMFYUI_ARCHIVE` (or a new local drive):

### Option A: Massive / NAS Migrations (`sg_migrate_paths.py` — Recommended for 5,000+ Files)
Use the standalone offline migration utility **`sg_migrate_paths.py`** (see [`SG_MIGRATE_PATHS_GUIDE.md`](./SG_MIGRATE_PATHS_GUIDE.md)):
- Remaps all paths and MD5 IDs directly inside `gallery_cache.sqlite` in **under 1 second**—with **zero network file reads** over `Z:\`.
- Preserves **100%** of favorites, collections, status flags, ratings, comments, AI data, workflow hashes, and `.webp` thumbnail links for images, videos, audio, and notes.
- Automatically moves/copies nothing on disk; you move files with `robocopy` / `rsync` / Explorer while **ALL SmartGallery instances (Main, `--exhibition`, AI Service) are stopped**, then run `sg_migrate_paths.py --dry-run` followed by live migration.

### Option B: Small / Ad-Hoc Moves Outside SmartGallery
If you move a smaller batch of files manually on disk while SmartGallery is closed, `full_sync_database()` includes automatic DAM metadata preservation:
- Before deleting old missing paths from SQLite, it matches moved **images** 1-to-1 by `content_sha256` and moved **videos/audio** 1-to-1 by `(type, name, size, duration, dimensions)`, transferring favorites, collections, ratings, comments, and AI captions to the new paths.
- If SmartGallery detects **5,000+ removed and 5,000+ added files** in the same startup scan, it prints a notice recommending `sg_migrate_paths.py` for instant NAS/drive migration while still proceeding safely with DAM-preserving sync.

---

## 8. Rules for Moving, Renaming & Creating Subfolders

When working with a mixed local + mounted setup (`SG_ROOT`), SmartGallery applies strict safety rules in the sidebar `⋮` folder menu to prevent broken symlinks or accidental multi-GB cross-drive copies inside web requests:

| Action in Folder `⋮` Menu | Normal Local Folder | Local Subfolder *Inside* a Local Mount | Network / Remote Mount Subfolder (`Z:\`) | Top-Level Mount Root (`🔗`) |
| :--- | :---: | :---: | :---: | :---: |
| **`ℹ️ Info`** | ✅ Shows path | ✅ Shows logical + physical real path | ✅ Shows logical + physical real path | ✅ Shows logical + link target |
| **`➕ New Subfolder`** | ✅ Live tree update | ✅ Live tree update | ✅ Live tree update (if writable) | ✅ Live tree update (if writable) |
| **`⋮ → ✏️ Rename`** | ✅ Atomic rename + DB update | ✅ Atomic rename + DB update | ✅ Atomic rename + DB update | ❌ Blocked (unmount & remount) |
| **`⋮ → 📁 Move`** | ✅ Same local drive only | ✅ Same local drive only (even back up to mount root!) | ❌ Blocked (use `sg_migrate_paths.py`) | ❌ Blocked |
| **`⋮ → ⛓️ Unmount`** | N/A | N/A | N/A | ✅ Safely removes link & DB rows only |
| **`⋮ → 🗑️ Delete`** | ⚠️ Deletes folder on disk | ⚠️ Deletes subfolder on disk | ⚠️ Deletes subfolder on disk | ✅ Unlinks mount point safely |

### How Smart `Move Folder` Works Under the Hood
- SmartGallery resolves the real physical paths (`realpath`) of both the source folder and destination parent, verifies **neither** is on a network drive (Windows `GetDriveTypeW`/UNC, Linux `/proc/mounts`, macOS `df`), and verifies both share the exact same filesystem device (`st_dev`).
- This means if you have `E:/SG_ROOT/ComfyUI Archive` mounted to local `E:/ComfyUI Archive`, you **can** freely reorganize and move subfolders inside it (e.g., moving `A-Zovya_Photoreal` into `Stable Diffusion 1.x`, or back up to `ComfyUI Archive 🔗`) in milliseconds with zero duplicate files or lost DAM metadata.
- If you ever need to move a folder **across different drives or onto a network share** (e.g., `E:\` → `Z:\`), SmartGallery blocks it in the web UI and points you to `sg_migrate_paths.py` so you can move the folder via your OS and remap the DB offline without losing DAM data.

---

## 9. Performance Tips for Large Libraries (50K–100K+ Files)

1. **Always keep `BASE_SMARTGALLERY_PATH` on a fast local NVMe/SSD:**
   Thumbnail loading and SQLite filtering/sorting depend heavily on local random-read IOPS.
2. **Expect longer startup `os.stat()` walks on network shares (`Z:\`):**
   Even with thumbnails and SQLite on `E:\`, `full_sync_database()` checks file existence, `mtime`, and `size` across all folders at startup. Over SMB, 50K `stat()` calls are significantly faster on wired **1GbE / 2.5GbE Ethernet** than Wi-Fi.
3. **Avoid unnecessary `Rescan All`:**
   Use **Refresh (`🔃`)** inside the specific folder you modified instead of running `Rescan All Files` on huge directories.
4. **Understand Content-Addressed Thumbnail Migration:**
   Images use SHA256-keyed `.webp` thumbnails in `.thumbnails_cache`. Unchanged existing images backfill only their SHA256 hash on startup (without re-encoding thumbnails or re-extracting workflows); `.webp` thumbnails are converted lazily on demand when viewed in the grid.
5. **Recommended Environment Tuning:**
   - `MAX_PARALLEL_WORKERS=""` — uses all CPU cores on Windows/Linux (SmartGallery automatically caps macOS to `4` to avoid file-descriptor / `BrokenProcessPool` limits on huge libraries).
   - `PAGE_SIZE=100` — keeps browser DOM rendering fast even in folders with 10K+ files.
   - `STREAM_THRESHOLD_MB=20` — keeps heavy video playback smooth.
   - `DELETE_TO="E:/SG_Trash"` — optional safety net that moves deleted files to a trash folder instead of deleting permanently *(note: if `DELETE_TO` is on `E:\` and you delete files from `Z:\`, moving to trash copies across the network; for instant trash on `Z:\` either leave `DELETE_TO` unset or adjust accordingly)*.
6. **Note on Exhibition Mode (`--exhibition`):**
   If you also run an Exhibition Portal sharing the same `BASE_SMARTGALLERY_PATH`, make sure its `BASE_OUTPUT_PATH`, `BASE_SMARTGALLERY_PATH`, and mount structure match your Main SmartGallery instance so both resolve the exact same file paths and IDs. **Always stop Exhibition instances before running `sg_migrate_paths.py`.**

---

## 10. Troubleshooting & FAQ

- **Error when mounting `Z:\`: `"Local volumes are required to complete the operation"` / Symlink failed**
  → Windows `mklink /J` only works on local NTFS drives, so SG falls back to `mklink /D`, which requires **Developer Mode** (recommended) or Admin privileges. Enable Windows Developer Mode (see [Section 5](#5-windows-symlinks-developer-mode--the-z-uac-trap)) and restart SG normally.

- **Error when mounting `Z:\` as Admin: `"Target path does not exist: Z:\..."`**
  → You are hitting the Windows UAC split-token issue where elevated processes cannot see mapped drives from your standard user session. **Do not** run SG as Administrator; enable **Windows Developer Mode** instead and launch SG as your regular user.

- **`Cannot move folders across different drives or volumes` or `Cannot move folders on network/remote drives`**
  → `⋮ → 📁 Move` only performs instant atomic same-drive moves on local disks. To move a folder across drives or onto/within a NAS share without losing favorites, collections, ratings, or comments, stop all SmartGallery instances, move the folder on disk with your OS, and run **`sg_migrate_paths.py`** (see [`SG_MIGRATE_PATHS_GUIDE.md`](./SG_MIGRATE_PATHS_GUIDE.md)).

- **LoRA previews / Matchmaker stopped working after switching to `BASE_OUTPUT_PATH=E:/SG_ROOT`**
  → Set `BASE_MODELS_PATH=E:/ComfyUI/models` explicitly in your startup script (see [Section 2](#2-the-recommended-4-variable-architecture)).

- **`database is locked` when querying `gallery_cache.sqlite`**
  → Make sure `BASE_SMARTGALLERY_PATH` is on a **local** filesystem (never on SMB/NFS). Also stop all SG / `--exhibition` / AI processes before running offline tools like `sg_migrate_paths.py`.
