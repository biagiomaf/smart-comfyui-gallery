// Version: 2.24.2 - October 03, 2026
/* Generation Metadata Inspector & UI Renderer
 * Anchored inspector with Alt+M Pinning, Desktop Lightbox Drag & Drop, Auto-avoidance & Mobile Docking.
 */
(() => {
    const panel = document.getElementById('generation-metadata-panel');
    const content = document.getElementById('generation-metadata-content');
    const name = document.getElementById('generation-metadata-name');
    const copyAll = document.getElementById('generation-copy-all');
    const pinBtn = document.getElementById('generation-metadata-pin');
    const pinStatus = document.getElementById('generation-metadata-pin-status');
    const pinText = document.getElementById('gm-pin-text');

    let enabled = false;
    try { enabled = localStorage.getItem('galleryGenerationMetadata') === 'true'; } catch (_) {}

    let pinnedId = null;
    let pinContext = location.pathname + location.search;

    let activeKey = null;
    let timer = null;
    let controller = null;
    let frame = null;
    let metadata = null;
    let retainedId = null;

    // Desktop Lightbox custom dragged position memory
    let lightboxCustomPos = null;
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };

    const cache = new Map();
    const settingsLabels = {
        cfg: 'CFG scale', steps: 'Steps', sampler: 'Sampler', scheduler: 'Scheduler',
        seed: 'Seed', width: 'Width', height: 'Height', denoise: 'Denoise',
        model_hash: 'Model hash', clip_skip: 'Clip skip', version: 'Version'
    };

    const present = v => v !== null && v !== undefined && v !== '';

    function element(tag, text, className) {
        const el = document.createElement(tag);
        if (text !== undefined) el.textContent = text;
        if (className) el.className = className;
        return el;
    }

    async function copy(text) {
        if (!text) return;
        if (typeof copyTextAndNotify === 'function') {
            copyTextAndNotify(text);
        } else {
            try {
                await navigator.clipboard.writeText(text);
                if (typeof showNotification === 'function') showNotification('📋 Copied to clipboard!', 'success');
            } catch (_) {
                const input = element('textarea');
                input.value = text;
                input.style.cssText = 'position:fixed;left:-9999px';
                document.body.appendChild(input);
                input.select();
                document.execCommand('copy');
                input.remove();
                if (typeof showNotification === 'function') showNotification('📋 Copied to clipboard!', 'success');
            }
        }
    }

    window.renderGenerationMetadataHTML = function(meta, message) {
        if (!meta) {
            return `<div style="text-align:center; color:var(--text-muted,#888); padding:16px;">${message || 'No supported generation metadata found.'}</div>`;
        }

        let html = '';
        html += `<div style="font-size:0.75rem; text-transform:uppercase; color:var(--favorite-color,#ffc107); font-weight:bold; margin-bottom:8px;">${meta.source || 'Generation parameters'}</div>`;

        // Checkpoint & LoRAs
        if (meta.model || (meta.loras && meta.loras.length > 0)) {
            html += `<div style="margin-bottom:10px;">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#aaa; font-weight:bold; margin-bottom:4px;">📦 Models & Resources</div>`;
            if (meta.model) {
                html += `
                <div class="gm-resource">
                    <span title="${meta.model}">${meta.model}</span>
                    <span class="gm-badge">Checkpoint</span>
                </div>`;
            }
            if (meta.loras && meta.loras.length > 0) {
                meta.loras.forEach(l => {
                    const val = present(l.value) ? `<span class="gm-badge">${l.value}</span>` : '';
                    html += `
                    <div class="gm-resource">
                        <span title="${l.name}">${l.name}</span>
                        <div style="display:flex; gap:4px; align-items:center;">
                            <span class="gm-badge">LoRA</span>
                            ${val}
                        </div>
                    </div>`;
                });
            }
            html += `</div>`;
        }

        // Prompts
        for (const [key, title, isPos] of [['positive_prompt', '✨ Positive Prompt', true], ['negative_prompt', '🚫 Negative Prompt', false]]) {
            if (!meta[key]) continue;
            const textSafe = (typeof escapeHTML === 'function') ? escapeHTML(meta[key]) : meta[key];
            const isLong = meta[key].length > 180 || meta[key].split(/\r?\n/).length > 3;

            html += `
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <span style="font-size:0.75rem; text-transform:uppercase; color:#aaa; font-weight:bold;">${title}</span>
                    <button type="button" class="gm-copy-btn" onclick="copyTextAndNotify(this.closest('div').nextElementSibling.innerText.trim(), this)">Copy</button>
                </div>
                <div class="gm-prompt ${isLong ? 'gm-collapsed' : ''}" style="${isPos ? 'border-color:rgba(40,167,69,0.3);' : 'border-color:rgba(220,53,69,0.3);'}">${textSafe}</div>
                ${isLong ? `<button type="button" class="gm-expand-btn" onclick="const p = this.previousElementSibling; const col = p.classList.toggle('gm-collapsed'); this.textContent = col ? 'Show more' : 'Show less';">Show more</button>` : ''}
            </div>`;
        }

        // Sampling Settings Badges
        let badgesHtml = '';
        for (const [k, lbl] of Object.entries(settingsLabels)) {
            if (present(meta[k])) {
                badgesHtml += `<span class="gm-badge" style="background:rgba(255,255,255,0.06); color:#fff; border-color:rgba(255,255,255,0.15);">${lbl}: <strong>${meta[k]}</strong></span>`;
            }
        }
        if (badgesHtml) {
            html += `
            <div>
                <div style="font-size:0.75rem; text-transform:uppercase; color:#aaa; font-weight:bold; margin-bottom:4px;">⚙️ Sampling Settings</div>
                <div class="gm-badges">${badgesHtml}</div>
            </div>`;
        }

        return html;
    };

    function renderInspector(meta, message) {
        metadata = meta;
        content.innerHTML = window.renderGenerationMetadataHTML(meta, message);
        copyAll.disabled = !meta;
    }

    copyAll.onclick = () => {
        if (!metadata) return;
        const m = metadata;
        const lines = [
            m.source,
            m.model && `Checkpoint: ${m.model}`,
            ...(m.loras || []).map(l => `LoRA: ${l.name}${present(l.value) ? ` (${l.value})` : ''}`),
            m.positive_prompt && `Prompt: ${m.positive_prompt}`,
            m.negative_prompt && `Negative prompt: ${m.negative_prompt}`,
            ...Object.entries(settingsLabels).filter(([k]) => present(m[k])).map(([k, label]) => `${label}: ${m[k]}`)
        ];
        copy(lines.filter(Boolean).join('\n'));
    };

    function blocked() {
        const openModal = document.querySelector('#smart-dialog-overlay.visible, #cq-overlay.visible, #compare-overlay.visible, #tagging-overlay.visible, #drag-drop-overlay.visible, #upload-overlay.visible, #full-file-details-overlay.visible, #ai-options-modal.visible, #clustering-modal-overlay.visible, #cluster-prompt-modal-overlay.visible, #shortcuts-help-overlay.visible');
        if (openModal) return true;
        
        const isLightbox = document.body.classList.contains('lightbox-open');
        if (!isLightbox) {
            if (document.querySelector('#node-summary-overlay.visible:not(.lb-nodes-docked), #file-info-overlay.visible:not(.lb-info-docked)')) return true;
        }
        return false;
    }

    function clearRequest() {
        clearTimeout(timer);
        if (controller) {
            controller.abort();
            controller = null;
        }
    }

    // Initialize dragging listener on header
    function initDragging() {
        if (!panel) return;
        const header = panel.querySelector('header');
        if (!header) return;

        header.addEventListener('mousedown', (e) => {
            // Drag only active in desktop lightbox
            if (!document.body.classList.contains('lightbox-open') || window.innerWidth <= 768) return;
            if (e.target.closest('button, input, a, kbd, span[onclick]')) return;

            isDragging = true;
            panel.classList.add('is-dragging');

            const rect = panel.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;

            e.preventDefault();
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            const winW = window.innerWidth;
            const winH = window.innerHeight;
            const panelW = panel.offsetWidth;
            const panelH = panel.offsetHeight;

            let newLeft = e.clientX - dragOffset.x;
            let newTop = e.clientY - dragOffset.y;

            // Constrain inside viewport
            newLeft = Math.max(10, Math.min(winW - panelW - 10, newLeft));
            newTop = Math.max(60, Math.min(winH - panelH - 20, newTop));

            panel.style.left = `${Math.round(newLeft)}px`;
            panel.style.top = `${Math.round(newTop)}px`;
            panel.style.bottom = 'auto';

            lightboxCustomPos = { left: newLeft, top: newTop };
        });

        window.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                panel.classList.remove('is-dragging');
            }
        });
    }

    // Dynamic placement anchored adjacent to thumbnail or inside Lightbox
    function placeInspector(item, isLightbox) {
        const gap = 12;
        const winW = window.innerWidth;
        const winH = window.innerHeight;

        if (isLightbox) {
            if (winW <= 768) {
                // Mobile layout: docked above bottom controls as a compact card
                const panelW = winW - 20;
                panel.style.width = `${panelW}px`;
                panel.style.left = '10px';
                panel.style.bottom = '20px';
                panel.style.top = 'auto';
                panel.style.maxHeight = '45vh';
                return;
            }

            const header = document.getElementById('lightbox-header')?.getBoundingClientRect();
            const topDefault = Math.max(gap, header ? header.bottom + gap : 86);
            const panelW = Math.min(360, winW - gap * 2);
            panel.style.width = `${panelW}px`;
            panel.style.maxHeight = `${Math.min(winH - topDefault - 80, 560)}px`;

            // If user has custom dragged position in this lightbox session, use it!
            if (lightboxCustomPos) {
                const clampLeft = Math.max(gap, Math.min(winW - panelW - gap, lightboxCustomPos.left));
                const clampTop = Math.max(gap, Math.min(winH - 100, lightboxCustomPos.top));
                panel.style.left = `${Math.round(clampLeft)}px`;
                panel.style.top = `${Math.round(clampTop)}px`;
                panel.style.bottom = 'auto';
                return;
            }

            // Check if rating / comments panel is active (docked on right side)
            const isRatingPanelActive = document.body.classList.contains('lb-info-docked') ||
                (document.getElementById('file-info-overlay') && document.getElementById('file-info-overlay').classList.contains('visible'));

            panel.style.top = `${topDefault}px`;
            panel.style.bottom = 'auto';

            if (isRatingPanelActive) {
                // Move Generation Data to the LEFT side so rating panel on the right doesn't collide
                panel.style.left = `${gap + 10}px`;
            } else {
                // Default: Right side
                panel.style.left = `${Math.max(gap, winW - panelW - 20)}px`;
            }
            return;
        }

        if (winW <= 768) {
            const panelW = winW - 20;
            panel.style.width = `${panelW}px`;
            panel.style.left = '10px';
            panel.style.bottom = '20px';
            panel.style.top = 'auto';
            panel.style.maxHeight = '50vh';
            return;
        }

        if (!item) {
            panel.style.top = '100px';
            panel.style.left = `${winW - 380}px`;
            panel.style.width = '360px';
            panel.style.maxHeight = 'calc(100dvh - 160px)';
            return;
        }

        const rect = item.getBoundingClientRect();
        const panelW = Math.min(360, Math.max(280, winW - 30));
        panel.style.width = `${panelW}px`;

        const spaceRight = winW - rect.right;
        const spaceLeft = rect.left;

        let targetLeft = rect.right + gap;
        if (spaceRight < panelW + gap && spaceLeft >= panelW + gap) {
            targetLeft = rect.left - panelW - gap;
        } else if (spaceRight < panelW + gap && spaceLeft < panelW + gap) {
            targetLeft = Math.max(gap, (winW - panelW) / 2);
        }

        let targetTop = rect.top;
        const maxH = Math.min(520, winH - 120);
        panel.style.maxHeight = `${maxH}px`;

        if (targetTop + maxH > winH - gap) {
            targetTop = Math.max(80, winH - maxH - gap);
        }

        panel.style.left = `${Math.round(targetLeft)}px`;
        panel.style.top = `${Math.round(targetTop)}px`;
        panel.style.bottom = 'auto';
    }

    function update() {
        frame = null;
        const isSuspended = blocked();
        const isLightbox = document.body.classList.contains('lightbox-open');
        const context = location.pathname + location.search;

        if (!isLightbox) {
            lightboxCustomPos = null;
        }

        if (isLightbox || context !== pinContext || (pinnedId && allFilesData && !allFilesData.some(f => f.id === pinnedId))) {
            pinnedId = null;
        }
        pinContext = context;

        // Update Pin button UI
        if (pinBtn) {
            pinBtn.hidden = isLightbox;
            pinBtn.classList.toggle('is-pinned', !!pinnedId);
            if (pinText) pinText.textContent = pinnedId ? 'Pinned (Alt+M)' : 'Pin Image';
            pinBtn.title = pinnedId ? 'Unpin metadata (Alt+M)' : 'Pin/Lock overlay on this image (Alt+M)';
        }
        if (pinStatus) {
            pinStatus.style.display = pinnedId ? 'inline' : 'none';
        }

        let item = pinnedId
            ? (galleryItems?.find(i => i.dataset.fileId === pinnedId))
            : (galleryItems ? galleryItems[focusedItemIndex] : null);

        if (!item && (panel.matches(':hover') || panel.contains(document.activeElement))) {
            item = galleryItems?.find(i => i.dataset.fileId === retainedId);
        }

        const file = isLightbox
            ? (typeof currentLightboxFile !== 'undefined' ? currentLightboxFile : null)
            : (allFilesData ? allFilesData.find(f => f.id === (pinnedId || item?.dataset.fileId || retainedId)) : null);

        const key = file ? `${file.id}:${file.mtime}:${file.size}:${isLightbox}` : null;

        if (!enabled || isSuspended || !file) {
            panel.hidden = true;
            clearRequest();
            activeKey = null;
            return;
        }

        panel.hidden = false;
        retainedId = file.id;

        const targetChanged = (key !== activeKey);
        if (targetChanged) {
            clearRequest();
            activeKey = key;
            if (name) name.textContent = file.name;

            const cacheKey = `${file.id}:${file.mtime}:${file.size}`;
            if (cache.has(cacheKey)) {
                renderInspector(cache.get(cacheKey));
            } else {
                renderInspector(null, 'Loading generation data...');
                timer = setTimeout(async () => {
                    const request = new AbortController();
                    controller = request;
                    try {
                        const response = await fetch(`/galleryout/api/generation_metadata/${encodeURIComponent(file.id)}`, { signal: request.signal });
                        const data = await response.json();
                        if (key !== activeKey || request.signal.aborted) return;
                        if (!response.ok) {
                            renderInspector(null, data.message || 'Unable to load generation data.');
                            return;
                        }
                        cache.set(cacheKey, data.metadata);
                        if (cache.size > 80) cache.delete(cache.keys().next().value);
                        renderInspector(data.metadata);
                    } catch (error) {
                        if (error.name !== 'AbortError' && key === activeKey) {
                            renderInspector(null, 'Unable to load generation data.');
                        }
                    }
                }, 80);
            }
        }

        placeInspector(item, isLightbox);
    }

    window.resetGenerationMetadataLightboxPos = () => {
        lightboxCustomPos = null;
    };

    // Toggle Pinning function (Alt+M)
    window.toggleGenerationMetadataPin = (fromPanel = false) => {
        if (blocked() || document.body.classList.contains('lightbox-open')) return;

        if (pinnedId) {
            pinnedId = null;
            if (typeof showNotification === 'function') showNotification('📌 Unpinned metadata', 'info', 1800);
        } else {
            const id = fromPanel ? retainedId : (galleryItems ? galleryItems[focusedItemIndex]?.dataset.fileId : null);
            if (!id || !allFilesData || !allFilesData.some(f => f.id === id)) return;
            pinnedId = id;
            if (!enabled) toggleGenerationMetadata(true);
            if (typeof showNotification === 'function') {
                const f = allFilesData.find(x => x.id === id);
                showNotification(`📌 Pinned metadata for "${f ? f.name : 'image'}" (Alt+M to unpin)`, 'success', 3000);
            }
        }
        scheduleGenerationMetadata();
    };

    window.scheduleGenerationMetadata = () => {
        if (!frame) frame = requestAnimationFrame(update);
    };

    window.toggleGenerationMetadata = (value) => {
        enabled = (typeof value === 'boolean') ? value : !enabled;
        if (!enabled) pinnedId = null;
        try { localStorage.setItem('galleryGenerationMetadata', String(enabled)); } catch (_) {}
        
        if (typeof showNotification === 'function') {
            if (enabled) {
                showNotification('⚙️ Generation data inspector ON (Press Alt+M to Pin)', 'success', 3000);
            } else {
                showNotification('⚙️ Generation data inspector OFF. Press Shift+M (or open Quick Menu /) to re-enable.', 'info multiline-msg', 4500);
            }
        }

        if (typeof updateOptionsUI === 'function') updateOptionsUI();

        if (enabled && typeof focusedItemIndex !== 'undefined' && focusedItemIndex < 0 && !document.body.classList.contains('lightbox-open') && typeof galleryItems !== 'undefined' && galleryItems && galleryItems.length > 0) {
            focusedItemIndex = 0;
            galleryItems[0].classList.add('focused');
            if (typeof updateFocusStatusBar === 'function') updateFocusStatusBar();
        }
        scheduleGenerationMetadata();
    };

    initDragging();
    window.addEventListener('resize', scheduleGenerationMetadata);
    window.addEventListener('scroll', scheduleGenerationMetadata, { passive: true });
    window.addEventListener('popstate', scheduleGenerationMetadata);

    const observer = new MutationObserver((records) => {
        if (records.some(r => !panel.contains(r.target) && (r.type !== 'attributes' || r.oldValue !== r.target.getAttribute('class')))) {
            scheduleGenerationMetadata();
        }
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'], attributeOldValue: true, subtree: true, childList: true });

    scheduleGenerationMetadata();
})();
