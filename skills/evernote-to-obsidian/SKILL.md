---
name: evernote-to-obsidian
description: Use when a user wants to migrate Evernote ENEX files or an Evernote account into an Obsidian vault, preview the migration, or inspect migration JSON with the evernote-to-obsidian CLI.
---

# Evernote to Obsidian

Use the installed `evernote-to-obsidian` command to move Evernote content into an Obsidian vault. Keep execution non-interactive, preview writes, and consume JSON results.

## Select the command

- Use `convert` when the user has an `.enex` file or directory. It does not contact Evernote and is the preferred path for agent work.
- Use `migrate` only when the user explicitly asks to export from an Evernote account. It requires credentials and network access.
- Ask for the ENEX path and Obsidian vault path when either is missing. Do not guess a vault or overwrite an unrelated directory.

## Check the CLI

Run:

```bash
command -v evernote-to-obsidian
evernote-to-obsidian --help
```

If the command is missing and the current project contains this repository's `pyproject.toml`, install it with `python3 -m pip install -e .`, then rerun `--help`. Do not install an unknown package or modify a managed Python environment without user direction.

## Convert ENEX files

Preview before writing:

```bash
evernote-to-obsidian convert \
  --input /path/export.enex \
  --output /path/ObsidianVault \
  --preview --json
```

For a directory, pass it to `--input`; the CLI discovers `.enex` files directly inside it. Parse the JSON object and inspect `success`, `stats`, `input`, `output`, and `error`.

If the preview succeeds and the user's request authorizes the migration, execute:

```bash
evernote-to-obsidian convert \
  --input /path/export.enex \
  --output /path/ObsidianVault \
  --json
```

Use `--config /path/config.yaml` when existing settings are needed; explicit `--input` and `--output` override YAML values.

## Run a full account migration

Supply credentials without placing them in command arguments or committed files:

```bash
EVERNOTE_USERNAME='user@example.com' \
EVERNOTE_PASSWORD='app-password' \
evernote-to-obsidian migrate \
  --config /path/config.yaml \
  --no-open --json
```

Prefer environment variables or a local untracked config. Never print or include the password in a response. If credentials are missing, stop with a clear request or recommend manual ENEX export; do not wait for a prompt.

Always pass `--no-open` so the agent does not launch a desktop application. Confirm the configured vault path before running a full migration.

## Handle results

- Treat a nonzero exit code or `success: false` as a failed operation. Read `error` and report the actionable cause; do not blindly retry a write.
- In JSON mode, stdout must contain exactly one JSON object. If progress text contaminates stdout, rerun with the repository's CLI installation or report the installation problem instead of guessing.
- On success, report the output vault and the relevant counts from `stats` (`total_notes`, `converted_notes`, `skipped_notes`, and attachments when present).
