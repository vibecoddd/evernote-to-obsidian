#!/usr/bin/env python3
"""Contract tests for the Codex/Claude Code friendly CLI."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


SAMPLE_ENEX = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="20231201T120000Z" application="Evernote" version="10.50.16">
  <notebook>测试笔记本</notebook>
  <note>
    <guid>test-guid-1</guid>
    <title>测试笔记</title>
    <content><![CDATA[<?xml version="1.0" encoding="UTF-8"?>
      <en-note><div>这是测试内容。</div></en-note>]]></content>
    <created>20231201T100000Z</created>
    <updated>20231201T110000Z</updated>
    <tag>测试</tag>
  </note>
</en-export>
"""


class AgentCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent_cli_test_"))
        self.enex = self.temp_dir / "notes.enex"
        self.enex.write_text(SAMPLE_ENEX, encoding="utf-8")
        self.vault = self.temp_dir / "vault"
        self.app_data = self.temp_dir / "app"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli(self, *argv):
        from agent_cli import main

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(list(argv))
        output = stdout.getvalue()
        return code, json.loads(output), output

    def test_preview_json_is_single_object_and_does_not_write(self):
        code, payload, stdout = self.run_cli(
            "convert",
            "--input",
            str(self.enex),
            "--output",
            str(self.vault),
            "--app-data",
            str(self.app_data),
            "--preview",
            "--json",
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.count("\n"), 1)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["command"], "convert")
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual(payload["stats"]["total_notes"], 1)
        self.assertFalse(self.vault.exists())
        self.assertFalse(self.app_data.exists())

    def test_convert_json_writes_markdown(self):
        code, payload, _ = self.run_cli(
            "convert",
            "--input",
            str(self.enex),
            "--output",
            str(self.vault),
            "--app-data",
            str(self.app_data),
            "--json",
        )

        self.assertEqual(code, 0)
        self.assertTrue(payload["success"])
        self.assertGreaterEqual(payload["stats"]["converted_notes"], 1)
        note_path = self.vault / "测试笔记本" / "测试笔记.md"
        self.assertTrue(note_path.is_file())
        self.assertIn("title: 测试笔记", note_path.read_text(encoding="utf-8"))
        self.assertTrue((self.app_data / "tasks" / payload["stats"]["task_id"]).is_dir())

    def test_command_line_paths_override_yaml_config(self):
        config = self.temp_dir / "config.yaml"
        config.write_text(
            "output:\n  obsidian_vault: /wrong/path\n",
            encoding="utf-8",
        )

        code, payload, _ = self.run_cli(
            "convert",
            "--config",
            str(config),
            "--input",
            str(self.enex),
            "--output",
            str(self.vault),
            "--app-data",
            str(self.app_data),
            "--preview",
            "--json",
        )

        self.assertEqual(code, 0)
        self.assertEqual(payload["output"], str(self.vault.resolve()))

    def test_migrate_without_credentials_fails_without_prompt(self):
        with patch.dict(
            os.environ,
            {"EVERNOTE_USERNAME": "", "EVERNOTE_PASSWORD": ""},
            clear=False,
        ):
            code, payload, _ = self.run_cli(
                "migrate",
                "--output",
                str(self.vault),
                "--app-data",
                str(self.app_data),
                "--json",
            )

        self.assertEqual(code, 1)
        self.assertFalse(payload["success"])
        self.assertIn("credentials", payload["error"].lower())
        self.assertFalse(self.app_data.exists())

    def test_pyproject_declares_console_script(self):
        text = (Path(__file__).parent / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('name = "evernote-to-obsidian"', text)
        self.assertIn('evernote-to-obsidian = "agent_cli:main"', text)
        self.assertIn('include = ["evernote_to_obsidian*"]', text)

    def test_agent_guides_use_json_preview_command(self):
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (Path(__file__).parent / name).read_text(encoding="utf-8")
            self.assertIn("evernote-to-obsidian convert", text)
            self.assertIn("--preview", text)
            self.assertIn("--json", text)
            self.assertIn("--no-open", text)


if __name__ == "__main__":
    unittest.main()
