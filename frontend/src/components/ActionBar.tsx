interface ActionBarProps { canGoBack: boolean; canGoNext: boolean; onBack: () => void; onNext: () => void; nextLabel?: string }

export function ActionBar({ canGoBack, canGoNext, onBack, onNext, nextLabel = "下一步" }: ActionBarProps) {
  return <div className="action-bar">
    <button type="button" className="secondary" onClick={onBack} disabled={!canGoBack}>上一步</button>
    <button type="button" onClick={onNext} disabled={!canGoNext}>{nextLabel}</button>
  </div>;
}
