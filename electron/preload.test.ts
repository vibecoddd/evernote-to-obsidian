// @vitest-environment node

import { describe, expect, it, vi } from "vitest";

const electron = vi.hoisted(() => ({
  contextBridge: { exposeInMainWorld: vi.fn() },
  ipcRenderer: { invoke: vi.fn(), on: vi.fn(), removeListener: vi.fn() },
}));

vi.mock("electron", () => electron);

import "./preload";

describe("desktop preload bridge", () => {
  it("exposes only the documented seven-method bridge", () => {
    expect(electron.contextBridge.exposeInMainWorld).toHaveBeenCalledOnce();
    const [name, bridge] = electron.contextBridge.exposeInMainWorld.mock.calls[0];

    expect(name).toBe("desktop");
    expect(Object.keys(bridge).sort()).toEqual([
      "confirmClose",
      "getBackendUrl",
      "onCloseRequested",
      "openPath",
      "selectDirectory",
      "selectEnexFiles",
      "setMigrationActive",
    ]);
  });

  it("uses named IPC channels and unsubscribes close listeners", () => {
    const bridge = electron.contextBridge.exposeInMainWorld.mock.calls[0][1];
    const callback = vi.fn();

    bridge.getBackendUrl();
    bridge.selectDirectory();
    bridge.selectEnexFiles();
    bridge.openPath("/tmp/vault");
    bridge.setMigrationActive(true);
    const unsubscribe = bridge.onCloseRequested(callback);
    bridge.confirmClose();
    unsubscribe();

    expect(electron.ipcRenderer.invoke.mock.calls).toEqual([
      ["desktop:get-backend-url"],
      ["desktop:select-directory"],
      ["desktop:select-enex-files"],
      ["desktop:open-path", "/tmp/vault"],
      ["desktop:set-migration-active", true],
      ["desktop:confirm-close"],
    ]);
    expect(electron.ipcRenderer.on).toHaveBeenCalledWith(
      "desktop:close-requested",
      expect.any(Function),
    );
    expect(electron.ipcRenderer.removeListener).toHaveBeenCalledWith(
      "desktop:close-requested",
      expect.any(Function),
    );
  });
});
