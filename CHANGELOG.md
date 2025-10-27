
# Changelog

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