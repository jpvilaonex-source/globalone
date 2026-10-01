from dataclasses import dataclass
from threading import Lock
from typing import Any

class PersistenceControlError(Exception):
    pass

@dataclass(frozen=True)
class CommitRecord:
    idempotency_key: str
    previous_hash: str
    event_hash: str
    payload: dict[str, Any]

class AppendOnlyAuditStore:
    """Process-safe append-only control store.

    This is an application-level control, not a claim of physical WORM
    immutability. Production WORM requires an immutable storage backend.
    """
    def __init__(self):
        self._lock = Lock()
        self._records: list[CommitRecord] = []
        self._keys: set[str] = set()

    def append(self, idempotency_key: str, payload: dict[str, Any], event_hash: str) -> CommitRecord:
        if not idempotency_key.strip():
            raise PersistenceControlError("Idempotency key required.")
        with self._lock:
            if idempotency_key in self._keys:
                raise PersistenceControlError("Replay detected: idempotency key already committed.")
            previous = self._records[-1].event_hash if self._records else "GENESIS"
            record = CommitRecord(idempotency_key, previous, event_hash, dict(payload))
            self._records.append(record)
            self._keys.add(idempotency_key)
            return record

    def snapshot(self) -> tuple[CommitRecord, ...]:
        with self._lock:
            return tuple(self._records)
