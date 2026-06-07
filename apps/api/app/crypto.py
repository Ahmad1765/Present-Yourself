"""AES-256-GCM vault for user API keys.

Master key from MASTER_ENCRYPTION_KEY (base64, 32 bytes). Each ciphertext stored
with its own 12-byte random nonce. Provider name binds as associated data so a
key for OpenAI can't be silently moved to the Anthropic slot.
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings


def _master_key() -> bytes:
    raw = get_settings().master_encryption_key
    key = base64.b64decode(raw)
    if len(key) != 32:
        raise ValueError("MASTER_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt_key(plaintext: str, provider: str) -> tuple[bytes, bytes, str]:
    """Returns (ciphertext, nonce, fingerprint)."""
    aes = AESGCM(_master_key())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), provider.encode("utf-8"))
    fp = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()[:16]
    return ct, nonce, fp


def decrypt_key(ciphertext: bytes, nonce: bytes, provider: str) -> str:
    aes = AESGCM(_master_key())
    return aes.decrypt(nonce, ciphertext, provider.encode("utf-8")).decode("utf-8")


def masked_preview(plaintext: str) -> str:
    """User-facing masked form: 'sk-...abc4'."""
    if len(plaintext) <= 8:
        return "•" * len(plaintext)
    return f"{plaintext[:3]}…{plaintext[-4:]}"
