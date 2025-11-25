# Changelog

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