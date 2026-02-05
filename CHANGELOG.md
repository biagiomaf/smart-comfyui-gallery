# Changelog

#### **[1.55] - 2026-02-05**

**Added**
** Video Storyboard & Analysis - ffmpeg required  **
*   **Quick Storyboard ('E'):** Hover over any video in the grid and press `E` to instantly open the storyboard.
*   **Grid Overview:** Instantly analyze video content with a clean **11-frame Grid** covering the entire duration from Start to the **True Last Frame**.
- **Thumbnail Grid Size:** Added a new toggle in the Options menu (`⚙️`) allowing users to switch between **Normal** and **Compact** view on desktop. This preference is saved automatically.
- **Options Menu & Autoplay Toggle:** New persistent **`⚙️ Options`** menu (Desktop/Mobile) to manage core gallery settings.
- **Video Autoplay Control:** Introduced a session-based toggle to explicitly enable/disable video autoplay in the grid. (Default: **OFF** to save bandwidth).
- **'P' Shortcut:** Added the **`P`** key shortcut to quickly toggle the Video Autoplay setting.
- **Dynamic UX for Videos:**
    - On **Desktop**, when Autoplay is OFF, a small **▶ icon** appears in the corner. Clicking it plays the video **in-grid** for quick preview.
    - On **Mobile**, the thumbnail is fully clickable to open the Lightbox (Click-to-Open).
- **Visual Feedback:** Added a full-screen loader (`loader-overlay`) to prevent interaction during the necessary page reload after changing the Autoplay setting.
- **Focus Mode:** A new streamlined view for professionals. Hides UI clutter and changes click behavior to "Select Only" for rapid batching. Accessible via the **`⚡`** button or **`Q`** key.
- **Shortcuts Button:** Added a dedicated `? Shortcuts` button in the desktop header.
- **Platform Detection:** The Shortcuts panel now automatically displays `⌘` symbols for Mac users and `Ctrl` for Windows/Linux.
- **Generation Dashboard:** Added a high-fidelity summary panel at the top of the Node Summary to show Seed, Model, Steps, and Prompts at a glance.
- **Grid View Shortcuts:** Enabled `N` (Node Summary) and other action keys directly in Grid View via mouse hover.
- **Smart Move (`M`):** The Move shortcut now detects context: if no files are selected, it automatically selects the hovered item and opens the dialog.
- **Real Path Resolution:** New "Folder Info" tool that resolves and displays the physical path on disk (useful for Docker volumes and Symlinks).
- **Asynchronous Rescan:** Re-engineered the "Rescan Folder" feature to run in a background thread to avoid 502/Timeout errors on massive libraries.

**Changed**
- **Unified Shortcut Logic:** Completely rewrote input handling. **Mouse Hover** now strictly takes priority over **Keyboard Focus** for all actions. This fixes inconsistencies where shortcuts would target the wrong file after closing the Lightbox.
- **Help UI Overhaul:** Redesigned the Keyboard Shortcuts (`?`) overlay into a clean, responsive layout.
- **Hybrid Parser:** Integrated `ComfyMetadataParser` to support both API-format and UI-format JSON metadata simultaneously for better accuracy.
- **Header Layout:** Reorganized the top bar to group tools (`Shortcuts`, `Focus Mode`, `AI Manager`) on the right side for better desktop usability.
- **Smart Dialog Accessibility & Interaction Overhaul** Enhanced Keyboard Navigation


**Fixed**
- **KSampler Data Alignment:** Fixed a critical parsing issue in Node Summary where the missing `control_after_generate` field caused values (Steps, CFG, Sampler) to shift and display incorrectly.
- **Focus Loss Bug:** Fixed an issue where the `V` key became unresponsive after returning to the grid until the mouse was moved.
- **Resolution Display:** Fixed an issue where linked resolutions appeared as node IDs (e.g., "41,0") instead of actual dimensions.


## [1.54] - 2026-01-20

