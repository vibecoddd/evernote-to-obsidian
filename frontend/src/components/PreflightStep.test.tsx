import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import type { ApiClient } from "../api/client";
import { initialWizardState } from "../domain/wizardReducer";
import { PreflightStep } from "./PreflightStep";

const readyState = {
  ...initialWizardState,
  source: { ...initialWizardState.source, mode: "enex" as const, input: { ...initialWizardState.source.input, enex_files: ["/exports/work.enex"] } },
  target: { ...initialWizardState.target, output: { ...initialWizardState.target.output, obsidian_vault: "/vault" } },
};

test("shows warnings but allows confirmation after a successful preflight", async () => {
  const user = userEvent.setup();
  const api = { preflight: vi.fn().mockResolvedValue({ ok: true, errors: [], warnings: [{ code: "vault_will_be_created", message: "Vault will be created" }], summary: { source_mode: "enex", enex_files: ["/exports/work.enex"], vault: "/vault" } }) } as unknown as ApiClient;
  const dispatch = vi.fn();
  const next = vi.fn();
  render(<PreflightStep state={readyState} api={api} dispatch={dispatch} onConfirm={next} />);

  await waitFor(() => expect(api.preflight).toHaveBeenCalledOnce());
  expect(screen.getByText("Vault will be created")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "确认并开始迁移" }));
  expect(next).toHaveBeenCalledOnce();
});

test("keeps confirmation unavailable when preflight reports blocking errors", async () => {
  const api = { preflight: vi.fn().mockResolvedValue({ ok: false, errors: [{ code: "vault_missing", message: "Select a Vault" }], warnings: [], summary: { source_mode: "enex", enex_files: [], vault: null } }) } as unknown as ApiClient;
  render(<PreflightStep state={readyState} api={api} dispatch={vi.fn()} onConfirm={vi.fn()} />);

  expect(await screen.findByText("Select a Vault")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "确认并开始迁移" })).toBeDisabled();
});
