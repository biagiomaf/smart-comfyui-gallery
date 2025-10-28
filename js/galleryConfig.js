// File: js/galleryConfig.js
// SmartGallery Configuration Sidebar Tab
// Provides dedicated UI for backend configuration management

console.log("%c[SmartGallery] Configuration tab script loaded.", "color: #4CAF50; font-weight: bold;");

import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

/**
 * SmartGallery Configuration UI Component
 * Manages all configuration interactions through a custom sidebar tab
 */
class GalleryConfigUI {
    constructor(container) {
        this.container = container;
        this.config = null;
        this.detectedPaths = null;
        this.effectiveConfig = null;
        this.validationTimeout = null;
        
        this.init();
    }
    
    async init() {
        // Show loading state
        this.container.innerHTML = '<div class="gallery-config-loading">Loading configuration...</div>';
        
        try {
            // Fetch current config from backend
            const response = await api.fetchApi('/smartgallery/config');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            this.config = data.config || {};
            this.detectedPaths = data.detected_paths || {};
            this.effectiveConfig = data.effective_config || {};
            
            console.log("[SmartGallery] Configuration loaded:", this.config);
            
            // Render UI
            this.render();
            
            // Load dashboard data
            this.loadStats();
            this.loadRecentFiles();
            
            // Auto-refresh stats every 30 seconds
            if (this.refreshTimer) clearInterval(this.refreshTimer);
            this.refreshTimer = setInterval(() => {
                this.loadStats();
                this.loadRecentFiles();
            }, 30000);
            
        } catch (error) {
            console.error("[SmartGallery] Failed to load configuration:", error);
            this.showError(`Failed to load configuration: ${error.message}`);
        }
    }
    
