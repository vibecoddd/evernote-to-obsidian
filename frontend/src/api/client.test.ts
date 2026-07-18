import { describe, expect, test, vi } from "vitest";

const socketHandlers = new Map<string, (payload?: unknown) => void>();
const socket = {
  on: vi.fn((name: string, handler: (payload?: unknown) => void) => {
    socketHandlers.set(name, handler);
    return socket;
  }),
  off: vi.fn(),
  emit: vi.fn(),
  disconnect: vi.fn(),
};

vi.mock("socket.io-client", () => ({ io: vi.fn(() => socket) }));

import { connectMigrationEvents, createApiClient, normalizeMigrationEvent } from "./client";
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
  test.each([
    ["migration_completed", { task_id: "migration-1", success: true, result: { message: "Migration complete", stats: { total_notes: 4, converted_notes: 3, total_attachments: 2, errors: ["one failed"] } } }, { type: "terminal", taskId: "migration-1", result: { status: "completed", message: "Migration complete", stats: { total_notes: 4, converted_notes: 3, total_attachments: 2, errors: ["one failed"] } } }],
    ["migration_error", { task_id: "migration-2", error: "Evernote is unavailable" }, { type: "terminal", taskId: "migration-2", result: { status: "failed", message: "Evernote is unavailable" } }],
    ["migration_cancelled", { task_id: "migration-3" }, { type: "terminal", taskId: "migration-3", result: { status: "cancelled", message: "Migration cancelled" } }],
    ["export_completed", { task_id: "export-1", success: true, result: { message: "Export complete", stats: { total_notes: 7, exported_files: ["/tmp/export.enex"] } } }, { type: "terminal", taskId: "export-1", result: { status: "completed", message: "Export complete", stats: { total_notes: 7, exported_files: ["/tmp/export.enex"] } } }],
    ["export_error", { task_id: "export-2", error: "No ENEX files" }, { type: "terminal", taskId: "export-2", result: { status: "failed", message: "No ENEX files" } }],
    ["export_cancelled", { task_id: "export-3" }, { type: "terminal", taskId: "export-3", result: { status: "cancelled", message: "Migration cancelled" } }],
  ])("normalizes the backend %s payload", (name, payload, expected) => {
    expect(normalizeMigrationEvent(name, payload)).toEqual(expected);
  });
});

describe("connectMigrationEvents", () => {
  test("joins the task room on connection and removes listeners on disconnect", () => {
    socketHandlers.clear();
    vi.clearAllMocks();

    const connection = connectMigrationEvents("http://127.0.0.1:43123", "task-1", vi.fn());
    socketHandlers.get("connect")?.();

    expect(socket.emit).toHaveBeenCalledWith("join_task", { task_id: "task-1" });

    connection.disconnect();

    expect(socket.off).toHaveBeenCalledWith("connect", expect.any(Function));
    expect(socket.off).toHaveBeenCalledWith("migration_completed", expect.any(Function));
    expect(socket.disconnect).toHaveBeenCalledOnce();
  });
});
