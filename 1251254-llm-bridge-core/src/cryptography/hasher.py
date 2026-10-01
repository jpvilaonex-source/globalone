import hashlib

def dual_digest(data: bytes) -> dict:
    return {"sha256": hashlib.sha256(data).hexdigest(), "sha512": hashlib.sha512(data).hexdigest()}
