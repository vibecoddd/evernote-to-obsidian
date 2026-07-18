import { describe, expect, test, vi } from "vitest";

import { createApiClient, normalizeMigrationEvent } from "./client";
import type { MigrationRequest } from "../domain/types";

describe("createApiClient", () => {
  test("keeps structured 422 preflight issues", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({
        ok: false,
        errors: [{ code: "vault_missing", message: "Select a vault." }],
        warnings: [],
        summary: { source_mode: "enex", enex_files: [], vault: null },
      }), { status: 422, headers: { "content-type": "application/json" } }),
    );

    await expect(createApiClient("http://127.0.0.1:43123", fetchMock).preflight({} as MigrationRequest)).rejects.toMatchObject({
      status: 422,
      code: "vault_missing",
      message: "Select a vault.",
    });
  });
});

describe("normalizeMigrationEvent", () => {
  test("normalizes export progress into the migration event shape", () => {
    expect(normalizeMigrationEvent("export_progress", {
      task_id: "task-1", progress: 50, message: "Exporting",
    })).toEqual({ type: "progress", taskId: "task-1", progress: 50, message: "Exporting" });
  });
});
