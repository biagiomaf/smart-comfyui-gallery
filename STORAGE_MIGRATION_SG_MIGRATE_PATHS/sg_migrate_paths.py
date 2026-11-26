#!/usr/bin/env python3
"""
sg_migrate_paths.py — SmartGallery Offline Path Migration Utility

Safely remaps file paths and MD5 file IDs in gallery_cache.sqlite when moving
large media libraries (10K–100K+ files) between drives, network shares (NAS),
mount points, or Docker container paths WITHOUT re-hashing or losing DAM data.

IMPORTANT: This is an OFFLINE standalone utility.
You MUST stop ALL running SmartGallery instances before running it:
  - Main SmartGallery server(s)
  - Exhibition Portal instances (--exhibition) where users can rate/comment
  
  - In future versions: AI Indexing/Search background services 
  - Any SQLite viewer/browser locking gallery_cache.sqlite that you are using outside of SmartGallery DAM.

Preserves:
  - Favorites (is_favorite)
  - Virtual Collections & Status Flags (collection_files)
  - User Ratings (file_ratings)
  - Comments & Direct Messages (file_comments)
  - AI Captions, Embeddings, Watched Folders & Queue (files.ai_*, ai_watched_folders, ai_indexing_queue)
  - Workflow Hashes & Content SHA256 Thumbnail Links (content_sha256)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime


EPILOG_HELP = r"""
================================================================================
IMPORTANT PREREQUISITE — STOP ALL SMARTGALLERY INSTANCES FIRST!
================================================================================
Before running a live migration (and while moving files on disk), you MUST stop
EVERY process that uses this database or media folder:
  [1] Main SmartGallery instance(s)
  [2] Any Exhibition Mode (--exhibition) portal instances (even read-only
      portals write ratings and comments into gallery_cache.sqlite!)
  [3] Any SmartGallery AI Service / worker processes
  [4] Any SQLite DB browser/inspector with gallery_cache.sqlite open

Running while an instance is active risks SQLite WAL lock conflicts or guests
submitting ratings/comments against old file IDs mid-migration.
This tool checks for running SmartGallery processes and active SQLite WAL locks
and will refuse to proceed if any active lock is detected.

================================================================================
HOW THIS TOOL WORKS & WHY USE IT
================================================================================
SmartGallery identifies each media file by an MD5 hash of its path string.
If you physically move 49,000+ files from one folder/drive to another (e.g., from
local E:/ComfyUI/output to a NAS share Z:/COMFYUI_ARCHIVE mounted in SG_ROOT),
starting SmartGallery directly would treat them as 49,000 removed + 49,000 new
files (re-reading tens of GB over the network).

This tool updates all path prefixes and MD5 IDs directly inside SQLite in
under 1 second, keeping every favorite, collection, status tag, rating, comment,
AI caption, and cached .webp thumbnail intact.

NOTE: This tool NEVER moves, copies, or deletes your actual files on disk.
You move/copy your media files with your OS (Explorer, robocopy, rsync, mv).
A WAL-checkpointed backup of gallery_cache.sqlite is created automatically.

================================================================================
RECOMMENDED MIGRATION WORKFLOW (EXAMPLE: MOVING ARCHIVE TO A NAS / NEW DRIVE)
================================================================================
1. Stop ALL SmartGallery instances (Main, --exhibition, AI Service).
2. Copy/move your ".sqlite_cache" and ".thumbnails_cache" folders to your fast
   local BASE_SMARTGALLERY_PATH (e.g. E:/SG_DATABASE) if changing it.
3. Copy/move your media files to the new drive (e.g. Z:/COMFYUI_ARCHIVE).
   Tip (Windows): robocopy "E:\ComfyUI\output" "Z:\COMFYUI_ARCHIVE" /E /COPY:DAT
4. Create your SG_ROOT directory (e.g. E:/SG_ROOT) and update env vars:
     BASE_OUTPUT_PATH=E:/SG_ROOT
     BASE_SMARTGALLERY_PATH=E:/SG_DATABASE
     BASE_MODELS_PATH=E:/ComfyUI/models
     BASE_INPUT_PATH=E:/ComfyUI/input
