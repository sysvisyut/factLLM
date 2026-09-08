import hashlib


def compute_sha256(content: bytes) -> str:
    """Computes SHA-256 hexadecimal digest for raw bytes."""
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()


def compute_text_hash(text: str) -> str:
    """Computes SHA-256 hash for a normalized text string."""
    normalized = " ".join(text.strip().split())
    return compute_sha256(normalized.encode("utf-8"))
