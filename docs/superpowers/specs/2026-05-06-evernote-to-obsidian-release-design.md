# Evernote to Obsidian Release Tool Design

Date: 2026-05-06

## Goal

Build a release-grade one-click migration tool from Yinxiang/Evernote China to Obsidian, based on the current repository and the upstream `evernote-backup` project. The tool must support both a local Web interface and a full command-line interface, preserve notebook structure, attachments, and readable metadata, and ship as Windows and macOS release packages.

The first release focuses on Yinxiang/Evernote China account sync plus local ENEX import. Evernote International account sync is not a first-release goal, but ENEX files exported from other sources should still be importable.

## User Decisions

- Delivery target: release-grade tool.
- Platforms: Windows and macOS.
- Migration inputs: account sync plus local ENEX import.
- Account sync scope: Yinxiang/Evernote China first.
- Attachment layout: one shared vault-level attachment directory.
- Metadata: complete readable YAML frontmatter.
- Web shape: local Web server that opens in the browser.
- CLI shape: full command set for migration, import, sync, recovery, reports, and diagnostics.
- Recovery: resumable migration tasks.
- `evernote-backup`: fixed bundled version in release packages.
- Security: do not save passwords; keep only local encrypted/session task state where needed.

## Existing Context

The current repository already contains a prototype migration stack:

- `migrate.py` and `src/unified_migrator.py` provide a CLI-oriented migration flow.
- `web_app.py`, `templates/`, and `static/` provide a Flask/Socket.IO Web interface.
- `src/evernote_exporter.py` shells out to `evernote-backup`.
- `src/enex_parser.py`, `src/markdown_converter.py`, and `src/file_organizer.py` parse ENEX, convert notes, and write files.
- `src/deduplication_manager.py`, `src/sync_manager.py`, and `src/obsidian_manager.py` contain early support for deduplication, sync state, and vault setup.

The existing code should be reorganized around a shared task engine instead of maintaining separate Web and CLI behavior.

The upstream `evernote-backup` README describes the capabilities this design relies on: local SQLite sync, ENEX export by notebooks, support for both Evernote and Yinxiang, `--backend china` for Yinxiang credentials, resumable `sync`, offline `export`, `reauth`, and `--use-system-ssl-ca` for SSL troubleshooting.

## Architecture

Use a release-grade single Python application with clear package boundaries. The Web UI and CLI are thin interfaces over the same migration engine.

Core packages:

- `migration_core`: task orchestration, task state, progress events, logs, error classification, reports, and resume behavior.
- `evernote_source`: wrapper around the bundled fixed-version `evernote-backup`; owns `init-db`, `reauth`, `sync`, and `export`.
- `enex_import`: parses synced or user-provided ENEX files into a shared `Note` and `Resource` model.
- `obsidian_writer`: writes Markdown, attachments, notebook directories, YAML frontmatter, indexes, and migration reports.
- `interfaces.cli`: command-line entry points.
- `interfaces.web`: local Flask/Socket.IO service and Web pages.
- `packaging`: Windows and macOS packaging scripts and smoke tests.

Runtime data goes into an application data directory, not the Obsidian vault. Each migration creates a task directory such as `tasks/<task-id>/` containing the local `evernote-backup` database, exported ENEX files, task state, logs, and reports.

The vault receives only user-facing output: Markdown notes, attachments, optional notebook indexes, and optional migration reports.

## Data Flow

### Account Sync

1. User starts a Yinxiang/Evernote China account migration from Web or CLI.
2. The tool creates a task directory and records initial configuration.
3. Password is accepted through a Web form or CLI prompt, used only in memory, and passed to the sync step.
4. `evernote_source` runs the bundled `evernote-backup` flow:
   - `init-db` for new tasks or `reauth` when required.
   - `sync` to download account data into SQLite.
   - `export` to create ENEX files by notebook.
5. `enex_import` parses the exported ENEX files.
6. `obsidian_writer` writes Markdown, attachments, indexes, and reports to the target vault.

### Local ENEX Import

