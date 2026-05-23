"""AES-GCM field-level encryption for sensitive PII (HKID, etc.).

Phase 1a usage: ID document numbers.
Stored format: base64(nonce || ciphertext || tag), single string column.
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _key() -> bytes:
    """Derive a 32-byte AES key from settings via SHA-256 (handles arbitrary input length)."""
    return hashlib.sha256(settings.FIELD_ENCRYPTION_KEY.encode()).digest()


def encrypt_field(plaintext: str | None) -> str | None:
    if plaintext is None or plaintext == "":
        return None
    aesgcm = AESGCM(_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_field(token: str | None) -> str | None:
    if not token:
        return None
    raw = base64.b64decode(token)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(_key())
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def mask_id_number(plaintext: str | None) -> str:
    """Return a masked display string. e.g. 'A1234...567(8)' for HKID-ish 8-char."""
    if not plaintext:
        return ""
    s = plaintext.strip()
    if len(s) <= 4:
        return "*" * len(s)
    return f"{s[:2]}{'*' * max(len(s) - 5, 3)}{s[-3:]}"
