# Storage, NAS & Migration Tools

This folder contains documentation and utilities for running SmartGallery with **large media libraries (50K–100K+ files)**, **multi-drive layouts**, **network shares (NAS / SMB / NFS)**, and **Docker**.

## Contents

| File | Description |
| :--- | :--- |
| **[`ADVANCED_STORAGE_NAS.md`](./ADVANCED_STORAGE_NAS.md)** | Complete guide to separating SmartGallery (`SG_ROOT` + local SSD `SG_DATABASE`) from ComfyUI's `output` folder, mounting network/external drives (`🔗`), Windows Developer Mode vs. the `Z:\` UAC trap, LAN setups (e.g., Windows GPU host + Mac storage/browser), and performance tips. |
| **[`SG_MIGRATE_PATHS_GUIDE.md`](./SG_MIGRATE_PATHS_GUIDE.md)** | Step-by-step instructions and CLI reference for migrating an existing library without losing favorites, collections, status tags, ratings, comments, AI data, or cached `.webp` thumbnails. |
| **[`sg_migrate_paths.py`](./sg_migrate_paths.py)** | Standalone offline Python utility (standard library only, no extra packages required) that remaps paths and MD5 IDs directly inside `gallery_cache.sqlite` in under 1 second. |

---

## Quick Start: Using `sg_migrate_paths.py`

> **⚠️ CRITICAL:** Stop **all** SmartGallery instances (**Main Gallery**, **`--exhibition` portals**, **AI Services**, and any **SQLite viewers**) before running a live migration. The tool automatically checks for active SmartGallery processes and exclusive SQLite WAL locks.

### Standard Installations (Windows / macOS / Linux)

Run from the root SmartGallery directory (always test with `--dry-run` first):

```bash
# Preview (read-only)
python STORAGE_MIGRATION/sg_migrate_paths.py \
  --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" \
  --old "E:/ComfyUI/output" \
  --new "E:/SG_ROOT/Archive" \
  --verify-disk --dry-run

# Live migration (creates an automatic WAL-checkpointed backup first)
python STORAGE_MIGRATION/sg_migrate_paths.py \
  --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" \
  --old "E:/ComfyUI/output" \
  --new "E:/SG_ROOT/Archive" \
  --verify-disk
```

You can also launch the interactive guided wizard or inspect all options with:
```bash
python STORAGE_MIGRATION/sg_migrate_paths.py --help
```

---

### Docker Installations

Stop all running SmartGallery / Exhibition / AI containers first:

```bash
docker compose down
```

Then choose one of these two methods:

1. **Run inside a one-off container (Recommended — `--verify-disk` works natively):**
   ```bash
   docker compose run --rm --no-deps --entrypoint python3 smartgallery \
     STORAGE_MIGRATION/sg_migrate_paths.py \
     --db "/app/sg_database/.sqlite_cache/gallery_cache.sqlite" \
     --old "/app/output" \
     --new "/app/sg_root/Archive" \
     --verify-disk --dry-run
   ```
   *(Replace `smartgallery` with your Compose service name, and `python3` with your container's Python path if using a virtualenv. Remove `--dry-run` when ready to apply.)*

2. **Run directly from the host (no `pip install` needed):**
   Point `--db` to the bind-mounted `.sqlite` path on your host, and pass the **in-container** paths to `--old` and `--new` (omit `--verify-disk`, and add `--sep posix` if running from a Windows host against a Linux container database):
   ```bash
   python3 STORAGE_MIGRATION/sg_migrate_paths.py \
     --db "/host/path/to/sg_database/.sqlite_cache/gallery_cache.sqlite" \
     --old "/app/output" \
     --new "/app/sg_root/Archive" \
     --sep posix --dry-run
   ```

When finished, start your containers again (`docker compose up -d`).
