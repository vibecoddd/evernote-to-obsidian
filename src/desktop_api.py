"""Validation helpers shared by the Electron sidecar API."""

import os
from pathlib import Path
from typing import Any


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(os.path.expanduser(value)).expanduser()


def preflight_config(config_data: dict[str, Any] | None) -> dict[str, Any]:
    """Return JSON-safe, side-effect-free validation results for a migration."""
    config_data = config_data if isinstance(config_data, dict) else {}
    input_config = config_data.get("input") or {}
    output_config = config_data.get("output") or {}
    credentials = config_data.get("evernote_credentials") or {}
    source_mode = config_data.get("source_mode")
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    enex_files = input_config.get("enex_files") or []
    if not isinstance(enex_files, list):
        enex_files = []
    expanded_enex = [_path(value) for value in enex_files]

    uses_enex = source_mode == "enex" or (source_mode is None and bool(expanded_enex))
    if uses_enex:
        if not expanded_enex:
            errors.append(_issue("invalid_enex", "Select at least one ENEX file."))
        for enex_file in expanded_enex:
            if enex_file is None or enex_file.suffix.lower() != ".enex":
                errors.append(_issue("invalid_enex", "Input files must use the .enex suffix."))
            elif not enex_file.is_file():
                errors.append(_issue("invalid_enex", f"ENEX file does not exist: {enex_file}"))
    else:
        username = credentials.get("username") if isinstance(credentials, dict) else None
        password = credentials.get("password") if isinstance(credentials, dict) else None
        if not isinstance(username, str) or not username.strip() or not isinstance(password, str) or not password:
            errors.append(_issue("credentials_missing", "Evernote username and password are required."))

    vault = _path(output_config.get("obsidian_vault"))
    create_vault = output_config.get("create_vault_if_not_exists", True)
    if vault is None:
        errors.append(_issue("vault_missing", "Select an Obsidian Vault directory."))
    elif vault.exists():
        if not vault.is_dir() or not os.access(vault, os.W_OK | os.X_OK):
            errors.append(_issue("vault_not_writable", f"Vault is not writable: {vault}"))
    elif not create_vault:
        errors.append(_issue("vault_missing", f"Vault does not exist: {vault}"))
    else:
        parent = vault.parent
        if not parent.is_dir() or not os.access(parent, os.W_OK | os.X_OK):
            errors.append(_issue("vault_not_writable", f"Vault parent is not writable: {parent}"))
        else:
            warnings.append(_issue("vault_will_be_created", f"Vault will be created: {vault}"))

    summary = {
        "source_mode": source_mode or ("enex" if expanded_enex else "account"),
        "enex_files": [str(path) for path in expanded_enex if path is not None],
        "vault": str(vault) if vault is not None else None,
    }
    return {"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}
