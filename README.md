<div align="center">
  
  <h1>SmartGallery DAM</h1>
  <p><strong>The Open Source Digital Asset Manager & Gallery Built for ComfyUI & AI Production Libraries</strong></p>
 
  <p>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/biagiomaf/smart-comfyui-gallery?color=yellow&style=flat-square" alt="License"></a>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python">
    <a href="https://hub.docker.com/r/mmartial/smart-comfyui-gallery"><img src="https://img.shields.io/docker/pulls/mmartial/smart-comfyui-gallery?color=099cec&label=docker%20pulls&style=flat-square&logo=docker&logoColor=white" alt="Docker Pulls"></a>
    <a href="https://github.com/biagiomaf/smart-comfyui-gallery/stargazers"><img src="https://img.shields.io/github/stars/biagiomaf/smart-comfyui-gallery?style=flat-square&logo=github" alt="Stars"></a>
    <a href="https://github.com/biagiomaf/smart-comfyui-gallery/releases/latest"><img src="https://img.shields.io/github/v/release/biagiomaf/smart-comfyui-gallery?color=emerald&style=flat-square" alt="Latest Release"></a>
  </p>
 
  <p>
    <a href="#21-installation"><b>🚀 Quick Install</b></a> •
    <a href="#12-whats-new-in-v222"><b>✨ What's New (v2.22)</b></a> •
    <a href="#-why-smartgallery-dam"><b>⚡ Core Features</b></a> •
    <a href="https://smartgallerydam.com"><b>🌐 Official Website</b></a> •
  </p>
</div>

---

## 🎯 Who is SmartGallery DAM for?

✅ You just installed ComfyUI and want a better gallery.  
✅ You have 50,000 generations and can't find anything anymore.  
✅ You want total control over your library, shifting from a workflow-centric canvas to a gallery-centric hub.  
✅ You work with clients and need reviews, production briefs, and approvals.  

**One Tool. Different Users.**  
![SmartGallery DAM — comic strip](assets/smartgallery_dam_comic_strip.png)  
Whether you're generating for fun, building a portfolio, or running a production studio.

---

* 🖼 **Ultra-Fast Browsing:** Browse AI generations with one of the fastest gallery interfaces available.
* 📂 **Universal Scalability:** Organize anything from hundreds to hundreds of thousands of images, videos and audio files.
* 🔎 **Deep Search:** Find any asset instantly by prompts, models, LoRAs, dates, comments, ratings or AI-powered SQL.
* 🎨 **Remix Engine, Nodepad, LoRA Synergy:** Edit raw JSON nodes, auto-match compatible LoRAs and queue generations directly without opening the ComfyUI interface.
* 👥 **Client Sharing Portal:** Share curated galleries with clients while keeping prompts and workflows private.
* 📱 **Mobile First Experience**  

> We are not aware of any other self-hosted media manager with a mobile experience this complete.  
> Browse, search, rate, review, organize, remix, read production briefs, and use high-density List View directly from your phone.
<p><strong>
    A gallery-centric hub for your work and decisions.
</strong></p>  

