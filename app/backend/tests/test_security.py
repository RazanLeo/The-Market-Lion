"""Security primitives — Argon2 + AES-GCM + JWT + TOTP."""
from app.core.security import (
    hash_password, verify_password, create_access_token, decode_token,
    encrypt_secret, decrypt_secret, generate_totp_secret, verify_totp,
)
import pyotp


def test_password_argon2_round_trip():
    h = hash_password("CorrectHorseBatteryStaple!")
    assert verify_password("CorrectHorseBatteryStaple!", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_round_trip():
    tok = create_access_token("user-123", claims={"role": "trader"})
    data = decode_token(tok)
    assert data and data["sub"] == "user-123" and data["role"] == "trader"


def test_aes_gcm_round_trip():
    pt = "exness_secret_key_xyz_123"
    ct = encrypt_secret(pt)
    assert ct != pt
    assert decrypt_secret(ct) == pt


def test_totp_verify():
    s = generate_totp_secret()
    code = pyotp.TOTP(s).now()
    assert verify_totp(s, code) is True
    assert verify_totp(s, "000000") is False
