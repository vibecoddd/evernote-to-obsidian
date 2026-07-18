from src.desktop_api import preflight_config


def test_preflight_accepts_existing_enex_and_writable_vault(tmp_path):
    enex_file = tmp_path / "notes.enex"
    enex_file.write_text("<en-export />", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()

    result = preflight_config({
        "source_mode": "enex",
        "input": {"enex_files": [str(enex_file)]},
        "output": {"obsidian_vault": str(vault)},
    })

    assert result["ok"] is True
    assert result["errors"] == []
    assert set(result) == {"ok", "errors", "warnings", "summary"}


def test_preflight_reports_invalid_enex_suffix(tmp_path):
    source_file = tmp_path / "notes.txt"
    source_file.write_text("not an ENEX file", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()

    result = preflight_config({
        "source_mode": "enex",
        "input": {"enex_files": [str(source_file)]},
        "output": {"obsidian_vault": str(vault)},
    })

    assert {error["code"] for error in result["errors"]} == {"invalid_enex"}


def test_preflight_reports_missing_vault_when_creation_is_disabled(tmp_path):
    enex_file = tmp_path / "notes.enex"
    enex_file.write_text("<en-export />", encoding="utf-8")

    result = preflight_config({
        "source_mode": "enex",
        "input": {"enex_files": [str(enex_file)]},
        "output": {
            "obsidian_vault": str(tmp_path / "missing-vault"),
            "create_vault_if_not_exists": False,
        },
    })

    assert {error["code"] for error in result["errors"]} == {"vault_missing"}


def test_preflight_requires_credentials_for_explicit_account_mode(tmp_path):
    enex_file = tmp_path / "notes.enex"
    enex_file.write_text("<en-export />", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()

    result = preflight_config({
        "source_mode": "account",
        "input": {"enex_files": [str(enex_file)]},
        "output": {"obsidian_vault": str(vault)},
    })

    assert {error["code"] for error in result["errors"]} == {"credentials_missing"}
