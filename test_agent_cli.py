#!/usr/bin/env python3
"""Contract tests for the Codex/Claude Code friendly CLI."""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


SAMPLE_ENEX = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="20231201T120000Z" application="Evernote" version="10.50.16">
  <notebook>
    <name>测试笔记本</name>
    <note>
      <guid>test-guid-1</guid>
      <title>测试笔记</title>
      <content><![CDATA[<?xml version="1.0" encoding="UTF-8"?>
        <en-note><div>这是测试内容。</div></en-note>]]></content>
      <created>20231201T100000Z</created>
      <updated>20231201T110000Z</updated>
      <tag>测试</tag>
    </note>
  </notebook>
</en-export>
"""


class AgentCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent_cli_test_"))
        self.enex = self.temp_dir / "notes.enex"
        self.enex.write_text(SAMPLE_ENEX, encoding="utf-8")
        self.vault = self.temp_dir / "vault"

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
            "convert", "--input", str(self.enex),
            "--output", str(self.vault), "--preview", "--json"
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout.count("\n"), 1)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["command"], "convert")
        self.assertEqual(payload["mode"], "preview")
        self.assertFalse(self.vault.exists())

    def test_convert_json_writes_markdown(self):
        code, payload, _ = self.run_cli(
            "convert", "--input", str(self.enex),
            "--output", str(self.vault), "--json"
        )

        self.assertEqual(code, 0)
        self.assertTrue(payload["success"])
        self.assertGreaterEqual(payload["stats"]["converted_notes"], 1)
        self.assertEqual(len(list(self.vault.rglob("*.md"))), 1)

    def test_command_line_paths_override_yaml_config(self):
        config = self.temp_dir / "config.yaml"
        config.write_text(
            "input:\n  enex_files: []\n"
            "output:\n  obsidian_vault: /wrong/path\n",
            encoding="utf-8",
        )

        code, payload, _ = self.run_cli(
            "convert", "--config", str(config),
            "--input", str(self.enex), "--output", str(self.vault),
            "--preview", "--json"
        )

        self.assertEqual(code, 0)
        self.assertEqual(payload["output"], str(self.vault.resolve()))

    def test_migrate_without_credentials_fails_without_prompt(self):
        code, payload, _ = self.run_cli(
            "migrate", "--output", str(self.vault), "--json"
        )

        self.assertEqual(code, 1)
        self.assertFalse(payload["success"])
        self.assertIn("credentials", payload["error"].lower())


if __name__ == "__main__":
    unittest.main()
