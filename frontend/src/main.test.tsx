import { screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

beforeEach(() => {
  window.desktop = {
    getBackendUrl: vi.fn(() => new Promise<string>(() => undefined)), selectDirectory: vi.fn(), selectEnexFiles: vi.fn(),
    openPath: vi.fn(), setMigrationActive: vi.fn(), onCloseRequested: vi.fn(), confirmClose: vi.fn(),
  };
});

test("renders the startup status while the desktop bridge resolves", async () => {
  await import("./main");
  expect(await screen.findByText("印象笔记迁移工具正在启动…")).toBeInTheDocument();
});
