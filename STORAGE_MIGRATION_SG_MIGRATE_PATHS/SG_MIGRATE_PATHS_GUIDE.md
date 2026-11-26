# SmartGallery Path Migration Guide (`sg_migrate_paths.py`)

When managing tens of thousands of AI-generated images and videos (49K–100K+ files), you may eventually want to reorganize your storage—for example:
- Moving an archive out of ComfyUI's `output` folder onto a dedicated drive or NAS share (`Z:\COMFYUI_ARCHIVE`)
- Separating `BASE_SMARTGALLERY_PATH` (database & `.thumbnails_cache`) onto a fast local NVMe SSD while keeping media on a larger HDD/NAS
- Changing mount points or container paths on **Windows, macOS, Linux, or Docker**

Because SmartGallery keys every database record by an MD5 hash of its file path (`id = md5(path)`), moving 50,000 files manually outside SmartGallery normally forces a full rescan over the network.

**`sg_migrate_paths.py`** remaps all paths and file IDs directly inside `gallery_cache.sqlite` in **under 1 second**, with **zero file reads over the network** and **100% preservation** of all DAM data.

---

## ⚠️ CRITICAL: Stop ALL SmartGallery Instances First!

`sg_migrate_paths.py` is an **offline standalone utility**. Before moving files or running a live migration, you **MUST stop every process** that touches `gallery_cache.sqlite` or your media folders:

1. **All Main SmartGallery instances**
2. **All Exhibition Mode instances (`--exhibition`)** — even though Exhibition is a viewing portal, guests actively **write ratings and comments** to `gallery_cache.sqlite`! Leaving an Exhibition portal running during migration can cause SQLite WAL lock errors, stale in-memory file lists, or ratings/comments submitted against old file IDs.
3. **Any SmartGallery AI Service / background indexer**
4. **Any SQLite DB viewer/editor** with `gallery_cache.sqlite` open

**Built-in Protection:** `sg_migrate_paths.py` automatically scans for running SmartGallery / Exhibition / AI processes and acquires an exclusive SQLite WAL lock probe before making any changes. If another instance (or Docker container) still has the database open, the tool **aborts safely** without modifying anything.

---

## What It Preserves

- ⭐ **Favorites** (`is_favorite`)
- 📚 **Virtual Collections & Status Flags** (`collection_files` — Approved, Review, To Edit, Rejected, Select, and custom albums)
- 🏅 **User Ratings** (`file_ratings`)
- 💬 **Comments & Direct Messages** (`file_comments`)
- 🧠 **AI Captions, Embeddings, Watched Folders & Queue** (`ai_caption`, `ai_embedding`, `ai_watched_folders`, `ai_indexing_queue`)
- ⚙️ **Workflow Metadata, Hashes & `.webp` Thumbnail Links** (`workflow_files`, `workflow_prompt`, `workflow_hash`, `prompt_hash`, `content_sha256`)

> **Important:** `sg_migrate_paths.py` **never** moves, copies, or deletes your actual image/video files on disk. It only updates the paths inside `gallery_cache.sqlite`.

---

## Safety Guarantees

1. **Process & Exclusive Lock Guard:** Detects running SmartGallery / `--exhibition` / AI processes and performs a strict `EXCLUSIVE` SQLite + `wal_checkpoint(TRUNCATE)` lock check before touching the DB.
2. **Automatic WAL-Safe Backup:** Creates a timestamped backup (`gallery_cache.sqlite.bak.YYYYMMDD_HHMMSS`) after truncating the WAL journal.
3. **Dry-Run Preview (`--dry-run`):** Shows exact row counts, DAM records to be preserved, and sample `OLD -> NEW` path conversions without writing anything.
4. **Optional Disk Verification (`--verify-disk`):** Verifies that your remapped files are actually reachable on disk at the `--new` location before you commit.
5. **Atomic Transaction + Integrity Check:** Runs inside a single SQLite `BEGIN EXCLUSIVE ... COMMIT` transaction, executes `PRAGMA foreign_key_check`, and automatically rolls back on any error.
6. **Cross-Platform Mixed-Slash Compliance:** Preserves SmartGallery's exact internal path convention (`/` for folder segments and `\` before filenames on Windows; `/` everywhere on macOS, Linux, and Docker) so no duplicate entries are created on subsequent scans.

