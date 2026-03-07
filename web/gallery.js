import { app } from "/scripts/app.js";

const SMART_GALLERY_URL = "/galleryout/view/_root_";

function mountSmartGallery(container) {
  container.innerHTML = "";
  container.className = "smart-gallery-container";

  const iframe = document.createElement("iframe");
  iframe.src = SMART_GALLERY_URL;
  iframe.className = "smart-gallery-iframe";
  iframe.style.width = "100%";
  iframe.style.height = "100%";
  iframe.style.border = "none";
  iframe.style.borderRadius = "4px";

  container.appendChild(iframe);

  const style = document.createElement("style");
  style.textContent = `
    .smart-gallery-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }
    .smart-gallery-iframe {
      flex: 1;
      min-height: 0;
    }
  `;
  container.appendChild(style);
}

app.registerExtension({
  name: "smart.comfyui.gallery",
  async setup() {
    if (app.extensionManager?.registerSidebarTab) {
      app.extensionManager.registerSidebarTab({
        id: "smart-gallery",
        icon: "pi pi-images",
        title: "Gallery",
        tooltip: "Gallery",
        label: "Gallery",
        type: "custom",
        render: (container) => mountSmartGallery(container),
      });
    } else {
      const button = document.createElement("button");
      button.textContent = "Gallery";
      button.style.cssText = "position: fixed; bottom: 20px; right: 20px; padding: 10px; background: #333; color: white; border: none; border-radius: 5px; cursor: pointer; z-index: 9999;";
      button.onclick = () => window.open(SMART_GALLERY_URL, "_blank");
      document.body.appendChild(button);
    }
  },
});
