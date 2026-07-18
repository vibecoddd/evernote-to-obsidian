import { useState } from "react";

import type { LogEntry, TerminalResult } from "../domain/types";
import { LogPanel } from "./LogPanel";

function outcome(result: TerminalResult): "success" | "partial" | "failed" | "cancelled" {
  const stats = result.stats;
  if (result.status === "cancelled") return "cancelled";
  if (result.status === "failed") return "failed";
  if ((stats?.errors?.length ?? 0) > 0 || (stats?.total_notes !== undefined && stats.converted_notes !== undefined && stats.converted_notes < stats.total_notes)) return "partial";
  return "success";
}

const headings = { success: "迁移完成", partial: "迁移部分完成", failed: "迁移失败", cancelled: "迁移已取消" };

export function ResultStep({ result, vaultPath, logs, onRestart }: { result: TerminalResult; vaultPath: string; logs: LogEntry[]; onRestart: () => void }) {
  const [logsExpanded, setLogsExpanded] = useState(false);
  const kind = outcome(result);
  const openVault = () => void window.desktop.openPath(vaultPath);
  return <section aria-labelledby="result-heading"><h2 id="result-heading">{headings[kind]}</h2><p>{result.message}</p>
    {kind === "cancelled" && <p>已写入的文件不会回滚。</p>}
    {result.stats && <dl className="migration-stats">
      {result.stats.total_notes !== undefined && <><dt>笔记总数</dt><dd>{result.stats.total_notes}</dd></>}
      {result.stats.converted_notes !== undefined && <><dt>已转换笔记</dt><dd>{result.stats.converted_notes}</dd></>}
      {result.stats.total_attachments !== undefined && <><dt>附件总数</dt><dd>{result.stats.total_attachments}</dd></>}
    </dl>}
    {kind === "partial" && <><h3>未完成的路径</h3><ul>{result.stats?.errors?.map((path) => <li key={path}>{path}</li>)}</ul></>}
    <div className="result-actions"><button type="button" onClick={openVault} disabled={!vaultPath}>打开 Vault</button><button type="button" className="secondary" onClick={() => setLogsExpanded(true)}>展开日志</button><button type="button" className="secondary" onClick={onRestart}>重新开始</button></div>
    <LogPanel logs={logs} expanded={logsExpanded} onExpandedChange={setLogsExpanded} />
  </section>;
}
