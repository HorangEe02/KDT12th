"""Password hashing helpers for auth routes.

Production prefers bcrypt when the package is installed. Local/test runs can
fall back to PBKDF2-HMAC from Python's standard library so auth routes remain
importable in minimal environments.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets

try:  # bcrypt is optional for local/test runtime resilience.
    import bcrypt as _bcrypt
except ImportError:  # pragma: no cover - exercised when bcrypt is absent.
    _bcrypt = None

_BCRYPT_ROUNDS = 12
_MAX_BYTES = 72  # bcrypt 자체 제한
_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 210_000
_PBKDF2_SALT_BYTES = 16
_PBKDF2_SCHEME = "pbkdf2_sha256"


def _to_bytes(plain: str) -> bytes:
    """Encode a password for bcrypt.

    Args:
        plain: Plain-text password supplied by a user.

    Returns:
        UTF-8 bytes truncated to bcrypt's 72-byte input limit.
    """
    return plain.encode("utf-8")[:_MAX_BYTES]


def _b64_encode(raw: bytes) -> str:
    """Encode bytes for storage in a password hash string.

    Args:
        raw: Byte string to encode.

    Returns:
        URL-safe base64 text without padding.
    """
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(value: str) -> bytes:
    """Decode storage base64 text back to bytes.

    Args:
        value: URL-safe base64 text that may omit padding.

    Returns:
        Decoded bytes.

    Raises:
        binascii.Error: If the value is not valid base64.
        ValueError: If decoding fails because the input is malformed.
    """
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _hash_password_pbkdf2(plain: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256.

    Args:
        plain: Plain-text password supplied by a user.

    Returns:
        Storage string containing scheme, iterations, salt, and digest.
    """
    salt = secrets.token_bytes(_PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        plain.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return "$".join(
        (
            _PBKDF2_SCHEME,
            str(_PBKDF2_ITERATIONS),
            _b64_encode(salt),
            _b64_encode(digest),
        )
    )


def _verify_password_pbkdf2(plain: str, hashed: str) -> bool:
    """Verify a password against a PBKDF2 storage string.

    Args:
        plain: Plain-text password supplied by a user.
        hashed: Stored PBKDF2 password hash.

    Returns:
        True when the password matches; otherwise False.
    """
    try:
        scheme, iterations_text, salt_text, digest_text = hashed.split("$", 3)
        if scheme != _PBKDF2_SCHEME:
            return False
        iterations = int(iterations_text)
        salt = _b64_decode(salt_text)
        expected = _b64_decode(digest_text)
        actual = hashlib.pbkdf2_hmac(
            _PBKDF2_ALGORITHM,
            plain.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)
    except (binascii.Error, TypeError, ValueError):
        return False


def hash_password(plain: str) -> str:
    """Hash a plain-text password.

    Args:
        plain: Plain-text password supplied by a user.

    Returns:
        Password hash suitable for storage.

    Raises:
        ValueError: If the password is shorter than the local minimum length.
    """
    if not plain or len(plain) < 8:
        raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
    if _bcrypt is None:
        # TODO: Install bcrypt in production or validate this fallback against
        # the team's security policy before using it outside local/dev setups.
        return _hash_password_pbkdf2(plain)

    salt = _bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return _bcrypt.hashpw(_to_bytes(plain), salt).decode("utf-8")


def verify_password(plain: str, hashed: str | None) -> bool:
    """Verify a plain-text password against a stored hash.

    Args:
        plain: Plain-text password supplied by a user.
        hashed: Stored password hash.

    Returns:
        True when the password matches; otherwise False.
    """
    if not hashed or not plain:
        return False
    if hashed.startswith(f"{_PBKDF2_SCHEME}$"):
        return _verify_password_pbkdf2(plain, hashed)
    if _bcrypt is None:
        return False
    try:
        return _bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
