import { render, screen, waitFor } from "@testing-library/react";
import { useReducer } from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiClient, MigrationEvent } from "../api/client";
import { initialWizardState, wizardReducer } from "../domain/wizardReducer";
import { MigrationStep } from "./MigrationStep";

let receiveEvent: ((event: MigrationEvent) => void) | undefined;

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return {
    ...actual,
    connectMigrationEvents: vi.fn((_url: string, _taskId: string, onEvent: (event: MigrationEvent) => void) => {
      receiveEvent = onEvent;
      return { disconnect: vi.fn() };
    }),
  };
});

const api: ApiClient = {
  health: vi.fn(),
  preflight: vi.fn(),
  start: vi.fn().mockResolvedValue({ success: true, task_id: "task-42", message: "Started" }),
  status: vi.fn(),
  cancel: vi.fn(),
};

function Harness() {
  const [state, dispatch] = useReducer(wizardReducer, {
    ...initialWizardState,
    preflight: { ok: true, errors: [], warnings: [], summary: { source_mode: "enex", enex_files: ["/export.enex"], vault: "/vault" } },
    source: { ...initialWizardState.source, mode: "enex", input: { ...initialWizardState.source.input, enex_files: ["/export.enex"] } },
    target: { ...initialWizardState.target, output: { ...initialWizardState.target.output, obsidian_vault: "/vault" } },
  });
  return <MigrationStep state={state} api={api} dispatch={dispatch} onTerminal={vi.fn()} />;
}

describe("MigrationStep", () => {
  beforeEach(() => {
    receiveEvent = undefined;
    window.desktop = {
      getBackendUrl: vi.fn(), selectDirectory: vi.fn(), selectEnexFiles: vi.fn(), openPath: vi.fn(),
      setMigrationActive: vi.fn().mockResolvedValue(undefined), onCloseRequested: vi.fn(), confirmClose: vi.fn(),
    };
  });

  test("renders a normalized progress event", async () => {
    render(<Harness />);

    await waitFor(() => expect(receiveEvent).toBeTypeOf("function"));
    receiveEvent?.({ type: "progress", taskId: "task-42", progress: 42, message: "正在转换笔记", step: 2, stepName: "转换为 Markdown" });

    expect(await screen.findByText("42%")).toBeInTheDocument();
    expect(screen.getByText("正在转换笔记", { selector: "p" })).toBeInTheDocument();
  });
});
