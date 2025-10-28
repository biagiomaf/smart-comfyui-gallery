
# Changelog

## [1.35.1] - 2025-10-28

### Performance

#### Parallel Processing (`smartgallery.py`)
- **10-20x Speedup**: Implemented parallel file processing using `ProcessPoolExecutor` with all available CPU cores
- **Progress Feedback**: Added `tqdm` console progress bar for real-time sync status during database operations
- **Batch Database Writes**: Implemented BATCH_SIZE=500 to prevent out-of-memory errors on large galleries (10,000+ files)
- **Worker Function**: Created `process_single_file()` multiprocessing-compatible worker that accepts config parameters instead of accessing Flask app context
- **Smart Defaults**: `MAX_PARALLEL_WORKERS=None` uses all CPU cores; set to 1 for sequential processing if needed

#### Affected Functions
- `full_sync_database()`: Refactored with ProcessPoolExecutor and batch writes
- `sync_folder_on_demand()`: Parallel processing with SSE (Server-Sent Events) maintained for browser updates

### Added

#### File Rename Feature (`smartgallery.py`, `templates/index.html`)
- **Backend Route**: New `/galleryout/rename_file/<file_id>` POST endpoint with comprehensive validation
- **Validation**: Filename length ≤250 characters, invalid character blocking, duplicate detection
- **Database Updates**: Automatic new file ID generation (MD5 hash) when path changes
- **Lightbox UI**: Added ✏️ rename button to lightbox toolbar with prompt-based interface
- **JavaScript Function**: `renameFileFromLightbox()` updates DOM, data structures, and refreshes display without page reload
- **UX Enhancement**: Added title tooltips to all 9 lightbox toolbar buttons for better accessibility

#### localStorage Persistence (`templates/index.html`)
- **Folder Expansion State**: Remembers which folders you expanded/collapsed between sessions
- **Sort Preferences**: Persists folder tree sort order (name/date, ascending/descending) for both nav and move panels
- **Sidebar State**: Remembers sidebar expansion state across page loads
- **Auto-Save**: All states saved immediately on user interactions (toggle folder, change sort, expand sidebar)

### Fixed

#### Timestamp Handling (`smartgallery.py`)
- **Issue**: Sync comparison used floating-point timestamps causing precision errors
- **Solution**: Added `int()` conversion in `sync_folder_on_demand()` for reliable file modification time comparisons

### Changed

#### Folder Tree Refactoring (`templates/index.html`)
- **Immutable Data**: Refactored `sortChildren()` to return sorted array instead of mutating `foldersData` in place
- **On-the-Fly Sorting**: Sorting now happens during tree rendering in `buildFolderTreeHTML()` 
- **Detailed Comments**: Added comprehensive inline documentation for localStorage and sorting logic
- **Cleaner Code**: Eliminated side effects from sorting operations

#### UI Improvements (`templates/index.html`)
- **Desktop Move Panel**: Widened to 650px (was 400px) on screens >1024px for better visibility
- **Responsive Design**: Used `max-width: 90vw` to maintain mobile compatibility

## [1.34.2] - 2025-10-28

### Changed

#### UI/UX Improvements (`galleryConfig.js`, `galleryConfig.css`)
- **Prominent "Open Gallery" Button**: Moved from quick actions to top-right of dashboard header with primary action styling
- **Dashboard Header Layout**: Added flex layout with title on left, Open Gallery button on right
- **Quick Actions Reorganized**: Changed from 4-button auto-fit grid to clean 3-column layout (Sync, Clear Cache, View Logs)
- **Recent Files Interactivity**: Made recent file thumbnails clickable - click opens file in gallery in new tab
- **File Deep-Linking**: Added URL hash fragment (`#file-{id}`) for future deep-linking functionality
- **Tooltip Enhancement**: Recent files now show "Click to open in gallery" on hover

### Added

#### New Method (`galleryConfig.js`)
- `openFileInGallery(fileId)`: Opens gallery in new tab with file ID in URL hash for future deep-linking support

## [1.34.1] - 2025-10-28

### Fixed

