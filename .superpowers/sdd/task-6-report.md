# Task 6: Migration progress and result workflow report

## Implementation

- Added `MigrationStep`, `ProgressSummary`, `LogPanel`, and `ResultStep` for the preflight-gated migration lifecycle, collapsed retained logs, terminal results, explicit Vault opening, and password-clearing restart.
- `App` now manages running-state navigation locks and the native close request confirmation. Active migrations are cancelled through the backend before close confirmation; the in-window copy warns that written files are not rolled back.
- The reducer preserves terminal statistics and completes successful progress at 100%.

### Changed files

- `frontend/src/App.tsx`
- `frontend/src/domain/wizardReducer.ts`
- `frontend/src/styles/app.css`
- `frontend/src/components/MigrationStep.tsx`
- `frontend/src/components/ProgressSummary.tsx`
- `frontend/src/components/LogPanel.tsx`
- `frontend/src/components/ResultStep.tsx`

### Tests

- Added `frontend/src/components/MigrationStep.test.tsx` for normalized Socket.IO progress rendering.
- Added `frontend/src/components/ResultStep.test.tsx` for partial-result failed paths and the explicit Vault-open action.
- `npm run test:frontend` — 10 files, 31 tests passed.
- `npm run typecheck` — passed.
- `npm run build` — passed.

### Concerns

- The backend only includes detailed statistics in terminal payloads today; progress events retain the latest known statistics until the terminal event supplies the final values.
- Closing during the very short interval before the start endpoint returns a task ID leaves the window open with a clear instruction to wait, since there is not yet an API target to cancel.
