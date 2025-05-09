import hashlib

def sha256_hex(data: str) -> str:
    """Return the SHA-256 hex digest of the input string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
