import { io, type Socket } from "socket.io-client";

import type { MigrationProgress, MigrationRequest, PreflightIssue, PreflightResult, ProgressStatistics, TerminalResult } from "../domain/types";

type JsonRecord = Record<string, unknown>;
type FetchLike = typeof fetch;

export class ApiError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null;
}

function issues(value: unknown): PreflightIssue[] {
  return Array.isArray(value)
    ? value.filter(isRecord).flatMap((issue) => typeof issue.code === "string" && typeof issue.message === "string"
      ? [{ code: issue.code, message: issue.message }] : [])
    : [];
}

async function responseJson(response: Response): Promise<unknown> {
  try { return await response.json(); } catch { return {}; }
}

export async function requestJson<T>(fetcher: FetchLike, url: string, init?: RequestInit): Promise<T> {
  const response = await fetcher(url, init);
  const body = await responseJson(response);
  if (!response.ok) {
    const data = isRecord(body) ? body : {};
    const firstIssue = issues(data.errors)[0];
    const message = firstIssue?.message ?? (typeof data.message === "string" ? data.message : typeof data.error === "string" ? data.error : response.statusText || `Request failed (${response.status})`);
    throw new ApiError(response.status, firstIssue?.code ?? (typeof data.code === "string" ? data.code : "request_failed"), message);
  }
  return body as T;
}

function endpoint(baseUrl: string, path: string): string {
  return new URL(path, baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`).toString();
}

export interface StartMigrationResponse { success: boolean; task_id: string; message: string }
export interface CancelMigrationResponse { task_id: string; status: "cancelling" }
export interface ApiClient {
  health(): Promise<{ status: "ok" }>;
  preflight(config: MigrationRequest): Promise<PreflightResult>;
  start(config: MigrationRequest): Promise<StartMigrationResponse>;
  status(taskId: string): Promise<MigrationProgress>;
  cancel(taskId: string): Promise<CancelMigrationResponse>;
}

export function createApiClient(baseUrl: string, fetcher: FetchLike = fetch): ApiClient {
  const json = <T>(path: string, init?: RequestInit) => requestJson<T>(fetcher, endpoint(baseUrl, path), init);
  const post = <T>(path: string, body?: unknown) => json<T>(path, { method: "POST", headers: { "content-type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  return {
    health: () => json("/api/healthz"),
    preflight: (config) => post("/api/preflight", config),
    start: (config) => post("/api/start_migration", config),
    status: async (taskId) => normalizeStatus(await json<JsonRecord>(`/api/migration_status/${encodeURIComponent(taskId)}`), taskId),
    cancel: (taskId) => post(`/api/cancel_migration/${encodeURIComponent(taskId)}`),
  };
}

function number(value: unknown): number | undefined { return typeof value === "number" ? value : undefined; }
function string(value: unknown): string | undefined { return typeof value === "string" ? value : undefined; }
function stats(value: unknown): ProgressStatistics | undefined { return isRecord(value) ? value as ProgressStatistics : undefined; }

function normalizeStatus(data: JsonRecord, taskId: string): MigrationProgress {
  return {
    taskId, status: (string(data.status) ?? "idle") as MigrationProgress["status"], progress: number(data.progress) ?? 0,
    message: string(data.message) ?? "", step: number(data.step), totalSteps: number(data.total_steps),
    stepName: string(data.current_step_name), stats: stats(data.stats),
  };
}

export type MigrationEvent =
  | { type: "progress"; taskId: string; progress: number; message: string; step?: number; stepName?: string }
  | { type: "terminal"; taskId: string; result: TerminalResult };

export function normalizeMigrationEvent(name: string, payload: unknown): MigrationEvent | null {
  if (!isRecord(payload) || typeof payload.task_id !== "string") return null;
  const taskId = payload.task_id;
  if (name === "migration_progress" || name === "export_progress") {
    return { type: "progress", taskId, progress: number(payload.progress) ?? 0, message: string(payload.message) ?? "", step: number(payload.step), stepName: string(payload.step_name) };
  }
  if (name === "migration_completed" || name === "export_completed") {
    const result = isRecord(payload.result) ? payload.result : {};
    return { type: "terminal", taskId, result: { status: payload.success === false ? "failed" : "completed", message: string(result.message) ?? string(payload.message) ?? "", stats: stats(result.stats) } };
  }
  if (name === "migration_cancelled" || name === "export_cancelled") return { type: "terminal", taskId, result: { status: "cancelled", message: string(payload.message) ?? "Migration cancelled" } };
  if (name === "migration_error" || name === "export_error") return { type: "terminal", taskId, result: { status: "failed", message: string(payload.error) ?? "Migration failed" } };
  return null;
}

export function connectMigrationEvents(baseUrl: string, taskId: string, onEvent: (event: MigrationEvent) => void): { disconnect(): void } {
  const socket: Socket = io(baseUrl, { transports: ["websocket", "polling"] });
  const names = ["migration_progress", "migration_completed", "migration_cancelled", "migration_error", "export_progress", "export_completed", "export_cancelled", "export_error"];
  socket.on("connect", () => socket.emit("join_task", { task_id: taskId }));
  for (const name of names) socket.on(name, (payload: unknown) => { const event = normalizeMigrationEvent(name, payload); if (event?.taskId === taskId) onEvent(event); });
  return { disconnect: () => socket.disconnect() };
}
