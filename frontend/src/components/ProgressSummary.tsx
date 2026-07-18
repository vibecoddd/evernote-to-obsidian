import type { MigrationProgress } from "../domain/types";

export function ProgressSummary({ migration }: { migration: MigrationProgress }) {
  const stats = migration.stats;
  return <section className="progress-summary" aria-labelledby="migration-progress-heading">
    <h2 id="migration-progress-heading">正在迁移</h2>
    {migration.stepName && <p>当前步骤：{migration.stepName}{migration.step && migration.totalSteps ? `（${migration.step}/${migration.totalSteps}）` : ""}</p>}
    <progress value={migration.progress} max={100} aria-label="迁移进度" />
    <strong>{migration.progress}%</strong>
    <p aria-live="polite">{migration.message || "正在准备迁移…"}</p>
    {stats && <dl className="migration-stats">
      {stats.total_notes !== undefined && <><dt>笔记总数</dt><dd>{stats.total_notes}</dd></>}
      {stats.converted_notes !== undefined && <><dt>已转换笔记</dt><dd>{stats.converted_notes}</dd></>}
      {stats.total_attachments !== undefined && <><dt>附件总数</dt><dd>{stats.total_attachments}</dd></>}
    </dl>}
  </section>;
}
