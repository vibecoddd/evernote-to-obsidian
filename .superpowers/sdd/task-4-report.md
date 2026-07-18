# Task 4: Typed renderer state and API client report

## Status

Implemented the Task 4 renderer model, immutable wizard reducer, typed backend transport, Socket.IO migration/export event adapter, and retryable Electron bridge bootstrap.

## Commits

- Task 4 implementation: `4679468` (`feat: add typed wizard state and backend client`)
- Starting Task 3 state: `3525355` (`fix: address Task 3 review findings`)

## Changed files

- Created `frontend/src/domain/types.ts`: strict wizard, Python-config, preflight, progress, log, terminal-result, and action types. Passwords are explicitly renderer-memory credentials only.
- Created `frontend/src/domain/wizardReducer.ts`: immutable navigation/form/preflight/migration/error/reset reducer and Python-aligned defaults.
- Created `frontend/src/domain/wizardReducer.test.ts`: form-preservation and password-reset reducer coverage.
- Created `frontend/src/api/client.ts`: typed HTTP transport, structured `ApiError`, status adapters, Socket.IO task-room connection, and migration/export event normalization.
- Created `frontend/src/api/client.test.ts`: structured 422 and export-progress normalization coverage.
- Modified `frontend/src/main.tsx`: awaits `window.desktop.getBackendUrl()`, constructs the client, and renders a retryable startup failure.

## RED/GREEN evidence

### Reducer

RED:

```text
$ npm run test:frontend -- frontend/src/domain/wizardReducer.test.ts
FAIL Failed to resolve import "./wizardReducer"
```

GREEN:

```text
PASS frontend/src/domain/wizardReducer.test.ts (3 tests)
```

### API client

RED:

```text
$ npm run test:frontend -- frontend/src/api/client.test.ts
FAIL Failed to resolve import "./client"
```

GREEN:

```text
PASS frontend/src/api/client.test.ts (2 tests)
```

## Final verification

```text
$ npm run test:frontend -- frontend/src/domain frontend/src/api
Test Files  2 passed (2)
Tests  5 passed (5)

$ npm run typecheck
PASS: tsc -p tsconfig.json --noEmit && tsc -p tsconfig.electron.json --noEmit

$ npm run build
Test Files  5 passed (5)
Tests  16 passed (16)
PASS: vite build --config vite.config.ts
PASS: tsc -p tsconfig.electron.json

$ git diff --check
PASS: no output
```

## Self-review and concerns

- Verified the reducer preserves source and target values during navigation and reset returns a fresh state with an empty password.
- Verified non-2xx JSON errors are converted to `ApiError { status, code, message }`; request bodies are never logged.
- The backend currently emits migration and export events with related but not identical payloads; the adapter covers the documented progress, completed, cancelled, and error forms. Future backend event fields will need explicit adapter updates.
- The startup screen intentionally retains only the constructed client for Task 5 to consume; it does not start a migration or persist credentials.
- The pre-existing unstaged edit to `欢迎使用Obsidian.md` remains untouched and unstaged. Existing `.superpowers/sdd` task materials also remain uncommitted.

## Fixes

- Added table-driven API client coverage for the backend's migration/export completed, error, and cancelled event payloads, including completion statistics and the cancellation-message fallback.
- Added a focused Socket.IO connection test verifying that the client joins the task room after connect and removes registered listeners before disconnecting.
- Updated `connectMigrationEvents` to unregister its `connect` and task-event listeners during `disconnect()`.

### Review-fix RED/GREEN evidence

RED:

```text
$ npm run test:frontend -- frontend/src/api/client.test.ts
FAIL connectMigrationEvents > joins the task room on connection and removes listeners on disconnect
expected socket.off to be called; received 0 calls
```

GREEN:

```text
$ npm run test:frontend -- frontend/src/api/client.test.ts
PASS frontend/src/api/client.test.ts (8 tests)
```
