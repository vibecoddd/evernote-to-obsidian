import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiClient } from "./api/client";
import { App } from "./App";

const api: ApiClient = {
  health: vi.fn(), preflight: vi.fn(), start: vi.fn(), status: vi.fn(), cancel: vi.fn(),
};

describe("setup wizard shell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.desktop = {
      getBackendUrl: vi.fn(), selectDirectory: vi.fn(), selectEnexFiles: vi.fn(), openPath: vi.fn(),
      setMigrationActive: vi.fn(), onCloseRequested: vi.fn(), confirmClose: vi.fn(),
    };
  });

  test("renders five setup labels and marks the active step", () => {
    render(<App api={api} />);

    const navigation = screen.getByRole("navigation", { name: "迁移步骤" });
    for (const label of ["选择数据源", "配置目标", "迁移预检", "执行迁移", "迁移结果"]) {
      expect(within(navigation).getByText(label)).toBeInTheDocument();
    }
    expect(within(navigation).getByText("选择数据源").closest("li")).toHaveAttribute("aria-current", "step");
  });

  test("selects multiple ENEX files through the desktop bridge and preserves them after back navigation", async () => {
    const user = userEvent.setup();
    vi.mocked(window.desktop.selectEnexFiles).mockResolvedValue(["/exports/work.enex", "/exports/archive.enex"]);
    render(<App api={api} />);

    await user.click(screen.getByRole("radio", { name: "ENEX 文件" }));
    await user.click(screen.getByRole("button", { name: "选择 ENEX 文件" }));
    expect(window.desktop.selectEnexFiles).toHaveBeenCalledOnce();
    expect(screen.getByText("/exports/work.enex")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "下一步" }));
    await user.click(screen.getByRole("button", { name: "上一步" }));
    expect(screen.getByText("/exports/work.enex")).toBeInTheDocument();
    expect(screen.getByText("/exports/archive.enex")).toBeInTheDocument();
  });
});
