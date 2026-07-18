# Task 2: Python desktop backend contract report

## Status and commit

- Task 2 commit: `cea8df0 feat: add desktop backend health and preflight APIs`
- Base inspected: `eed5f1d docs: record Task 1 review fixes`
- The user-owned `欢迎使用Obsidian.md` remained modified and unstaged throughout.

## Contract delivered

- `src.desktop_api.preflight_config(config_data)` returns exactly `ok`, `errors`, `warnings`, and `summary`. It expands user paths; validates ENEX mode files and suffixes; requires account credentials in account mode; and checks an existing Vault or the parent/create option for a missing Vault without creating files during preflight.
- `backend_app.py` exposes only `--port` and `--debug`; `run_backend` sets desktop mode and runs `WebMigrator` on `127.0.0.1` with `allow_unsafe_werkzeug=True`.
- `web_app.py` now exposes `GET /api/healthz`, `POST /api/preflight` (200/422), and `POST /api/cancel_migration/<task_id>` (200/404). Desktop mode limits Flask and Socket.IO CORS to `null`, `http://localhost:5173`, and `http://127.0.0.1:5173`; ordinary Web mode retains its existing wildcard Socket.IO policy.
- Migration cancellation uses one `threading.Event` per task, checks it before migration phases and inside the ENEX-file loop, preserves files already written, records `cancelled`, and emits `migration_cancelled`.

## RED/GREEN evidence

1. RED — `.venv/bin/pytest -q test_desktop_api.py`
   - Result: collection error, `ModuleNotFoundError: No module named 'src.desktop_api'`.
2. GREEN — `.venv/bin/pytest -q test_desktop_api.py`
   - Result: `3 passed in 0.14s` after the initial preflight implementation.
3. RED — `.venv/bin/pytest -q test_backend_app.py test_desktop_api.py`
   - Result: `2 failed, 3 passed`; `/api/healthz` returned 404 and `backend_app` was missing.
4. RED — after adding the preflight endpoint test, the same focused command reported `3 failed, 3 passed`; health and preflight returned 404 and the sidecar module was absent.
5. GREEN — `.venv/bin/pytest -q test_backend_app.py test_desktop_api.py`
   - Result: `6 passed, 1 warning in 2.62s` after health, preflight, CORS, and sidecar implementation.
6. RED — after adding cancellation tests, the focused command reported `2 failed, 6 passed`; `WebMigrator` lacked `cancel_events`.
7. GREEN — `.venv/bin/pytest -q test_backend_app.py test_desktop_api.py`
   - Result: `8 passed, 1 warning in 5.41s` after cancellation implementation.
8. RED — `.venv/bin/pytest -q test_desktop_api.py`
   - Result: `1 failed, 3 passed`; explicit account mode incorrectly accepted stale ENEX paths without credentials.
9. GREEN — `.venv/bin/pytest -q test_desktop_api.py`
   - Result: `4 passed in 0.07s` after mode selection was corrected.

## Final test evidence

Commands run:

```text
.venv/bin/pytest -q test_web_integration.py
# 1 passed, 1 warning in 6.03s

.venv/bin/pytest -q test_backend_app.py test_desktop_api.py test_web_integration.py
# 10 passed, 2 warnings in 8.09s

git diff --check
# exit 0; no output
```

## Changed files

- `backend_app.py`
- `src/desktop_api.py`
- `web_app.py`
- `requirements.txt`
- `test_backend_app.py`
- `test_desktop_api.py`

## Self-review

- Confirmed the sidecar run call has exact loopback host, supplied port/debug values, and `allow_unsafe_werkzeug=True`.
- Confirmed preflight has a JSON-compatible, fixed-shape response and returns 422 for invalid input.
- Confirmed existing route names and existing Socket.IO event names were retained; the only added event is `migration_cancelled`.
- Confirmed known-task cancellation is machine-readable and unknown tasks return HTTP 404.
- Confirmed cancellation stops at phase boundaries and at every ENEX file, without cleanup/rollback behavior.
- Confirmed `git diff --check` was clean and the commit staged only the six Task 2 files.

## Concerns

- The focused test run emits an existing Eventlet deprecation warning from its installed transport dependency.
- `test_web_integration.py` emits an existing `PytestReturnNotNoneWarning` because its test function returns a boolean. This task intentionally preserved that Web integration behavior.

## Fixes

- `web_app.py`: `/api/start_export` now creates a cancellation event. Export work checks it at each phase boundary, records `cancelled`, emits `export_cancelled`, and intentionally leaves already-created ENEX files in place.
- `test_backend_app.py`: added deterministic fake-exporter tests for pre-export and post-export cancellation, plus default Web route assertions for `/`, `/config`, `/migrate`, and `/results`.
- `test_web_integration.py`: moved the real-account workflow into `run_web_integration()` and skips it under pytest, so the existing command remains usable without network credentials or a return-value warning.

Exact verification commands and output:

```text
.venv/bin/pytest -q test_backend_app.py test_desktop_api.py
# 13 passed, 1 warning in 2.31s

.venv/bin/pytest -q test_web_integration.py
# 1 skipped in 0.01s

git diff --check
# exit 0; no output
```

The remaining warning is Eventlet's installed-dependency deprecation warning; no PytestReturnNotNoneWarning is emitted.
