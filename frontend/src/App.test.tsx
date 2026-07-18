import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiClient } from "./api/client";
import { App } from "./App";

const api: ApiClient = {
  health: vi.fn(), preflight: vi.fn(), start: vi.fn(), status: vi.fn(), cancel: vi.fn(),
};

describe("setup wizard shell", () => {
  let closeListener: (() => void) | undefined;

  beforeEach(() => {
    vi.clearAllMocks();
    window.desktop = {
      getBackendUrl: vi.fn(), selectDirectory: vi.fn(), selectEnexFiles: vi.fn(), openPath: vi.fn(),
      setMigrationActive: vi.fn().mockResolvedValue(undefined), onCloseRequested: vi.fn((listener) => { closeListener = listener; return vi.fn(); }), confirmClose: vi.fn(),
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

  test("defers an accepted close request until the pending start returns a task id", async () => {
    const user = userEvent.setup();
    let resolveStart: (value: { success: boolean; task_id: string; message: string }) => void;
    vi.mocked(api.preflight).mockResolvedValue({ ok: true, errors: [], warnings: [], summary: { source_mode: "account", enex_files: [], vault: "/vault" } });
    vi.mocked(api.start).mockImplementationOnce(() => new Promise((resolve) => { resolveStart = resolve; }));
    vi.mocked(api.status).mockResolvedValue({ taskId: "task-42", status: "running", progress: 0, message: "Started" });
    vi.mocked(api.cancel).mockResolvedValue({ task_id: "task-42", status: "cancelling" });
    vi.mocked(window.desktop.selectDirectory).mockResolvedValue("/vault");
    render(<App api={api} />);

    await user.type(screen.getByLabelText("用户名"), "name");
    await user.type(screen.getByLabelText("密码"), "password");
    await user.click(screen.getByRole("button", { name: "下一步" }));
    await user.click(screen.getByRole("button", { name: "选择 Vault 目录" }));
    await user.click(screen.getByRole("button", { name: "下一步" }));
    await user.click(await screen.findByRole("button", { name: "确认并开始迁移" }));
    await waitFor(() => expect(window.desktop.setMigrationActive).toHaveBeenCalledWith(true));

    document.querySelector("main")?.focus();
    closeListener?.();
    const dialog = await screen.findByRole("dialog", { name: "取消迁移并关闭？" });
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("button", { name: "继续迁移" })).toHaveFocus();

    await user.click(screen.getByRole("button", { name: "取消迁移并关闭" }));
    expect(api.cancel).not.toHaveBeenCalled();
    expect(window.desktop.confirmClose).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "继续迁移" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());

    resolveStart!({ success: true, task_id: "task-42", message: "Started" });
    await waitFor(() => expect(api.start).toHaveBeenCalled());
    expect(api.cancel).not.toHaveBeenCalled();
    closeListener?.();
    await screen.findByRole("dialog", { name: "取消迁移并关闭？" });
    await user.click(screen.getByRole("button", { name: "取消迁移并关闭" }));
    await waitFor(() => expect(api.cancel).toHaveBeenCalledWith("task-42"));
    await waitFor(() => expect(window.desktop.confirmClose).toHaveBeenCalledOnce());
  });

  test("dismisses a close request with Escape and restores focus without changing migration state", async () => {
    const user = userEvent.setup();
    vi.mocked(api.preflight).mockResolvedValue({ ok: true, errors: [], warnings: [], summary: { source_mode: "account", enex_files: [], vault: "/vault" } });
    vi.mocked(api.start).mockResolvedValue({ success: true, task_id: "task-42", message: "Started" });
    vi.mocked(api.status).mockResolvedValue({ taskId: "task-42", status: "running", progress: 0, message: "Started" });
    vi.mocked(window.desktop.selectDirectory).mockResolvedValue("/vault");
    render(<App api={api} />);

    await user.type(screen.getByLabelText("用户名"), "name");
    await user.type(screen.getByLabelText("密码"), "password");
    await user.click(screen.getByRole("button", { name: "下一步" }));
    await user.click(screen.getByRole("button", { name: "选择 Vault 目录" }));
    await user.click(screen.getByRole("button", { name: "下一步" }));
    await user.click(await screen.findByRole("button", { name: "确认并开始迁移" }));
    await waitFor(() => expect(api.start).toHaveBeenCalled());

    const main = document.querySelector("main")!;
    main.focus();
    closeListener?.();
    await screen.findByRole("dialog", { name: "取消迁移并关闭？" });
    await user.keyboard("{Escape}");

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(main).toHaveFocus();
    expect(api.cancel).not.toHaveBeenCalled();
    expect(window.desktop.confirmClose).not.toHaveBeenCalled();
  });
});
