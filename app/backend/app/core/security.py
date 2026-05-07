"""Security primitives: password hashing (Argon2), JWT, 2FA TOTP, AES-GCM encryption for API keys."""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt

from .config import settings

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    return ph.check_needs_rehash(hashed)


# ── JWT ─────────────────────────────────────────────────────────────
def create_access_token(subject: str, *, claims: dict | None = None, expires_min: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_min or settings.JWT_ACCESS_EXPIRES_MIN)
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc), "type": "access"}
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.JWT_SECRET.get_secret_value(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRES_DAYS)
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh", "jti": secrets.token_hex(8)}
    token = jwt.encode(payload, settings.JWT_SECRET.get_secret_value(), algorithm=settings.JWT_ALGORITHM)
    return token, expire


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET.get_secret_value(), algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# ── 2FA ─────────────────────────────────────────────────────────────
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, account_email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=account_email, issuer_name=settings.TWO_FA_ISSUER)


def verify_totp(secret: str, code: str, *, valid_window: int = 1) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=valid_window)


# ── Symmetric encryption for stored secrets (broker API keys, etc.) ─
def _aesgcm() -> AESGCM:
    raw = settings.ENCRYPTION_KEY.get_secret_value()
    # Allow either raw 32-byte UTF-8 string or base64-encoded
    try:
        key = base64.b64decode(raw)
        if len(key) != 32:
            raise ValueError
    except Exception:
        key = hashlib.sha256(raw.encode()).digest()
    return AESGCM(key)


def encrypt_secret(plaintext: str) -> str:
    aes = _aesgcm()
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_secret(token: str) -> str:
    aes = _aesgcm()
    blob = base64.b64decode(token)
    nonce, ct = blob[:12], blob[12:]
    return aes.decrypt(nonce, ct, None).decode()


# Constant-time random tokens
def gen_token(n_bytes: int = 32) -> str:
    return secrets.token_urlsafe(n_bytes)


def stable_id() -> str:
    return f"{int(time.time()*1000):x}{secrets.token_hex(4)}"
