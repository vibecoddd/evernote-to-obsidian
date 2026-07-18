import { contextBridge, ipcRenderer } from "electron";

const api = {
  getBackendUrl: () => ipcRenderer.invoke("desktop:get-backend-url"),
  selectDirectory: () => ipcRenderer.invoke("desktop:select-directory"),
  selectEnexFiles: () => ipcRenderer.invoke("desktop:select-enex-files"),
  openPath: (filePath: string) => ipcRenderer.invoke("desktop:open-path", filePath),
  setMigrationActive: (active: boolean) =>
    ipcRenderer.invoke("desktop:set-migration-active", active),
  onCloseRequested: (listener: () => void) => {
    const wrapped = () => listener();
    ipcRenderer.on("desktop:close-requested", wrapped);
    return () => ipcRenderer.removeListener("desktop:close-requested", wrapped);
  },
  confirmClose: () => ipcRenderer.invoke("desktop:confirm-close"),
};

contextBridge.exposeInMainWorld("desktop", api);
