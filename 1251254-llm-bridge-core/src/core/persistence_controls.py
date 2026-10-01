from dataclasses import dataclass
from threading import Lock
from typing import Any
import hashlib
import json


class PersistenceControlError(Exception):
    pass


@dataclass(frozen=True)
class CommitRecord:
    idempotency_key: str
    previous_hash: str
    event_hash: str
    payload: dict[str, Any]


class AppendOnlyAuditStore:
    """Process-safe application-level append-only audit control.

    This is not physical WORM. A production deployment must use an immutable
    storage service or database policy whose immutability can itself be tested.
    """

    def __init__(self):
        self._lock = Lock()
        self._records: list[CommitRecord] = []
        self._keys: set[str] = set()

    @staticmethod
    def _payload_digest(payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def append(self, idempotency_key: str, payload: dict[str, Any], event_hash: str) -> CommitRecord:
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise PersistenceControlError("Idempotency key required.")
        if not isinstance(event_hash, str) or not event_hash.strip():
            raise PersistenceControlError("Event hash required.")
        if not isinstance(payload, dict):
            raise TypeError("Audit payload must be a dictionary.")

        with self._lock:
            if idempotency_key in self._keys:
                raise PersistenceControlError(
                    "Replay detected: idempotency key already committed."
                )
            previous = self._records[-1].event_hash if self._records else "GENESIS"
            expected_hash = self._payload_digest(
                {"previousHash": previous, "payload": payload}
            )
            if event_hash != expected_hash:
                raise PersistenceControlError(
                    "Event hash does not match payload and previous event hash."
                )
            record = CommitRecord(
                idempotency_key, previous, event_hash, dict(payload)
            )
            self._records.append(record)
            self._keys.add(idempotency_key)
            return record

    def verify_chain(self) -> bool:
        with self._lock:
            previous = "GENESIS"
            for record in self._records:
                if record.previous_hash != previous:
                    return False
                expected = self._payload_digest(
                    {"previousHash": previous, "payload": record.payload}
                )
                if record.event_hash != expected:
                    return False
                previous = record.event_hash
            return True

    def snapshot(self) -> tuple[CommitRecord, ...]:
        with self._lock:
            return tuple(self._records)
