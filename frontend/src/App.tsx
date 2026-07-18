import { useEffect, useReducer, useRef, useState } from "react";

import type { ApiClient } from "./api/client";
import { initialWizardState, wizardReducer } from "./domain/wizardReducer";
import { AppShell } from "./components/AppShell";
import { MigrationStep } from "./components/MigrationStep";
import { PreflightStep } from "./components/PreflightStep";
import { ResultStep } from "./components/ResultStep";
import { SourceStep, sourceIsValid } from "./components/SourceStep";
import { TargetStep, targetIsValid } from "./components/TargetStep";

export function App({ api }: { api: ApiClient }) {
  const [state, dispatch] = useReducer(wizardReducer, initialWizardState);
  const [closeRequested, setCloseRequested] = useState(false);
  const [closeCancellationRequested, setCloseCancellationRequested] = useState(false);
  const [closeCancellationInFlight, setCloseCancellationInFlight] = useState(false);
  const closeCancellationInFlightRef = useRef(false);
  const closeCancellationTaskRef = useRef<string | null>(null);
  const closeConfirmationFinalizedRef = useRef(false);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const continueButtonRef = useRef<HTMLButtonElement>(null);
  const taskIsActive = state.migration.status === "running" || state.migration.status === "cancelling";

  useEffect(() => window.desktop.onCloseRequested(() => {
    if (taskIsActive) {
      setCloseRequested(true);
      setCloseCancellationRequested(false);
      closeCancellationTaskRef.current = null;
      closeConfirmationFinalizedRef.current = false;
    }
    else void window.desktop.confirmClose();
  }), [taskIsActive]);

  const dismissCloseRequest = () => {
    if (closeCancellationInFlightRef.current) return;
    setCloseCancellationRequested(false);
    setCloseRequested(false);
    window.setTimeout(() => returnFocusRef.current?.focus(), 0);
  };

  useEffect(() => {
    if (!closeRequested) return;
    returnFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    continueButtonRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        dismissCloseRequest();
        return;
      }
      if (event.key !== "Tab") return;
      const buttons = Array.from(document.querySelectorAll<HTMLButtonElement>(".close-confirmation button:not(:disabled)"));
      if (buttons.length === 0) return;
      const first = buttons[0];
      const last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [closeRequested]);

  useEffect(() => {
    if (!closeCancellationRequested || !taskIsActive || !state.migration.taskId || closeCancellationInFlightRef.current || closeCancellationTaskRef.current === state.migration.taskId) return;
    closeCancellationInFlightRef.current = true;
    closeCancellationTaskRef.current = state.migration.taskId;
    setCloseCancellationInFlight(true);
    const progressBeforeCancellation = state.migration;
    dispatch({ type: "migration/progress", progress: { ...progressBeforeCancellation, status: "cancelling", message: "正在取消迁移…" } });
    void api.cancel(state.migration.taskId).then(() => {
      if (closeConfirmationFinalizedRef.current) return;
      closeConfirmationFinalizedRef.current = true;
      return window.desktop.confirmClose();
    }).catch(() => {
      closeCancellationTaskRef.current = null;
      dispatch({ type: "migration/progress", progress: { ...progressBeforeCancellation, status: "running", message: "迁移仍在进行。" } });
      dispatch({ type: "error", message: "无法取消迁移，窗口将保持打开。" });
      setCloseCancellationRequested(false);
      setCloseRequested(false);
    }).finally(() => {
      closeCancellationInFlightRef.current = false;
      setCloseCancellationInFlight(false);
    });
  }, [api, closeCancellationRequested, state.migration, taskIsActive]);

  useEffect(() => {
    if (!closeCancellationRequested || taskIsActive || closeCancellationInFlightRef.current || closeConfirmationFinalizedRef.current) return;
    closeConfirmationFinalizedRef.current = true;
    void window.desktop.confirmClose();
  }, [closeCancellationRequested, taskIsActive]);

  const canGoNext = !taskIsActive && (state.step === 0 ? sourceIsValid(state.source) : state.step === 1 ? targetIsValid(state.target) : false);
  const canGoBack = !taskIsActive && state.step > 0 && state.step < 3;
  const content = state.step === 0 ? <SourceStep source={state.source} dispatch={dispatch} />
    : state.step === 1 ? <TargetStep target={state.target} dispatch={dispatch} />
      : state.step === 2 ? <PreflightStep state={state} api={api} dispatch={dispatch} onConfirm={() => dispatch({ type: "navigation/next" })} />
        : state.step === 3 ? <MigrationStep state={state} api={api} dispatch={dispatch} onTerminal={() => dispatch({ type: "navigation/next" })} />
          : state.result ? <ResultStep result={state.result} vaultPath={state.target.output.obsidian_vault} logs={state.logs} onRestart={() => dispatch({ type: "reset" })} /> : null;

  return <><AppShell step={state.step} canGoBack={canGoBack} canGoNext={canGoNext} onBack={() => dispatch({ type: "navigation/back" })} onNext={() => dispatch({ type: "navigation/next" })}>{content}</AppShell>
    {closeRequested && <div className="close-confirmation" role="dialog" aria-modal="true" aria-labelledby="close-heading" aria-describedby="close-description"><section><h2 id="close-heading">取消迁移并关闭？</h2><p id="close-description">已写入的文件不会回滚。确认后将请求取消迁移并关闭窗口。</p><button type="button" onClick={() => setCloseCancellationRequested(true)} disabled={closeCancellationInFlight}>{closeCancellationInFlight ? "正在取消迁移…" : "取消迁移并关闭"}</button><button ref={continueButtonRef} type="button" className="secondary" onClick={dismissCloseRequest} disabled={closeCancellationInFlight}>继续迁移</button></section></div>}
  </>;
}
