# Changelog

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