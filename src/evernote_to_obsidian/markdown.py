from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import html2text
import yaml

from .models import Note


class MarkdownConverter:
    def __init__(self) -> None:
        self._html2text = html2text.HTML2Text()
        self._html2text.body_width = 0
        self._html2text.ignore_images = False
        self._html2text.ignore_links = False
        self._html2text.ignore_tables = False
        self._html2text.unicode_snob = True
        self._html2text.wrap_links = False
        self._html2text.single_line_break = False

    def convert(
        self,
        note: Note,
        attachment_links: dict[str, str],
        attachment_metadata: list[dict[str, Any]],
        task_id: str,
        migrated_at: str,
    ) -> str:
        frontmatter = self._frontmatter(note, attachment_metadata, task_id, migrated_at)
        content = self._prepare_enml(note.content, attachment_links)
        markdown = self._html2text.handle(content)
        markdown = self._post_process(markdown)
        return f"---\n{frontmatter}---\n\n{markdown}".rstrip() + "\n"

    def _frontmatter(
        self,
        note: Note,
        attachments: list[dict[str, Any]],
        task_id: str,
        migrated_at: str,
    ) -> str:
        data: dict[str, Any] = {
            "title": note.title,
            "evernote_guid": note.guid,
            "created": self._format_datetime(note.created),
            "updated": self._format_datetime(note.updated),
            "notebook": note.notebook,
            "tags": note.tags,
            "source": note.source,
            "source_url": note.source_url,
            "author": note.author,
            "latitude": note.attributes.get("latitude"),
            "longitude": note.attributes.get("longitude"),
            "altitude": note.attributes.get("altitude"),
            "attachments": attachments,
            "migration_task_id": task_id,
            "migration_time": migrated_at,
            "content_hash": note.content_hash,
        }
        data = {key: value for key, value in data.items() if value not in (None, "", [])}
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)

    def _prepare_enml(self, content: str, attachment_links: dict[str, str]) -> str:
        content = re.sub(r"<\?xml[^>]*>", "", content, flags=re.IGNORECASE)
        content = re.sub(r"<!DOCTYPE[^>]*>", "", content, flags=re.IGNORECASE)
        content = re.sub(r"</?en-note[^>]*>", "", content, flags=re.IGNORECASE)
        content = re.sub(
            r"<en-todo\s+checked=\"true\"[^>]*/?>",
            "- [x] ",
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(r"<en-todo[^>]*/?>", "- [ ] ", content, flags=re.IGNORECASE)

        def replace_media(match: re.Match[str]) -> str:
            tag = match.group(0)
            hash_match = re.search(r"hash=\"([^\"]+)\"", tag, flags=re.IGNORECASE)
            if not hash_match:
                return "[Unsupported attachment]"
            return attachment_links.get(hash_match.group(1), "[Missing attachment]")

        return re.sub(r"<en-media\b[^>]*/?>", replace_media, content, flags=re.IGNORECASE)

    def _post_process(self, markdown: str) -> str:
        markdown = markdown.replace("\\- [x]", "- [x]").replace("\\- [ ]", "- [ ]")
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        return markdown.strip()

    def _format_datetime(self, value: datetime | None) -> str | None:
        if not value:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")

