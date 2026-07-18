import { useEffect, useRef, type Dispatch } from "react";

import { connectMigrationEvents, type ApiClient, type MigrationEvent } from "../api/client";
import type { MigrationProgress, MigrationRequest, TerminalResult, WizardAction, WizardState } from "../domain/types";
import { LogPanel } from "./LogPanel";
import { ProgressSummary } from "./ProgressSummary";

function requestFrom(state: WizardState): MigrationRequest {
  return { ...state.target, source_mode: state.source.mode, evernote_backend: state.source.evernote_backend, evernote_credentials: state.source.credentials, input: state.source.input };
}

function entry(message: string, level: "info" | "error" = "info") {
  return { level, message, at: new Date().toISOString() } as const;
}

function resultFromStatus(progress: MigrationProgress): TerminalResult | null {
  if (progress.status !== "completed" && progress.status !== "failed" && progress.status !== "cancelled") return null;
  return { status: progress.status, message: progress.message, stats: progress.stats };
}

export function MigrationStep({ state, api, dispatch, onTerminal }: { state: WizardState; api: ApiClient; dispatch: Dispatch<WizardAction>; onTerminal: () => void }) {
  const started = useRef(false);
  const terminal = useRef(false);
  const stateRef = useRef(state);
  const onTerminalRef = useRef(onTerminal);
  stateRef.current = state;
  onTerminalRef.current = onTerminal;

  useEffect(() => {
    if (!stateRef.current.preflight?.ok || started.current) return;
    started.current = true;
    let connection: { disconnect(): void } | undefined;
    let reconciliationTimer: ReturnType<typeof setInterval> | undefined;
    let desktopMigrationActive = false;
    let deactivatePromise: Promise<void> | undefined;
    let active = true;
    const stopTracking = () => {
      connection?.disconnect();
      connection = undefined;
      if (reconciliationTimer !== undefined) clearInterval(reconciliationTimer);
      reconciliationTimer = undefined;
    };
    const deactivate = async () => {
      if (!desktopMigrationActive) return deactivatePromise;
      desktopMigrationActive = false;
      deactivatePromise = window.desktop.setMigrationActive(false);
      try { await deactivatePromise; } finally { deactivatePromise = undefined; }
    };
    const finish = async (result: TerminalResult) => {
      if (terminal.current) return;
      terminal.current = true;
      stopTracking();
      if (active) {
        dispatch({ type: "migration/log", entry: entry(result.message, result.status === "failed" ? "error" : "info") });
        dispatch({ type: "migration/terminal", result });
      }
      await deactivate();
      if (active) onTerminalRef.current();
    };
    const consume = (event: MigrationEvent) => {
      if (event.type === "terminal") { void finish(event.result); return; }
      dispatch({ type: "migration/progress", progress: { ...stateRef.current.migration, taskId: event.taskId, status: "running", progress: event.progress, message: event.message, step: event.step, totalSteps: event.totalSteps, stepName: event.stepName, stats: event.stats ?? stateRef.current.migration.stats } });
      dispatch({ type: "migration/log", entry: entry(event.message) });
    };
    const reconcile = (taskId: string) => {
      void api.status(taskId).then((progress) => {
        if (!active || terminal.current) return;
        const result = resultFromStatus(progress);
        if (result) { void finish(result); return; }
        if (progress.status !== "not_found") dispatch({ type: "migration/progress", progress });
      }).catch(() => {
        // A worker may not have populated its state yet; the next poll reconciles it.
      });
    };
    const start = async () => {
      try {
        dispatch({ type: "migration/progress", progress: { ...stateRef.current.migration, status: "running", message: "正在启动迁移…" } });
        await window.desktop.setMigrationActive(true);
        desktopMigrationActive = true;
        if (!active) { await deactivate(); return; }
        const response = await api.start(requestFrom(stateRef.current));
        if (!active) { await deactivate(); return; }
        if (!response.success || !response.task_id) throw new Error(response.message || "迁移未能启动。");
        dispatch({ type: "migration/progress", progress: { ...stateRef.current.migration, taskId: response.task_id, status: "running", progress: 0, message: response.message } });
        dispatch({ type: "migration/log", entry: entry(response.message) });
        reconciliationTimer = setInterval(() => reconcile(response.task_id), 250);
        connection = connectMigrationEvents(stateRef.current.backend.url ?? window.location.origin, response.task_id, consume);
        reconcile(response.task_id);
      } catch (error) {
        await finish({ status: "failed", message: error instanceof Error ? error.message : "迁移未能启动。" });
      }
    };
    void start();
    return () => { active = false; stopTracking(); void deactivate(); };
  }, [api, dispatch]);

  return <section aria-labelledby="migration-heading"><h1 id="migration-heading" className="sr-only">执行迁移</h1><ProgressSummary migration={state.migration} /><LogPanel logs={state.logs} /></section>;
}
