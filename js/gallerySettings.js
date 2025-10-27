// File: js/gallerySettings.js

console.log("%c[SmartGallery] Settings script loaded.", "color: orange; font-weight: bold;");

import { app } from "/scripts/app.js";

async function saveSettings(settings) {
    try {
        const response = await app.fetchApi('/smartgallery/save_config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        const result = await response.json();
        if (result.status !== 'success') {
            app.ui.notifications.addMessage(`[SmartGallery] Error: ${result.message}`, "error");
        } else {
            app.ui.notifications.addMessage(result.message, "success", 8000);
        }
    } catch (error) {
        console.error("[SmartGallery] Failed to save settings:", error);
        app.ui.notifications.addMessage("[SmartGallery] Failed to save settings. See browser console for details.", "error");
    }
}

app.registerExtension({
    name: "Comfy.SmartGallery.Settings",
    
    async addSettings() {
        let currentSettings;
        try {
            // This is the critical API call that was likely failing silently.
            const resp = await app.fetchApi("/smartgallery/get_config");
            currentSettings = await resp.json();
        } catch (error) {
            console.error("[SmartGallery] CRITICAL: Failed to fetch config from backend.", error);
            console.error("[SmartGallery] The settings panel will not be displayed. Ensure the backend API routes are registered correctly.");
            // Stop execution if we can't get the settings.
            return;
        }

        const saveOnChange = async () => {
            const newSettings = {
                base_output_path: app.ui.settings.getSettingValue('SmartGallery.base_output_path'),
                base_input_path: app.ui.settings.getSettingValue('SmartGallery.base_input_path'),
                server_port: app.ui.settings.getSettingValue('SmartGallery.server_port'),
                ffprobe_manual_path: app.ui.settings.getSettingValue('SmartGallery.ffprobe_manual_path'),
            };
            await saveSettings(newSettings);
        };

        app.ui.settings.addSetting({
            id: "SmartGallery.base_output_path",
            name: "[SmartGallery] Output Path",
            type: "text",
            defaultValue: currentSettings.base_output_path,
            tooltip: "Absolute path to ComfyUI's output folder. Leave blank to auto-detect (recommended). Requires restart.",
            onChange: saveOnChange,
        });

        app.ui.settings.addSetting({
            id: "SmartGallery.base_input_path",
            name: "[SmartGallery] Input Path",
            type: "text",
            defaultValue: currentSettings.base_input_path,
            tooltip: "Absolute path to ComfyUI's input folder. Leave blank to auto-detect (recommended). Requires restart.",
            onChange: saveOnChange,
        });

        app.ui.settings.addSetting({
            id: "SmartGallery.server_port",
            name: "[SmartGallery] Gallery Port",
            type: "number",
            defaultValue: currentSettings.server_port,
            tooltip: "Port for the gallery server. Must be different from ComfyUI's port. Requires restart.",
            attrs: { min: 1025, max: 65535, step: 1 },
            onChange: saveOnChange,
        });

        app.ui.settings.addSetting({
            id: "SmartGallery.ffprobe_manual_path",
            name: "[SmartGallery] FFprobe Path (Optional)",
            type: "text",
            defaultValue: currentSettings.ffprobe_manual_path,
            tooltip: "Optional. Full path to ffprobe.exe for video metadata. Requires restart.",
            onChange: saveOnChange,
        });
    },
});
