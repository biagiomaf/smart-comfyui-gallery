# 📝 Collection Notes & Production Briefs — User Manual
**SmartGallery DAM for ComfyUI**

Welcome to the official user manual for **Collection Notes** (also known as **Production Briefs**). This guide will help you understand how to attach, manage, format, and review project documentation directly within your Virtual Collections, as well as how to collaborate with clients using Exhibition Mode.

---

## 1. What are Collection Notes?

In digital production pipelines, media assets rarely exist in isolation. Projects require creative briefs, style guides, client specifications, prompt engineering guidelines, and task checklists.

**Collection Notes** bridge the gap between media assets and project documentation. They allow you to attach Markdown (`.md`) or plain text (`.txt`) files directly to any Virtual Collection in SmartGallery. 

Instead of searching through external cloud folders for project instructions, team members and clients can view production briefs right alongside the media assets.

---

## 2. Supported Formatting (Markdown Engine)

Collection Notes features a native Markdown rendering engine. When you open a note, SmartGallery automatically formats your text into a clean document view.

### Supported Formatting Options:
* **Headers**: Use `# Header 1`, `## Header 2`, or `### Header 3` to structure sections.
* **Task Checklists**: Create interactive task lists using `- [ ] Pending Task` and `- [x] Completed Task`.
* **Bold & Italic**: Emphasize text using `**bold**` or `*italic*`.
* **Tables**: Structure data using standard table formatting (`| Column 1 | Column 2 |`).
* **Code Blocks**: Display technical prompts, JSON payloads, or code using triple backticks (```).
* **Blockquotes**: Add reference quotes or notes using `> Quote text`.

---

## 3. How to Attach & Manage Collection Notes (Step-by-Step)

### Step 1: Uploading a Note to a Collection
1. Open the **Collections** panel in the sidebar.
2. Locate the collection where you want to add documentation.
3. Click the context menu button (**⋮**) next to the collection name.
4. Select **📝 Add / Manage Notes**.
5. Choose or drag any `.md` or `.txt` file from your computer.
6. SmartGallery securely attaches the note file to the selected collection.

---

### Step 2: Reading Collection Notes
1. Open any Virtual Collection that has attached notes.
2. A gold button labeled **`📝 Collection Notes`** will appear in the top breadcrumb toolbar.
3. Click **`📝 Collection Notes`** to open the **Notes Reader Window**.
4. The document will display with full Markdown formatting.

---

### Step 3: Working with Multiple Notes (Tabbed View)
A single Virtual Collection can contain multiple notes (for example, a *Project Brief*, a *Style Guide*, and a *Client Feedback Log*).

* When a collection contains more than one note, a **tabbed selector bar** appears at the top of the Notes Reader window.
* Click any tab to switch instantly between different document files. Each tab displays the filename and creation timestamp.

---

### Step 4: Downloading and Deleting Notes
Inside the Notes Reader window:
* **Download**: Click **`💾 Download Note`** to download a local copy of the file.
* **Delete**: Click **`🗑️ Delete Note`** to permanently remove the note file from the collection and storage.

---

## 4. Interactive Ratings & Comments on Notes

SmartGallery treats Collection Notes as active media assets within your library. This allows team members and clients to rate and discuss project briefs in real time.

### How to Rate and Comment on a Note:
1. Open the Notes Reader window for your collection.
2. Click the **`⭐/💬 Ratings & Comments`** button at the bottom of the window.
3. The note file will open inside the **Theater / Lightbox View**.
4. From here, you can:
   * **Assign a 1-to-5 star rating** to evaluate the brief or specification.
   * **Post threaded comments** to ask questions, suggest changes, or log approvals.

---

## 5. Exhibition Mode & Client Collaboration

Collection Notes seamlessly extend into **Exhibition Mode**, transforming the client review portal into an interactive briefing hub.

### How Clients Interact with Notes in Exhibition Mode:
1. **Prominent Visibility**: When a client or guest opens an Exhibition-ready collection that contains notes, a prominent **`📝 Collection Notes`** button appears in the header bar.
2. **Reading Briefs**: Clients can click the button to read project specifications and guidelines directly inside the Exhibition Portal.
3. **Downloading Briefs**: Clients can click **`💾 Download Note`** to save local copies of guidelines or requirements.
4. **Client Feedback & Discussion**: Clients can click **`⭐/💬 Rate & Comment Note`** to open the brief in the Exhibition Lightbox, where they can give a star rating and leave comments on project specs in real time.

---

## 6. Practical Use Cases & Real-World Scenarios

### 📋 Scenario 1: Project Onboarding & Deliverable Checklists
* **Goal**: Onboard a new artist onto an ongoing character rendering series.
* **Workflow**:
  1. Create a note file named `Character_Series_Brief.md` with deliverable checklists (`- [ ] Concept`, `- [x] Model Render`) and moodboard descriptions.
  2. Upload the file to your "Cyberpunk Characters" Virtual Collection.
  3. When artists open the collection, they click **`📝 Collection Notes`** to review tasks and specs before starting work.

---

### 🎨 Scenario 2: Prompt Engineering & Style Guides
* **Goal**: Ensure all team members use consistent prompt parameters, negative prompts, and LoRA trigger words for a specific aesthetic.
* **Workflow**:
  1. Create a `Style_Guide.md` note containing approved positive/negative prompts and LoRA trigger words inside code blocks.
  2. Attach it to your production collection.
  3. Artists can open the brief, copy exact prompt strings, and paste them directly into ComfyUI.

---

### 🤝 Scenario 3: Client Approval Loop in Exhibition Mode
* **Goal**: Get client sign-off on project scope and style guidelines before rendering final high-resolution assets.
* **Workflow**:
  1. Attach `Client_Requirements_v2.md` to an Exhibition-ready collection.
  2. Share the collection with your client via Exhibition Mode.
  3. The client opens the collection, reads the brief, and uses the **`Rate & Comment Note`** feature to leave feedback or approve the specifications.

---

## 7. Visual Indicators Reference Summary

| Visual Indicator | Location | Meaning |
| :--- | :--- | :--- |
| **Bold Gold Text** | Sidebar Collections List | Indicates that this Virtual Collection contains active Collection Notes |
| **`📝 Collection Notes`** | Breadcrumb Toolbar | Clickable button to open the Notes Reader window for the active collection |
| **Document Tabs** | Notes Reader Header | Allows switching between multiple attached note files |
| **`⭐/💬 Ratings & Comments`** | Notes Reader Footer | Opens the note file in Lightbox mode for rating and threaded discussions |

---
*SmartGallery DAM — Seamlessly connecting media assets and production intelligence.*