5. Create the Mount link inside E:/SG_ROOT (e.g. E:/SG_ROOT/Archive -> Z:/COMFYUI_ARCHIVE).
6. Run a Dry Run first:
     python sg_migrate_paths.py ^
       --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" ^
       --old "E:/ComfyUI/output" ^
       --new "E:/SG_ROOT/Archive" ^
       --verify-disk --dry-run
7. Run the actual migration (remove --dry-run):
     python sg_migrate_paths.py ^
       --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" ^
       --old "E:/ComfyUI/output" ^
       --new "E:/SG_ROOT/Archive" ^
       --verify-disk
8. Start SmartGallery (and any Exhibition instances) normally.

================================================================================
MORE PLATFORM EXAMPLES
================================================================================
Windows (CMD / PowerShell):
  python sg_migrate_paths.py --db "E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite" --old "E:/ComfyUI/output" --new "E:/SG_ROOT/Archive" --dry-run

macOS / Linux:
  python3 sg_migrate_paths.py --db "$HOME/SG_DB/.sqlite_cache/gallery_cache.sqlite" --old "$HOME/ComfyUI/output" --new "/mnt/nas/sg_root/Archive" --dry-run

Docker (stop ALL SG/Exhibition/AI containers first, then run against mounted DB):
  python3 sg_migrate_paths.py --db "/host/path/sg_db/.sqlite_cache/gallery_cache.sqlite" --old "/app/output" --new "/app/output/Archive" --sep posix --dry-run
