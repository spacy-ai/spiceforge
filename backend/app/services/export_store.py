from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


@dataclass
class ExportRecord:
    export_id: str
    file_path: Path
    user_id: int
    created_at: datetime


class ExportStore:
    def __init__(self) -> None:
        self._records: dict[str, ExportRecord] = {}
        self._lock = Lock()

    def create(self, *, file_path: Path, user_id: int) -> ExportRecord:
        export_id = uuid4().hex
        record = ExportRecord(
            export_id=export_id,
            file_path=file_path,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._records[export_id] = record
        return record

    def get(self, export_id: str) -> ExportRecord | None:
        with self._lock:
            return self._records.get(export_id)


export_store = ExportStore()
