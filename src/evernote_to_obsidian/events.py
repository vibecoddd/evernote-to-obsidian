from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from .models import utc_now_iso


@dataclass
class ProgressEvent:
    task_id: str
    phase: str
    progress: int
    message: str
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = utc_now_iso()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ProgressEmitter:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[ProgressEvent], None]] = []

    def subscribe(self, callback: Callable[[ProgressEvent], None]) -> None:
        self._subscribers.append(callback)

    def emit(self, event: ProgressEvent) -> None:
        for callback in list(self._subscribers):
            callback(event)