[**🌐 smartgallerydam.com**](https://smartgallerydam.com) · full documentation, wiki and feature reference · [**▶️ Presentation Video**](https://smartgallerydam.com/smartgallerydam-2.13.mp4)

---

## ⚡ Why SmartGallery DAM?

| Feature | Why It Matters |
| :--- | :--- |
| 🗂️ **File Manager** | Rename, move, copy, delete, create folders in-browser |
| 🧬 [**Smart Asset Clustering**](docs/Smart_Asset_Clustering_manual.md) | Group generations by node architecture or prompt text (`Shift+C`) using colorful `#HASH` badges for at-a-glance visual grouping - **NEW** |
| 📋 [**Full Asset Details**](docs/Asset_Info_Panel_manual.md) | Instant 360° inspector for disk paths, symlink targets & node pipelines (`I`) - **NEW** |
| 📝 [**Collection Notes & Briefs**](docs/Collection_Notes_manual.md) | Attach rich Markdown specs & checklists to virtual albums - **NEW** |
| 🔍 **Instant Search** | Find by prompt, checkpoint, LoRA (with live autocomplete), date or comment |
| 🧠 [**OmniQuery**](docs/OmniQuery.md) | Search your gallery in plain English, any criteria. Let AI write complex SQL queries to find hyper-specific cross-referenced media |
| 🔗 **Any Folder & Drive Mounts** | Point at any ComfyUI output, NAS, symlink or network path |
| 📤 **Magic Upload** | Drag & drop from PC/smartphone, auto-extract & index workflows |
| 📑 **Grid & List Views** | Browse the way you prefer (with inline audio player in List View) |
| 🪄 [**Remix Engine**](docs/remix_workflow_nodepad_lora_synergy_manual.pdf) | Generate without opening ComfyUI. A 3-tier workspace to extract workflows, build custom dashboards, edit raw JSON with live dictionary lookups, and queue directly |
| 🔌 [**LoRA Synergy™**](docs/LORA_SYNERGY.md) | Fully offline matchmaker. Scans Safetensors to guarantee checkpoint compatibility (SD1.5, SDXL, Flux), surfaces trigger words, and auto-wires the workflow |
| ⚖️ **Compare Generations** | A/B slider with automatic parameter diff |
| 👥 **Team Ready** | Roles, per-image comments, star ratings |
| 🗃️ **Nested Collections** | Virtual albums & tree hierarchies, zero duplication on disk |
| 🏷️ **Status Tags** | Track approval status across the whole library |
| 🛡️ **Client Portal & Filtering** | Share curated collections with clients; new filter overlay for Exhibition Mode |
| 🎬 **Video & Audio** | Multimedia, transcoding included. Thumbnails, storyboard preview, dynamic audio waveforms, and on-the-fly FFmpeg transcoding |
| 🌐 **Cross Platform** | Windows, macOS, Linux, Docker: everywhere |
| ⚡ **Simple Installation** | Zero-config Portable App for Windows (unzip & run) and official Docker image |

---

## 💡 ComfyUI-Aware. ComfyUI-Independent.

SmartGallery DAM runs as a fully independent process, outside ComfyUI's environment. It keeps indexing and organizing your library whether ComfyUI is up, down, updating, or completely uninstalled. No custom node, no shared dependencies.

SmartGallery DAM is *ComfyUI-aware* (it reads workflows, extracts prompts, understands models and LoRAs) but *ComfyUI-independent* by design. Your DAM outlives any tool it connects to.

**What this means in practice:**

- ComfyUI is broken after a Python update? SmartGallery keeps running.
- Run it alongside ComfyUI on the same machine on a different port. Or install it on a separate machine or laptop and just link the output folder over the network.
- You switched tools entirely? SmartGallery works on *any* folder of media. It was never ComfyUI-only to begin with.

![SmartGallery DAM — main workspace](assets/infographic.png)

---

## 📌 Table of Contents

1.  [**OVERVIEW & CONCEPTS**](#1-overview--concepts)
    *   [1.1 What is SmartGallery DAM?](#11-what-is-smartgallery-dam)
    *   [1.2 What's New in v2.22](#12-whats-new-in-v222)
    *   [1.3 Core Features](#13-core-features)
    *   [1.4 Use Case Scenarios](#14-use-case-scenarios)
2.  [**SETUP & CONFIGURATION**](#2-setup--configuration)
    *   [2.1 Installation](#21-installation)
    *   [2.2 Launch Parameters](#22-launch-parameters)
    *   [2.3 FFmpeg Integration](#23-ffmpeg-integration)
3.  [**INTERFACE WALKTHROUGH**](#3-interface-walkthrough)
    *   [3.1 The Main Workspace (Creator Hub)](#31-the-main-workspace-creator-hub)
        *   [3.1.1 Sidebar Navigation](#311-sidebar-navigation)
        *   [3.1.2 Top Toolbar & Global Actions](#312-top-toolbar--global-actions)
        *   [3.1.3 Search, Filters & Fuzzy Auto-Suggest](#313-search-filters--fuzzy-auto-suggest)
        *   [3.1.4 OmniQuery – AI-Powered SQL Explorer](#314-omniquery--ai-powered-sql-explorer)
        *   [3.1.5 Gallery Grid & Focus Mode](#315-gallery-grid--focus-mode)
        *   [3.1.6 Batch Selection Bar](#316-batch-selection-bar)
    *   [3.2 Advanced Media Inspection](#32-advanced-media-inspection)
        *   [3.2.1 The Lightbox (Media Viewer)](#321-the-lightbox-media-viewer)
        *   [3.2.2 Full Asset Details Panel (📋 / Shortcut I)](#322-full-asset-details-panel---shortcut-i)
        *   [3.2.3 Smart Asset Clustering & Inspector (🧬 / Shortcut Shift+C)](#323-smart-asset-clustering--inspector---shortcut-shiftc)
        *   [3.2.4 ComfyUI Node Summary (📝 / Shortcut N)](#324-comfyui-node-summary---shortcut-n)
        *   [3.2.5 Remix Workflow & The { } Nodepad (✦ / Shortcut B)](#325-remix-workflow--the---nodepad---shortcut-b)
        *   [3.2.6 LoRA Synergy™](#326-lora-synergy)
        *   [3.2.7 Compare Mode](#327-compare-mode)
        *   [3.2.8 Video Storyboard](#328-video-storyboard)
    *   [3.3 Digital Asset Management (DAM) & Communication](#33-digital-asset-management-dam--communication)
        *   [3.3.1 Virtual Collections & Sharing](#331-virtual-collections--sharing)
        *   [3.3.2 Collection Notes & Production Briefs (📝)](#332-collection-notes--production-briefs-)
        *   [3.3.3 Pipeline Status Tags](#333-pipeline-status-tags)
        *   [3.3.4 Ratings & Comments](#334-ratings--comments)
    *   [3.4 User Management & Access Control](#34-user-management--access-control)
    *   [3.5 The Exhibition Portal (Client Hub)](#35-the-exhibition-portal-client-hub)
4.  [**ADVANCED TOPICS & REFERENCE**](#4-advanced-topics--reference)
    *   [4.1 Sharing Online](#41-sharing-online)
    *   [4.2 Keyboard Shortcuts Reference](#42-keyboard-shortcuts-reference)
    *   [4.3 Experimental Features](#43-experimental-features)
    *   [4.4 Philosophy, Feedback & License](#44-philosophy-feedback--license)

---

## 1. OVERVIEW & CONCEPTS

### 1.1 What is SmartGallery DAM?

**SmartGallery DAM** is the evolution of *SmartGallery for ComfyUI*. What started as a fast local gallery for browsing outputs has grown into a powerful and easy-to-use **Digital Asset Management system**. 

Evolve your workflow from a simple collection of files into a structured, searchable library. Designed for individual creators and professional teams, this platform is ridiculously simple to use, yet powerful enough to act as the ultimate file manager for your generations. Every asset is automatically indexed, linked to its original generative parameters, and ready for secure review. The system is open-source, private, and entirely local: no cloud dependencies and no recurring costs.

**Who is this for?**

- **The AI Artist & Creator.** You run ComfyUI all day. Your output folder has tens of thousands of files and you can never find anything. SmartGallery lives outside that chaos. It indexes every generation with its full workflow, groups variations automatically using Smart Asset Clustering (`Shift+C`), lets you search by prompt, model, or LoRA with live auto-suggest, and lets you cull while batches are still running. When ComfyUI breaks, SmartGallery doesn't even blink.
- **The Creative Pro or Team.** You deliver AI visuals to clients. Sharing via Google Drive or Dropbox feels unprofessional. SmartGallery gives you Production Briefs (`.md`/`.txt`) attached to collections, status tags, and an optional Exhibition portal where clients rate and comment on images in real time, while your prompts and workflows stay completely invisible to them.
- **Everyone else.** You just want to organize photos, videos, or art and share them nicely. SmartGallery works with any folder on your system.  
- **The Remote or Multi-Machine User.** You want your gallery on a dedicated machine (a laptop, a NAS, a home server) without installing ComfyUI there. Install SmartGallery on that machine, link your ComfyUI output folder over the network, and access the full DAM from any browser, on any device, including your phone.

---

### 1.2 What's New in v2.22

- 📁 **Folder File Count Badges & Dynamic Tree Collapse**: Folder navigation now features real-time file count badges across the entire directory tree in both the main sidebar and file management dialogs. 
- **Direct & Subfolder File Counts:** Displays a badge for files directly contained within a folder. When a parent folder is collapsed, a secondary `+N` badge automatically appears to indicate the combined file count of all its nested subfolders.  
- 🐛 **Bug Fixes & Stability**: Fixed Batch File Move & Copy Operations. Resolved a backend exception that in v2.21 caused file relocation and copying between folders to fail. 

---

- 🧬 [**Smart Asset Clustering & Visual Inspector (`Shift+C`)**](docs/Smart_Asset_Clustering_manual.md): Instantly group and compare media generated by identical ComfyUI graph architectures (`workflow_hash`) or identical positive prompts (`prompt_hash`). Click any colorful `#HASH` badge to open the interactive **Cluster Inspector** to view node pipeline chains, loaded model inventories, and launch one-click cluster searches. 👉 READ the **[Smart Asset Clustering Manual](docs/Smart_Asset_Clustering_manual.md)**.
- 📋 [**Redesigned 'Full Asset Details' Panel (<kbd>I</kbd> Key)**](docs/Asset_Info_Panel_manual.md): Press <kbd>I</kbd> on any asset in the main workspace to open a high-density, two-tab diagnostic inspector. Tab 1 handles file metrics, Megapixel density, absolute disk paths vs. real symlink targets, and nested collection ancestry. Tab 2 visualizes the node execution pipeline, loaded checkpoints/LoRAs, prompt text with one-click copy, and one-click clustering launch. 👉 READ the **[Full Asset Details Manual](docs/Asset_Info_Panel_manual.md)**.
- 📝 [**Interactive Collection Notes & Production Briefs**](docs/Collection_Notes_manual.md): Attach rich Markdown production briefs (`.md` or `.txt`) to Virtual Collections. Collections with notes are highlighted with a distinct yellow accent. Access notes via the top toolbar button, switch between multiple briefs with tabs, and let clients or team members rate and comment directly on project briefs. 👉 READ the **[Collection Notes Manual](docs/Collection_Notes_manual.md)**.
- ⚙️ **Cluster Badges in Normal Grid:** Toggle `🧬 Cluster Badges` in Settings & Info to show interactive `#HASH` badges on normal grid thumbnails instead of the standard workflow badge.
- 🔍 **Fuzzy Workflow Search & Live Auto-Suggest:** Search models, LoRAs, and workflow files effortlessly with alphanumeric normalization (e.g. `wan 2.2` matches `wan2.2_i2v_high.safetensors`), a live two-line autocomplete dropdown, and native "Did You Mean?" suggestions.
- 🎵 **Embedded Audio Player in List View:** Play, pause, scrub, and check track durations directly within List View rows in both the Main Workspace and Exhibition Portal.
- 🔍 **Dedicated Exhibition Filter Panel:** External stakeholders in Exhibition Mode can now filter large collections by smart filename queries, file extensions, and date ranges.
- 🛡️ **API Route & System Hardening:** Enhanced backend route fortification, strict session validation, and strengthened data isolation across public, guest, and administrative contexts.

> **Previous Highlights:**
> - 🧠 [**OmniQuery (AI-Powered SQL Explorer)**](docs/OmniQuery.md): Ask complex questions to your DAM in natural language via LLMs. 👉 READ the **[OmniQuery Manual](docs/OmniQuery.md)**.
> - 🔌 [**LoRA Synergy™**](docs/LORA_SYNERGY.md): Offline LoRA matchmaker that reads safetensors headers to guarantee checkpoint compatibility and auto-wire nodes. 👉 READ the **[LoRA Synergy Manual](docs/LORA_SYNERGY.md)**.
> - 📑 **List View:** High-density browsing mode with sortable sticky columns.

> [!NOTE]
> Read the **[Full Changelog](CHANGELOG.md)** so you don't miss out on all the quality-of-life improvements and bug fixes!

---

### 1.3 Core Features

<details>
<summary><strong>Live Workspace and File Management</strong></summary>

-   **Cross-platform, Cross-device:** Runs locally on Windows, macOS, Linux, and Docker. The responsive web interface works flawlessly across desktops, tablets, and smartphones.
-   **Auto-Watch:** Detects new ComfyUI outputs the moment they are saved. Cull with `Del`, favorite with `F`, move with `M`, all while generation is still running.
-   **Magic Upload:** Drag & drop or upload files from your PC or smartphone directly into any folder via the web interface. ComfyUI metadata is extracted automatically.
-   **Full File Manager:** Select files individually or in bulk. Move, copy, delete, or ZIP directly from the browser.
-   **Focus Mode:** Press `Q` to hide all UI chrome. Maximum screen space for pure curation.
-   **External Drive Mounting:** Link any external drive, NAS, or network path via Symlinks directly from the UI.
-   **List View with Audio Player:** High-density table layout with inline audio playback controls.

</details>

<details>
<summary><strong>Workflow Intelligence & Asset Clustering</strong></summary>

-   **Smart Asset Clustering (`Shift+C`):** Group generations by identical node graph architecture or exact prompt text across folders. Includes the Cluster Inspector for pipeline visualization and one-click clustering.
-   **Full Asset Details Panel (`I`):** High-density 2-tab inspector for metrics, Megapixels, physical disk paths, real symlink targets, collection ancestry, and model inventories.
-   **LoRA Synergy:** Zero-API offline matching that prevents architecture mismatch errors by reading safetensors and automatically wiring your graph.
-   **Node Summary Dashboard (`N`):** Press `N` on any image to see Seed, CFG, Steps, Sampler, Scheduler, all active Models, LoRAs with weights, and full positive/negative prompts.
-   **Remix 3-Tier Workflow (`B`):** Press `B` to break out of the canvas. Use the *Auto-Form* for simple prompts, build a custom dashboard in *My Panel*, or edit raw backend JSON safely with the revolutionary *{ } Nodepad*.
-   **Workflow Download and Copy:** Press `W` to download the raw JSON workflow, `C` to copy it to clipboard and paste directly back into ComfyUI.
-   **Clean Export:** Press `Shift+W` to download a pixel-perfect copy stripped of all EXIF data and embedded workflows. Safe to share externally.
-   **Compare Mode:** Select two generations, open the A/B slider with synchronized zoom and pan. A parameter diff table shows only the values that changed.

</details>

<details>
<summary><strong>Organization (DAM) & Search</strong></summary>

-   **Collection Notes & Production Briefs:** Attach rich Markdown `.md` or `.txt` briefs to Virtual Collections. Collections with notes feature a yellow accent, top toolbar access button, tabbed multi-note reader, and interactive rating/commenting.
-   **Fuzzy Workflow Search & Auto-Suggest:** Search models and LoRAs with alphanumeric normalization (`wan 2.2` -> `wan2.2_i2v_high.safetensors`), live two-line autocomplete dropdown, and "Did You Mean?" suggestions.
-   **OmniQuery (AI SQL Explorer):** Query the database using AI to answer complex questions safely (read-only).
-   **Virtual Nested Collections:** Group files from different physical folders into a hierarchical tree of albums without duplicating a byte on disk.
-   **Collection Sharing:** Keep collections private, mark them as Exhibition Ready for all guests, or share them *exclusively* with specific users.
-   **Status Tags:** Keyboard shortcuts `1` to `5` apply color-coded team statuses: Approved, Review, To Edit, Rejected, Select.
-   **Favorites:** Press `F` to toggle a Favorite flag on any file.
-   **Search by Anything:** Prompt keywords, checkpoint name, LoRA name, comment text, date range, file extension, or star rating ranges.

</details>

<details>
<summary><strong>Media Tools & Exhibition Mode</strong></summary>

-   **Exhibition Mode & Filter Panel:** A separate, secure portal for clients or collaborators. Physical folder browsing is disabled. Includes a dedicated filter overlay for external stakeholders.
-   **Blind Rating System:** Hides global average ratings from users to prevent group bias during review sessions.
-   **Video Storyboard:** Press `E` in the Lightbox to generate a grid of 11 evenly-spaced frames from start to last frame.
-   **Dynamic Audio Waveforms:** Real-time amplitude scaling (🌊) without media regeneration.
-   **Video Transcoding:** ProRes, MKV, AVI, MOV are auto-transcoded via FFmpeg for smooth browser playback.

</details>

---

### 1.4 Use Case Scenarios

SmartGallery has two interfaces: the **Main Interface** (your personal workspace) and **Exhibition** (an optional sharing portal for clients, collaborators, or friends). They are completely independent. You can run just the Main Interface forever and never touch Exhibition. You can launch Exhibition only when you have something to share and shut it down when the review is over. Neither requires the other to be running.

<details>
<summary><strong>Scenario 1: Solo user, no sharing needed (upgrading from v1)</strong></summary>

If you used SmartGallery v1 as an advanced file manager and have no need to share your work, nothing changes. Launch it exactly as before, with no extra parameters:

```bash
python smartgallery.py
```

ComfyUI is generating hundreds of files. As each one appears in the grid, you decide in real time: delete the bad seeds immediately with `Del`, move the keepers to the right folder with `M`, mark favorites with `F`, or tag them with a color status. You do all of this while generation is still running. When you want to review later, you search by prompt keywords, model name, or LoRA, pull up the full node summary for any image from months ago, or compare two generations side by side with a parameter diff.

When ComfyUI is not running, the same interface works as a full file manager for all your media. No Exhibition needed, ever, unless you decide you want it.

What is new in v2 that you can start using immediately, with no additional setup:

-   **Virtual Collections:** group files from different folders into named albums without moving anything on disk. Open the Collections tab in the left sidebar and click + to create one.
-   **Status Tags:** mark any image with a workflow state using keys `1` to `5`. For example, press `3` to flag a file as "To Edit" and come back to it later. Browse all files with a given status from the Status tab in the sidebar.
-   **Ratings and personal notes:** press `G` on any image to open the Details panel. Assign a 1 to 5 star rating and write a note to yourself. These notes are searchable: use the comment keyword filter to find any image by words you wrote in your own comments.
-   **Clean Export:** to send a file to someone without exposing your ComfyUI workflow and models, press `Shift+W`. You get a pixel-perfect copy with all metadata stripped.

</details>

<details>
<summary><strong>Scenario 2: Sharing your work with Exhibition</strong></summary>

Exhibition is a separate, read-only portal you share with clients, collaborators, or anyone you want to show your work to.

**Step 1: Launch the Main Interface with authentication.**

> The line below shows only the launch command with the relevant parameters. In practice you should add these parameters to your platform launch script (the `.bat` or `.sh` file you created during installation), which also sets your folder paths and ffprobe location. If you have not created a launch script yet, see the [Installation](#21-installation) section, pick your platform, and follow the instructions there first.

```bash
python smartgallery.py --port 8189 --admin-pass yourpassword --force-login
```

Log in at `http://localhost:8189` with username `admin` (always lowercase) and the password you set above.

**Step 2: Create Collections and set Permissions.** In the left sidebar, open the Collections tab and click +. Give each collection a name. You can toggle it as "Exhibition Ready" (public for everyone in the portal), or click the `⋮` menu -> 👥 **Share / Permissions** to assign it exclusively to a specific client.

**Step 3: Create user accounts.** Click the user management icon in the sidebar. Create an account for each person who will access Exhibition. For clients and external viewers, assign the role CUSTOMER or USER. Share their credentials and the Exhibition URL with them directly.

**Step 4: Launch Exhibition.**

> Same as above: add these parameters to a second launch script for Exhibition (a separate `.bat` or `.sh` file), keeping your folder paths and other settings identical to the Main Interface script. Run it from a second terminal when you are ready to share.

```bash
python smartgallery.py --exhibition --port 8190 --admin-pass yourpassword
```

Share `http://youraddress:8190` with your users. They will see only the collections assigned to them, with no prompts, no workflow data, and no folder structure. They can leave star ratings and write comments on individual images. You can read and reply to their feedback from the Main Interface at any time.

</details>

<details>
<summary><strong>Scenario 3: Small team working together (Blind Rating)</strong></summary>

The team lead runs the Main Interface with `--force-login` and `--admin-pass` so the workspace is password-protected. Each team member gets a STAFF account and logs into the same Main Interface remotely to review files, apply status tags, and leave internal comments on specific images.

```bash
python smartgallery.py --port 8189 --admin-pass yourpassword --force-login
```

When work is ready for a client, a CUSTOMER account is created, the relevant Collections are mapped, and Exhibition is launched on a separate port. To prevent the client (or team members) from being influenced by what others voted, the lead launches Exhibition with the `--blind-rating` flag:

```bash
python smartgallery.py --exhibition --port 8190 --admin-pass yourpassword --blind-rating
```

Now, when clients log into `http://youraddress:8190`, they cannot see the global average score. They only see their own stars. Admins reviewing the gallery can press `B` to toggle the blind mode off temporarily and see the real consensus. 

All feedback runs through the same database, with no file transfers, no email threads, and no ZIP files.

</details>

---

## 2. SETUP & CONFIGURATION

### 2.1 Installation

**Requirements:**
*   **Portable/Docker Installation:** No installation required. Everything is pre-configured (Python is already embedded).
*   **Manual Installation:** Python 3.10+ installed on your system.
*   **Strongly Recommended:** FFmpeg/FFprobe (for advanced video features).

<details>
<summary><strong>Windows Installation Guide</strong></summary>

There are two ways to run SmartGallery on Windows: using the ready-to-use **Portable Version** (Recommended) or the **Manual Git Installation**.

---

### Method 1: Portable Version (Recommended)
This version includes a fully self-contained environment. You do not need to install Python or any dependencies on your system—it is **completely plug-and-play**.

**1. Download & Extract**
* **Direct Download:** [SmartGallery-v2.22-Windows-Portable.zip](https://github.com/biagiomaf/smart-comfyui-gallery/releases/download/2.22/SmartGallery-v2.22-Windows-Portable.zip)
* **Releases Page:** Alternatively, view all builds on the [Releases page](https://github.com/biagiomaf/smart-comfyui-gallery/releases/latest).
* Extract the archive into a folder of your choice.

**2. Configure and Run**
* **Read First:** Before launching, open the `00_START_HERE.txt` file included in the root folder for essential setup instructions.
* **Customize:** Rename `sample_run_smartgallery.bat` to `run_smartgallery.bat`, right-click it, and select **Edit**.
* **Setup Paths:** Update the `CONFIGURATION` section to point to your specific ComfyUI folders (ensure you use forward slashes `/`).
* **Launch:** Save the file and double-click `run_smartgallery.bat` to launch the server!

**3. Updating to a Newer Version**
To update to a newer release while preserving your settings:
1. Download and extract the new Portable ZIP into a fresh folder.
2. Simply copy your existing `run_smartgallery.bat` (and any custom `.bat` files for Exhibition Mode) into the new folder.
3. Launch your copied `.bat` file; your configuration will be preserved automatically.

*Note: SmartGallery DAM is completely standalone; your database and settings are kept safe in your chosen configuration path.*

---

### Method 2: Manual / Git Installation
For advanced users who prefer managing their own Python virtual environments and updating via Git.

**1. Clone and setup**

```bat
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Or download the Source Code ZIP from [Releases](https://github.com/biagiomaf/smart-comfyui-gallery/releases/latest), extract, and run the pip commands above.

**2. Create your launch script**

Create `run_smartgallery.bat` in the root folder:

```bat
@echo off
cd /d %~dp0
call venv\Scripts\activate.bat

:: --- CONFIGURATION: replace with your real paths ---
:: Use forward slashes (/) even on Windows
set "BASE_OUTPUT_PATH=C:/Path/To/ComfyUI/output"
set "BASE_INPUT_PATH=C:/Path/To/ComfyUI/input"
set "BASE_SMARTGALLERY_PATH=C:/Path/To/ComfyUI/output"
set "FFPROBE_MANUAL_PATH=C:/Path/To/ffmpeg/bin/ffprobe.exe"
set SERVER_PORT=8189

:: --- OPTIONAL LAUNCH PARAMETERS ---
:: Add any of the following to the python command below depending on your scenario:
::
::   --admin-pass yourpassword   Set the admin password (log in as: admin / yourpassword)
::   --force-login               Require login on the Main Interface (use with --admin-pass)
::   --exhibition                Start in Exhibition Mode instead of the Main Interface
::   --port 8190                 Use a different port (default: 8189)
::   --enable-guest-login        Allow anonymous guest access in Exhibition
::   --blind-rating              Hide global averages to prevent user bias
::
:: Example – Main Interface with login enforced:
::   python smartgallery.py --port 8189 --admin-pass yourpassword --force-login
::
:: Example – Exhibition on port 8190 with Blind Rating:
::   python smartgallery.py --exhibition --port 8190 --admin-pass yourpassword --blind-rating

:: --- START ---
python smartgallery.py
pause
```

Double-click `run_smartgallery.bat` to start.

**3. Update**

```bat
cd smart-comfyui-gallery
git pull
venv\Scripts\activate
pip install -r requirements.txt
```

</details>

<details>
<summary><strong>macOS Installation Guide</strong></summary>

**1. Clone and setup**

```bash
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create your launch script**

Create `run_smartgallery.sh` and make it executable (`chmod +x run_smartgallery.sh`):

```bash
#!/bin/bash
source venv/bin/activate

# Fix for "Too many open files" on macOS
ulimit -n 4096

# --- CONFIGURATION: replace with your real paths ---
export BASE_OUTPUT_PATH="$HOME/ComfyUI/output"
export BASE_INPUT_PATH="$HOME/ComfyUI/input"
export BASE_SMARTGALLERY_PATH="$HOME/ComfyUI/output"
export FFPROBE_MANUAL_PATH="/opt/homebrew/bin/ffprobe"
export SERVER_PORT=8189

# --- OPTIONAL LAUNCH PARAMETERS ---
# Add any of the following to the python command below depending on your scenario:
#
#   --admin-pass yourpassword   Set the admin password (log in as: admin / yourpassword)
#   --force-login               Require login on the Main Interface (use with --admin-pass)
#   --exhibition                Start in Exhibition Mode instead of the Main Interface
#   --port 8190                 Use a different port (default: 8189)
#   --enable-guest-login        Allow anonymous guest access in Exhibition
#   --blind-rating              Hide global averages to prevent user bias
#
# Example – Main Interface with login enforced:
#   python smartgallery.py --port 8189 --admin-pass yourpassword --force-login
#
# Example – Exhibition on port 8190 with Blind Rating:
#   python smartgallery.py --exhibition --port 8190 --admin-pass yourpassword --blind-rating

# --- START ---
python smartgallery.py
```

Run with: `./run_smartgallery.sh`

Install FFmpeg via Homebrew: `brew install ffmpeg`

**3. Update**

```bash
cd smart-comfyui-gallery && git pull
source venv/bin/activate && pip install -r requirements.txt
```

</details>

<details>
<summary><strong>Linux Installation Guide</strong></summary>

**1. Clone and setup**

```bash
git clone https://github.com/biagiomaf/smart-comfyui-gallery
cd smart-comfyui-gallery
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create your launch script**

Create `run_smartgallery.sh` and make it executable (`chmod +x run_smartgallery.sh`):

```bash
#!/bin/bash
source venv/bin/activate

# --- CONFIGURATION: replace with your real paths ---
export BASE_OUTPUT_PATH="$HOME/ComfyUI/output"
export BASE_INPUT_PATH="$HOME/ComfyUI/input"
export BASE_SMARTGALLERY_PATH="$HOME/ComfyUI/output"
export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
export SERVER_PORT=8189

# --- OPTIONAL LAUNCH PARAMETERS ---
# Add any of the following to the python command below depending on your scenario:
#
#   --admin-pass yourpassword   Set the admin password (log in as: admin / yourpassword)
#   --force-login               Require login on the Main Interface (use with --admin-pass)
#   --exhibition                Start in Exhibition Mode instead of the Main Interface
#   --port 8190                 Use a different port (default: 8189)
#   --enable-guest-login        Allow anonymous guest access in Exhibition
#   --blind-rating              Hide global averages to prevent user bias
#
# Example – Main Interface with login enforced:
#   python smartgallery.py --port 8189 --admin-pass yourpassword --force-login
#
# Example – Exhibition on port 8190:
#   python smartgallery.py --exhibition --port 8190 --admin-pass yourpassword --blind-rating

# --- START ---
python smartgallery.py
```

Run with: `./run_smartgallery.sh`

**3. Update**

```bash
cd smart-comfyui-gallery && git pull
source venv/bin/activate && pip install -r requirements.txt
```

</details>

<details>
<summary><strong>Docker & Unraid Setup Guide</strong></summary>

> Special thanks to [Martial Michel (@mmartial)](https://github.com/mmartial) for orchestrating Docker support and contributing to the core application logic.

Pre-built image on [DockerHub](https://hub.docker.com/r/mmartial/smart-comfyui-gallery) and **Unraid Community Apps**.

![Unraid CA](assets/smart-comfyui-gallery-unraidCA.png)

**Run:**

```bash
docker run \
  --name smartgallery \
  -v /your/host/output:/mnt/output \
  -v /your/host/input:/mnt/input \
  -v /your/host/SmartGallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e BASE_INPUT_PATH=/mnt/input \
  -e BASE_SMARTGALLERY_PATH=/mnt/SmartGallery \
  -e WANTED_UID=`id -u` \
  -e WANTED_GID=`id -g` \
  # -e CLI_ARGS="..."   # Optional: add launch parameters here (see below) \
  -p 8189:8189 \
  mmartial/smart-comfyui-gallery
```

The `CLI_ARGS` environment variable passes optional launch parameters to SmartGallery inside the container. Add it to the command above depending on your scenario:

| Scenario | CLI_ARGS value | Port mapping |
|---|---|---|
| Main Interface with login | `--admin-pass yourpassword --force-login` | `-p 8189:8189` |
| Exhibition | `--exhibition --admin-pass yourpassword` | `-p 8190:8189` |
| Exhibition with guest access | `--exhibition --admin-pass yourpassword --enable-guest-login` | `-p 8190:8189` |
| Exhibition with Blind Rating | `--exhibition --admin-pass yourpassword --blind-rating` | `-p 8190:8189` |

For Exhibition scenarios, replace `-p 8189:8189` in the `docker run` command above with `-p 8190:8189`. This maps port 8190 on your host to the container's internal port 8189, so clients reach Exhibition at `http://youraddress:8190`.

When using `--admin-pass`, log in with username `admin` (always lowercase) and the password you set.

For running both instances simultaneously, see the dedicated section under [Launch Parameters](#22-launch-parameters).

**Update:**

```bash
docker pull mmartial/smart-comfyui-gallery
docker stop smartgallery && docker rm smartgallery
# Re-run the docker run command above
```

Full Docker guide: [docs/DOCKER_HELP.md](docs/DOCKER_HELP.md)

</details>

Once installed, open SmartGallery at:
```
http://127.0.0.1:8189/galleryout
```

> [!IMPORTANT]
> **When you update to a new version:**
> 
> * **For Portable Installations:** Simply download the new version, extract it, and overwrite your existing files. Remember to **keep your existing launch scripts** (`.bat` or `.sh` files) to preserve your custom paths and settings.
> * **For Docker Installations:** Pull the latest image and restart your container. Your configuration is preserved via your volume mappings.
> * **For Manual Installations:** Remember to keep your existing launch scripts (`.bat` or `.sh` files). After updating your files, refresh your environment dependencies by running: `pip install -r requirements.txt`

---

### 2.2 Launch Parameters

The Main Interface and Exhibition are completely independent. You can run just one, both at the same time, or alternate between them. Neither requires the other to be running.

<details>
<summary><strong>Main Interface parameters</strong></summary>

All parameters are optional. Launched with no flags, SmartGallery runs on port 8189 and treats you as admin automatically when accessed from a local network.

| Flag | Required | Description |
|---|---|---|
| `--port <number>` | Optional | Override the default port (8189). |
| `--admin-pass <pwd>` | Optional* | Set the Admin password. Required to enable user management. Minimum 8 characters. Log in with username `admin` (always lowercase) and the password you set here. |
| `--force-login` | Optional* | Enforces authentication. Must always be combined with `--admin-pass`. Use when accessing from outside the local network. |
| `--blind-rating` | Optional | Forces Blind Rating mode. Useful if you want team members in the main UI to vote without bias. |

`*` `--admin-pass` and `--force-login` must be used together when either is specified.

> **Accessing the main interface from outside your local network?** Always use `--admin-pass` and `--force-login` together, without exception. Without these two flags the interface is open to anyone who finds the URL.

</details>

<details>
<summary><strong>Exhibition parameters</strong></summary>

| Flag | Required | Description |
|---|---|---|
| `--exhibition` | Yes | Start in Exhibition Mode. Only assigned or public collections are visible. Physical folder browsing is disabled. |
| `--admin-pass <pwd>` | Yes | Set the Admin password. Required to protect the instance and enable user management. Minimum 8 characters. |
| `--port <number>` | Yes | Use a different port when running Exhibition alongside the main interface. Typically 8190. |
| `--enable-guest-login` | Optional | Shows a "Login as Guest" button. No account needed to browse Exhibition. |
| `--blind-rating` | Optional | **Blind Rating Mode.** Hides global average ratings from the UI. Users see and sort only by their own personal ratings, ensuring unbiased curation feedback from clients and guests. |

</details>

<details>
<summary><strong>Running both instances: together or independently</strong></summary>

The two instances can run at the same time from two separate terminals or scripts, or independently whenever needed. Launch Exhibition only when you have something to share. There is no requirement to keep both running permanently.

**Python: two terminals or scripts**

```bash
# Terminal 1: Main interface
python smartgallery.py --port 8189 --admin-pass yourpassword --force-login

# Terminal 2: Exhibition (launch only when needed, with Blind Rating active)
python smartgallery.py --exhibition --port 8190 --admin-pass yourpassword --blind-rating
```

**Docker: same image, launched twice**

```bash
# Main interface container (port 8189 on host)
docker run --name smartgallery-main \
  -v /your/host/output:/mnt/output \
  -v /your/host/input:/mnt/input \
  -v /your/host/SmartGallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e BASE_INPUT_PATH=/mnt/input \
  -e BASE_SMARTGALLERY_PATH=/mnt/SmartGallery \
  -e WANTED_UID=`id -u` \
  -e WANTED_GID=`id -g` \
  -e CLI_ARGS="--admin-pass yourpassword --force-login" \
  -p 8189:8189 \
  mmartial/smart-comfyui-gallery

# Exhibition container (port 8190 on host)
docker run --name smartgallery-exhibition \
  -v /your/host/output:/mnt/output \
  -v /your/host/input:/mnt/input \
  -v /your/host/SmartGallery:/mnt/SmartGallery \
  -e BASE_OUTPUT_PATH=/mnt/output \
  -e BASE_INPUT_PATH=/mnt/input \
  -e BASE_SMARTGALLERY_PATH=/mnt/SmartGallery \
  -e WANTED_UID=`id -u` \
  -e WANTED_GID=`id -g` \
  -e CLI_ARGS="--exhibition --admin-pass yourpassword --blind-rating" \
  -p 8190:8189 \
  mmartial/smart-comfyui-gallery
```

Docker port mapping: the syntax is `HOST:CONTAINER`. Both containers run internally on port 8189, but are reachable at `:8189` and `:8190` respectively on your machine. They share the same data volumes, so files, tags, and collections are visible in both.

</details>

---

### 2.3 FFmpeg Integration

FFmpeg is optional but strongly recommended. Without it, video files will not generate thumbnails, the storyboard feature will not work, and formats like ProRes, MKV, AVI, and MOV will not transcode for browser playback.

If you only work with images, you can skip this entirely.

<details>
<summary><strong>What FFmpeg enables</strong></summary>

-   Thumbnail generation for MP4, WEBM, and all transcoded formats
-   Video Storyboard: the 11-frame grid preview (`E` key in the Lightbox)
-   Interactive Audio Waveforms (`GENERATE_WAVEFORMS=true`)
-   On-the-fly transcoding of ProRes, MKV, AVI, MOV to a browser-compatible format
-   Workflow extraction from video files generated by ComfyUI

SmartGallery uses `ffprobe` (included in every FFmpeg installation) to read video metadata, and `ffmpeg` itself for transcoding. You point SmartGallery to the `ffprobe` binary via the `FFPROBE_MANUAL_PATH` variable in your launch script.

</details>

<details>
<summary><strong>Install FFmpeg on Windows</strong></summary>

1.  Download a pre-built release from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) (the "Windows builds" section, for example from gyan.dev or BtbN).
2.  Extract the archive to a permanent location, for example `C:/ffmpeg`.
3.  The binaries you need are inside the `bin` folder: `ffmpeg.exe` and `ffprobe.exe`.
4.  In your `run_smartgallery.bat`, set:

```bat
set "FFPROBE_MANUAL_PATH=C:/ffmpeg/bin/ffprobe.exe"
```

You do not need to add FFmpeg to your system PATH. SmartGallery only needs the full path to `ffprobe.exe`.

</details>

<details>
<summary><strong>Install FFmpeg on macOS</strong></summary>

The easiest way is Homebrew:

```bash
brew install ffmpeg
```

After installation, ffprobe will typically be at `/opt/homebrew/bin/ffprobe` (Apple Silicon) or `/usr/local/bin/ffprobe` (Intel). Set it in your launch script:

```bash
export FFPROBE_MANUAL_PATH="/opt/homebrew/bin/ffprobe"
```

To confirm the path on your machine: `which ffprobe`

</details>

<details>
<summary><strong>Install FFmpeg on Linux</strong></summary>

On Debian/Ubuntu:

```bash
sudo apt update && sudo apt install ffmpeg
```

On Fedora/RHEL:

```bash
sudo dnf install ffmpeg
```

ffprobe is installed alongside ffmpeg. The default path is usually `/usr/bin/ffprobe`. Set it in your launch script:

```bash
export FFPROBE_MANUAL_PATH="/usr/bin/ffprobe"
```

To confirm: `which ffprobe`

</details>

<details>
<summary><strong>Docker: nothing to install</strong></summary>

The official Docker image (`mmartial/smart-comfyui-gallery`) already includes FFmpeg and ffprobe. Video transcoding, thumbnail generation, and storyboard creation all work out of the box with no additional configuration.

</details>

---

## 3. INTERFACE WALKTHROUGH

### 3.1 The Main Workspace (Creator Hub)

**Access:** `http://localhost:8189/galleryout`

![SmartGallery Main Workspace — grid view with batch selection bar active](assets/hero_main_workspace.png)
<br><em>The Main Workspace: grid view with sidebar navigation, batch selection bar at the bottom, and Workflow badges on each card. Fully responsive and functional on mobile devices.</em>
<br>
<div align="center">
  <table>
    <tr>
      <td align="center"><img src="assets/mobile3.png" height="460" alt="Mobile View"></td>
      <td align="center"><img src="assets/mobile-node-summary.png" height="460" alt="Node Summary"></td>
    </tr>
    <tr>
      <td align="center"><em>Mobile interface</em></td>
      <td align="center"><em>Node Summary: full workflow recall at a glance</em></td>
    </tr>
  </table>
</div>

---

### 3.1.1 Sidebar Navigation

The left sidebar contains three main tabs:  

![Sidebar with three tabs: Folders, Collections, Status](assets/sidebar_tabs.png)

*The three-tab sidebar: Folders (directory tree), Collections (virtual albums), Status (browse by pipeline state).*

-   **📁 Folders (Physical):** Browse actual folders on your hard drive.
    -   `+` — Create a subfolder
    -   🔗 — Mount an external drive or network folder via symlink
    -   `⋮` — Rename, Delete, Unmount, or force AI Indexing on a folder
-   **📚 Collections (Virtual):** Virtual albums grouping files from different folders without moving them on disk. Collections with attached **Collection Notes** feature a distinct **yellow accent**.
-   **🏷 Status:** Browse all files by their color-coded pipeline status across every folder at once.
-   **👤 User Profile (bottom):** Shows your current role. Click 👥 to open User Management, `×` to log out.

---

### 3.1.2 Top Toolbar & Global Actions

![Top toolbar with Filters, Upload, Rescan, Refresh buttons and sort options](assets/top_main_toolbar.png)

*The top toolbar: action buttons on the left, file count and sort options on the right.*

-   **🛠️ Tools:** Opens tools menu including **🧬 Smart Clustering**, Remix Workflow, and ComfyUI launcher.
-   **⚙️ Options:** Global settings — thumbnail size (Normal 320px / Compact 220px), video autoplay, and **🧬 Cluster Badges** toggle.
-   **? Shortcuts:** Full keyboard shortcut list for the current interface.
-   **⚡ Focus (Q):** Toggle Focus Mode.
-   **🕵️ My Ratings:** Quickly toggle between the global average rating view and your personal, blind rating view.
-   **📤 Upload:** Magic Upload via drag & drop. ComfyUI metadata is extracted automatically.
-   **♻️ Rescan:** Forces a background disk scan for externally added or modified files.

#### Auto-Watch & Refresh

![Auto-Watch popup with Enable Watch toggle and 10 second interval](assets/auto_watch.png)

*Auto-Watch: click the `⋮` next to Refresh, enable the toggle and set an interval. A pulsing red dot confirms it's active.*

-   **Manual Refresh:** Click the 🔃 icon to instantly scan for new files.
-   **Auto-Watch (`⋮`):** Silently scans in the background and injects new ComfyUI files into the grid **without a page reload**. Enable it while ComfyUI is generating to cull in real time.

---

### 3.1.3 Search, Filters & Fuzzy Auto-Suggest

![Advanced search panel showing all filter options](assets/filter_panel.png)

*The Filters panel: search scope, multi-keyword fields, extensions, date range, and options.*

Click **🔍 Filters** to open the advanced search engine. Filters work across both physical Folders and virtual Collections.

**Search Scope:** Current Folder or Global (All Folders). Toggle *Include Subfolders* for recursive search.

**Fuzzy Search & Live Auto-Suggest:**
The **⚙️ Workflow Files** input features alphanumeric normalization (e.g. `wan 2.2` seamlessly matches `wan2.2_i2v_high.safetensors`). As you type, a two-line autocomplete dropdown displays clean filenames alongside folder paths. Native `difflib` string matching provides "Did You Mean?" suggestions when queries yield zero or low results.

**Multi-Keyword Fields** (Workflow Files, Prompt Keywords, Comment Keywords):

| Syntax | Logic | Example |
|---|---|---|
| `,` comma | **AND** — must contain both | `red, car` |
| `;` semicolon | **OR** — contains either | `cat; dog` |
| `!` exclamation | **NOT** — exclude keyword | `!lora`, `!cat` |
| `" "` quotes | **Exact Match** | `"man"` (won't match `woman`) |

*💡 **Pro Tip**: You can combine Exact Matches and Exclusions! Use `!"bad anatomy"` to completely exclude a specific phrase from your search results.*

**Extensions & Prefixes:** Filter by file type or filename prefix.

**Date Range:** Filter by generation/upload date.

**Options:** Favorites Only · No Workflow. 

**Advanced Ratings Filtering:**
Filter feedback by **Star Rating Ranges** (e.g., select '4-5 stars' and '1-2 stars' simultaneously) and by **Specific Raters** to isolate feedback from key clients or team members.

#### Sort Buttons

Sort by **Date** (📅), **Name** (🔤), **Rating** (⭐), or **Comments** (💬). 

Sorting criteria for Ratings and Comments feature sub-menus to effortlessly toggle between "Highest/Lowest Rated", **"Not Rated"**, "Most/Least Discussed", **"Uncommented"**, or **"Newest Comments"**.

---

### 3.1.4 OmniQuery – AI-Powered SQL Explorer

**If you can describe it, you can find it.**  
Click the **⚡ OmniQuery** icon in the gallery toolbar to open the AI-Assisted SQL Explorer. Ask questions in natural language, let an LLM generate read-only SQLite queries, and execute them safely.

👉 **[Read the full OmniQuery Guide](docs/OmniQuery.md)** for detailed instructions and examples.

---

### 3.1.5 Gallery Grid & Focus Mode

**Persistent Metadata Hover Bar:** 
Hovering over any image reveals a status bar at the bottom of the screen with exact dimensions, calculated megapixels, file size, and current rating status without needing to open the Lightbox.

**Cluster Badges Toggle:** Enable `🧬 Cluster Badges` in Settings to replace standard green workflow badges on thumbnails with interactive architecture and prompt `#HASH` badges.

**Standard Grid View (Focus Mode OFF):** Hovering reveals the quick-action card with Node Summary (📝), Favorite (⭐), Download (💾), Delete (🗑️). Clicking opens the Lightbox.

![Standard Grid View — Focus Mode OFF, showing hover cards with action buttons](assets/focus_mode_off.png)

**Focus Mode ON (`Q`):** Hides all UI chrome, metadata, titles, and quick-action cards. A golden star marks favorites. Selected items show a massive **fuchsia border**. Use keyboard arrows to navigate. Click or press `V`/`Enter` to open the Lightbox.

![Focus Mode ON — clean grid with fuchsia selection borders](assets/focus_mode_active.png)

> **Power User Tip:** Enable Auto-Watch, activate Focus Mode with `Q`, then use `←→` arrows + `Del`/`F`/`X` to blaze through a batch while it's still generating. Press `I` on any item to view its exact file path, real symlink source target, and node pipeline.

---

### 3.1.6 Batch Selection Bar

Click the checkmark `✓` on any image (or `Space`/`X` in Focus Mode) to select it. The floating **Selection Bar** appears at the bottom.

![Batch selection bar with context menu expanded showing all batch actions](assets/batch_selection_bar.png)

| Action | Shortcut | Description |
|---|---|---|
| ✕ Deselect All | `Esc` | Clears the selection |
| ✅ Select All | `Ctrl+A` | Selects all visible files |
| ↔️ Range Select | — | Appears when exactly 2 files selected; selects all between them |
| ⭐ Add Favorite | — | Marks all selected as favorites |
| 🏷 Set Status | `Y` | Apply a pipeline color tag to the batch |
| 📚 Add/Remove Collections | `A` | Add or remove batch from virtual albums |
| ⚖️ Compare Selected | — | Split-screen comparison (exactly 2 files required) |
| 🏅 Rate Selected | `Shift+R` | Apply 1–5 stars to multiple files at once |
| 📁 Move / Copy | `M` | Transfer files to another physical folder |
| 📦 Download as Zip | `Z` | Package selection into a downloadable `.zip` |
| ☆ Remove Favorite | — | Remove the favorite flag from the batch |
| 🗑️ Delete Selected | `Del` | Permanently delete selected files |

---

## 3.2 Advanced Media Inspection

### 3.2.1 The Lightbox (Media Viewer)

Open the full-screen Lightbox with `V` or `Enter`.

![Lightbox open with Node Summary panel on the left, image in center, Ratings & Comments panel on the right](assets/lightbox_node_summary.png)

**Enhanced Player Controls:** The custom video/audio player supports Spacebar to Play/Pause, arrow keys to seek by 5 seconds, and full volume/mute controls (`M`).

**Dynamic Audio Waveforms:** Real-time visual waveforms (🌊) with an amplitude slider to adjust height without re-rendering media.

**Toolbar Buttons:**

| Button | Key | Description |
|---|---|---|
| / MENU | `/` | Touch-friendly list of all commands |
| − / + | `-` / `+` | Zoom out / Zoom in |
| 🔄 Rotate | `T` | Rotate 90° (non-destructive) |
| 💾 Download | `S` | Download original file |
| 🛡 Clean Export | `Shift+W` | Download with all metadata stripped (prompts, nodes, EXIF) |
| ✏️ Rename | `R` | Rename file on disk |
| 📋 Asset Details | `I` | Open Full Asset Details Panel (2 tabs: Overview & Architecture) |
| 🧬 Clusterize | `Shift+C` | Open Smart Asset Clustering modal for this file |
| 📝 Node Summary | `N` | Open ComfyUI generation dashboard |
| ✦ Remix Workflow | `B` | Edit workflow parameters and queue new generations |
| ⭐💬 Ratings & Comments | `G` | Open side panel for ratings and messages |
| ⚙️ Workflow JSON | `W` | Download raw ComfyUI `.json` workflow |
| 📋 Copy JSON | `C` | Copy workflow to clipboard |
| 🎞 Storyboard | `E` | Generate 11-frame video overview |
| 📁 Move File | `M` | Open the Move File dialog |
| 👁 Hide Toolbar | `H` | "Clean View" — hides all chrome |
| ↗️ Open in New Tab | `O` | Full-resolution in a new browser tab |
| 🗑️ Delete | `Del` | Delete the file |
| × Exit | `Esc` | Return to Grid View |

---

### 3.2.2 Full Asset Details Panel (📋 / Shortcut <kbd>I</kbd>)

Press <kbd>I</kbd> on any image or click the **ⓘ** icon to open a high-density diagnostic panel featuring two organized tabs.

👉 **[Read the Full Asset Details Manual](docs/Asset_Info_Panel_manual.md)**

* **Tab 1: 📋 Overview & Paths:**
  * **Header Card:** Preview thumbnail/video, filename, file type badge, clickable `⚙️ Workflow` JSON download button, Favorite badge, and Workflow Status tag (`📍 Approved`, `📍 Review`, etc.).
  * **Metrics Grid:** Resolution with Megapixel density calculation (e.g. `1024x1024 (1 MP)`), file size, modified date, scan date, and video/audio duration.
  * **Folder Hierarchy:** Full directory breadcrumb chain (`📂 Main ➔ 📂 Projects ➔ 📂 CharacterRenders`).
  * **Physical Disk Path:** Absolute server path. If the folder is on an external drive, highlights the **🔗 Real Target** physical path.
  * **Collection Ancestry:** Complete parent-to-child hierarchy chains for every assigned Virtual Collection.
  * **Generation Metadata:** Formatted A1111 / WebUI Forge parameters with a one-click `📋 Copy` button.
* **Tab 2: 🧬 Architecture & Cluster:**
  * **Cluster Quick Stats:** Counts of assets in your library sharing the same Architecture (`🧬 #HASH`) or Prompt (`💬 #HASH`).
  * **One-Click Clusterize:** `🚀 Clusterize Gallery by this Reference Asset` button to enter Cluster Mode immediately.
  * **Node Pipeline Architecture:** Sequential color-coded chips showing node execution flow (`[CheckpointLoaderSimple] ➔ [CLIPTextEncode] ➔ [KSampler] ➔ [VAEDecode]`).
  * **Models Loaded:** Itemized list of `.safetensors`, `.ckpt`, `.lora`, and `.gguf` files.
  * **Prompt Text:** Positive prompt string with a `📋 Copy` button.

---

### 3.2.3 Smart Asset Clustering & Inspector (🧬 / Shortcut <kbd>Shift</kbd>+<kbd>C</kbd>)

Smart Asset Clustering organizes your gallery into visual groups based on how your images were created, letting you group and compare images sharing either the same workflow pipeline or the same prompt text.

👉 **[Read the Smart Asset Clustering Manual](docs/Smart_Asset_Clustering_manual.md)**

* **The 2 Clustering Modes:**
  1. **By Architecture (`workflow`):** Groups images created with the exact same workflow setup (node structure + model files), ignoring random seeds, steps, CFG, or prompt text changes.
  2. **By Prompt Text (`prompt`):** Groups images sharing the exact same positive prompt across different models, Flux/SDXL workflows, or settings.
* **Interactive Hash Inspector Modal:**
  Clicking any `#HASH` badge on a thumbnail card opens an **Inspector Panel** showing you:
  * **The Visual Pipeline:** Sequence of color-coded chips (`CheckpointLoader ➔ LoraLoader ➔ KSampler ➔ VAEDecode`).
  * **Models Loaded:** Exact checkpoint and LoRA model files used.
  * **Asset Prompt:** Prompt text with a one-click **📋 Copy** button.
  * **Cluster Stats:** Total matching assets in your library.
  * **One-Click Launch:** A **`🚀 Clusterize Gallery`** button pre-targeted on that asset.
* **Sub-Badges:** When clustering by Prompt, badges display both the primary Prompt badge (`💬 #PROMPT`) and secondary Architecture variant badge (`🧬 #ARCH`).

---

### 3.2.4 ComfyUI Node Summary (📝 / Shortcut <kbd>N</kbd>)

Press `N` on any image to open the Node Summary.

<table width="100%">
  <tr>
    <td align="center" width="50%" valign="top">
      <img src="assets/improved-node-summary.png" height="350"><br>
      <em>Node Summary dashboard: positive prompt with one-click Copy, and all generation parameters at a glance.</em>
    </td>
    <td align="center" width="50%" valign="top">
      <img src="assets/raw_nodes.png" height="350"><br>
      <em>Raw Node List: every single node in the ComfyUI graph with all parameters.</em>
    </td>
  </tr>
</table>

- **Positive & Negative Prompts** — with one-click Copy buttons
- **Generation Parameters** — Seed (with copy button), Steps, CFG, Sampler, Scheduler, Resolution
- **Active LoRAs** — all LoRAs used and their weights
- **Source Media (Inputs)** — downloadable source files for Image2Image, ControlNet, or Video workflows
- **Raw Node List** — complete scrollable list of every node in the workflow graph

---

### 3.2.5 Remix Workflow & The { } Nodepad (✦ / Shortcut <kbd>B</kbd>)

Select an image or video in your gallery and press <kbd>B</kbd> to open the Remix Engine.

![Remix Overlay with press B activation](assets/press_b.png)

#### 1️⃣ Simple Tweaks: 📝 Auto-Form
Scans embedded workflow and exposes the most important editable parameters (Prompts, Seeds, Steps, Denoise, Dimensions).

#### 2️⃣ Build Your Dashboard: 🛠️ My Panel
Click the **📌 Pin icon** next to inputs in the Auto-Form to build a clean dashboard populated *exclusively* with your pinned fields.

![My Panel](assets/my_panel.png)

#### 3️⃣ Pro Control: { } The Nodepad
An advanced JSON editor for power users. Interrogates your live ComfyUI server for node definitions, provides visual UI injectors for inputs, and formats JSON automatically.

![Nodepad](assets/dictionary_lookup.png)

#### Video Companion PNGs
If a video file lacks API workflow data, click **🔍 Find companion PNG**. SmartGallery automatically locates the VHS sidecar image, extracts the hidden data, and enables direct queuing.

![Companion PNG Warning](assets/companion_png.png)

---

### 3.2.6 LoRA Synergy™

Offline LoRA matchmaker built into **Remix Workflow → Nodepad**. Scans `.safetensors` headers to guarantee checkpoint architecture compatibility (SD1.5, SDXL, Flux), surfaces trigger words, and auto-wires `MODEL` and `CLIP` nodes.

👉 **[Read the full LoRA Synergy Guide](docs/LORA_SYNERGY.md)** for detailed instructions.

---

### 3.2.7 Compare Mode  

Select **2 files** → `⋮` in Selection Bar → **Compare Selected**.

![Compare Mode with A/B slider on a mandrill image, and Parameter Differences table below](assets/compare2.png)

- **Visual Slider:** Drag central handle to compare. Videos synchronize automatically.
- **Parameter Differences (`I`):** Table showing only changed parameters.

---

### 3.2.8 Video Storyboard (🎞)

Press `E` in the Lightbox on any video to generate **11 perfectly spaced frames** in a grid to evaluate motion consistency.

![Video Storyboard showing 11 evenly-spaced frames of an elephant video](assets/storyboard.png)

---

## 3.3 Digital Asset Management (DAM) & Communication

### 3.3.1 Virtual Collections & Sharing

Virtual albums grouping files across physical folders without duplicating disk space. Supports nested parent/child tree hierarchies.

![Collections sidebar tab with context menu open, and Manage Collections modal on the right](assets/collections.jpg)

- **Create:** Collections tab → `+` → name it → choose Public, Private, or select specific users.
- **Add files:** Select files → click 📚 in Selection Bar or press `A`.
- **Untag (`U`):** Remove files from current collection.

---

### 3.3.2 Collection Notes & Production Briefs (📝)

Attach rich documentation to Virtual Collections.

👉 **[Read the Collection Notes Manual](docs/Collection_Notes_manual.md)**

* **Simple Creation Workflow:** Attach a brief to any collection by clicking the **⋮** menu next to its name in the sidebar and selecting **📤 Upload Note** to upload `.txt` or `.md` files.
* **Visual Yellow Accent:** Collections containing active notes are immediately highlighted with a distinct **yellow accent** across the sidebar and breadcrumbs.
* **Top Header Access Button:** When viewing a collection with notes, a prominent **`📝 Collection Notes`** button automatically appears in the top toolbar header for instant one-click access.
* **Rich Markdown Rendering:** Full native rendering of Markdown documentation (headers, lists, tables, code fences, task lists, and formatting).
* **Multi-Note Reader & Feedback:** View and switch between multiple notes via tabs, download notes, or open them in the details panel to leave ratings and public/private comments just like any media asset.

---

### 3.3.3 Pipeline Status Tags

Press keys `1`–`5` on any item or selection:
* `1` Approved (Green) · `2` Rejected (Red) · `3` Review (Yellow) · `4` Select (Purple) · `5` To Edit (Blue) · `0` Clear

![Thumbnails with color status bars on the left edge](assets/status_color_vertical_strips.png)

---

### 3.3.4 Ratings & Comments (⭐💬)

Press `G` on any image to open Ratings & Comments.

![Ratings & Comments panel showing global rating 3.5, your vote, collections & status, comment count](assets/main_rating_comments_panel.png)

- **Ratings:** Click ⭐ stars (1–5) to vote. Click 👁️ **Details** to see voter breakdown. Use `--blind-rating` to hide averages and prevent voting bias.
- **Review queue:** Items you have not rated stay first. After your rating is saved, that item moves behind the unrated group without changing the selected sort order inside either group; clearing your rating returns it to the unrated group.
- **Comments:** Threaded discussions with visibility controls (🌐 Public, 🔒 Internal/Staff Only, 👤 Direct Message).

---

## 3.4 User Management & Access Control

![User Management panel with role table and user creation form](assets/user_management_modal.png)

Click 👥 in the sidebar footer to manage users. Assign roles (ADMIN, MANAGER, STAFF, FRIEND, USER/CUSTOMER, GUEST) and monitor user activity via the **Last Login timestamp**.

---

## 3.5 The Exhibition Portal (Client Hub)

**Access:** Launch with `--exhibition` (port 8190).

![Exhibition Portal grid showing curated collections with ratings and comment counts on each card](assets/hero_exhibition_portal.png)

- **Strictly Read-Only:** Guests can vote and comment; they cannot delete, move, or alter files.
- **Metadata Stripped:** Workflows, prompts, and EXIF are completely hidden.
- **Dedicated Exhibition Filter Panel:** Allows clients to filter media by smart filename queries, file extensions, and date ranges.
- **Embedded Audio Player:** List View includes inline audio playback controls.
- **Client Briefing:** Clients can open **Collection Notes**, read project specs, and leave ratings/comments directly on production briefs.

---

## 4. ADVANCED TOPICS & REFERENCE

### 4.1 Sharing Online

Expose Exhibition (port 8190) remotely using Nginx, Apache, or tunnels like ngrok (`ngrok http 8190`) or Cloudflare Tunnel.

---

### 4.2 Keyboard Shortcuts Reference

<details>
<summary><strong>Main Interface Shortcuts</strong></summary>

**Global App Controls**

| Shortcut | Action |
|---|---|
| `?` | Open Shortcuts Help panel |
| `Q` | Toggle Focus Mode |
| `T` | Scroll to Top and open Search/Filters |
| `P` | Toggle Video Autoplay |
| `L` | Refresh view |
| `K` | Open Rescan Folder modal |
| `Ctrl+A` / `Cmd+A` | Select all files |
| `Esc` | Close modal / deselect all |
| `Home` / `End` | Scroll to top / bottom |
| `PgUp` / `PgDn` | Scroll page by page |

**Grid & Lightbox Actions**

| Shortcut | Action |
|---|---|
| `I` | **Open Full Asset Details Panel (2 tabs: Overview & Paths / Architecture & Cluster)** |
| `Shift+C` | **Open Smart Asset Clustering modal / cluster by reference asset** |
| `V` / `Enter` | Open Lightbox |
| `N` | View Node Summary |
| `B` | Open Remix Workflow modal |
| `F` | Toggle Favorite |
| `A` | Add to / remove from Virtual Collection |
| `Y` | Set Status Tag |
| `W` | Download Workflow JSON |
| `Shift+W` | Clean Export: download stripped of all metadata |
| `C` | Copy Workflow JSON |
| `S` | Download media file |
| `R` | Rename file |
| `E` | Generate Video Storyboard |
| `G` | Open Ratings & Comments panel |
| `Shift+R` | Batch Rate modal |
| `1`–`5` / `0` | Assign / Clear Status Tag |
| `Del` | Delete file |

**Selection & Batch Actions**

| Shortcut | Action |
|---|---|
| `Click` | Focus OFF: opens Lightbox. Focus ON: selects item |
| `Ctrl+Click` | Add single item to selection |
| `Shift+Click` | Select range between two files |
| `A` | Add / remove selection to/from Collection |
| `Y` | Open Status Tagging modal |
| `M` | Move selected files to another folder |
| `U` | Remove selection from current Virtual Collection |
| `Z` | Download selection as ZIP |
| `Shift+R` | Batch Rate modal for selected files |
| `Del` | Delete selection |
| `Esc` | Deselect all |

</details>

<details>
<summary><strong>Exhibition Portal Shortcuts</strong></summary>

| Shortcut | Action |
|---|---|
| `←` `↑` `→` `↓` | Move keyboard focus |
| `Enter` / `V` | Open Lightbox / Theater |
| `1` to `5` / `0` | Rate media 1–5 stars / clear rating |
| `H` | Toggle toolbar (clean view) |
| `G` | Toggle Ratings & Comments panel |
| `B` | Toggle Admin Blind Rating Override |
| `T` | Rotate media 90° |
| `+` / `-` | Zoom in / out |
| `S` | Download media |
| `Esc` | Close Lightbox |

</details>

---

### 4.3 Experimental Features

The [`/experiments`](experiments/) folder contains beta versions and hotfixes under active development.

---

### 4.4 Philosophy, Feedback & License

Local-first. Privacy-first. Minimal dependencies. Cross-platform. MIT License.

---

> ### 🎞️ **Presentation Video**
>
> <div align="center">
>   <a href="https://smartgallerydam.com/smartgallerydam-2.13.mp4">
>     <img src="assets/video-cover_2.13.png" width="550" alt="Watch the presentation video">
>   </a>
>   <br>
>   <em>(Click on the image to play the video)</em>
> </div>

---

<p align="center">
  <a href="https://smartgallerydam.com"><strong>smartgallerydam.com</strong></a> · full documentation, wiki and feature reference
  <br><br>
  <a href="https://smartgallerydam.com">
    <img src="assets/logo.png" width="120" alt="SmartGallery DAM logo">
  </a>
  <br><br>
  <em>Made for the ComfyUI community and every digital creator who takes their work seriously.</em>
</p>
