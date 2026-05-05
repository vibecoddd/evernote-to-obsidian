import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evernote_to_obsidian.enex import ENEXParser
from evernote_to_obsidian.writer import ObsidianWriter


FIXTURE = Path(__file__).parent / "fixtures" / "sample_complex.enex"


def _frontmatter(markdown: str) -> dict:
    assert markdown.startswith("---\n")
    raw = markdown.split("---", 2)[1]
    return yaml.safe_load(raw)


def test_enex_parser_extracts_notes_metadata_and_resource_hash():
    notes, notebook = ENEXParser().parse_file(FIXTURE)

    assert notebook == "Work Notes"
    assert len(notes) == 2
    assert notes[0].guid == "11111111-1111-1111-1111-111111111111"
    assert notes[0].tags == ["工作", "meeting"]
    assert notes[0].source_url == "https://example.com/source"
    assert notes[0].author == "Alice"
    assert notes[0].attributes["latitude"] == "31.2304"
    assert notes[0].resources[0].filename == "diagram.png"
    assert notes[0].resources[0].hash == "f9831439379ccdb20cc6ba12b54eb868"


def test_obsidian_writer_preserves_structure_attachments_and_metadata(tmp_path):
    notes, notebook = ENEXParser().parse_file(FIXTURE)
    vault = tmp_path / "vault"
    result = ObsidianWriter(vault).write_notes(notes, notebook, task_id="task-enex")

    notebook_dir = vault / "Work Notes"
    note_files = sorted(path for path in notebook_dir.glob("*.md") if not path.name.endswith("_Index.md"))
    index_file = notebook_dir / "Work Notes_Index.md"
    attachment = vault / "attachments" / "11111111-1111-1111-1111-111111111111" / "diagram.png"
    report_json = vault / "migration-reports" / "task-enex.json"
    report_md = vault / "migration-reports" / "task-enex.md"

    assert result.stats.total_notes == 2
    assert result.stats.converted_notes == 2
    assert result.stats.total_attachments == 1
    assert len(note_files) == 2
    assert note_files[0].name != note_files[1].name
    assert index_file.exists()
    assert attachment.read_bytes() == b"image-bytes"
    assert report_json.exists()
    assert report_md.exists()

    first_note = ""
    for path in note_files:
        content = path.read_text(encoding="utf-8")
        if _frontmatter(content)["evernote_guid"] == "11111111-1111-1111-1111-111111111111":
            first_note = content
            break
    assert first_note
    metadata = _frontmatter(first_note)

    assert metadata["title"] == "Meeting/Plan: Q1?"
    assert metadata["evernote_guid"] == "11111111-1111-1111-1111-111111111111"
    assert metadata["notebook"] == "Work Notes"
    assert metadata["tags"] == ["工作", "meeting"]
    assert metadata["source_url"] == "https://example.com/source"
    assert metadata["author"] == "Alice"
    assert metadata["latitude"] == "31.2304"
    assert metadata["attachments"][0]["path"] == "attachments/11111111-1111-1111-1111-111111111111/diagram.png"
    assert "- [x] Confirm scope" in first_note
    assert "![[attachments/11111111-1111-1111-1111-111111111111/diagram.png]]" in first_note