1. User uploads ENEX files in Web or passes files to CLI.
2. The tool records those files in the task directory.
3. The import starts at ENEX parsing and reuses the same writer, metadata, deduplication, and reporting path as account sync.

### Obsidian Output

Default vault structure:

```text
<vault>/
  <notebook>/
    <note-title>.md
    <note-title>-<short-id>.md
    <notebook>_Index.md
  attachments/
    <note-guid-or-content-hash>/
      <filename.ext>
  migration-reports/
    <task-id>.md
    <task-id>.json
```

Notes preserve notebook structure by default. Invalid path characters are sanitized consistently across Windows and macOS. Path length limits are enforced before writing, with deterministic shortening and report entries when names are changed.

Attachments live in `attachments/<note-guid-or-content-hash>/` to avoid filename collisions. Markdown content links attachments with Obsidian-compatible links by default. A future setting may allow standard relative Markdown links, but the first release defaults to Obsidian wiki-style links.

YAML frontmatter includes readable metadata:

- `title`
- `evernote_guid`
- `created`
- `updated`
- `notebook`
- `tags`
- `source`
- `source_url`
- `author`
- latitude/longitude/altitude when present
- attachment list
- migration task id
- migration timestamp
- content hash

File conflict behavior:

- Same GUID or same content hash maps to the same logical note and is not duplicated.
- Same title with different GUID gets a short deterministic suffix.
- Existing user files are not overwritten unless the user explicitly selects overwrite mode.

## Web Interface

The release package starts a local service bound to `127.0.0.1` on a random available port and opens the browser automatically. It does not listen on LAN interfaces.

The first screen is the migration workspace, not a marketing landing page.

Main screens:

- Source selection: Yinxiang account sync or local ENEX import.
- Target selection: choose or create an Obsidian vault path.
- Options: preserve notebook structure, unified attachment directory, YAML metadata, conflict strategy, indexes, and reports.
- Run page: phase progress, current log line, elapsed time, error details, resume/retry controls.
- Result page: notes converted, notes skipped, failed notes, attachment count, output path, and links to reports.

Web API rules:

- Sensitive endpoints require a local session token.
- Password fields are never persisted in browser local storage or task state.
- Logs sent to the browser are redacted.
- Uploaded ENEX files are stored only in the task directory and can be deleted through task cleanup.

## CLI

The CLI should be useful both for one-click migration and for diagnosis.

Commands:

- `evernote2obsidian migrate`: account sync and full migration to a vault.
- `evernote2obsidian import-enex <files...>`: import local ENEX files to a vault.
- `evernote2obsidian sync`: sync account and export ENEX without writing the vault.
- `evernote2obsidian resume <task-id>`: resume a failed or interrupted task.
- `evernote2obsidian report <task-id>`: show or export a task report.
- `evernote2obsidian doctor`: check network, SSL, bundled dependency, write permissions, disk space, path limits, and Obsidian target path.
- `evernote2obsidian web`: start the local Web interface.

CLI and Web subscribe to the same progress events from `migration_core`. CLI displays progress bars and concise logs; Web displays WebSocket updates.

## Recovery And Task State

Tasks have explicit phases:

- `created`
- `auth_ready`
- `synced`
- `exported`
- `parsed`
- `written`
- `verified`
- `completed`
- `failed`

Each phase writes state after successful completion. Resume starts after the last completed phase. If a phase is partially complete, its component records decide what can be reused.

State records include:

- task id
- tool version
- bundled `evernote-backup` version
- platform
- source mode
- target vault
- ENEX file inventory
- parsed note inventory
- written file inventory
- error list
- warnings
- timestamps

The account sync phase relies on `evernote-backup` SQLite incremental sync. The write phase relies on GUID/content hash and attachment hash to avoid duplicate notes and duplicate attachments.

## Errors

Errors are classified and surfaced with user actions.

Authentication errors:

- account not found
- wrong password
- expired token
- two-factor or application password issue

Network errors:

- DNS failure
- SSL certificate failure
- proxy interference
- server unavailable
- retry exhaustion

Data errors:

- invalid ENEX XML
- corrupt base64 resource
- unknown MIME type
- HTML/ENML conversion failure