### Added
- **Compare Mode:** Implemented a split-view comparison engine for Images and Videos.
  - **Sync Engine:** Mathematical synchronization of Zoom (`scale`) and Pan (`translate`) coordinates between two viewports.
  - **Diff Algorithm:** Backend endpoint (`/api/compare_files`) that parses workflow JSONs, flattens nodes, and returns a sorted table of parameter differences.
  - **UX Tools:** Added image rotation (90° steps) for vertical layouts and interactive floating labels to toggle between filename and resolution.
- **Link External Folders:** Added capability to mount arbitrary filesystem paths (e.g., external drives, network shares) into the gallery root. Includes a recursive directory browser API (`/api/browse_filesystem`).
- **Mount Guard:** Implemented a startup safety check that verifies the accessibility of linked mount roots. If a drive is offline, the system prevents the database garbage collector from deleting associated metadata (Favorites, AI Data).
- **Quick Actions (Grid View):**  
  - **Keyboard Shortcuts:** Added `T` hotkey to instantly show/hide the Search & Filter overlay panel.
  - **Quick Delete:** Added `DEL`/`CANC` listener. Hovering over an item and pressing the key executes deletion immediately, bypassing the confirmation modal for rapid culling.
  - **Quick Favorite:** Added `F` listener. Hovering over an image and pressing `F` toggles the favorite status instantly with visual feedback.
- **Enhanced Lightbox Metadata:** 
  - **Megapixel Calculation:** Frontend now dynamically calculates and displays the MP count (e.g., `16.7 MP`) based on image dimensions, essential for verifying upscales.
  - **Path Resolution:** Clicking the folder name now resolves symlinks/junctions to display the *Real Disk Path* alongside the internal gallery path.
- **DB Migration:** Added automatic schema verification for the `size` column during initialization to ensure compatibility with legacy databases.

### Changed
- **Performance (Smart Grid):** Completely rewrote the `IntersectionObserver` logic for video elements. Videos now strictly execute `.pause()` when leaving the viewport and `.play()` when entering, resolving high resource usage in large grids.
- **Mounting Logic (Windows):** Refactored the `mount_folder` endpoint to handle Windows specifics robustly. It now attempts a Junction (`mklink /J`) first, and automatically falls back to a Symbolic Link (`mklink /D`) if the target is a Virtual Drive (VXHD) or Network Share, capturing specific `stderr` messages for debugging.
- **Consistency:** The application now enforces a **Full Sync** on every startup (removing the check for empty DB) to guarantee that files deleted or renamed externally via the OS are correctly purged from the internal database.
- **Scanning Logic:** Switched file indexing from a Blacklist approach to a strict **Whitelist** of valid media extensions. This prevents the scanner from attempting to process temporary files (e.g., `_output_images_will_be_put_here`) or partial downloads.

### Fixed
- **Mounting Errors:** Fixed generic "returned non-zero exit status 1" errors during folder linking by sanitizing path separators before passing them to the Windows shell.
- **Video Playback:** Fixed race conditions in the lazy loading logic to ensure the video poster/thumbnail is always visible while the video buffer is loading.

## [1.53] - 2026-01-07

### Added

#### Automation & Refresh
- **"Auto-Watch" Folder Mode**: A configurable background monitoring system. Users can set a custom interval (via the refresh menu options) to automatically check for and display new files without manual reloads.

#### Search & Filtering
- **Recursive Search Mode**: New "Include Subfolders" toggle enables deep searching through all nested directories from the current location.
- **Smart Filter Persistence**: Active search filters and sorting preferences are preserved when navigating between folders.
- **Dynamic Filter Discovery**: Dropdowns for file extensions and filename prefixes now update dynamically via AJAX based on the content of subfolders.

#### Video & Workflow Support
- **ProRes Video Support**: Native-like preview for ProRes `.mov` files directly in the browser via real-time ffmpeg transcoding (no intermediate files required).
- **Workflow Shortcut**: Press `C` to instantly copy the current image's workflow metadata to the clipboard.