#### CORS Support for Dashboard (`smartgallery.py`)
- **Critical Fix**: Added CORS (Cross-Origin Resource Sharing) support using `flask-cors` package
- **Issue**: Dashboard API calls from ComfyUI (port 8000) to Gallery server (port 8008) were blocked by browser CORS policy
- **Solution**: Configured CORS to allow requests from `http://127.0.0.1:8000` and `http://localhost:8000`
- **Affected Endpoints**: All `/smartgallery/*` routes (stats, recent, sync_all, clear_cache, logs)
- **Error Fixed**: `"Access to fetch at 'http://localhost:8008/smartgallery/stats' from origin 'http://127.0.0.1:8000' has been blocked by CORS policy"`

### Changed

#### Dependencies (`pyproject.toml`)
- Added `flask-cors` package to dependencies list
- Required for cross-origin requests between ComfyUI and gallery servers

## [1.34] - 2025-10-28

### Added

#### ComfyUI Sidebar Dashboard (`galleryConfig.js`, `galleryConfig.css`, `smartgallery.py`)
- **Gallery Statistics Dashboard**: Added real-time stats panel showing:
  - Total files count
  - Breakdown by type (images, videos, animated images, audio)
  - Files with workflows count
  - Favorites count
  - Cache size metrics (thumbnails + database)
  - Request counter for server activity monitoring
- **Recent Files Preview**: Display 6 most recently added files with thumbnails directly in the sidebar
- **Quick Actions Panel**: One-click buttons for:
  - 🔄 **Sync All Folders**: Triggers full gallery synchronization
  - 🗑️ **Clear Cache**: Removes thumbnail cache and memory caches
  - 📋 **View Logs**: Opens modal dialog displaying latest 100 log entries
  - 🌐 **Open Gallery**: Quick link to open gallery in new browser tab
- **Auto-refresh**: Dashboard stats and recent files automatically update every 30 seconds
- **Logs Viewer Modal**: Full-featured modal with:
  - Scrollable log content
  - File name and line count display
  - Keyboard/mouse close functionality
  - Monospace font for readability

#### Backend API Endpoints (`smartgallery.py`)
- **GET /smartgallery/stats**: Returns gallery statistics (file counts, cache sizes, request count)
- **GET /smartgallery/recent**: Returns N most recent files with thumbnail URLs
- **POST /smartgallery/sync_all**: Triggers full folder synchronization and cache clearing
- **POST /smartgallery/clear_cache**: Clears thumbnail cache and/or memory caches (supports partial clearing)
- **GET /smartgallery/logs**: Returns recent log entries from daily log files
- **Request Counter Middleware**: Tracks all incoming requests for stats dashboard

#### Logging System (`smartgallery.py`)
- **Structured Logging**: Added Python logging module with daily rotating log files
- **Log Directory**: Logs stored in `{output_path}/smartgallery_logs/gallery_YYYYMMDD.log`
- **Console + File Output**: All log messages written to both console and file
- **Initialization Logging**: Key events logged (startup, DB rebuilds, sync operations)

### Changed

#### Version Numbers
- Updated `smartgallery.py` header to v1.34
- Updated `pyproject.toml` version to 1.34.0

#### Dependencies
- Added `logging` and `datetime` imports to `smartgallery.py`

### Technical Details

#### Architecture
- Dashboard communicates directly with Flask server on configured port (default 8008)
- Uses `fetch()` for direct Flask calls (CORS-compatible)
- Stats and recent files loaded on sidebar tab activation
- Timer-based auto-refresh with proper cleanup on tab close

#### UI/UX
- Dashboard section appears at top of Gallery Config sidebar tab
- Stats displayed in responsive grid layout (2-3 columns depending on screen width)
- Recent files shown as 6-item thumbnail grid with workflow badges
- Quick actions as 4-button responsive grid
- Modern Aura design system styling with hover effects and animations

#### Performance
- Stats queries optimized with single DB connection
- Thumbnail cache size calculated lazily (only when stats requested)
- Memory caches cleared efficiently with thread-safe locks
- Auto-refresh debounced to prevent excessive API calls

