from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable


class ErrorCategory(str, Enum):
    AUTH = "auth"
    NETWORK = "network"
    DATA = "data"
    OUTPUT = "output"
    RUNTIME = "runtime"


@dataclass
class ErrorRecord:
    category: ErrorCategory
    message: str
    detail: str = ""
    recoverable: bool = True

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["category"] = self.category.value
        return data


def redact_secrets(value: str | Iterable[str], secrets: Iterable[str] | None = None) -> str:
    text = " ".join(str(part) for part in value) if not isinstance(value, str) else value
    secret_values = [secret for secret in (secrets or []) if secret]

    for secret in secret_values:
        text = text.replace(secret, "[REDACTED]")

    text = re.sub(r"(--password(?:=|\s+))\S+", r"\1[REDACTED]", text)
    text = re.sub(r"(--token(?:=|\s+))\S+", r"\1[REDACTED]", text)
    text = re.sub(r"(Authorization:\s*)\S+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    text = re.sub(r"(Cookie:\s*)[^\n]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    return text


def classify_error(message: str) -> ErrorCategory:
    lowered = message.lower()
    if any(term in lowered for term in ["password", "auth", "login", "username", "token"]):
        return ErrorCategory.AUTH
    if any(term in lowered for term in ["dns", "ssl", "network", "connection", "timeout", "proxy"]):
        return ErrorCategory.NETWORK
    if any(term in lowered for term in ["enex", "xml", "base64", "html", "mime"]):
        return ErrorCategory.DATA
    if any(term in lowered for term in ["permission", "disk", "path", "filename", "vault", "write"]):
        return ErrorCategory.OUTPUT
    return ErrorCategory.RUNTIME

