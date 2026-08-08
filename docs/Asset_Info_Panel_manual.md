# 📋 Asset Info Panel (`I` Key) — User Manual
**SmartGallery DAM for ComfyUI**

Welcome to the official user manual for the **Asset Info Panel** (Full File Details). This guide explains how to use the instant inspection panel to review technical attributes, physical disk locations, virtual collection hierarchies, node pipelines, and generation metadata in your main workspace.

---

## 1. What is the Asset Info Panel?

The **Asset Info Panel** is a 360-degree diagnostic tool available in the SmartGallery main workspace. 

By simply pressing the **`I`** key on your keyboard while hovering or highlighting any asset, you can inspect comprehensive metadata, physical disk paths, collection lineages, and ComfyUI workflow structures without interrupting your creative workflow or leaving your current view.

---

## 2. Opening & Navigating the Panel

### How to Trigger the Panel:
* **Keyboard Shortcut**: Press **`I`** or **`i`** on your keyboard when an item is hovered, focused, or selected in the **Grid View**, **List View**, **Lightbox**, or **Cluster Mode**.
* **Card Info Button**: Click the small **`i`** icon located on any image/video thumbnail card.
* **Lightbox Title Area**: Click the **`ⓘ`** icon next to the filename in the top Lightbox bar.

### How to Close the Panel:
* Press the **`ESC`** key on your keyboard.
* Or click the **`×`** close button in the top-right corner of the modal window.

---

## 3. Tab 1: 📋 Overview & Paths

The **Overview & Paths** tab aggregates essential file attributes, physical locations, collection memberships, and embedded generation metadata.

```
+-------------------------------------------------------------+
| 📋 Full Asset Details                                    x  |
+-------------------------------------------------------------+
| [ 📋 Overview & Paths ]   [ 🧬 Architecture & Cluster ]     |
|-------------------------------------------------------------|
| +----+  render_final_0042.png                                |
| |    |  [image] [⚙️ Workflow] [⭐ Favorite] [📍 Approved]   |
| +----+                                                      |
| 📐 1024x1024 (1 MP) | 💾 3.2 MB | 📅 10/08/2026 14:30        |
|-------------------------------------------------------------|
| 📁 Folder Tree: Main ➔ Projects ➔ CharacterRenders          |
| 📍 Disk Path: C:/ComfyUI/output/Projects/render_final.png   |
| 📚 Collections: ConceptArt ➔ Season1 ➔ Cyberpunk           |
|-------------------------------------------------------------|
| 🖼️ Generation Metadata (A1111 / WebUI Forge)               |
| "Steps: 30, Sampler: Euler a, CFG scale: 7, Seed: 42..."   |
|                                                [ 📋 Copy ]  |
+-------------------------------------------------------------+
```

### Key Sections:

1. **Header Preview & Status Badges**:
   * **Thumbnail Preview**: Displays a visual thumbnail or video preview.
   * **File Badges**: Indicates file type (`image`, `video`, etc.), Workflow availability (`⚙️ Workflow`), Favorite status, and DAM Workflow Status tag (`📍 Approved`, `📍 Review`, `📍 To Edit`, etc.).

2. **Metrics Grid**:
   * **Dimensions & Megapixels**: Displays resolution along with calculated Megapixel density (e.g., `1024x1024 (1 MP)` or `3840x2160 (8.3 MP)`).
   * **File Size & Dates**: Shows exact file size in MB/GB, file modification date, and system scan timestamps.

3. **Folder Tree Location & Physical Disk Path**:
   * **Folder Tree Breadcrumb**: Displays the exact folder hierarchy leading to the asset (`📂 Main ➔ 📂 Projects ➔ 📂 CharacterRenders`).
   * **Physical Disk Path**: Displays the absolute server disk path in monospace format.
   * **🔗 Real Target Resolution**: If the file resides on a linked external drive (Mount Point or Symlink), it explicitly highlights the **Real Target** drive location on your machine.

4. **Collections & Sub-Collections Ancestry**:
   * Displays all Virtual Collections containing this file.
   * Preserves full parent-to-child hierarchy chains (e.g., `📚 ConceptArt ➔ 📚 Characters ➔ 📚 Cyberpunk`).

5. **Generation Metadata (WebUI Forge / A1111)**:
   * If the file contains embedded WebUI Forge or Automatic1111 generation text, SmartGallery automatically formats the positive/negative prompts, seeds, samplers, and steps into a clean card with a **`📋 Copy`** button.

---

## 4. Tab 2: 🧬 Architecture & Cluster

The **Architecture & Cluster** tab delivers deep technical analysis of ComfyUI workflow structures and model dependencies.