#### Gallery & UI Enhancements
- **Modernized Design System**: Unified "Glass/Dark" theme using CSS variables and backdrop-filters, offering improved contrast and reduced visual noise.
- **Seamless Infinite Scrolling**: Images now load dynamically as you scroll, eliminating the need for "Load More" buttons and optimizing memory usage on both desktop and mobile.
- **Enhanced Notification System**: Improved state persistence to ensure feedback messages remain visible across page reloads.
- **Collapsible Sidebar**: The folder sidebar can now be resized or completely collapsed to maximize the gallery workspace.
- **Lightbox Immersive Mode (Hide Toolbar)**: New toggle button (shortcut `H`) to hide the overlay toolbar, allowing for a distraction-free, full-screen viewing experience.
- **Lightbox Help Overlay**: Added a "Help" toggle that displays text labels for all toolbar icons, significantly improving accessibility on touch devices where hover tooltips are unavailable.
- **Improved Mobile-First Architecture**: Fully responsive layout with an independently scrollable sidebar and adaptive thumbnail grid for mobile devices.
- **Asynchronous Modal System**: Replaced blocking native browser alerts with non-blocking "Smart Dialogs" using Promises (async/await) for a smoother user experience.

### Fixed
- Improved stability during image/video loading when complex filters are active.
- Fixed sidebar scrolling issues and layout glitches in deeply nested folder structures.

### Changed
- General UI/UX optimizations for performance, responsiveness, and visual consistency across all devices.

## [1.51] - 2025-12-17

### Added

#### Search & Filtering
### Added
- **Prompt Keywords Search**: New filter to search for text strings directly within the generation prompt. Supports comma-separated multiple keywords (e.g., "woman, kimono").
- **Deep Workflow Search**: Added a new `Workflow Files` search field. This searches specifically within the metadata of the generated files to find references to models, LoRAs, and input images used in the workflow (e.g., search for "sd_xl").
- **Global Search**: Users can now toggle between searching the "Current Folder" or performing a "Global" search across the entire library.
- **Date Range Filters**: Added `From` and `To` date pickers to filter files by their creation/modification time.
- **"No Workflow" Filter**: A new checkbox option to quickly identify files that do not contain embedded workflow metadata.
- **Redesigned Filter Panel**: The search and filter options have been moved to a collapsible overlay panel for a cleaner UI on both desktop and mobile.

#### Backend & Database
- **Database Migration (v26)**: Added `workflow_files` column to the database.
- **Metadata Backfilling**: On first startup after update, the system automatically scans existing files to populate the new `workflow_files` search data for deep searching.
- **Optimized SQL**: Improved query performance for filtered searches using `WAL` journal mode and optimized synchronous settings.

### Fixed
- **Filter Dropdown Performance**: Added a limit (`MAX_PREFIX_DROPDOWN_ITEMS`) to the Prefix dropdown to prevent UI freezing in folders with thousands of unique prefixes.
- **Navigation Logic**: Fixed state retention issues when switching between global search results and folder navigation.

## [1.41.1] - 2025-12-05

### Fixed
- **Image Size**: Fixed an issue where the image size for thumbnail generation.
- **Docker**: Added `FORCE_CHOWN` environment variable to force chown of the BASE_SMARTGALLERY_PATH folder only. Pre-checked permissions for the BASE_SMARTGALLERY_PATH to avoid permission errors.

## [1.41] - 2025-11-24

### Added

#### Core & Configuration
- **Batch Zip Download**: Users can now select multiple files and download them as a single `.zip` archive. The generation happens in the background to prevent timeouts, with a notification appearing when the download is ready.
- **Environment Variable Support**: All major configuration settings (`BASE_OUTPUT_PATH`, `SERVER_PORT`, etc.) can now be set via OS environment variables, making deployment and containerization easier.
- **Startup Diagnostics (GUI)**: Added graphical popup alerts on startup to immediately warn users about critical errors (e.g., invalid Output Path) or missing optional dependencies (FFmpeg) without needing to check the console.
- **Automatic Update Check**: The application now checks the GitHub repository upon launch and notifies the console if a newer version of `smartgallery.py` is available.
- **Safe Deletion (`DELETE_TO`)**: Introduced a new `DELETE_TO` environment variable. If set, deleting a file moves it to the specified path (e.g., `/tmp` or a Trash folder) instead of permanently removing it. This is ideal for Unix systems with auto-cleanup policies for temporary files.

