// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

const electron = vi.hoisted(() => ({
  app: { getAppPath: () => "/test/app.asar" },
  BrowserWindow: class {},
  dialog: {},
  ipcMain: {},
  shell: {},
}));

vi.mock("electron", () => electron);

import {
  createDesktopLifecycle,
  reserveLoopbackPort,
  resolveRendererPath,
  startBackend,
  waitForBackend,
} from "./main";

describe("resolveRendererPath", () => {
  it("locates the bundled renderer beneath Electron's app path", () => {
    expect(resolveRendererPath("/Applications/Migrator.app/Contents/Resources/app.asar")).toBe(
      "/Applications/Migrator.app/Contents/Resources/app.asar/dist/renderer/index.html",
    );
  });
});

describe("waitForBackend", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("retries until health succeeds", async () => {
    const fetchImpl = vi
      .fn()
      .mockRejectedValueOnce(new Error("not ready"))
      .mockResolvedValueOnce(new Response('{"status":"ok"}', { status: 200 }));

    await waitForBackend("http://127.0.0.1:43123", {
      fetchImpl,
      timeoutMs: 100,
      intervalMs: 1,
    });

    expect(fetchImpl).toHaveBeenCalledTimes(2);
    expect(fetchImpl).toHaveBeenLastCalledWith(
      "http://127.0.0.1:43123/api/healthz",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it("reports the health URL and final failure after timing out", async () => {
    vi.useFakeTimers();
    const fetchImpl = vi.fn().mockRejectedValue(new Error("connection refused"));
    const rejection = expect(
      waitForBackend("http://127.0.0.1:43123", {
        fetchImpl,
        timeoutMs: 5,
        intervalMs: 1,
      }),
    ).rejects.toThrow("http://127.0.0.1:43123/api/healthz: connection refused");

    await vi.advanceTimersByTimeAsync(10);

    await rejection;
  });

  it("times out and aborts a health request that never settles", async () => {
    const fetchImpl = vi.fn<typeof fetch>(
      () => new Promise<Response>(() => undefined),
    );

    await expect(
      waitForBackend("http://127.0.0.1:43123", {
        fetchImpl,
        timeoutMs: 10,
      }),
    ).rejects.toThrow(
      "Backend health check timed out for http://127.0.0.1:43123/api/healthz: Health request timed out after 10ms",
    );

    expect(fetchImpl).toHaveBeenCalledOnce();
    expect(fetchImpl.mock.calls[0]?.[1]).toMatchObject({
      signal: expect.any(AbortSignal),
    });
  }, 200);
});

describe("reserveLoopbackPort", () => {
  it("returns an ephemeral TCP port that has been released", async () => {
    const port = await reserveLoopbackPort();

    expect(port).toBeGreaterThan(0);
    expect(port).toBeLessThanOrEqual(65535);
  });
});

describe("backend shutdown", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("force kills a child that remains alive after SIGTERM marks it killed", async () => {
    vi.useFakeTimers();
    const child = {
      exitCode: null as number | null,
      killed: false,
      kill: vi.fn((_signal: NodeJS.Signals) => {
        child.killed = true;
        return true;
      }),
      once: vi.fn(),
    };
    const backend = await startBackend({
      reservePort: vi.fn().mockResolvedValue(43123),
      spawnImpl: vi.fn().mockReturnValue(child),
      stopTimeoutMs: 5,
    });

    const stopping = backend.stop();
    expect(child.kill).toHaveBeenCalledWith("SIGTERM");

    await vi.advanceTimersByTimeAsync(5);
    await stopping;

    expect(child.kill).toHaveBeenLastCalledWith("SIGKILL");
  });
});

describe("desktop lifecycle", () => {
  it("focuses the existing window when a second instance starts", async () => {
    const secondInstanceHandlers: Array<() => void> = [];
    const window = {
      isDestroyed: vi.fn().mockReturnValue(false),
      isMinimized: vi.fn().mockReturnValue(true),
      restore: vi.fn(),
      focus: vi.fn(),
      on: vi.fn(),
      once: vi.fn(),
      loadFile: vi.fn().mockResolvedValue(undefined),
      webContents: { on: vi.fn(), send: vi.fn() },
    };
    const app = {
      getAppPath: vi.fn(() => "/app"),
      requestSingleInstanceLock: vi.fn().mockReturnValue(true),
      whenReady: vi.fn().mockResolvedValue(undefined),
      on: vi.fn((event: string, listener: () => void) => {
        if (event === "second-instance") secondInstanceHandlers.push(listener);
      }),
      quit: vi.fn(),
    };
    const lifecycle = createDesktopLifecycle({
      app,
      BrowserWindow: vi.fn(() => window),
      dialog: { showOpenDialog: vi.fn() },
      ipcMain: { handle: vi.fn() },
      shell: { openPath: vi.fn() },
      startBackend: vi.fn().mockResolvedValue({
        url: "http://127.0.0.1:43123",
        process: {},
        stop: vi.fn(),
      }),
      waitForBackend: vi.fn().mockResolvedValue(undefined),
      rendererPath: "/app/dist/renderer/index.html",
    });

    await lifecycle.start();
    secondInstanceHandlers[0]();

    expect(window.restore).toHaveBeenCalledOnce();
    expect(window.focus).toHaveBeenCalledOnce();
  });

  it("loads the renderer after health and stops the backend before quitting", async () => {
    const beforeQuitHandlers: Array<(event: { preventDefault: () => void }) => void> = [];
    const events: string[] = [];
    const window = {
      isDestroyed: vi.fn().mockReturnValue(false),
      isMinimized: vi.fn().mockReturnValue(false),
      restore: vi.fn(),
      focus: vi.fn(),
      on: vi.fn(),
      once: vi.fn(),
      loadFile: vi.fn().mockResolvedValue(undefined),
      webContents: { on: vi.fn(), send: vi.fn() },
    };
    const app = {
      getAppPath: vi.fn(() => "/app"),
      requestSingleInstanceLock: vi.fn().mockReturnValue(true),
      whenReady: vi.fn().mockResolvedValue(undefined),
      on: vi.fn((event: string, listener: (event: { preventDefault: () => void }) => void) => {
        if (event === "before-quit") beforeQuitHandlers.push(listener);
      }),
      quit: vi.fn(() => events.push("quit")),
    };
    const lifecycle = createDesktopLifecycle({
      app,
      BrowserWindow: vi.fn(() => window),
      dialog: { showOpenDialog: vi.fn() },
      ipcMain: { handle: vi.fn() },
      shell: { openPath: vi.fn() },
      startBackend: vi.fn().mockResolvedValue({
        url: "http://127.0.0.1:43123",
        process: {},
        stop: vi.fn(async () => events.push("stop")),
      }),
      waitForBackend: vi.fn().mockResolvedValue(undefined),
      rendererPath: "/app/dist/renderer/index.html",
    });

    await lifecycle.start();
    beforeQuitHandlers[0]({ preventDefault: vi.fn() });
    await vi.waitFor(() => expect(app.quit).toHaveBeenCalledOnce());

    expect(window.loadFile).toHaveBeenCalledWith("/app/dist/renderer/index.html");
    expect(events).toEqual(["stop", "quit"]);
  });

  it("reports a backend child exit before the health check timeout", async () => {
    const childExitHandlers: Array<(code: number | null, signal: NodeJS.Signals | null) => void> =
      [];
    const child = {
      exitCode: null as number | null,
      killed: false,
      kill: vi.fn((_signal: NodeJS.Signals) => true),
      once: vi.fn((event: string, listener: (code: number | null, signal: NodeJS.Signals | null) => void) => {
        if (event === "exit") childExitHandlers.push(listener);
      }),
    };
    let rejectHealth: ((error: Error) => void) | undefined;
    const app = {
      getAppPath: vi.fn(() => "/app"),
      requestSingleInstanceLock: vi.fn().mockReturnValue(true),
      whenReady: vi.fn().mockResolvedValue(undefined),
      on: vi.fn(),
      quit: vi.fn(),
    };
    const lifecycle = createDesktopLifecycle({
      app,
      BrowserWindow: vi.fn(),
      dialog: { showOpenDialog: vi.fn() },
      ipcMain: { handle: vi.fn() },
      shell: { openPath: vi.fn() },
      startBackend: vi.fn().mockResolvedValue({
        url: "http://127.0.0.1:43123",
        process: child,
        stop: vi.fn().mockResolvedValue(undefined),
      }),
      waitForBackend: vi.fn(
        () =>
          new Promise<void>((_resolve, reject) => {
            rejectHealth = reject;
          }),
      ),
      rendererPath: "/app/dist/renderer/index.html",
    });

    const starting = lifecycle.start();
    await vi.waitFor(() => expect(childExitHandlers).toHaveLength(1));
    child.exitCode = 78;
    childExitHandlers[0](78, null);
    rejectHealth?.(new Error("health timeout"));

    await expect(starting).rejects.toThrow(
      "Backend exited before health check with code 78",
    );
  });

  it("uses a longer health timeout for packaged sidecar cold starts", async () => {
    const child = {
      exitCode: null as number | null,
      killed: false,
      kill: vi.fn((_signal: NodeJS.Signals) => true),
      once: vi.fn(),
    };
    const window = {
      isDestroyed: vi.fn().mockReturnValue(false),
      isMinimized: vi.fn().mockReturnValue(false),
      restore: vi.fn(),
      focus: vi.fn(),
      on: vi.fn(),
      once: vi.fn(),
      loadFile: vi.fn().mockResolvedValue(undefined),
      webContents: { on: vi.fn(), send: vi.fn() },
    };
    const waitForBackend = vi.fn().mockResolvedValue(undefined);
    const app = {
      getAppPath: vi.fn(() => "/app"),
      isPackaged: true,
      requestSingleInstanceLock: vi.fn().mockReturnValue(true),
      whenReady: vi.fn().mockResolvedValue(undefined),
      on: vi.fn(),
      quit: vi.fn(),
    };
    const lifecycle = createDesktopLifecycle({
      app,
      BrowserWindow: vi.fn(() => window),
      dialog: { showOpenDialog: vi.fn() },
      ipcMain: { handle: vi.fn() },
      shell: { openPath: vi.fn() },
      startBackend: vi.fn().mockResolvedValue({
        url: "http://127.0.0.1:43123",
        process: child,
        stop: vi.fn(),
      }),
      waitForBackend,
      rendererPath: "/app/dist/renderer/index.html",
    });

    await lifecycle.start();

    expect(waitForBackend).toHaveBeenCalledWith("http://127.0.0.1:43123", {
      timeoutMs: 60_000,
    });
  });

  it("force kills a still-alive child when its stop method resolves prematurely", async () => {
    vi.useFakeTimers();
    const beforeQuitHandlers: Array<(event: { preventDefault: () => void }) => void> = [];
    const child = {
      exitCode: null as number | null,
      killed: false,
      kill: vi.fn((_signal: NodeJS.Signals) => {
        child.killed = true;
        return true;
      }),
      once: vi.fn(),
    };
    const window = {
      isDestroyed: vi.fn().mockReturnValue(false),
      isMinimized: vi.fn().mockReturnValue(false),
      restore: vi.fn(),
      focus: vi.fn(),
      on: vi.fn(),
      once: vi.fn(),
      loadFile: vi.fn().mockResolvedValue(undefined),
      webContents: { on: vi.fn(), send: vi.fn() },
    };
    const app = {
      getAppPath: vi.fn(() => "/app"),
      requestSingleInstanceLock: vi.fn().mockReturnValue(true),
      whenReady: vi.fn().mockResolvedValue(undefined),
      on: vi.fn((event: string, listener: (event: { preventDefault: () => void }) => void) => {
        if (event === "before-quit") beforeQuitHandlers.push(listener);
      }),
      quit: vi.fn(),
    };
    const lifecycle = createDesktopLifecycle({
      app,
      BrowserWindow: vi.fn(() => window),
      dialog: { showOpenDialog: vi.fn() },
      ipcMain: { handle: vi.fn() },
      shell: { openPath: vi.fn() },
      startBackend: vi.fn().mockResolvedValue({
        url: "http://127.0.0.1:43123",
        process: child,
        stop: vi.fn(async () => {
          child.kill("SIGTERM");
        }),
      }),
      stopTimeoutMs: 5,
      waitForBackend: vi.fn().mockResolvedValue(undefined),
      rendererPath: "/app/dist/renderer/index.html",
    });

    await lifecycle.start();
    beforeQuitHandlers[0]({ preventDefault: vi.fn() });
    await vi.advanceTimersByTimeAsync(5);

    expect(child.kill).toHaveBeenLastCalledWith("SIGKILL");
  });
});