```
+-------------------------------------------------------------+
|  Cluster Metrics Summary:                                   |
|  [ 🧬 #A1F3E ]                      [ 💬 #C89B1 ]           |
|  14 Assets with Architecture        3 Assets with Prompt    |
+-------------------------------------------------------------+
|  [ 🚀 Clusterize Gallery by this Reference Asset ]          |
+-------------------------------------------------------------+
|  🧩 Node Pipeline Architecture:                             |
|  [CheckpointLoaderSimple] ➔ [CLIPTextEncode] ➔ [KSampler]   |
|  ➔ [VAEDecode] ➔ [SaveImage]                                |
+-------------------------------------------------------------+
|  📦 Checkpoints & Models Loaded:                            |
|  [📦 flux1-dev.safetensors]  [📦 RealismLora.safetensors]   |
+-------------------------------------------------------------+
|  💬 Asset Prompt Text:                          [ 📋 Copy ] |
|  "A cinematic portrait of a cybernetic engineer..."         |
+-------------------------------------------------------------+
```

### Key Sections:

1. **Cluster Quick Stats & One-Click Clusterize**:
   * Displays the short hash IDs for the asset's node graph architecture (`🧬 #HASH`) and positive prompt (`💬 #HASH`).
   * Displays total counts of other assets in your library sharing this exact architecture or prompt.
   * Click **`🚀 Clusterize Gallery by this Reference Asset`** to instantly enter Cluster Mode for the entire library using this asset as the baseline.

2. **Node Pipeline Architecture**:
   * Displays a visual sequence of color-coded chips representing the node execution chain (e.g., `[CheckpointLoaderSimple] ➔ [CLIPTextEncode] ➔ [KSampler] ➔ [VAEDecode]`).

3. **Checkpoints & Models Loaded**:
   * Itemizes all model files (`.safetensors`, `.ckpt`, `.lora`, `.gguf`, `.vae`) wired into this generation workflow.

4. **Asset Prompt Text**:
   * Displays the clean positive prompt text extracted from the workflow, along with a one-click **`📋 Copy`** button.

---

## 5. Practical Use Cases & Scenarios

### 📍 Scenario 1: Identifying Files on Linked External Drives
* **Goal**: You need to know if a file is stored on your local SSD or on a linked external drive (Mount Point).
* **How to do it**:
  1. Highlight the asset and press **`I`**.
  2. Look at the **Physical Disk Path** section in Tab 1.
  3. If the file is on a mounted drive, the panel displays **`🔗 Real Target:`** followed by the actual external drive path.

---

### 📦 Scenario 2: Auditing Checkpoints & LoRAs Used in a Render
* **Goal**: You rendered a great image weeks ago and need to know exactly which LoRA and Checkpoint files were used.
* **How to do it**:
  1. Press **`I`** on the image card or inside the Lightbox.
  2. Switch to **Tab 2 (🧬 Architecture & Cluster)**.
  3. Review the **Checkpoints & Models Loaded** list to see all model filenames.

---

### 🚀 Scenario 3: Finding All Images Made with the Same Workflow
* **Goal**: You want to see every image in your library generated with the same ComfyUI node pipeline.
* **How to do it**:
  1. Press **`I`** on the reference image.
  2. Switch to **Tab 2**.
  3. Click **`🚀 Clusterize Gallery by this Reference Asset`**.
* **Result**: SmartGallery closes the modal and filters your gallery grid to show only items matching that exact workflow structure.

---

### 📚 Scenario 4: Tracing Nested Collection Memberships
* **Goal**: You want to see all virtual collections and sub-collections an asset belongs to.
* **How to do it**:
  1. Press **`I`** on the asset.
  2. Scroll to **Collections & Sub-Collections** in Tab 1.
  3. View the full parent-to-child hierarchy chains (e.g., `📚 Season 1 ➔ 📚 Characters ➔ 📚 Protagonists`).

---

## 6. Summary Reference Table

| Feature / Action | Hotkey / Location | Description |
| :--- | :--- | :--- |
| **Open Panel** | **`I`** or **`i`** | Opens Info Panel for hovered, focused, or active file |
| **Close Panel** | **`ESC`** or **`×`** | Closes the Info Panel modal |
| **Switch Tabs** | Click Tab Header | Toggle between `📋 Overview & Paths` and `🧬 Architecture & Cluster` |
| **Copy Prompt** | Click `📋 Copy` | Copies WebUI metadata or ComfyUI prompt text to clipboard |
| **Launch Clustering** | Click `🚀 Clusterize` | Filters gallery grid by the asset's workflow architecture |

---
*SmartGallery DAM — Instant asset intelligence for digital creators.*