#### Gallery & File Management
- **Workflow Input Visualization**: The Node Summary tool now intelligently detects input media (Images, Videos, Audio) used in the workflow (referenced in nodes like `Load Image`, `LoadAudio`, `VHS_LoadVideo`, etc.) located in the `BASE_INPUT_PATH`.
- **Source Media Gallery**: Added a dedicated "Source Media" section at the top of the Node Summary overlay. It displays previews for all detected inputs in a responsive grid layout.
- **Audio Input Support**: Added a native audio player within the Node Summary to listen to audio files used as workflow inputs.
- **Advanced Folder Rescan**: Added a "Rescan" button with a modal dialog allowing users to choose between scanning "All Files" or only "Recent Files" (files checked > 1 hour ago). This utilizes a new `last_scanned` database column for optimization.
- **Range Selection**: Added a "Range" button (`↔️`) to the selection bar. When exactly two files are selected, this button appears and allows selecting all files between them.
- **Enhanced Node Summary**: The workflow parser has been updated to support both ComfyUI "UI format" and "API format" JSONs, ensuring node summaries work for a wider range of generated files.
- **Smart File Counter**: Added a dynamic badge in the toolbar that displays the count of currently visible files. If filters are active (or viewing a subset), it explicitly shows the total number of files in the folder (e.g., "10 Files (50 Total)").

#### User Interface & Lightbox
- **Keyboard Shortcuts Help**: Added a help overlay (accessible via the `?` key) listing all available keyboard shortcuts for navigation and file management.
- **Visual Shortcut Bar**: Added a floating shortcuts bar inside the Lightbox view to guide users on available controls (Zoom, Pan, Rename, etc.).
- **Advanced Lightbox Navigation**: 
    - Added **Numpad Panning**: Use Numpad keys (1-9) to pan around zoomed images.
    - Added **Pan Step Cycling**: Press `.` to change the speed/distance of keyboard panning.
    - Added **Smart Loader**: New visual loader for high-res images in the lightbox for a smoother experience.

#### Docker & Deployment
- **Containerization Support**: Added full Docker support to run SmartGallery in an isolated environment.
- **Docker Compose & Makefile**: Included `compose.yaml` for easy deployment and a `Makefile` for advanced build management.
- **Permission Handling**: Implemented `WANTED_UID` and `WANTED_GID` environment variables to ensure the container can correctly read/write files on the host system without permission errors.

### Fixed
- **Security Patch**: Implemented robust checks to prevent potential path traversal vulnerabilities.
- **FFprobe in Multiprocessing**: Fixed an issue where the path to `ffprobe` was not correctly passed to worker processes during parallel scanning on some systems.

## [1.31] - 2025-10-27

### Performance
- **Massive Performance Boost with Parallel Processing**: Thumbnail generation and metadata analysis have been completely parallelized for both the initial database build and on-demand folder syncing. This drastically reduces waiting times (from many minutes to mere seconds or a few minutes, depending on hardware) by leveraging all available CPU cores.
- **Configurable CPU Usage**: A new `MAX_PARALLEL_WORKERS` setting has been added to allow users to specify the number of parallel processes to use. Set to `None` for maximum speed (using all cores) or to a specific number to limit CPU usage.

### Added
- **File Renaming from Lightbox**: Users can now rename files directly from the lightbox view using a new pencil icon in the toolbar. The new name is immediately reflected in the gallery view and all associated links without requiring a page reload. Includes validation to prevent conflicts with existing files.
- **Persistent Folder Sort**: Folder sort preferences (by name or date) are now saved to the browser's `localStorage`. The chosen sort order now persists across page reloads and navigation to other folders.
- **Console Progress Bar for Initial Scan**: During the initial database build (the offline process), a detailed progress bar (`tqdm`) is now displayed in the console. It provides real-time feedback on completion percentage, processing speed, and estimated time remaining.

### Fixed
- **Critical 'Out of Memory' Error**: Fixed a critical 'out of memory' error that occurred during the initial scan of tens of thousands of files. The issue was resolved by implementing batch processing (`BATCH_SIZE`) for database writes.

### Changed
- **Code Refactoring**: File processing logic was centralized into a `process_single_file` worker function to improve code maintainability and support parallel execution.

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