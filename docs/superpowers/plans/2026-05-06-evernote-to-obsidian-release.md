# Evernote to Obsidian Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first release-grade Windows/macOS-capable Evernote China/Yinxiang to Obsidian migration tool with a shared core engine, full CLI, local Web UI, resumable tasks, complete metadata, unified attachments, diagnostics, packaging scripts, and tests.

**Architecture:** Introduce a focused `evernote_to_obsidian` package under `src/` and make the existing root entry points delegate to it. Web and CLI call the same task engine. The current prototype modules remain available during migration but the new implementation owns release behavior.

**Tech Stack:** Python 3, Click, Flask, Flask-SocketIO, html2text, PyYAML, PyInstaller packaging scripts, pytest-compatible tests.

**Execution Mode:** Inline execution in this session, because the user explicitly asked not to stop for execution choices.

---

### Task 1: Core Package, Models, State, Reports

**Files:**
- Create: `src/evernote_to_obsidian/__init__.py`
- Create: `src/evernote_to_obsidian/models.py`
- Create: `src/evernote_to_obsidian/paths.py`
- Create: `src/evernote_to_obsidian/errors.py`
- Create: `src/evernote_to_obsidian/events.py`
- Create: `src/evernote_to_obsidian/state.py`
- Create: `src/evernote_to_obsidian/reports.py`
- Test: `tests/test_core_state.py`

- [ ] **Step 1: Write failing core state tests**

Create tests that instantiate a task state in a temporary app-data directory, advance phases, reload the JSON state file, redact a sensitive command, and write JSON/Markdown reports.

Run: `pytest tests/test_core_state.py -v`

Expected: FAIL because the package and classes do not exist yet.

- [ ] **Step 2: Implement core dataclasses and utilities**

Implement:

- `Resource`, `Note`, `MigrationConfig`, `TaskStats`, and `TaskReport`
- app data path helpers with `EVERNOTE2OBSIDIAN_HOME` override
- deterministic note id helpers based on GUID or content hash
- error categories and redaction helpers
- progress event dataclass and callback dispatcher
- `TaskStateStore` that writes atomic JSON state files
- report JSON and Markdown writers

- [ ] **Step 3: Run core tests**

Run: `pytest tests/test_core_state.py -v`

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```bash
git add src/evernote_to_obsidian tests/test_core_state.py
git commit -m "feat: add migration core state and reports"
```

### Task 2: ENEX Import, Markdown Conversion, Obsidian Writer

**Files:**
- Create: `src/evernote_to_obsidian/enex.py`
- Create: `src/evernote_to_obsidian/markdown.py`
- Create: `src/evernote_to_obsidian/writer.py`
- Test: `tests/fixtures/sample_complex.enex`
- Test: `tests/test_enex_writer.py`

- [ ] **Step 1: Write failing ENEX writer tests**

Create a sample ENEX fixture with:

- notebook title
- one note with GUID, created/updated timestamps, tags, source URL, author, geolocation, todo, link, table, and an inline `en-media`
- one binary resource with a filename and MIME type
- a second note with the same title but a different GUID

Tests must verify:

- parser returns the notebook name and two notes
- resource hash is the MD5 hex of decoded data
- YAML frontmatter includes complete readable metadata
- attachments are written under `attachments/<note-id>/`
- same-title notes do not overwrite each other
- notebook index and migration reports are created

Run: `pytest tests/test_enex_writer.py -v`

Expected: FAIL because parser and writer do not exist yet.

- [ ] **Step 2: Implement ENEX parser**

Implement XML parsing with `xml.etree.ElementTree`, robust timestamp parsing, note attribute extraction, resource decoding, MIME extension fallback, content hash generation, and notebook fallback to file stem when ENEX lacks notebook metadata.

- [ ] **Step 3: Implement Markdown converter**

Implement ENML cleanup, `en-todo` checkbox conversion, `en-media` replacement using writer-provided attachment links, html2text conversion, YAML frontmatter generation with PyYAML, and Obsidian wiki links for attachments.

- [ ] **Step 4: Implement Obsidian writer**

Implement vault creation, Windows/macOS-safe path sanitization, deterministic attachment layout, conflict-safe note filenames, per-notebook index files, report writing, and note timestamp preservation when available.

- [ ] **Step 5: Run ENEX writer tests**

Run: `pytest tests/test_enex_writer.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/evernote_to_obsidian/enex.py src/evernote_to_obsidian/markdown.py src/evernote_to_obsidian/writer.py tests/fixtures/sample_complex.enex tests/test_enex_writer.py
git commit -m "feat: add ENEX import and Obsidian writer"
```

### Task 3: Task Runner, Resume, Doctor

**Files:**
- Create: `src/evernote_to_obsidian/runner.py`
- Create: `src/evernote_to_obsidian/doctor.py`
- Test: `tests/test_runner.py`

- [ ] **Step 1: Write failing runner tests**

Tests must verify:

- `import_enex` creates a task directory and transitions through `created`, `parsed`, `written`, `verified`, and `completed`
- progress callbacks receive phase events
- `resume(task_id)` continues a task with existing ENEX inventory
- `doctor` reports vault write permissions, disk space, Python version, path length capability, Web port availability, and `evernote-backup` command availability without requiring a real account

Run: `pytest tests/test_runner.py -v`

Expected: FAIL because runner and doctor do not exist yet.

