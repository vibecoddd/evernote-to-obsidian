# Release Checklist

Use this checklist before publishing a Windows or macOS build.

## Required Verification

- Run `pytest -q`.
- Run `python migrate.py doctor --json`.
- Run `python packaging/smoke_test.py`.
- Build the platform bundle with the matching script:
  - Windows: `powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1`
  - macOS: `bash packaging/build_macos.sh`
- Run the packaged CLI:
  - `dist/evernote2obsidian/evernote2obsidian doctor --json`
  - `dist/evernote2obsidian/evernote2obsidian import-enex tests/fixtures/sample_complex.enex --vault <temp-vault>`
- Start the packaged local Web UI and import the sample ENEX file.

## Manual Account Sync Check

Default CI and smoke tests do not use a real account. Before a public release, run one manual Yinxiang account migration with a test account:

```bash
python migrate.py migrate --username "$YINXIANG_TEST_USER" --vault /tmp/e2o-account-vault
```

Review generated logs and reports before publishing. They must not contain passwords, tokens, cookies, or full authentication headers.

## Release Notes Must Include

- Tool version.
- Bundled Python version.
- Pinned `evernote-backup` version.
- Platforms tested.
- Known limitation: first release supports Yinxiang account sync as the primary account path; Evernote International users should use ENEX import.
- Cache location and cleanup guidance.

