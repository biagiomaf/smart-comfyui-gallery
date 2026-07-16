## OmniQuery – AI‑Powered SQL Explorer

**OmniQuery** is a powerful extension inside SmartGallery DAM that gives you full SQL access to your media library, assisted by AI.  
It’s designed for power users who need to ask **complex, cross‑table questions** that go beyond the standard filter panel.

---

### Why OmniQuery?

The built‑in filter panel is great for everyday searches: by date, rating, collection, etc.  
But sometimes you need queries like:

> *“Show me all images that have never been rated and that belong to collections shared with user #3”*  
> *“Find videos longer than 2 minutes that have at least 3 comments mentioning ‘review’”*

These kinds of questions require joining multiple tables and applying logic that no simple form can express.  
OmniQuery **bridges this gap** by letting you use natural language to generate the perfect SQL query – with the help of your favourite AI assistant (ChatGPT, Gemini, Claude, DeepSeek…).

---

### How It Works

1. **Prepare a Prompt** – OmniQuery automatically builds a detailed prompt containing the full database schema, rules, and your request in plain English.  
2. **Copy & Ask an LLM** – Copy that prompt to an AI assistant and let it write the SQL for you.  
3. **Paste & Run** – Paste the SQL back into OmniQuery, preview the results, and execute the query.  
The results replace the current gallery view, and you can browse, sort, or download just like any other folder.

Only `SELECT` statements are allowed – your data is never at risk.

---

### Interface Overview

The OmniQuery window is divided into two main panels:

| Left Panel | Right Panel |
|------------|-------------|
| **Prompt Editor** – Here you write (or edit) the natural language request that will be sent to the AI. A factory template is loaded automatically and can be customised. | **SQL Input** – Paste the SQL returned by the AI. Syntax highlighting and smart paste handling prevent formatting issues. |
| **Schema Reference** (collapsible) – A handy list of all available tables and columns so you know exactly what data you can query. | **Action Buttons** – Run the query, preview first, or save/load your favourite SQL snippets. |

Both text areas can be maximised with the **⛶** button for a distraction‑free editing experience.

---

### Steps to Use

1. **Open OmniQuery** – Click the ⚡ icon in the gallery toolbar (or use the keyboard shortcut if configured).  
2. **Write your request** in the left panel.  
   Example: *“List all photos with an average rating above 4 and that are inside a collection named ‘Holidays’”*.  
3. **Copy the prompt** – Click **📋 Copy** (or select all and copy manually).  
4. **Paste it into your AI assistant** (ChatGPT, Gemini, Claude, DeepSeek…). It will return a `SELECT` statement.  
5. **Paste the SQL** back into the right panel (use the **📋 Paste** button or Ctrl+V).  
6. **Preview** (optional) – Click **🔍 Preview** to see a sample of the first rows without leaving the page.  
7. **Run** – Click **🚀 Run Query**. The gallery will reload showing only the matching files.

---

### Saving and Managing Queries / Prompts

Both your prompts and SQL queries can be saved for later reuse:

- **💾 Save** – Give your query/prompt a name and an optional description.  
- **📂 Load** – Browse a list of all saved items. You can rename or delete them from the same view.  
- **🔄 Factory** – Reset the prompt to the original template at any time.  
- **Clear** – Start with an empty prompt or query.

Everything is stored on the server, so your saved items follow you across devices.

---

### Security

OmniQuery enforces **read‑only access** at the database level.  
Only `SELECT` statements are permitted; any attempt to use `UPDATE`, `DELETE`, `INSERT`, or other modifying commands is rejected by the server.  
You can safely let the AI generate any query – your files and metadata remain untouched.

---

### Tips & Tricks

- **Order matters** – If your query includes `ORDER BY`, the usual UI sort buttons are disabled to respect your custom order.  
- **Session persistence** – Your last prompt and SQL are saved in the browser’s local storage, so you can close the modal and come back without losing your work.  
- **Preview first** – Always use the Preview button to check how many results you’ll get and what columns are returned before running the full query.  
- **Combine with Collections** – You can create a dynamic collection from an OmniQuery result by using the bulk‑select tools after the search.  
- **Keyboard shortcuts** – Use `Escape` to close child modals (like help or saved lists), or press it again to close the entire OmniQuery window.

---

> **OmniQuery gives you the freedom to explore your media library like never before – with the intelligence of AI and the safety of read‑only SQL.**  
> If you can describe it, you can find it.