- [ ] **Step 2: Implement task runner**

Implement `MigrationRunner` with:

- task creation
- source-mode inventory
- import ENEX flow
- account-sync flow entry point delegated to `EvernoteBackupSource`
- resume by task id
- report retrieval
- structured stats and skipped-error records

- [ ] **Step 3: Implement doctor checks**

Implement local checks for Python version, app data writeability, vault writeability, disk free space, command availability, path length, and local port binding.

- [ ] **Step 4: Run runner tests**

Run: `pytest tests/test_runner.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/evernote_to_obsidian/runner.py src/evernote_to_obsidian/doctor.py tests/test_runner.py
git commit -m "feat: add resumable migration runner"
```

### Task 4: Evernote Backup Wrapper And CLI

**Files:**
- Create: `src/evernote_to_obsidian/evernote_backup.py`
- Create: `src/evernote_to_obsidian/cli.py`
- Modify: `migrate.py`
- Modify: `requirements.txt`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Use `click.testing.CliRunner` to verify:

- `doctor` emits JSON when `--json` is passed
- `import-enex` writes the sample fixture into a vault
- `report <task-id>` reads a completed task
- `sync --dry-run` validates arguments without contacting Evernote
- help output includes `migrate`, `import-enex`, `sync`, `resume`, `report`, `doctor`, and `web`

Run: `pytest tests/test_cli.py -v`

Expected: FAIL because CLI does not exist yet.

- [ ] **Step 2: Implement `evernote-backup` wrapper**

Implement subprocess wrapper with:

- fixed command discovery
- `init-db`, `reauth`, `sync`, and `export`
- backend default `china`
- `--use-system-ssl-ca`
- password redaction in stored command/log output
- dry-run support for tests

- [ ] **Step 3: Implement Click CLI**

Implement commands:

- `migrate`
- `import-enex`
- `sync`
- `resume`
- `report`
- `doctor`
- `web`

Root `migrate.py` delegates to `evernote_to_obsidian.cli:cli`.

- [ ] **Step 4: Pin release dependency**

Change `evernote-backup>=1.9.0` to the fixed version selected for the release.

- [ ] **Step 5: Run CLI tests**

Run: `pytest tests/test_cli.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/evernote_to_obsidian/evernote_backup.py src/evernote_to_obsidian/cli.py migrate.py requirements.txt tests/test_cli.py
git commit -m "feat: add release CLI commands"
```

### Task 5: Local Web UI Backed By Task Engine

**Files:**
- Create: `src/evernote_to_obsidian/web.py`
- Modify: `web_app.py`
- Modify: `templates/migrate.html`
- Modify: `templates/results.html`
- Modify: `static/js/app.js`
- Test: `tests/test_web_release.py`

- [ ] **Step 1: Write failing Web tests**

Use Flask test client to verify:

- `/api/doctor` returns JSON diagnostics
- `/api/import_enex` accepts a fixture upload and target vault path
- `/api/migration_status/<task-id>` returns completed state for the import task
- `/api/report/<task-id>` returns JSON report
- root pages render without requiring external account access

Run: `pytest tests/test_web_release.py -v`

Expected: FAIL because release Web wrapper does not exist yet.

- [ ] **Step 2: Implement Web app factory**

Implement `create_app()` and local task registry backed by `MigrationRunner`. Keep server binding default to `127.0.0.1`; random port selection is handled by CLI `web`.

- [ ] **Step 3: Update root `web_app.py`**

Make root script delegate to `evernote_to_obsidian.web:main` and preserve `python web_app.py` behavior.

- [ ] **Step 4: Update frontend API calls**

Update migration upload and status calls to use the new endpoints. Keep account sync UI present, but make backend default to `china` and route through the new task engine.

- [ ] **Step 5: Run Web tests**

Run: `pytest tests/test_web_release.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/evernote_to_obsidian/web.py web_app.py templates/migrate.html templates/results.html static/js/app.js tests/test_web_release.py
git commit -m "feat: connect web UI to migration engine"
```

### Task 6: Packaging, Release Docs, Full Verification

**Files:**
- Create: `packaging/pyinstaller-evernote2obsidian.spec`
- Create: `packaging/build_windows.ps1`
- Create: `packaging/build_macos.sh`
- Create: `packaging/smoke_test.py`
- Create: `docs/release-checklist.md`
- Modify: `README.md`
- Modify: `WEB_USAGE_GUIDE.md`

- [ ] **Step 1: Add packaging scripts**

Create PyInstaller spec and platform scripts that include templates, static files, docs, and the package entry points.

- [ ] **Step 2: Add smoke test script**

Smoke test must run `doctor`, import `tests/fixtures/sample_complex.enex` into a temporary vault, inspect the generated report, and exit nonzero on failure.

- [ ] **Step 3: Update user docs**

Update README, Web guide, CLI command reference, security/cache notes, troubleshooting, and release checklist.

- [ ] **Step 4: Run full verification**

Run:

```bash
pytest -q
python migrate.py doctor --json
python migrate.py import-enex tests/fixtures/sample_complex.enex --vault /tmp/evernote2obsidian-smoke-vault --app-data /tmp/evernote2obsidian-smoke-data
python packaging/smoke_test.py
```

Expected: all commands pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add packaging docs README.md WEB_USAGE_GUIDE.md
git commit -m "chore: add release packaging and docs"
```

