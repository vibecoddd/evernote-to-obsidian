import type { LogEntry } from "../domain/types";

export function LogPanel({ logs, expanded, onExpandedChange }: { logs: LogEntry[]; expanded?: boolean; onExpandedChange?: (expanded: boolean) => void }) {
  return <details className="log-panel" open={expanded} onToggle={(event) => onExpandedChange?.(event.currentTarget.open)}>
    <summary>迁移日志（{logs.length}）</summary>
    {logs.length === 0 ? <p>尚无日志。</p> : <ol>
      {logs.map((entry, index) => <li key={`${entry.at}-${index}`} className={`log-${entry.level}`}><time dateTime={entry.at}>{entry.at}</time> {entry.message}</li>)}
    </ol>}
  </details>;
}
