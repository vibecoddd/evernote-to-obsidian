import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { app, BrowserWindow, dialog, ipcMain, shell } from "electron";

import type { BackendHandle, StartBackendOptions } from "./types";

export interface WaitForBackendOptions {
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
  intervalMs?: number;
  now?: () => number;
  sleep?: (milliseconds: number) => Promise<void>;
}

const DEFAULT_HEALTH_TIMEOUT_MS = 15_000;
const DEFAULT_HEALTH_INTERVAL_MS = 200;
const DEFAULT_STOP_TIMEOUT_MS = 5_000;

export async function reserveLoopbackPort(): Promise<number> {
  const server = net.createServer();

  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });

  const address = server.address();
  if (address === null || typeof address === "string") {
    server.close();
    throw new Error("Could not reserve a loopback port");
  }

  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });

  return address.port;
}

export async function waitForBackend(
  backendUrl: string,
  options: WaitForBackendOptions = {},
): Promise<void> {
  const fetchImpl = options.fetchImpl ?? fetch;
  const timeoutMs = options.timeoutMs ?? DEFAULT_HEALTH_TIMEOUT_MS;
  const intervalMs = Math.max(1, options.intervalMs ?? DEFAULT_HEALTH_INTERVAL_MS);
  const now = options.now ?? (() => performance.now());
  const sleep =
    options.sleep ??
    ((milliseconds: number) =>
      new Promise<void>((resolve) => setTimeout(resolve, milliseconds)));
  const healthUrl = new URL("/api/healthz", backendUrl).toString();
  const deadline = now() + timeoutMs;
  let lastFailure: unknown = new Error("No health response received");

  do {
    try {
      const response = await fetchImpl(healthUrl);
      if (response.ok) {
        return;
      }
      lastFailure = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastFailure = error;
    }

    const remainingMs = deadline - now();
    if (remainingMs <= 0) {
      break;
    }
    await sleep(Math.min(intervalMs, remainingMs));
  } while (now() <= deadline);

  const detail = lastFailure instanceof Error ? lastFailure.message : String(lastFailure);
  throw new Error(`Backend health check timed out for ${healthUrl}: ${detail}`);
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function stopChildProcess(
  child: BackendHandle["process"],
  timeoutMs: number,
): Promise<void> {
  if (child.exitCode !== null || child.killed) {
    return;
  }

  const exited = new Promise<void>((resolve) => {
    const childWithEvents = child as BackendHandle["process"] & {
      once?: (event: "exit", listener: () => void) => void;
    };
    childWithEvents.once?.("exit", resolve);
  });

  child.kill("SIGTERM");
  await Promise.race([exited, delay(timeoutMs)]);

  if (child.exitCode === null && !child.killed) {
    child.kill("SIGKILL");
  }
}

export async function startBackend(
  options: StartBackendOptions = {},
): Promise<BackendHandle> {
  const appRoot = options.appRoot ?? process.cwd();
  const isPackaged = options.isPackaged ?? app.isPackaged;
  const platform = options.platform ?? process.platform;
  const port = await (options.reservePort ?? reserveLoopbackPort)();
  const backendUrl = `http://127.0.0.1:${port}`;
  const stopTimeoutMs = options.stopTimeoutMs ?? DEFAULT_STOP_TIMEOUT_MS;
  const spawnImpl = options.spawnImpl ?? spawn;
  const command = isPackaged
    ? path.join(
        options.resourcesPath ?? process.resourcesPath,
        "backend",
        `evernote-backend${platform === "win32" ? ".exe" : ""}`,
      )
    : options.env?.PYTHON || process.env.PYTHON || "python3";
  const args = isPackaged
    ? ["--port", String(port)]
    : [path.join(appRoot, "backend_app.py"), "--port", String(port)];
  const child = spawnImpl(command, args, {
    cwd: appRoot,
    env: options.env ?? process.env,
    stdio: "inherit",
    windowsHide: true,
  });

  return {
    url: backendUrl,
    process: child,
    stop: () => stopChildProcess(child, stopTimeoutMs),
  };
}

interface DesktopWindow {
  close?: () => void;
  focus: () => void;
  isDestroyed: () => boolean;
  isMinimized: () => boolean;
  loadFile: (filePath: string) => Promise<void>;
  on: (event: "close", listener: (event: { preventDefault: () => void }) => void) => void;
  once: (event: "ready-to-show", listener: () => void) => void;
  restore: () => void;
  show?: () => void;
  webContents: {
    on: (
      event: "will-navigate",
      listener: (event: { preventDefault: () => void }, url: string) => void,
    ) => void;
    send: (channel: string) => void;
  };
}

interface DesktopDependencies {
  app: {
    isPackaged?: boolean;
    on: (event: string, listener: (...args: any[]) => void) => unknown;
    quit: () => void;
    requestSingleInstanceLock: () => boolean;
    whenReady: () => Promise<void>;
  };
  BrowserWindow: new (options: {
    minHeight: number;
    minWidth: number;
    show: boolean;
    webPreferences: {
      contextIsolation: boolean;
      nodeIntegration: boolean;
      preload: string;
      sandbox: boolean;
    };
  }) => DesktopWindow;
  dialog: {
    showOpenDialog: (
      window: DesktopWindow | undefined,
      options: Record<string, unknown>,
    ) => Promise<{ canceled: boolean; filePaths: string[] }>;
  };
  ipcMain: {
    handle: (channel: string, listener: (...args: unknown[]) => unknown) => void;
  };
  rendererPath: string;
  shell: { openPath: (filePath: string) => Promise<string> };
  startBackend: (options?: StartBackendOptions) => Promise<BackendHandle>;
  stopTimeoutMs: number;
  waitForBackend: (
    url: string,
    options?: WaitForBackendOptions,
  ) => Promise<void>;
}

export function createDesktopLifecycle(
  overrides: Partial<DesktopDependencies> = {},
): { start: () => Promise<boolean>; stopBackend: () => Promise<void> } {
  const dependencies: DesktopDependencies = {
    app: app as unknown as DesktopDependencies["app"],
    BrowserWindow,
    dialog: dialog as unknown as DesktopDependencies["dialog"],
    ipcMain,
    rendererPath: path.resolve(process.cwd(), "dist", "renderer", "index.html"),
    shell,
    startBackend,
    stopTimeoutMs: DEFAULT_STOP_TIMEOUT_MS,
    waitForBackend,
    ...overrides,
  };
  let backend: BackendHandle | undefined;
  let mainWindow: DesktopWindow | undefined;
  let migrationActive = false;
  let closeConfirmed = false;
  let shutdown: Promise<void> | undefined;
  let allowingQuit = false;

  const focusMainWindow = () => {
    if (!mainWindow || mainWindow.isDestroyed()) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  };

  const stopBackend = async () => {
    if (shutdown) return shutdown;
    shutdown = (async () => {
      if (!backend) return;
      const handle = backend;
      let stopped = false;
      await Promise.race([
        handle.stop().then(() => {
          stopped = true;
        }),
        delay(dependencies.stopTimeoutMs),
      ]).catch(() => undefined);
      if (!stopped && handle.process.exitCode === null && !handle.process.killed) {
        handle.process.kill("SIGKILL");
      }
    })();
    return shutdown;
  };

  dependencies.ipcMain.handle("desktop:get-backend-url", () => backend?.url);
  dependencies.ipcMain.handle("desktop:select-directory", async () => {
    const result = await dependencies.dialog.showOpenDialog(mainWindow, {
      properties: ["openDirectory", "createDirectory"],
    });
    return result.canceled ? undefined : result.filePaths[0];
  });
  dependencies.ipcMain.handle("desktop:select-enex-files", async () => {
    const result = await dependencies.dialog.showOpenDialog(mainWindow, {
      filters: [{ extensions: ["enex"], name: "Evernote export" }],
      properties: ["openFile", "multiSelections"],
    });
    return result.canceled ? [] : result.filePaths;
  });
  dependencies.ipcMain.handle("desktop:open-path", (_event, filePath: unknown) =>
    typeof filePath === "string" ? dependencies.shell.openPath(filePath) : "Invalid path",
  );
  dependencies.ipcMain.handle(
    "desktop:set-migration-active",
    (_event, active: unknown) => {
      migrationActive = active === true;
    },
  );
  dependencies.ipcMain.handle("desktop:confirm-close", () => {
    closeConfirmed = true;
    mainWindow?.close?.();
  });

  dependencies.app.on("second-instance", focusMainWindow);
  dependencies.app.on("before-quit", (event: { preventDefault: () => void }) => {
    if (allowingQuit) return;
    event.preventDefault();
    void stopBackend().finally(() => {
      allowingQuit = true;
      dependencies.app.quit();
    });
  });

  return {
    async start() {
      if (!dependencies.app.requestSingleInstanceLock()) {
        dependencies.app.quit();
        return false;
      }

      await dependencies.app.whenReady();
      backend = await dependencies.startBackend();
      try {
        await dependencies.waitForBackend(backend.url);
      } catch (error) {
        await stopBackend();
        throw error;
      }

      const rendererUrl = pathToFileURL(dependencies.rendererPath).toString();
      mainWindow = new dependencies.BrowserWindow({
        minHeight: 640,
        minWidth: 960,
        show: false,
        webPreferences: {
          contextIsolation: true,
          nodeIntegration: false,
          preload: path.join(__dirname, "preload.js"),
          sandbox: true,
        },
      });
      mainWindow.webContents.on("will-navigate", (event, url) => {
        if (url !== rendererUrl) event.preventDefault();
      });
      mainWindow.once("ready-to-show", () => mainWindow?.show?.());
      mainWindow.on("close", (event) => {
        if (migrationActive && !closeConfirmed) {
          event.preventDefault();
          mainWindow?.webContents.send("desktop:close-requested");
        }
      });
      await mainWindow.loadFile(dependencies.rendererPath);
      return true;
    },
    stopBackend,
  };
}

if (require.main === module) {
  void createDesktopLifecycle().start();
}
