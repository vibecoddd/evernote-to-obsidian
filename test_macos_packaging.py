from pathlib import Path


SPEC_PATH = Path(__file__).parent / "packaging" / "macos" / "evernote_to_obsidian.spec"


def test_macos_app_spec_uses_onedir_bundle_mode():
    spec = SPEC_PATH.read_text(encoding="utf-8")

    assert "exclude_binaries=True" in spec
    assert "coll = COLLECT(" in spec
    assert "BUNDLE(\n    coll," in spec