## [1.31] - 2025-10-27

### Changed

#### `__init__.py`
- **Robust Path Detection**: Refactored automatic path detection to use ComfyUI's official `folder_paths` API instead of relative directory navigation
- **Universal Compatibility**: Path detection now works correctly with ALL ComfyUI configurations including:
  - Custom node paths set via `--custom-nodes-path` CLI argument
  - Alternative paths configured in `extra_model_paths.yaml`
  - Symlinked or network-mounted custom_nodes directories
  - Docker containers and multi-instance production setups
- **Future-Proof Design**: Automatically adapts to any ComfyUI directory structure changes

### Fixed
- Fixed path detection failures in advanced ComfyUI configurations with non-standard custom node locations
- Fixed initialization order bug where derived paths were calculated before command-line arguments were parsed
- Resolved "TypeError: expected str, bytes or os.PathLike object, not NoneType" crash on startup

### Technical Improvements
- Replaced brittle `os.path.join(__file__, "..", "..")` logic with `folder_paths.get_output_directory()` and `folder_paths.get_input_directory()`
- Moved derived path calculations from global scope into `initialize_gallery()` function
- Added comprehensive error logging and diagnostic capabilities
- Implemented proper subprocess lifecycle management with `atexit` cleanup handlers

## [1.30] - 2025-10-26

### Added

#### Folder Navigation & Management (`index.html`)
- **Expandable Sidebar**: Added an "Expand" button (`↔️`) to widen the folder sidebar, making long folder names fully visible. On mobile, this opens a full-screen overlay for maximum readability.
- **Real-time Folder Search**: Implemented a search bar above the folder tree to filter folders by name instantly.
- **Bi-directional Folder Sorting**: Added buttons to sort the folder tree by Name (A-Z / Z-A) or Modification Date (Newest / Oldest). The current sort order is indicated by an arrow (↑↓).
- **Enhanced "Move File" Panel**: All new folder navigation features (Search, and Bi-directional Sorting) have been fully integrated into the "Move File" dialog for a consistent experience.

#### Gallery View (`index.html`)
- **Bi-directional Thumbnail Sorting**: Added sort buttons for "Date" and "Name" to the main gallery view. Each button toggles between ascending and descending order on click, indicated by an arrow.

#### Lightbox Experience (`index.html`)
- **Zoom with Mouse Wheel**: Implemented zooming in and out of images in the lightbox using the mouse scroll wheel.
- **Persistent Zoom Level**: The current zoom level is now maintained when navigating to the next or previous image, or after deleting an item.
- **Zoom Percentage Display**: The current zoom level is now displayed next to the filename in the lightbox title (e.g., `my_image.png (120%)`).
- **Delete Functionality**: Added a delete button (`🗑️`) to the lightbox toolbar and enabled the `Delete` key on the keyboard for quick deletion (no confirmation required with the key).

#### System & Feedback (`smartgallery.py` & `index.html`)
- **Real-time Sync Feedback**: Implemented a non-blocking, real-time folder synchronization process using Server-Sent Events (SSE).
- **Sync Progress Overlay**: When new or modified files are detected, a progress overlay is now displayed, showing the status and a progress bar of the indexing and thumbnailing operation. The check is silent if no changes are found.

### Changed

#### `smartgallery.py`
- **Dynamic Workflow Filename**: When downloading a workflow, the file is now named after the original image (e.g., `my_image.png` -> `my_image.json`) instead of a generic `workflow.json`.
- **Folder Metadata**: The backend now retrieves the modification time for each folder to enable sorting by date.


## [1.22] - 2025-10-08

### Changed

#### index.html
- Minor aesthetic improvements

#### smartgallery.py
- Implemented intelligent file management for moving files between folders
- Added automatic file renaming when destination file already exists
- Files are now renamed with progressive numbers (e.g., `myfile.png` → `myfile(1).png`, `myfile(2).png`, etc.)

### Fixed
- Fixed issue where file move operations would fail when a file with the same name already existed in the destination folder
- Files are now successfully moved with the new name instead of failing the operation