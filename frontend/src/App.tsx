import { useReducer } from "react";

import type { ApiClient } from "./api/client";
import { initialWizardState, wizardReducer } from "./domain/wizardReducer";
import { AppShell } from "./components/AppShell";
import { PreflightStep } from "./components/PreflightStep";
import { SourceStep, sourceIsValid } from "./components/SourceStep";
import { TargetStep, targetIsValid } from "./components/TargetStep";

export function App({ api }: { api: ApiClient }) {
  const [state, dispatch] = useReducer(wizardReducer, initialWizardState);
  const canGoNext = state.step === 0 ? sourceIsValid(state.source) : state.step === 1 ? targetIsValid(state.target) : false;
  const content = state.step === 0 ? <SourceStep source={state.source} dispatch={dispatch} />
    : state.step === 1 ? <TargetStep target={state.target} dispatch={dispatch} />
      : state.step === 2 ? <PreflightStep state={state} api={api} dispatch={dispatch} onConfirm={() => dispatch({ type: "navigation/next" })} />
        : <section aria-labelledby="next-stage-heading"><h2 id="next-stage-heading">此步骤将在下一阶段实现</h2><p>请先完成迁移预检。</p></section>;
  return <AppShell step={state.step} canGoBack={state.step > 0} canGoNext={canGoNext} onBack={() => dispatch({ type: "navigation/back" })} onNext={() => dispatch({ type: "navigation/next" })}>{content}</AppShell>;
}