Output errors:

- vault path not writable
- disk full
- path too long
- filename conflict
- invalid characters after sanitization

Packaging/runtime errors:

- bundled `evernote-backup` unavailable
- subprocess launch failure
- browser launch failure
- port allocation failure

The migration report includes failed notes and resources without stopping the whole task when skipping is safe. Fatal errors stop the task and preserve enough state for diagnosis or resume.

## Security

Passwords are never saved. They are accepted only for the authentication step and removed from application-level references after subprocess launch.

Task directories may contain sensitive data: local SQLite database, tokens generated by `evernote-backup`, ENEX exports, logs, and reports. They stay in the user data directory, not in the vault. The Web UI and CLI must show the cache location and provide cleanup.

Logs must redact:

- passwords
- auth tokens
- cookies
- full request headers
- command invocations containing credentials

The Web server binds only to `127.0.0.1`. Browser APIs require a session token to prevent unrelated local pages from starting tasks.

Release packages pin dependency versions. Reports record versions for reproducibility.

## Non-Goals For First Release

- Evernote International account sync as a first-class supported path.
- Tasks and reminders sync. Upstream support requires extra token handling outside the public API flow, so this should be deferred.
- Native desktop shell with Electron or Tauri.
- Linux release package.
- Cloud-hosted migration service.
- Automatic Obsidian plugin installation beyond optional generated settings or recommendations.

## Testing

Unit tests:

- ENEX parser handles notes, tags, timestamps, attributes, resources, and corrupt records.
- ENML/HTML conversion handles tables, todos, links, images, and unsupported tags.
- Frontmatter generation escapes strings and preserves metadata.
- Filename/path sanitizer works on Windows and macOS constraints.
- Attachment layout and deduplication are deterministic.
- Task state machine resumes correctly.
- Error classifier maps common subprocess and parsing failures.

Integration tests:

- Sample ENEX files convert into the expected vault structure.
- Attachments are written and linked correctly.
- Duplicate notes do not create duplicate Markdown files.
- Reports include counts, warnings, and skipped items.

Web/CLI smoke tests:

- `doctor` completes in packaged and source environments.
- `import-enex` converts a sample ENEX file.
- `report` reads a completed task.
- local Web starts, creates an ENEX import task, streams progress, and shows a result page.

Account sync tests:

- Not run in default CI.
- Manual release checklist uses environment variables or local secure input for a test Yinxiang account.
- Logs and reports from real-account tests are reviewed for redaction before release.

Release package tests:

- Windows package runs without external Python or user-installed `evernote-backup`.
- macOS package runs without external Python or user-installed `evernote-backup`.
- Local Web starts and opens the browser.
- CLI imports sample ENEX.
- Task cache cleanup works.

## Packaging And Release

Package the Python application with a fixed bundled `evernote-backup` version. Directory-style packages are preferred for the first release because they make dynamic dependencies and diagnostics easier than a single-file executable.

Windows:

- ship a directory bundle with `evernote2obsidian.exe`
- include Web assets and templates
- include CLI entry point
- provide a PowerShell smoke test script

macOS:

- ship a command-line bundle or `.app`
- first release may be unsigned or ad-hoc signed with clear Gatekeeper instructions
- later releases should add Developer ID signing and notarization

Release documentation:

- quick start
- Web usage
- CLI reference
- troubleshooting
- security and cache location
- release test checklist

Versioning:

- record tool version
- record bundled Python version
- record bundled `evernote-backup` version
- record platform test results

## Implementation Order

1. Reorganize the current prototype into package boundaries without changing user behavior.
2. Build `migration_core` task state, progress events, reports, and error classification.
3. Wrap `evernote-backup` behind `evernote_source`.
4. Stabilize ENEX parsing, metadata extraction, attachment handling, and Obsidian writer behavior.
5. Replace current CLI with the full command set.
6. Replace Web routes with task-engine-backed flows.
7. Add tests and sample ENEX fixtures.
8. Add packaging scripts and release smoke tests.
9. Update documentation for release users.

