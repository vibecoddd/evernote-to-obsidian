export {};

declare global {
  interface Window {
    desktop: DesktopBridge;
  }
}

interface DesktopBridge {
  getBackendUrl(): Promise<string | undefined>;
  selectDirectory(): Promise<string | undefined>;
  selectEnexFiles(): Promise<string[]>;
  openPath(filePath: string): Promise<string>;
  setMigrationActive(active: boolean): Promise<void>;
  onCloseRequested(listener: () => void): () => void;
  confirmClose(): Promise<void>;
}
