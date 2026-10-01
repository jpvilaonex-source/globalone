import json
from typing import Any
def canonicalize(payload: dict[str,Any])->bytes:
    """Deterministic JSON encoding; full RFC 8785 conformance is not asserted."""
    return json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