---

## Step-by-Step Guide: Moving an Archive Out of ComfyUI `output` to a NAS / External Drive

Suppose your current setup is:
- Everything in `E:/ComfyUI/output` (both ComfyUI's new renders and your 49K+ archive)

And your goal is:
- `E:/ComfyUI/output/` → ComfyUI continues writing new renders here
- `Z:/COMFYUI_ARCHIVE/` → Network/external drive holding your 49K+ archive
- `E:/SG_ROOT/` → SmartGallery `BASE_OUTPUT_PATH` containing two SG Mount links:
  - `E:/SG_ROOT/ComfyUI_Output` → `E:/ComfyUI/output`
  - `E:/SG_ROOT/Archive` → `Z:/COMFYUI_ARCHIVE`
- `E:/SG_DATABASE/` → SmartGallery `BASE_SMARTGALLERY_PATH` (fast local SSD for `.sqlite_cache` and `.thumbnails_cache`)

### Step 1: Stop ALL SmartGallery, Exhibition & AI Instances
Close every SmartGallery server window, `--exhibition` portal, and AI service cleanly.

### Step 2: Move/Copy SG Cache Folders to `E:/SG_DATABASE`
Move (or copy) these hidden service folders from `E:/ComfyUI/output/` to `E:/SG_DATABASE/`:
- `.sqlite_cache`
- `.thumbnails_cache`
- *(if present)* `.clean_cache`, `.collection_notes`, `.imported_workflows`, `.omniquery`, `.zip_downloads`

### Step 3: Move/Copy Your Media Archive to `Z:/COMFYUI_ARCHIVE`
Move your archive folders from `E:/ComfyUI/output/` to `Z:/COMFYUI_ARCHIVE/` using your OS file manager or `robocopy` / `rsync`.

Example on Windows (preserving timestamps):
```bat
robocopy "E:\ComfyUI\output\MyArchiveFolder" "Z:\COMFYUI_ARCHIVE\MyArchiveFolder" /E /COPY:DAT /MOVE
```
*(Tip: Copy first and delete the source only after verifying if you want extra peace of mind!)*

### Step 4: Configure Your Environment Variables
Update your SmartGallery startup script (and any Exhibition startup script sharing this database!):
```bat
set "BASE_OUTPUT_PATH=E:/SG_ROOT"
set "BASE_SMARTGALLERY_PATH=E:/SG_DATABASE"
set "BASE_MODELS_PATH=E:/ComfyUI/models"
set "BASE_INPUT_PATH=E:/ComfyUI/input"
```
Create the empty folder `E:/SG_ROOT` if it doesn't exist yet.

### Step 5: Create the Mount Links Inside `E:/SG_ROOT`
You want SmartGallery to register the mounts in `mounted_folders` (so offline-drive protection protects `Z:` if it ever disconnects).

**Recommended on Windows (avoids UAC mapped-drive issues):**
- Enable **Windows Developer Mode** (*Settings → System → For developers*). This lets non-admin SmartGallery create `mklink /D` symlinks to `Z:\` directly without "Run as Administrator" (and avoids the UAC issue where an elevated Admin prompt cannot see user-mapped `Z:\` drives).
- Or run SG once as Administrator to create the mount, then run normally afterwards.

*(Tip: Create the mount to an empty temporary folder or before moving files in—or create `E:\SG_ROOT\Archive` pointing to `Z:\COMFYUI_ARCHIVE`, then immediately run `sg_migrate_paths.py` before letting SG scan `E:\SG_ROOT`.)*

### Step 6: Dry Run (Preview Only)
```bash
python sg_migrate_paths.py ^
  --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" ^
  --old "E:/ComfyUI/output" ^
  --new "E:/SG_ROOT/Archive" ^
  --verify-disk --dry-run
```
Check the preview output:
- Verify `Matched DB file rows` matches the expected count.
- Verify `Sample Path Remapping Preview` looks right (on Windows, folder slashes `/` and filename separator `\`, e.g. `E:/SG_ROOT/Archive/Sub\img.png`).
- Verify `Disk verification` shows `X/X files found at new path`.

### Step 7: Run Live Migration
Remove `--dry-run` and type `YES` when prompted:
```bash
python sg_migrate_paths.py ^
  --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" ^
  --old "E:/ComfyUI/output" ^
  --new "E:/SG_ROOT/Archive" ^
  --verify-disk
```

### Step 8: Start SmartGallery (and Any Exhibition Instances)
Start SmartGallery normally. On startup, `full_sync_database` will see all 49K+ files already matching the DB—no duplicates, no network re-hashing, and all favorites, collections, status tags, ratings, and comments preserved.

---

## Platform-Specific Examples

### Windows (CMD / PowerShell)
```bat
python sg_migrate_paths.py --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" --old "E:/ComfyUI/output" --new "E:/SG_ROOT/Archive" --verify-disk --dry-run
```

### Linux / macOS
```bash
python3 sg_migrate_paths.py \
  --db "$HOME/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" \
  --old "$HOME/ComfyUI/output" \
  --new "/mnt/nas/sg_root/Archive" \
  --verify-disk --dry-run
```

### Docker
Stop **all** SmartGallery, Exhibition, and AI Docker containers first, then run against the bind-mounted database folder from the host:
```bash
python3 sg_migrate_paths.py \
  --db "/host/path/to/sg_db/.sqlite_cache/gallery_cache.sqlite" \
  --old "/app/output" \
  --new "/app/output/Archive" \
  --sep posix --dry-run
```
*(Use `--sep posix` if running from a Windows host against a Linux Docker SQLite DB, or `--sep win` if running from Linux against a Windows SQLite DB.)*

### Interactive Guided Mode
If you run the script with no arguments (or `--interactive`), it prints the full guide and walks you through each parameter interactively, always running a `--dry-run` preview before asking for confirmation:
```bash
python sg_migrate_paths.py
```

---

## CLI Options Reference

| Flag | Description |
| :--- | :--- |
| `--db` | Path to `gallery_cache.sqlite` |
| `--old` | Old folder path prefix stored in the database |
| `--new` | New folder path prefix as SmartGallery will see it |
| `--dry-run` | Preview counts, DAM stats, and sample paths without writing |
| `--verify-disk` | Check if the remapped paths actually exist on disk |
| `--sep auto\|win\|posix` | Separator before filename (`auto` detects from `--new` path format) |
| `--case auto\|insensitive\|sensitive` | Prefix matching case sensitivity |
| `--include-mounts` | Also remap `mounted_folders` entries under `--old` |
| `--yes`, `-y` | Skip interactive `YES` confirmation prompt |
| `--interactive` | Launch guided interactive wizard |

---

## Troubleshooting & Rollback

- **`Running SmartGallery instance(s) detected` or `Database is currently locked`:** Another SmartGallery server, `--exhibition` portal, AI service, or Docker container is still running or holding a lock. Stop **all** instances cleanly and re-run.
- **`MISSING` files reported by `--verify-disk`:** Either your files haven't been moved to the new location yet, your `--new` prefix doesn't match the folder/mount path on disk, or `Z:\` isn't currently accessible. Do **not** run without `--dry-run` until `--verify-disk` finds your files.
- **How to rollback:** Ensure all instances are stopped, replace `gallery_cache.sqlite` with the `.bak.YYYYMMDD_HHMMSS` file created by the tool (and remove any stale `-wal`/`-shm` files if present).
