import type { PreflightIssue } from "../domain/types";

interface ErrorPanelProps { errors?: PreflightIssue[]; warnings?: PreflightIssue[]; message?: string | null }

export function ErrorPanel({ errors = [], warnings = [], message }: ErrorPanelProps) {
  if (!message && errors.length === 0 && warnings.length === 0) return null;
  return <section className="error-panel" aria-live="polite">
    {message && <p role="alert">{message}</p>}
    {errors.map((issue) => <p key={`error-${issue.code}`} role="alert">{issue.message}</p>)}
    {warnings.map((issue) => <p key={`warning-${issue.code}`} className="warning">{issue.message}</p>)}
  </section>;
}
