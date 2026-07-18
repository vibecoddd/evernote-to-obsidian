import { useEffect, useRef, type ReactNode } from "react";

import { ActionBar } from "./ActionBar";
import { StepIndicator } from "./StepIndicator";

interface AppShellProps { step: number; canGoBack: boolean; canGoNext: boolean; onBack: () => void; onNext: () => void; children: ReactNode }

export function AppShell({ step, canGoBack, canGoNext, onBack, onNext, children }: AppShellProps) {
  const mainRef = useRef<HTMLElement>(null);
  useEffect(() => { mainRef.current?.focus(); }, [step]);
  return <div className="app-shell">
    <header><div className="brand"><p className="eyebrow">Evernote → Obsidian</p><h1>印象笔记迁移工具</h1></div><StepIndicator step={step} /></header>
    <main ref={mainRef} tabIndex={-1}>{children}</main>
    <footer><ActionBar canGoBack={canGoBack} canGoNext={canGoNext} onBack={onBack} onNext={onNext} /></footer>
  </div>;
}
