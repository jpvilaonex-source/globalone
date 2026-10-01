import json

def canonicalize(payload: dict) -> bytes:
    # Deterministic JSON serialization. This is not claimed as full RFC 8785
    # interoperability until the implementation is validated against JCS vectors.
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