================================================================================
"""


SG_PROC_PATTERN = re.compile(r'(?:^|[/\\"\'\s])smartgallery(?:_[a-z0-9_]+)?\.py\b', re.IGNORECASE)


def find_running_smartgallery_processes():
    """
    Best-effort cross-platform scan for running SmartGallery / Exhibition / AI processes.
    Returns a list of (pid, cmdline) tuples.
    """
    my_pid = os.getpid()
    parent_pid = os.getppid() if hasattr(os, "getppid") else -1
    found = []

    def is_sg_cmd(cmd: str) -> bool:
        if not cmd:
            return False
        low = cmd.lower()
        if "sg_migrate_paths" in low or "patch_" in low:
            return False
        return bool(SG_PROC_PATTERN.search(cmd))

    # 1. Linux / Docker (/proc)
    if os.path.isdir("/proc"):
        try:
            for entry in os.listdir("/proc"):
                if not entry.isdigit():
                    continue
                pid = int(entry)
                if pid in (my_pid, parent_pid):
                    continue
                try:
                    with open(f"/proc/{pid}/cmdline", "rb") as f:
                        raw = f.read()
                    if not raw:
                        continue
                    cmd = raw.replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
                    if is_sg_cmd(cmd):
                        found.append((pid, cmd))
                except OSError:
                    continue
            return found
        except OSError:
            pass

    # 2. Windows (PowerShell CIM, fallback WMIC)
    if os.name == "nt":
        cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            ps_cmd = (
                "Get-CimInstance Win32_Process | "
                "Where-Object { $_.CommandLine -match 'smartgallery' } | "
                "Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=cf,
            )
            if res.returncode == 0 and res.stdout.strip():
                parsed = json.loads(res.stdout.strip())
                if isinstance(parsed, dict):
                    parsed = [parsed]
                for item in parsed:
                    pid = int(item.get("ProcessId", -1))
                    cmd = str(item.get("CommandLine") or "")
                    if pid not in (my_pid, parent_pid) and is_sg_cmd(cmd):
                        found.append((pid, cmd))
                return found
        except Exception:
            pass

        try:
            res = subprocess.run(
                ["wmic", "process", "where", "CommandLine like '%smartgallery%'", "get", "ProcessId,CommandLine", "/FORMAT:CSV"],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=cf,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3 and parts[-1].isdigit():
                        pid = int(parts[-1])
                        cmd = ",".join(parts[1:-1])
                        if pid not in (my_pid, parent_pid) and is_sg_cmd(cmd):
                            found.append((pid, cmd))
                return found
        except Exception:
            pass
        return found

    # 3. macOS / BSD / POSIX fallback (ps)
    try:
        res = subprocess.run(
            ["ps", "-ax", "-o", "pid=,command="],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2 and parts[0].isdigit():
                    pid = int(parts[0])
                    cmd = parts[1]
                    if pid not in (my_pid, parent_pid) and is_sg_cmd(cmd):
                        found.append((pid, cmd))
    except Exception:
        pass

    return found


def assert_no_active_sg_instances(dry_run: bool = False):
    procs = find_running_smartgallery_processes()
    if not procs:
        return
    print("\n" + "!" * 72)
    print("WARNING / BLOCKED: Running SmartGallery instance(s) detected!")
    for pid, cmd in procs:
        tag = " [EXHIBITION PORTAL]" if "--exhibition" in cmd.lower() else ""
        print(f"  PID {pid}{tag}: {cmd}")
    print("!" * 72)
    if dry_run:
        print("DRY RUN NOTE: You may preview now, but you MUST stop ALL listed processes")
        print("(including Exhibition Portal & AI workers) before running a LIVE migration.\n")
    else:
        raise RuntimeError(
            "Live migration aborted: stop ALL SmartGallery / Exhibition / AI instances first."
        )


def normalize_prefix(raw: str) -> str:
    s = raw.strip().replace("\\", "/")
    if s == "/":
        return "/"
    if s.startswith("//"):
        return "//" + s[2:].rstrip("/")
    return s.rstrip("/")


def detect_target_sep(new_prefix_slash: str, sep_mode: str) -> str:
    if sep_mode == "win":
        return "\\"
    if sep_mode == "posix":
        return "/"
    if (len(new_prefix_slash) >= 2 and new_prefix_slash[1] == ":") or new_prefix_slash.startswith("//"):
        return "\\"
    if new_prefix_slash.startswith("/"):
        return "/"
    return os.sep


def build_canonical_sg_path(new_prefix_slash: str, rel_slash: str, target_sep: str) -> str:
    """
    Preserves SmartGallery's exact path convention:
      - Windows target: '/' for all folder segments, '\\' only before filename
        e.g. 'E:/SG_ROOT/Archive/Sub\\img.png'
      - POSIX target:   '/' everywhere
        e.g. '/mnt/nas/Archive/Sub/img.png'
    """
    base = new_prefix_slash.rstrip("/") if new_prefix_slash != "/" else ""
    if "/" in rel_slash:
        rel_dir, filename = rel_slash.rsplit("/", 1)
        folder_part = f"{base}/{rel_dir}" if base else f"/{rel_dir}"
    else:
        filename = rel_slash
        folder_part = base if base else "/"

    if folder_part == "/":
        return f"/{filename}"
    return f"{folder_part}{target_sep}{filename}"


def standardize_ai_queue_path(path_str: str, target_sep: str) -> str:
    std = path_str.replace("\\", "/")
    if target_sep == "\\":
        return std.lower()
    return std


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    return row is not None


def verify_exclusive_db_access_and_backup(db_path: str) -> str:
    """
    Probes SQLite for true exclusive access (busy_timeout=0, EXCLUSIVE locking,
    and WAL checkpoint). Aborts immediately if ANY other process (including an idle
    Exhibition instance or Docker container) holds a lock on the DB or WAL/SHM.
    """
    chk_conn = None
    try:
        chk_conn = sqlite3.connect(db_path, timeout=0, isolation_level=None)
        chk_conn.execute("PRAGMA busy_timeout = 0;")
        chk_conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
        chk_conn.execute("BEGIN EXCLUSIVE;")
        row = chk_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
        if row and row[0] != 0:
            raise sqlite3.OperationalError(
                "WAL checkpoint reported busy=1 (another process is actively reading/holding a snapshot)."
            )
        chk_conn.execute("COMMIT;")
        chk_conn.close()
        chk_conn = None
    except sqlite3.OperationalError as e:
        if chk_conn:
            try:
                chk_conn.execute("ROLLBACK;")
            except Exception:
                pass
            try:
                chk_conn.close()
            except Exception:
                pass
        raise RuntimeError(
            f"Database is currently locked or in use by another process ({e}).\n"
            "Please STOP ALL SmartGallery instances (Main Gallery, --exhibition portals, AI Services, DB tools) and retry."
        )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak.{ts}"
    shutil.copy2(db_path, backup_path)
    for ext in ("-wal", "-shm"):
        side = db_path + ext
        if os.path.exists(side) and os.path.getsize(side) > 0:
            shutil.copy2(side, backup_path + ext)
    return backup_path


def run_migration(
    db_path: str,
    old_raw: str,
    new_raw: str,
    sep_mode: str = "auto",
    case_sensitive_mode: str = "auto",
    dry_run: bool = False,
    verify_disk: bool = False,
    assume_yes: bool = False,
    include_mounts: bool = False,
):
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    assert_no_active_sg_instances(dry_run=dry_run)

    old_slash = normalize_prefix(old_raw)
    new_slash = normalize_prefix(new_raw)

    if not old_slash or not new_slash:
        raise ValueError("Both --old and --new prefixes must be non-empty.")

    target_sep = detect_target_sep(new_slash, sep_mode)

    if case_sensitive_mode == "auto":
        is_case_insensitive = (
            (len(old_slash) >= 2 and old_slash[1] == ":")
            or old_slash.startswith("//")
            or os.name == "nt"
        )
    elif case_sensitive_mode == "insensitive":
        is_case_insensitive = True
    else:
        is_case_insensitive = False

    old_cmp = old_slash.lower() if is_case_insensitive else old_slash
    new_cmp = new_slash.lower() if is_case_insensitive else new_slash

    if old_cmp == new_cmp and target_sep == detect_target_sep(old_slash, "auto"):
        raise ValueError("Old and new prefixes resolve to the exact same path.")

    print("=" * 72)
    print("SmartGallery Path Migration Tool")
    print("=" * 72)
    print(f"Database        : {os.path.abspath(db_path)}")
    print(f"Old Prefix      : {old_slash}")
    print(f"New Prefix      : {new_slash}")
    print(f"Target File Sep : {'\\\\ (Windows mixed style)' if target_sep == '\\\\' else '/ (POSIX)'}")
    print(f"Case Matching   : {'Case-insensitive' if is_case_insensitive else 'Case-sensitive'}")
    print(f"Mode            : {'DRY RUN (read-only preview)' if dry_run else 'LIVE MIGRATION'}")
    print("-" * 72)

    try:
        conn = sqlite3.connect(db_path, timeout=5 if dry_run else 15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 3000;")
        if dry_run:
            conn.execute("PRAGMA query_only = ON;")
    except sqlite3.OperationalError as e:
        raise RuntimeError(
            f"Cannot open database ({e}). Ensure ALL SmartGallery / Exhibition / AI instances are stopped."
        )

    try:
        if not table_exists(conn, "files"):
            raise RuntimeError("Invalid database: 'files' table not found.")

        all_rows = conn.execute("SELECT id, path FROM files").fetchall()
        existing_id_to_path = {r["id"]: r["path"] for r in all_rows}

        groups_by_new_id = defaultdict(list)
        old_prefix_prefix = (old_cmp if old_cmp == "/" else old_cmp + "/")

        for r in all_rows:
            cur_path = r["path"]
            cur_slash = cur_path.replace("\\", "/")
            if cur_slash.startswith("//"):
                cur_slash_clean = "//" + "/".join(p for p in cur_slash[2:].split("/") if p)
            elif cur_slash.startswith("/"):
                cur_slash_clean = "/" + "/".join(p for p in cur_slash[1:].split("/") if p)
            else:
                cur_slash_clean = "/".join(p for p in cur_slash.split("/") if p)

            cur_cmp = cur_slash_clean.lower() if is_case_insensitive else cur_slash_clean
            if cur_cmp.startswith(old_prefix_prefix):
                rel_slash = cur_slash_clean[len(old_prefix_prefix):]
                if not rel_slash:
                    continue
                new_path = build_canonical_sg_path(new_slash, rel_slash, target_sep)
                new_id = hashlib.md5(new_path.encode()).hexdigest()
                if new_id == r["id"] and new_path == cur_path:
                    continue
                groups_by_new_id[new_id].append((r["id"], cur_path, new_path))

        watched_updates = []
        if table_exists(conn, "ai_watched_folders"):
            for r in conn.execute("SELECT path FROM ai_watched_folders").fetchall():
                wp = r["path"]
                wp_slash = normalize_prefix(wp)
                wp_cmp = wp_slash.lower() if is_case_insensitive else wp_slash
                if wp_cmp == old_cmp:
                    watched_updates.append((new_slash, wp))
                elif wp_cmp.startswith(old_prefix_prefix):
                    rel_w = wp_slash[len(old_prefix_prefix):]
                    watched_updates.append((f"{new_slash.rstrip('/')}/{rel_w}", wp))

        mount_matches = []
        if table_exists(conn, "mounted_folders"):
            for r in conn.execute("SELECT path FROM mounted_folders").fetchall():
                mp = r["path"]
                mp_slash = normalize_prefix(mp)
                mp_cmp = mp_slash.lower() if is_case_insensitive else mp_slash
                if mp_cmp == old_cmp or mp_cmp.startswith(old_prefix_prefix):
                    rel_m = mp_slash[len(old_prefix_prefix):] if mp_cmp.startswith(old_prefix_prefix) else ""
                    new_mp = f"{new_slash.rstrip('/')}/{rel_m}" if rel_m else new_slash
                    mount_matches.append((new_mp, mp))

        total_old_rows = sum(len(v) for v in groups_by_new_id.values())
        unique_targets = len(groups_by_new_id)
        collisions_with_existing = sum(
            1 for nid, items in groups_by_new_id.items()
            if nid in existing_id_to_path and all(old_id != nid for old_id, _, _ in items)
        )

        matched_old_ids = [old_id for items in groups_by_new_id.values() for old_id, _, _ in items]
        dam_stats = {"favorites": 0, "collections": 0, "ratings": 0, "comments": 0, "ai_captions": 0}
        for i in range(0, len(matched_old_ids), 500):
            chunk = matched_old_ids[i:i + 500]
            ph = ",".join(["?"] * len(chunk))
            dam_stats["favorites"] += conn.execute(
                f"SELECT COUNT(*) FROM files WHERE id IN ({ph}) AND is_favorite = 1", chunk
            ).fetchone()[0]
            dam_stats["ai_captions"] += conn.execute(
                f"SELECT COUNT(*) FROM files WHERE id IN ({ph}) AND ai_caption IS NOT NULL AND ai_caption != ''", chunk
            ).fetchone()[0]
            if table_exists(conn, "collection_files"):
                dam_stats["collections"] += conn.execute(
                    f"SELECT COUNT(*) FROM collection_files WHERE file_id IN ({ph})", chunk
                ).fetchone()[0]
            if table_exists(conn, "file_ratings"):
                dam_stats["ratings"] += conn.execute(
                    f"SELECT COUNT(*) FROM file_ratings WHERE file_id IN ({ph})", chunk
                ).fetchone()[0]
            if table_exists(conn, "file_comments"):
                dam_stats["comments"] += conn.execute(
                    f"SELECT COUNT(*) FROM file_comments WHERE file_id IN ({ph})", chunk
                ).fetchone()[0]

        print(f"Matched DB file rows   : {total_old_rows} (unique target paths: {unique_targets})")
        if total_old_rows > unique_targets:
            print(f"Slash-duplicate cleanup: {total_old_rows - unique_targets} duplicate row(s) will be merged")
        if collisions_with_existing:
            print(f"Existing target merges : {collisions_with_existing} row(s) already exist at new path and will receive DAM data")
        print(f"DAM records preserved  : favorites={dam_stats['favorites']}, collection_links={dam_stats['collections']}, "
              f"ratings={dam_stats['ratings']}, comments={dam_stats['comments']}, ai_captions={dam_stats['ai_captions']}")
        print(f"AI watched folders     : {len(watched_updates)} to remap")
        if mount_matches:
            print(f"Mounted folders match  : {len(mount_matches)} ({'will remap' if include_mounts else 'skipped unless --include-mounts'})")

        if unique_targets == 0 and not watched_updates and not (include_mounts and mount_matches):
            print("\nNo matching entries found for the specified --old prefix. Nothing to change.")
            return

        print("\nSample Path Remapping Preview (first 5):")
        for nid, items in list(groups_by_new_id.items())[:5]:
            old_id, old_p, new_p = items[0]
            print(f"  OLD: {old_p}")
            print(f"  NEW: {new_p}")
            print("")

        if verify_disk and unique_targets > 0:
            print("Verifying new file paths on disk...")
            all_new_paths = [items[0][2] for items in groups_by_new_id.values()]
            missing_count = 0
            missing_samples = []
            for np in all_new_paths:
                if not os.path.exists(os.path.normpath(np)):
                    missing_count += 1
                    if len(missing_samples) < 5:
                        missing_samples.append(np)
            found_count = len(all_new_paths) - missing_count
            print(f"Disk verification      : {found_count}/{len(all_new_paths)} files found at new path.")
            if missing_count > 0:
                print(f"WARNING: {missing_count} target file(s) were NOT found on disk! Sample missing:")
                for ms in missing_samples:
                    print(f"  MISSING: {ms}")
                print("If you haven't moved your files yet or haven't created the Mount link at --new, cancel now!")

        if dry_run:
            print("\nDRY RUN COMPLETE: No changes were written to the database.")
            return

        if not assume_yes:
            print("\nSAFETY CHECK: Have you stopped ALL SmartGallery instances")
            print("(Main Gallery, any --exhibition portals, AI Services, and DB viewers)?")
            ans = input("Type 'YES' to confirm and run live migration: ").strip()
            if ans != "YES":
                print("Aborted by user. No changes made.")
                return

    finally:
        conn.close()

    # Re-check running processes and acquire exclusive WAL lock before backup & write
    assert_no_active_sg_instances(dry_run=False)
    backup_path = verify_exclusive_db_access_and_backup(db_path)
    print(f"\nBackup created: {backup_path}")

    t0 = time.time()
    conn = sqlite3.connect(db_path, timeout=0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 0;")
    conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
    conn.execute("PRAGMA foreign_keys = OFF;")

    has_collections = table_exists(conn, "collection_files")
    has_ratings = table_exists(conn, "file_ratings")
    has_comments = table_exists(conn, "file_comments")
    has_omni = table_exists(conn, "omniquery_results")
    has_ai_res = table_exists(conn, "ai_search_results")
    has_ai_q = table_exists(conn, "ai_indexing_queue")

    try:
        conn.execute("BEGIN EXCLUSIVE;")

        updated_count = 0
        merged_count = 0
        deduped_count = 0

        def transfer_child_refs(src_id: str, dst_id: str, dst_path: str, src_path: str):
            if src_id == dst_id:
                return
            if has_collections:
                conn.execute(
                    "INSERT OR IGNORE INTO collection_files (collection_id, file_id, added_at) "
                    "SELECT collection_id, ?, added_at FROM collection_files WHERE file_id = ?",
                    (dst_id, src_id),
                )
                conn.execute("DELETE FROM collection_files WHERE file_id = ?", (src_id,))
            if has_ratings:
                conn.execute(
                    "INSERT OR IGNORE INTO file_ratings (file_id, client_uuid, rating, created_at) "
                    "SELECT ?, client_uuid, rating, created_at FROM file_ratings WHERE file_id = ?",
                    (dst_id, src_id),
                )
                conn.execute("DELETE FROM file_ratings WHERE file_id = ?", (src_id,))
            if has_comments:
                conn.execute("UPDATE file_comments SET file_id = ? WHERE file_id = ?", (dst_id, src_id))
            if has_omni:
                conn.execute("UPDATE omniquery_results SET file_id = ? WHERE file_id = ?", (dst_id, src_id))
            if has_ai_res:
                conn.execute("UPDATE ai_search_results SET file_id = ? WHERE file_id = ?", (dst_id, src_id))
            if has_ai_q:
                conn.execute(
                    "UPDATE OR REPLACE ai_indexing_queue SET file_path = ?, file_id = ? WHERE file_path = ? OR file_id = ?",
                    (
                        standardize_ai_queue_path(dst_path, target_sep),
                        dst_id,
                        standardize_ai_queue_path(src_path, target_sep),
                        src_id,
                    ),
                )

        for new_id, items in groups_by_new_id.items():
            target_new_path = items[0][2]
            old_ids_in_group = {oid for oid, _, _ in items}
            target_already_exists_outside = (new_id in existing_id_to_path) and (new_id not in old_ids_in_group)

            if target_already_exists_outside:
                for old_id, old_p, _ in items:
                    old_row = conn.execute(
                        "SELECT is_favorite, ai_last_scanned, ai_caption, ai_embedding, ai_error FROM files WHERE id = ?",
                        (old_id,),
                    ).fetchone()
                    if old_row:
                        conn.execute(
                            """
                            UPDATE files
                            SET is_favorite = CASE WHEN is_favorite = 0 THEN ? ELSE is_favorite END,
                                ai_last_scanned = CASE WHEN (ai_last_scanned IS NULL OR ai_last_scanned = 0) THEN ? ELSE ai_last_scanned END,
                                ai_caption = COALESCE(ai_caption, ?),
                                ai_embedding = COALESCE(ai_embedding, ?),
                                ai_error = COALESCE(ai_error, ?)
                            WHERE id = ?
                            """,
                            (
                                old_row["is_favorite"] or 0,
                                old_row["ai_last_scanned"] or 0,
                                old_row["ai_caption"],
                                old_row["ai_embedding"],
                                old_row["ai_error"],
                                new_id,
                            ),
                        )
                    transfer_child_refs(old_id, new_id, target_new_path, old_p)
                    conn.execute("DELETE FROM files WHERE id = ?", (old_id,))
                merged_count += 1
            else:
                primary_old_id, primary_old_path, _ = items[0]
                if len(items) > 1:
                    for dup_old_id, dup_old_path, _ in items[1:]:
                        dup_row = conn.execute(
                            "SELECT is_favorite, ai_last_scanned, ai_caption, ai_embedding, ai_error FROM files WHERE id = ?",
                            (dup_old_id,),
                        ).fetchone()
                        if dup_row:
                            conn.execute(
                                """
                                UPDATE files
                                SET is_favorite = CASE WHEN is_favorite = 0 THEN ? ELSE is_favorite END,
                                    ai_last_scanned = CASE WHEN (ai_last_scanned IS NULL OR ai_last_scanned = 0) THEN ? ELSE ai_last_scanned END,
                                    ai_caption = COALESCE(ai_caption, ?),
                                    ai_embedding = COALESCE(ai_embedding, ?),
                                    ai_error = COALESCE(ai_error, ?)
                                WHERE id = ?
                                """,
                                (
                                    dup_row["is_favorite"] or 0,
                                    dup_row["ai_last_scanned"] or 0,
                                    dup_row["ai_caption"],
                                    dup_row["ai_embedding"],
                                    dup_row["ai_error"],
                                    primary_old_id,
                                ),
                            )
                        transfer_child_refs(dup_old_id, primary_old_id, primary_old_path, dup_old_path)
                        conn.execute("DELETE FROM files WHERE id = ?", (dup_old_id,))
                        deduped_count += 1

                conn.execute(
                    "UPDATE files SET id = ?, path = ? WHERE id = ?",
                    (new_id, target_new_path, primary_old_id),
                )
                transfer_child_refs(primary_old_id, new_id, target_new_path, primary_old_path)
                updated_count += 1

        if watched_updates and table_exists(conn, "ai_watched_folders"):
            for new_wp, old_wp in watched_updates:
                conn.execute(
                    "INSERT OR REPLACE INTO ai_watched_folders (path, recursive, added_at) "
                    "SELECT ?, recursive, added_at FROM ai_watched_folders WHERE path = ?",
                    (new_wp, old_wp),
                )
                if new_wp != old_wp:
                    conn.execute("DELETE FROM ai_watched_folders WHERE path = ?", (old_wp,))

        if include_mounts and mount_matches and table_exists(conn, "mounted_folders"):
            for new_mp, old_mp in mount_matches:
                conn.execute(
                    "INSERT OR REPLACE INTO mounted_folders (path, target_source, created_at) "
                    "SELECT ?, target_source, created_at FROM mounted_folders WHERE path = ?",
                    (new_mp, old_mp),
                )
                if new_mp != old_mp:
                    conn.execute("DELETE FROM mounted_folders WHERE path = ?", (old_mp,))

        fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_errors:
            raise RuntimeError(f"Foreign key integrity check failed: {len(fk_errors)} issue(s).")

        conn.execute("COMMIT;")
        elapsed = time.time() - t0
        print(f"\nSUCCESS in {elapsed:.2f}s:")
        print(f"  Remapped rows        : {updated_count}")
        print(f"  Merged existing rows : {merged_count}")
        print(f"  Deduped slash rows   : {deduped_count}")
        print(f"  AI watched folders   : {len(watched_updates)}")
        if include_mounts:
            print(f"  Mounted folders      : {len(mount_matches)}")
        print("\nYou can now start SmartGallery (and any Exhibition instances).")

    except Exception as e:
        try:
            conn.execute("ROLLBACK;")
        except Exception:
            pass
        print(f"\nERROR: Migration failed and rolled back cleanly: {e}")
        print(f"Your database backup is safe at: {backup_path}")
        sys.exit(1)
    finally:
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass
        conn.close()


def interactive_wizard():
    print(EPILOG_HELP)
    print("Interactive Mode — Press Ctrl+C at any time to exit.\n")
    default_db = ".sqlite_cache/gallery_cache.sqlite"
    db_in = input(f"Path to gallery_cache.sqlite [{default_db}]: ").strip() or default_db
    old_in = input("Old folder prefix in DB (e.g. E:/ComfyUI/output): ").strip()
    new_in = input("New folder prefix on disk/mount (e.g. E:/SG_ROOT/Archive): ").strip()
    if not old_in or not new_in:
        print("ERROR: Old and new prefixes are required.")
        sys.exit(1)
    verify_in = input("Verify new file paths exist on disk during preview? [Y/n]: ").strip().lower()
    verify_disk = verify_in not in ("n", "no")

    print("\n--- Running DRY RUN first ---")
    run_migration(db_in, old_in, new_in, dry_run=True, verify_disk=verify_disk)

    ans = input(
        "\nConfirm ALL SmartGallery instances (Main, --exhibition, AI Services) are STOPPED.\n"
        "Type 'YES' to run the LIVE migration now: "
    ).strip()
    if ans != "YES":
        print("Exited after dry run. No changes made.")
        return

    run_migration(db_in, old_in, new_in, dry_run=False, verify_disk=False, assume_yes=True)


def main():
    parser = argparse.ArgumentParser(
        prog="sg_migrate_paths.py",
        description="SmartGallery Offline Database Path Migration Tool (100% lossless DAM metadata remapping).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG_HELP,
    )
    parser.add_argument("--db", help="Path to gallery_cache.sqlite (e.g. E:/SG_DATABASE/.sqlite_cache/gallery_cache.sqlite)")
    parser.add_argument("--old", help="Old folder path prefix currently in the DB (e.g. E:/ComfyUI/output)")
    parser.add_argument("--new", help="New folder path prefix as SmartGallery will see it (e.g. E:/SG_ROOT/Archive)")
    parser.add_argument(
        "--sep",
        choices=["auto", "win", "posix"],
        default="auto",
        help="Path separator before filename in target DB paths (default: auto).",
    )
    parser.add_argument(
        "--case",
        choices=["auto", "insensitive", "sensitive"],
        default="auto",
        help="Path prefix matching case sensitivity (default: auto).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying the database.")
    parser.add_argument("--verify-disk", action="store_true", help="Check whether remapped file paths exist on disk.")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt (for scripts/automation).")
    parser.add_argument("--include-mounts", action="store_true", help="Also remap mounted_folders entries under --old.")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive guided setup.")

    if len(sys.argv) == 1:
        if sys.stdin.isatty():
            interactive_wizard()
            return
        parser.print_help()
        return

    args = parser.parse_args()
    if args.interactive:
        interactive_wizard()
        return

    if not args.db or not args.old or not args.new:
        parser.error("--db, --old, and --new are all required (or run with --interactive / no arguments).")

    try:
        run_migration(
            db_path=args.db,
            old_raw=args.old,
            new_raw=args.new,
            sep_mode=args.sep,
            case_sensitive_mode=args.case,
            dry_run=args.dry_run,
            verify_disk=args.verify_disk,
            assume_yes=args.yes,
            include_mounts=args.include_mounts,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()