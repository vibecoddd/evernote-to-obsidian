import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { ResultStep } from "./ResultStep";

describe("ResultStep", () => {
  beforeEach(() => {
    window.desktop = {
      getBackendUrl: vi.fn(), selectDirectory: vi.fn(), selectEnexFiles: vi.fn(), openPath: vi.fn(),
      setMigrationActive: vi.fn(), onCloseRequested: vi.fn(), confirmClose: vi.fn(),
    };
  });

  test("lists failed paths for a partial result", () => {
    render(<ResultStep result={{ status: "completed", message: "完成", stats: { total_notes: 2, converted_notes: 1, errors: ["/vault/failed-note.md"] } }} vaultPath="/vault" logs={[]} onRestart={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "迁移部分完成" })).toBeInTheDocument();
    expect(screen.getByText("/vault/failed-note.md")).toBeInTheDocument();
  });

  test("opens the selected Vault only when the user requests it", async () => {
    const user = userEvent.setup();
    render(<ResultStep result={{ status: "completed", message: "完成" }} vaultPath="/vault" logs={[]} onRestart={vi.fn()} />);

    expect(window.desktop.openPath).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "打开 Vault" }));
    expect(window.desktop.openPath).toHaveBeenCalledWith("/vault");
  });
});
