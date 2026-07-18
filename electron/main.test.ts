// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

const electron = vi.hoisted(() => ({
  app: {},
  BrowserWindow: class {},
  dialog: {},
  ipcMain: {},
  shell: {},
}));

vi.mock("electron", () => electron);

import {
  createDesktopLifecycle,
  reserveLoopbackPort,
  waitForBackend,
} from "./main";

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
});

describe("reserveLoopbackPort", () => {
  it("returns an ephemeral TCP port that has been released", async () => {
    const port = await reserveLoopbackPort();

    expect(port).toBeGreaterThan(0);
    expect(port).toBeLessThanOrEqual(65535);
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
});
