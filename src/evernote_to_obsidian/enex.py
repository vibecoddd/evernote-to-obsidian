from __future__ import annotations

import base64
import hashlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .models import Note, Resource


class ENEXParser:
    def parse_file(self, enex_path: str | Path) -> tuple[list[Note], str]:
        path = self._validate_file(enex_path)
        notebook = self.notebook_name(path)
        return list(self.iter_notes(path, notebook_name=notebook)), notebook

    def notebook_name(self, enex_path: str | Path) -> str:
        path = self._validate_file(enex_path)
        try:
            with path.open("rb") as handle:
                for _event, element in ET.iterparse(handle, events=("end",)):
                    if element.tag == "notebook" and element.text and element.text.strip():
                        return self._clean_text(element.text)
                    if element.tag == "note":
                        break
        except ET.ParseError as exc:
            raise ValueError(f"Invalid ENEX XML: {path}: {exc}") from exc
        return self._clean_text(path.stem) or "Default Notebook"

    def iter_notes(self, enex_path: str | Path, notebook_name: str | None = None) -> Iterator[Note]:
        path = self._validate_file(enex_path)
        notebook = notebook_name or self.notebook_name(path)
        try:
            with path.open("rb") as handle:
                for _event, element in ET.iterparse(handle, events=("end",)):
                    if element.tag != "note":
                        continue
                    note = self._parse_note(element)
                    note.notebook = notebook
                    yield note
                    element.clear()
        except ET.ParseError as exc:
            raise ValueError(f"Invalid ENEX XML: {path}: {exc}") from exc

    def _validate_file(self, enex_path: str | Path) -> Path:
        path = Path(enex_path)
        if not path.exists():
            raise FileNotFoundError(f"ENEX file not found: {path}")
        return path

    def _parse_note(self, note_el: ET.Element) -> Note:
        title = self._child_text(note_el, "title", "Untitled Note")
        content = self._child_text(note_el, "content", "")
        attributes = self._note_attributes(note_el)
        tags = [self._clean_text(tag.text or "") for tag in note_el.findall("tag") if (tag.text or "").strip()]
        resources = self._resources(note_el)

        source_url = attributes.get("source-url") or self._child_text(note_el, "source-url", "")
        author = attributes.get("author") or self._child_text(note_el, "author", "")
        guid = self._child_text(note_el, "guid", "") or None
        content_hash = hashlib.sha256(f"{title}\n{content}".encode("utf-8")).hexdigest()

        return Note(
            title=self._clean_text(title),
            content=content,
            created=self._parse_datetime(self._child_text(note_el, "created", "")),
            updated=self._parse_datetime(self._child_text(note_el, "updated", "")),
            tags=tags,
            source_url=source_url or None,
            author=author or None,
            resources=resources,
            attributes=attributes,
            guid=guid,
            content_hash=content_hash,
        )

    def _child_text(self, parent: ET.Element, tag: str, default: str = "") -> str:
        child = parent.find(tag)
        if child is None or child.text is None:
            return default
        return child.text.strip()

    def _note_attributes(self, note_el: ET.Element) -> dict[str, str]:
        attrs: dict[str, str] = {}
        attrs_el = note_el.find("note-attributes")
        if attrs_el is None:
            return attrs
        for child in attrs_el:
            if child.text and child.text.strip():
                attrs[child.tag] = child.text.strip()
        return attrs

    def _resources(self, note_el: ET.Element) -> list[Resource]:
        resources: list[Resource] = []
        for resource_el in note_el.findall("resource"):
            data_el = resource_el.find("data")
            if data_el is None or not data_el.text:
                continue
            try:
                raw = base64.b64decode("".join(data_el.text.split()))
            except Exception as exc:
                raise ValueError("Invalid base64 resource in ENEX") from exc

            mime_type = self._child_text(resource_el, "mime", "application/octet-stream")
            filename = self._resource_filename(resource_el, len(resources), mime_type)
            resource_hash = hashlib.md5(raw).hexdigest()
            width = self._optional_int(self._resource_attr(resource_el, "width"))
            height = self._optional_int(self._resource_attr(resource_el, "height"))

            resources.append(
                Resource(
                    data=raw,
                    mime_type=mime_type,
                    filename=filename,
                    hash=resource_hash,
                    width=width,
                    height=height,
                )
            )
        return resources

    def _resource_filename(self, resource_el: ET.Element, index: int, mime_type: str) -> str:
        for tag in ("file-name", "filename"):
            value = self._resource_attr(resource_el, tag)
            if value:
                return self._clean_text(value)
        return f"attachment_{index}{self._extension_for_mime(mime_type)}"

    def _resource_attr(self, resource_el: ET.Element, tag: str) -> str:
        direct = resource_el.find(tag)
        if direct is not None and direct.text and direct.text.strip():
            return direct.text.strip()
        attrs_el = resource_el.find("resource-attributes")
        if attrs_el is not None:
            child = attrs_el.find(tag)
            if child is not None and child.text and child.text.strip():
                return child.text.strip()
        return ""

    def _optional_int(self, value: str) -> int | None:
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _parse_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        normalized = re.sub(r"\.\d+Z?$", "Z", value.strip())
        for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        return None

    def _extension_for_mime(self, mime_type: str) -> str:
        return {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/svg+xml": ".svg",
            "application/pdf": ".pdf",
            "text/plain": ".txt",
            "text/html": ".html",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/zip": ".zip",
        }.get(mime_type, ".bin")

    def _clean_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        return text
