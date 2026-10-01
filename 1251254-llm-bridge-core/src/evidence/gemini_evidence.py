"""Gemini evidence preservation controls for Master Reference 1251254.

Records source material and analytical fields separately. No offence determination
is made by this module; legal conclusions remain for the applicable proceeding.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib, json

@dataclass(frozen=True)
class GeminiEvidenceRecord:
    exhibit_id: str
    source_artifact: str
    conversation_id: str
    statement: str
    statement_timestamp: str
    proposition: str
    attribution: str
    materiality_basis: str
    contradiction_evidence: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    knowledge_indicators: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    authenticity_status: str = "PENDING_PRIMARY_SOURCE_CHECK"

    def canonical_bytes(self) -> bytes:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode()

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def sha512(self) -> str:
        return hashlib.sha512(self.canonical_bytes()).hexdigest()

class GeminiEvidenceRegister:
    def __init__(self, master_reference="1251254"):
        if master_reference != "1251254":
            raise ValueError("Register must belong to Master Reference 1251254.")
        self.master_reference = master_reference
        self._records = []

    def add(self, record: GeminiEvidenceRecord):
        if not record.exhibit_id.strip() or not record.statement.strip():
            raise ValueError("Exhibit ID and original statement are required.")
        self._records.append(record)
        return record

    def snapshot(self):
        return tuple(self._records)

    def manifest(self):
        return {
            "masterReference": self.master_reference,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "recordCount": len(self._records),
            "records": [{**asdict(r), "sha256": r.sha256(), "sha512": r.sha512()}
                        for r in self._records],
            "legalStatus": "EVIDENCE_REGISTER_ONLY_NO_OFFENCE_DETERMINATION",
        }
