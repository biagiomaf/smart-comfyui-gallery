// File: js/gallerySettings.js

console.log("%c[SmartGallery] Settings script loaded.", "color: orange; font-weight: bold;");

import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

app.registerExtension({
    name: "Comfy.SmartGallery.Settings",

    registerSettings() {
        // This async function contains the logic to save settings to the backend.
        const saveToServer = async () => {
            const newSettings = {
                base_output_path: app.ui.settings.getSettingValue('SmartGallery.base_output_path'),
                base_input_path: app.ui.settings.getSettingValue('SmartGallery.base_input_path'),
                server_port: app.ui.settings.getSettingValue('SmartGallery.server_port'),
                ffprobe_manual_path: app.ui.settings.getSettingValue('SmartGallery.ffprobe_manual_path'),
            };

            try {
                const response = await api.fetchApi('/smartgallery/save_config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
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
        };

        // This is the synchronous handler that ComfyUI will call.
        const onChangeHandler = (newValue, oldValue, setting) => {
            // Trigger the async save function but don't wait for it.
            saveToServer();
            
            // Return false to prevent ComfyUI's default save behavior.
            // This is the key fix for the "Cannot read properties of undefined (reading 'id')" error.
            return false;
        };

        // Register settings with the synchronous handler.
        app.ui.settings.addSetting({
            id: "SmartGallery.base_output_path",
            name: "[SmartGallery] Output Path",
            type: "text",
            defaultValue: "",
            tooltip: "Absolute path to ComfyUI's output folder. Leave blank to auto-detect (recommended). Requires restart.",
            onChange: onChangeHandler,
        });
        app.ui.settings.addSetting({
            id: "SmartGallery.base_input_path",
            name: "[SmartGallery] Input Path",
            type: "text",
            defaultValue: "",
            tooltip: "Absolute path to ComfyUI's input folder. Leave blank to auto-detect (recommended). Requires restart.",
            onChange: onChangeHandler,
        });
        app.ui.settings.addSetting({
            id: "SmartGallery.server_port",
            name: "[SmartGallery] Gallery Port",
            type: "number",
            defaultValue: 8008,
            tooltip: "Port for the gallery server. Must be different from ComfyUI's port. Requires restart.",
            attrs: { min: 1025, max: 65535, step: 1 },
            onChange: onChangeHandler,
        });
        app.ui.settings.addSetting({
            id: "SmartGallery.ffprobe_manual_path",
            name: "[SmartGallery] FFprobe Path (Optional)",
            type: "text",
            defaultValue: "",
            tooltip: "Optional. Full path to ffprobe.exe for video metadata. Requires restart.",
            onChange: onChangeHandler,
        });
    },

    async setup() {
        try {
            const resp = await api.fetchApi("/smartgallery/get_config");
            if (!resp.ok) {
                throw new Error(`Failed to fetch config with status: ${resp.status}`);
            }
            const currentSettings = await resp.json();
            
            // The 'false' argument prevents the onChange handler from firing on load.
            app.ui.settings.setSettingValue('SmartGallery.base_output_path', currentSettings.base_output_path, false);
            app.ui.settings.setSettingValue('SmartGallery.base_input_path', currentSettings.base_input_path, false);
            app.ui.settings.setSettingValue('SmartGallery.server_port', currentSettings.server_port, false);
            app.ui.settings.setSettingValue('SmartGallery.ffprobe_manual_path', currentSettings.ffprobe_manual_path, false);

        } catch (error) {
            console.error("[SmartGallery] CRITICAL: Failed to fetch config from backend.", error);
            app.ui.notifications.addMessage("[SmartGallery] Could not load initial settings from backend.", "error");
        }
    }
});