    async loadStats() {
        const port = this.config.server_port || 8008;
        try {
            const response = await fetch(`http://localhost:${port}/smartgallery/stats`, {
                method: 'GET',
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            if (result.success) {
                const data = result.data;
                document.getElementById('stat-total').textContent = data.total_files.toLocaleString();
                document.getElementById('stat-images').textContent = data.by_type.images.toLocaleString();
                document.getElementById('stat-videos').textContent = data.by_type.videos.toLocaleString();
                document.getElementById('stat-workflows').textContent = data.with_workflow.toLocaleString();
                document.getElementById('stat-favorites').textContent = data.favorites.toLocaleString();
                document.getElementById('stat-cache').textContent = `${data.cache_size_mb} MB`;
            }
        } catch (error) {
            console.error('[SmartGallery] Failed to load stats:', error);
            // Silently fail - don't show error to user for auto-refresh
        }
    }
    
    async loadRecentFiles() {
        const port = this.config.server_port || 8008;
        const container = document.getElementById('recent-files');
        if (!container) return;
        
        try {
            const response = await fetch(`http://localhost:${port}/smartgallery/recent?limit=6`, {
                method: 'GET',
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            if (result.success && result.data.length > 0) {
                container.innerHTML = result.data.map(file => `
                    <div class="recent-file-card" 
                         title="${file.name} - Click to open in gallery"
                         onclick="window.galleryConfigInstance.openFileInGallery('${file.id}')">
                        <img src="http://localhost:${port}${file.thumbnail_url}" 
                             alt="${file.name}"
                             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23333%22 width=%22100%22 height=%22100%22/%3E%3Ctext fill=%22%23666%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22%3E?%3C/text%3E%3C/svg%3E'">
                        <div class="recent-file-info">
                            <div class="recent-file-name">${file.name.length > 20 ? file.name.substring(0, 20) + '...' : file.name}</div>
                            ${file.has_workflow ? '<span class="workflow-badge">⚡</span>' : ''}
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<div class="empty-state">No recent files</div>';
            }
        } catch (error) {
            console.error('[SmartGallery] Failed to load recent files:', error);
            container.innerHTML = '<div class="error-state">Failed to load recent files</div>';
        }
    }
    
    async syncGallery() {
        const port = this.config.server_port || 8008;
        const statusDiv = document.getElementById('status-message');
        
        if (statusDiv) {
            statusDiv.innerHTML = '<div class="loading-box">🔄 Syncing all folders...</div>';
        }
        
        try {
            const response = await fetch(`http://localhost:${port}/smartgallery/sync_all`, {
                method: 'POST',
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            if (result.success) {
                if (statusDiv) {
                    statusDiv.innerHTML = '<div class="success-box">✅ All folders synced successfully</div>';
                    setTimeout(() => { if (statusDiv) statusDiv.innerHTML = ''; }, 5000);
                }
                // Refresh stats after sync
                this.loadStats();
                this.loadRecentFiles();
            } else {
                throw new Error(result.error || 'Sync failed');
            }
        } catch (error) {
            console.error('[SmartGallery] Sync failed:', error);
            if (statusDiv) {
                statusDiv.innerHTML = `<div class="error-box">❌ Sync failed: ${error.message}</div>`;
            }
        }
    }
    
    async clearCache() {
        const port = this.config.server_port || 8008;
        const statusDiv = document.getElementById('status-message');
        
        if (!confirm('Clear thumbnail cache? Thumbnails will be regenerated on demand.')) {
            return;
        }
        
        if (statusDiv) {
            statusDiv.innerHTML = '<div class="loading-box">🗑️ Clearing cache...</div>';
        }
        
        try {
            const response = await fetch(`http://localhost:${port}/smartgallery/clear_cache`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'all' }),
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            if (result.success) {
                if (statusDiv) {
                    statusDiv.innerHTML = `<div class="success-box">✅ ${result.message}</div>`;
                    setTimeout(() => { if (statusDiv) statusDiv.innerHTML = ''; }, 5000);
                }
                // Refresh stats after clearing cache
                this.loadStats();
            } else {
                throw new Error(result.error || 'Clear failed');
            }
        } catch (error) {
            console.error('[SmartGallery] Clear cache failed:', error);
            if (statusDiv) {
                statusDiv.innerHTML = `<div class="error-box">❌ Clear failed: ${error.message}</div>`;
            }
        }
    }
    
    async viewLogs() {
        const port = this.config.server_port || 8008;
        
        try {
            const response = await fetch(`http://localhost:${port}/smartgallery/logs?lines=100`, {
                method: 'GET',
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            if (result.success) {
                this.showLogsModal(result.data);
            } else {
                throw new Error(result.error || 'Failed to load logs');
            }
        } catch (error) {
            console.error('[SmartGallery] Failed to load logs:', error);
            alert(`Failed to load logs: ${error.message}`);
        }
    }
    
    showLogsModal(data) {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'logs-modal-overlay';
        modal.innerHTML = `
            <div class="logs-modal">
                <div class="logs-modal-header">
                    <h3>📋 Gallery Logs</h3>
                    <button class="logs-modal-close" onclick="this.closest('.logs-modal-overlay').remove()">✕</button>
                </div>
                <div class="logs-modal-info">
                    <span>📄 ${data.file}</span>
                    <span>📊 ${data.total} lines</span>
                </div>
                <div class="logs-modal-content">
                    <pre>${data.lines.join('\n')}</pre>
                </div>
            </div>
        `;
        
        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        document.body.appendChild(modal);
    }
    
    openGallery() {
        const port = this.config.server_port || 8008;
        window.open(`http://localhost:${port}/galleryout/`, '_blank');
    }
    
    openFileInGallery(fileId) {
        const port = this.config.server_port || 8008;
        // Open gallery and try to highlight/show the specific file
        // The gallery will need to handle the file parameter
        window.open(`http://localhost:${port}/galleryout/#file-${fileId}`, '_blank');
    }
    
    render() {
        const autoDetect = this.config.auto_detect_paths !== false;
        const hasDetectedPaths = this.detectedPaths.output_path && this.detectedPaths.input_path;
        
        const html = `
            <div class="gallery-config-container">
                <div class="gallery-config-header">
                    <h2>🖼️ Gallery Configuration</h2>
                    <p class="gallery-config-subtitle">Configure SmartGallery backend settings</p>
                </div>
                
                <!-- Dashboard Section -->
                <section class="config-section dashboard-section">
                    <div class="dashboard-header">
                        <h3>📊 Gallery Dashboard</h3>
                        <button class="btn-open-gallery" onclick="window.galleryConfigInstance.openGallery()">
                            🌐 Open Gallery
                        </button>
                    </div>
                    
                    <div class="dashboard-grid">
                        <div class="stat-card">
                            <div class="stat-icon">📁</div>
                            <div class="stat-content">
                                <div class="stat-label">Total Files</div>
                                <div class="stat-value" id="stat-total">-</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">🖼️</div>
                            <div class="stat-content">
                                <div class="stat-label">Images</div>
                                <div class="stat-value" id="stat-images">-</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">🎬</div>
                            <div class="stat-content">
                                <div class="stat-label">Videos</div>
                                <div class="stat-value" id="stat-videos">-</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">⚡</div>
                            <div class="stat-content">
                                <div class="stat-label">With Workflows</div>
                                <div class="stat-value" id="stat-workflows">-</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">⭐</div>
                            <div class="stat-content">
                                <div class="stat-label">Favorites</div>
                                <div class="stat-value" id="stat-favorites">-</div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">💾</div>
                            <div class="stat-content">
                                <div class="stat-label">Cache Size</div>
                                <div class="stat-value" id="stat-cache">-</div>
                            </div>
                        </div>
                    </div>
                    
                    <h4>📸 Recent Files</h4>
                    <div class="recent-files-grid" id="recent-files">
                        <div class="loading-box">Loading recent files...</div>
                    </div>
                    
                    <h4>⚡ Quick Actions</h4>
                    <div class="quick-actions-grid">
                        <button class="btn-action" onclick="window.galleryConfigInstance.syncGallery()">
                            🔄 Sync All Folders
                        </button>
                        <button class="btn-action" onclick="window.galleryConfigInstance.clearCache()">
                            🗑️ Clear Cache
                        </button>
                        <button class="btn-action" onclick="window.galleryConfigInstance.viewLogs()">
                            📋 View Logs
                        </button>
                    </div>
                </section>
                
                <!-- Path Configuration Section -->
                <section class="config-section">
                    <h3>📁 Path Configuration</h3>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" 
                                   id="auto-detect-paths" 
                                   ${autoDetect ? 'checked' : ''}
                                   onchange="window.galleryConfigInstance.toggleAutoDetect(this.checked)">
                            <span>Auto-detect paths from ComfyUI</span>
                        </label>
                        ${hasDetectedPaths ? 
                            `<div class="hint success">✓ Detected output: <code>${this.detectedPaths.output_path}</code></div>
                             <div class="hint success">✓ Detected input: <code>${this.detectedPaths.input_path}</code></div>` : 
                            '<div class="hint warning">⚠ Could not auto-detect paths from ComfyUI</div>'}
                    </div>
                    
                    <div id="manual-paths" ${autoDetect ? 'style="display:none"' : ''}>
                        <div class="form-group">
                            <label>Output Directory</label>
                            <input type="text" 
                                   id="output-path" 
                                   class="path-input"
                                   value="${this.config.base_output_path || ''}"
                                   placeholder="C:/ComfyUI/output"
                                   onblur="window.galleryConfigInstance.validateField('base_output_path')">
                            <div class="hint">Where generated images are stored</div>
                            <div id="base_output_path-error" class="error-message"></div>
                        </div>
                        
                        <div class="form-group">
                            <label>Input Directory</label>
                            <input type="text" 
                                   id="input-path" 
                                   class="path-input"
                                   value="${this.config.base_input_path || ''}"
                                   placeholder="C:/ComfyUI/input"
                                   onblur="window.galleryConfigInstance.validateField('base_input_path')">
                            <div class="hint">Additional images to display in gallery</div>
                            <div id="base_input_path-error" class="error-message"></div>
                        </div>
                    </div>
                </section>
                
                <!-- Server Configuration Section -->
                <section class="config-section">
                    <h3>🌐 Server Settings</h3>
                    
                    <div class="form-group">
                        <label>Gallery Port</label>
                        <input type="number" 
                               id="server-port" 
                               value="${this.config.server_port || 8008}"
                               min="1024" 
                               max="65535"
                               onblur="window.galleryConfigInstance.validateField('server_port')">
                        <div class="hint">Port for gallery web server (1024-65535). Default: 8008</div>
                        <div id="server_port-error" class="error-message"></div>
                    </div>
                </section>
                
                <!-- Feature Configuration Section -->
                <section class="config-section">
                    <h3>✨ Features</h3>
                    
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" 
                                   id="enable-upload" 
                                   ${this.config.enable_upload !== false ? 'checked' : ''}
                                   onchange="window.galleryConfigInstance.toggleUpload(this.checked)">
                            <span>Enable file uploads</span>
                        </label>
                    </div>
                    
                    <div class="form-group" id="upload-settings" ${this.config.enable_upload === false ? 'style="display:none"' : ''}>
                        <label>Max Upload Size (MB)</label>
                        <input type="number" 
                               id="max-upload-size" 
                               value="${this.config.max_upload_size_mb || 100}"
                               min="1"
                               max="1000">
                        <div class="hint">Maximum file size for uploads</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Thumbnail Quality (1-100)</label>
                        <div class="slider-container">
                            <input type="range" 
                                   id="thumbnail-quality" 
                                   value="${this.config.thumbnail_quality || 85}"
                                   min="1" 
                                   max="100"
                                   oninput="document.getElementById('quality-value').textContent = this.value">
                            <span id="quality-value" class="slider-value">${this.config.thumbnail_quality || 85}</span>
                        </div>
                        <div class="hint">Lower values = smaller files, higher values = better quality</div>
                    </div>
                </section>
                
                <!-- Advanced Configuration Section -->
                <section class="config-section">
                    <h3>⚙️ Advanced</h3>
                    
                    <div class="form-group">
                        <label>FFprobe Path (optional)</label>
                        <input type="text" 
                               id="ffprobe-path" 
                               class="path-input"
                               value="${this.config.ffprobe_manual_path || ''}"
                               placeholder="Auto-detect from system PATH">
                        <div class="hint">Required for video workflow extraction. Leave empty for auto-detection.</div>
                        <div id="ffprobe_manual_path-error" class="error-message"></div>
                    </div>
                </section>
                
                <!-- Validation Messages -->
                <div id="validation-messages" class="validation-messages"></div>
                
                <!-- Action Buttons -->
                <div class="config-actions">
                    <button class="btn-primary" onclick="window.galleryConfigInstance.saveConfig()">
                        💾 Save Configuration
                    </button>
                    <button class="btn-secondary" onclick="window.galleryConfigInstance.testConnection()">
                        🔗 Test Gallery Connection
                    </button>
                    <button class="btn-secondary" onclick="window.galleryConfigInstance.resetToDefaults()">
                        ↺ Reset to Defaults
                    </button>
                </div>
                
                <!-- Status Messages -->
                <div id="status-message" class="status-message"></div>
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    toggleAutoDetect(enabled) {
        const manualPaths = document.getElementById('manual-paths');
        if (manualPaths) {
            manualPaths.style.display = enabled ? 'none' : 'block';
        }
        
        if (enabled && this.detectedPaths.output_path) {
            // Clear manual paths when auto-detect is enabled
            const outputInput = document.getElementById('output-path');
            const inputInput = document.getElementById('input-path');
            if (outputInput) outputInput.value = '';
            if (inputInput) inputInput.value = '';
        }
    }
    
    toggleUpload(enabled) {
        const uploadSettings = document.getElementById('upload-settings');
        if (uploadSettings) {
            uploadSettings.style.display = enabled ? 'block' : 'none';
        }
    }
    
    async validateField(fieldName) {
        // Debounce validation
        if (this.validationTimeout) {
            clearTimeout(this.validationTimeout);
        }
        
        this.validationTimeout = setTimeout(async () => {
            const config = this.collectFormData();
            
            try {
                const response = await api.fetchApi('/smartgallery/config/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                // Show field-specific errors
                const errorDiv = document.getElementById(`${fieldName}-error`);
                if (errorDiv) {
                    const fieldErrors = result.errors?.filter(e => 
                        e.toLowerCase().includes(fieldName.replace('_', ' '))
                    ) || [];
                    errorDiv.textContent = fieldErrors.join(', ');
                    errorDiv.style.display = fieldErrors.length ? 'block' : 'none';
                }
                
            } catch (error) {
                console.error('[SmartGallery] Validation failed:', error);
            }
        }, 500);
    }
    
    collectFormData() {
        return {
            auto_detect_paths: document.getElementById('auto-detect-paths')?.checked ?? true,
            base_output_path: document.getElementById('output-path')?.value || '',
            base_input_path: document.getElementById('input-path')?.value || '',
            server_port: parseInt(document.getElementById('server-port')?.value || '8008'),
            enable_upload: document.getElementById('enable-upload')?.checked ?? true,
            max_upload_size_mb: parseFloat(document.getElementById('max-upload-size')?.value || '100'),
            thumbnail_quality: parseInt(document.getElementById('thumbnail-quality')?.value || '85'),
            ffprobe_manual_path: document.getElementById('ffprobe-path')?.value || ''
        };
    }
    
    async saveConfig() {
        const newConfig = this.collectFormData();
        
        console.log("[SmartGallery] Saving configuration:", newConfig);
        
        const statusDiv = document.getElementById('status-message');
        if (statusDiv) {
            statusDiv.innerHTML = '<div class="loading-box">💾 Saving configuration...</div>';
        }
        
        try {
            const response = await api.fetchApi('/smartgallery/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            
            const result = await response.json();
            
            this.showValidationResult(result);
            
            if (result.success) {
                this.config = newConfig;
                
                if (result.requires_restart) {
                    this.showRestartPrompt();
                }
            }
            
        } catch (error) {
            console.error('[SmartGallery] Save failed:', error);
            this.showError(`Failed to save configuration: ${error.message}`);
        }
    }
    
    showValidationResult(result) {
        const messagesDiv = document.getElementById('validation-messages');
        const statusDiv = document.getElementById('status-message');
        
        let html = '';
        
        if (result.errors && result.errors.length) {
            html += '<div class="error-box"><strong>❌ Errors:</strong><ul>';
            result.errors.forEach(err => html += `<li>${err}</li>`);
            html += '</ul></div>';
        }
        
        if (result.warnings && result.warnings.length) {
            html += '<div class="warning-box"><strong>⚠️ Warnings:</strong><ul>';
            result.warnings.forEach(warn => html += `<li>${warn}</li>`);
            html += '</ul></div>';
        }
        
        if (messagesDiv) {
            messagesDiv.innerHTML = html;
        }
        
        if (result.success && statusDiv) {
            statusDiv.innerHTML = '<div class="success-box">✅ Configuration saved successfully</div>';
            setTimeout(() => {
                if (statusDiv) statusDiv.innerHTML = '';
            }, 5000);
        } else if (!result.success && statusDiv) {
            statusDiv.innerHTML = `<div class="error-box">❌ ${result.message || 'Save failed'}</div>`;
        }
    }
    
    showRestartPrompt() {
        const statusDiv = document.getElementById('status-message');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="info-box">
                    ℹ️ Gallery server requires restart to apply changes.
                    <button class="btn-restart" onclick="window.galleryConfigInstance.restartServer()">
                        🔄 Restart Now
                    </button>
                </div>
            `;
        }
    }
    
    async restartServer() {
        const statusDiv = document.getElementById('status-message');
        if (statusDiv) {
            statusDiv.innerHTML = '<div class="loading-box">🔄 Restarting gallery server...</div>';
        }
        
        try {
            const response = await api.fetchApi('/smartgallery/restart', { method: 'POST' });
            const result = await response.json();
            
            if (result.success && statusDiv) {
                statusDiv.innerHTML = '<div class="success-box">✅ Gallery server restarted successfully</div>';
                setTimeout(() => {
                    if (statusDiv) statusDiv.innerHTML = '';
                }, 5000);
            } else if (statusDiv) {
                statusDiv.innerHTML = `<div class="error-box">❌ Failed to restart: ${result.message}</div>`;
            }
        } catch (error) {
            console.error('[SmartGallery] Restart failed:', error);
            if (statusDiv) {
                statusDiv.innerHTML = `<div class="error-box">❌ Restart failed: ${error.message}</div>`;
            }
        }
    }
    
    async testConnection() {
        const port = document.getElementById('server-port')?.value || 8008;
        const statusDiv = document.getElementById('status-message');
        
        if (statusDiv) {
            statusDiv.innerHTML = '<div class="loading-box">🔗 Testing connection...</div>';
        }
        
        try {
            // Try to fetch from the gallery server
            const testUrl = `http://localhost:${port}/galleryout/`;
            const response = await fetch(testUrl, { 
                mode: 'no-cors',  // Gallery is different origin
                cache: 'no-cache'
            });
            
            // With no-cors, we can't read the response, but if it doesn't throw, connection works
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="success-box">
                        ✅ Gallery is accessible at port ${port}
                        <a href="${testUrl}" target="_blank" class="btn-link">Open Gallery →</a>
                    </div>
                `;
                setTimeout(() => {
                    if (statusDiv) statusDiv.innerHTML = '';
                }, 8000);
            }
            
        } catch (error) {
            console.error('[SmartGallery] Connection test failed:', error);
            if (statusDiv) {
                statusDiv.innerHTML = `
                    <div class="error-box">
                        ❌ Cannot connect to gallery on port ${port}
                        <br><small>Make sure the gallery server is running</small>
                    </div>
                `;
            }
        }
    }
    
    async resetToDefaults() {
        if (!confirm('Reset all settings to defaults? This will clear your custom configuration.')) {
            return;
        }
        
        const defaults = {
            auto_detect_paths: true,
            base_output_path: '',
            base_input_path: '',
            server_port: 8008,
            enable_upload: true,
            max_upload_size_mb: 100,
            thumbnail_quality: 85,
            ffprobe_manual_path: ''
        };
        
        try {
            const response = await api.fetchApi('/smartgallery/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(defaults)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log("[SmartGallery] Reset to defaults");
                this.init(); // Reload the UI
            } else {
                this.showValidationResult(result);
            }
            
        } catch (error) {
            console.error('[SmartGallery] Reset failed:', error);
            this.showError(`Failed to reset: ${error.message}`);
        }
    }
    
    showError(message) {
        this.container.innerHTML = `
            <div class="gallery-config-error">
                <h3>❌ Error</h3>
                <p>${message}</p>
                <button class="btn-primary" onclick="window.galleryConfigInstance.init()">
                    ↺ Retry
                </button>
            </div>
        `;
    }
}

// Register the extension with ComfyUI
app.registerExtension({
    name: "Comfy.SmartGallery.ConfigTab",
    
    async setup() {
        console.log("[SmartGallery] Registering configuration sidebar tab");
        
        // Load CSS file programmatically
        const cssLink = document.createElement("link");
        cssLink.rel = "stylesheet";
        cssLink.type = "text/css";
        cssLink.href = new URL("./galleryConfig.css", import.meta.url).href;
        
        cssLink.onload = () => {
            console.log("[SmartGallery] ✅ CSS loaded successfully:", cssLink.href);
        };
        
        cssLink.onerror = () => {
            console.error("[SmartGallery] ❌ Failed to load CSS:", cssLink.href);
        };
        
        document.head.appendChild(cssLink);
        
        // Register custom sidebar tab
        app.extensionManager.registerSidebarTab({
            id: "smart-gallery-config",
            icon: "pi pi-images",
            title: "Gallery Config",
            tooltip: "Configure SmartGallery settings",
            type: "custom",
            
            render: (container) => {
                // Create and store the config UI instance
                window.galleryConfigInstance = new GalleryConfigUI(container);
                return container;
            },
            
            destroy: () => {
                // Cleanup when tab is closed
                if (window.galleryConfigInstance) {
                    if (window.galleryConfigInstance.refreshTimer) {
                        clearInterval(window.galleryConfigInstance.refreshTimer);
                    }
                    window.galleryConfigInstance = null;
                }
            }
        });
        
        console.log("[SmartGallery] Configuration tab registered successfully");
    }
});
