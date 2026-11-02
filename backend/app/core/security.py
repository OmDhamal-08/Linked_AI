"""Password hashing (PBKDF2-SHA256 from the standard library) and JWT helpers."""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

PBKDF2_ITERATIONS = 390_000
ALGORITHM_TAG = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "{}${}${}${}".format(
        ALGORITHM_TAG,
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        tag, iterations, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if tag != ALGORITHM_TAG:
        return False
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(digest_b64)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
    return hmac.compare_digest(candidate, expected)


def create_access_token(subject: str, *, secret: str, algorithm: str, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "iss": "linkdine-ai",
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str, audience: str | None = None) -> dict[str, Any]:
    """Raises jwt.PyJWTError on invalid or expired tokens."""
    options = {"require": ["exp", "sub"]}
    kwargs: dict[str, Any] = {"algorithms": [algorithm], "options": options}
    if audience:
        kwargs["audience"] = audience
    return jwt.decode(token, secret, **kwargs)
