import { useEffect, useReducer, useState } from "react";

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
  const taskIsActive = state.migration.status === "running" || state.migration.status === "cancelling";

  useEffect(() => window.desktop.onCloseRequested(() => {
    if (taskIsActive) setCloseRequested(true);
    else void window.desktop.confirmClose();
  }), [taskIsActive]);

  const cancelAndClose = async () => {
    if (!state.migration.taskId) {
      dispatch({ type: "error", message: "迁移正在启动，请稍候再关闭窗口。" });
      setCloseRequested(false);
      return;
    }
    try {
      dispatch({ type: "migration/progress", progress: { ...state.migration, status: "cancelling", message: "正在取消迁移…" } });
      await api.cancel(state.migration.taskId);
      await window.desktop.confirmClose();
    } catch {
      dispatch({ type: "error", message: "无法取消迁移，窗口将保持打开。" });
      setCloseRequested(false);
    }
  };

  const canGoNext = !taskIsActive && (state.step === 0 ? sourceIsValid(state.source) : state.step === 1 ? targetIsValid(state.target) : false);
  const canGoBack = !taskIsActive && state.step > 0 && state.step < 3;
  const content = state.step === 0 ? <SourceStep source={state.source} dispatch={dispatch} />
    : state.step === 1 ? <TargetStep target={state.target} dispatch={dispatch} />
      : state.step === 2 ? <PreflightStep state={state} api={api} dispatch={dispatch} onConfirm={() => dispatch({ type: "navigation/next" })} />
        : state.step === 3 ? <MigrationStep state={state} api={api} dispatch={dispatch} onTerminal={() => dispatch({ type: "navigation/next" })} />
          : state.result ? <ResultStep result={state.result} vaultPath={state.target.output.obsidian_vault} logs={state.logs} onRestart={() => dispatch({ type: "reset" })} /> : null;

  return <><AppShell step={state.step} canGoBack={canGoBack} canGoNext={canGoNext} onBack={() => dispatch({ type: "navigation/back" })} onNext={() => dispatch({ type: "navigation/next" })}>{content}</AppShell>
    {closeRequested && <div className="close-confirmation" role="dialog" aria-modal="true" aria-labelledby="close-heading"><section><h2 id="close-heading">取消迁移并关闭？</h2><p>已写入的文件不会回滚。确认后将请求取消迁移并关闭窗口。</p><button type="button" onClick={() => void cancelAndClose()}>取消迁移并关闭</button><button type="button" className="secondary" onClick={() => setCloseRequested(false)}>继续迁移</button></section></div>}
  </>;
}
