from pathlib import Path


SPEC_PATH = Path(__file__).parent / "packaging" / "macos" / "evernote_to_obsidian.spec"


def test_macos_app_spec_uses_onedir_bundle_mode():
    spec = SPEC_PATH.read_text(encoding="utf-8")

    assert "exclude_binaries=True" in spec
    assert "coll = COLLECT(" in spec
    assert "BUNDLE(\n    coll," in spec


def test_macos_app_exe_leaves_binaries_for_collect():
    spec = SPEC_PATH.read_text(encoding="utf-8")
    exe_block = spec.split("exe = EXE(", 1)[1].split("\n)", 1)[0]

    assert "    a.binaries," not in exe_block
    assert "    a.datas," not in exe_block
