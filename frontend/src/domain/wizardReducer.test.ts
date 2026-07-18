import { describe, expect, test } from "vitest";

import { initialWizardState, wizardReducer } from "./wizardReducer";

describe("wizardReducer", () => {
  test("preserves source and target form values when navigating forward", () => {
    const configured = wizardReducer(initialWizardState, {
      type: "form/source",
      source: {
        mode: "account",
        credentials: { username: "alice", password: "secret" },
      },
    });
    const withTarget = wizardReducer(configured, {
      type: "form/target",
      target: { output: { obsidian_vault: "/vault" } },
    });

    const next = wizardReducer(withTarget, { type: "navigation/next" });

    expect(next.step).toBe(1);
    expect(next.source.credentials.username).toBe("alice");
    expect(next.target.output.obsidian_vault).toBe("/vault");
  });

  test("preserves source and target form values when navigating back", () => {
    const state = {
      ...initialWizardState,
      step: 2,
      source: {
        ...initialWizardState.source,
        credentials: { username: "alice", password: "secret" },
      },
      target: {
        ...initialWizardState.target,
        output: { ...initialWizardState.target.output, obsidian_vault: "/vault" },
      },
    };

    const previous = wizardReducer(state, { type: "navigation/back" });

    expect(previous.step).toBe(1);
    expect(previous.source.credentials.username).toBe("alice");
    expect(previous.target.output.obsidian_vault).toBe("/vault");
  });

  test("clears an in-memory password when reset", () => {
    const state = wizardReducer(initialWizardState, {
      type: "form/source",
      source: {
        mode: "account",
        credentials: { username: "alice", password: "secret" },
      },
    });

    const reset = wizardReducer(state, { type: "reset" });

    expect(reset.source.credentials.password).toBe("");
    expect(reset.source.credentials.username).toBe("");
  });
});
