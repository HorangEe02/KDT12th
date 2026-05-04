"""JWT issuing and verification helpers.

python-jose is preferred when installed. A compact HS256 fallback keeps the
local app and tests running when the optional dependency is missing.

Token payload shape:
    {
      "sub": "<user_id>",
      "email": "...",
      "role": "admin" | "user",
      "iat": <unix>,
      "exp": <unix>,
    }

Environment:
  - JWT_SECRET: Required in production. Missing values generate a process-local
    temporary secret, which invalidates tokens on restart.
  - JWT_EXPIRE_HOURS: Default access token lifetime in hours.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from jose import jwt as _jose_jwt
    from jose.exceptions import JWTError as _JoseJWTError
except ImportError:  # pragma: no cover - exercised when python-jose is absent.
    _jose_jwt = None
    _JoseJWTError = None

logger = logging.getLogger(__name__)

JWT_ALGO = "HS256"


class _FallbackJWTError(Exception):
    """Raised when fallback JWT validation fails."""


JWTError = _JoseJWTError or _FallbackJWTError


def _resolve_secret() -> str:
    """Resolve the process JWT signing secret.

    Returns:
        Configured secret or a temporary development secret.
    """
    val = os.environ.get("JWT_SECRET", "").strip()
    if not val:
        # 운영에서는 .env에 반드시 설정. 개발 편의를 위해 임시 발급 후 경고.
        val = secrets.token_urlsafe(32)
        logger.warning(
            "JWT_SECRET 환경변수 미설정 → 임시 시크릿 발급. "
            "재시작 시 모든 토큰이 무효화됩니다. .env에 영구 값 설정 권장."
        )
    return val


_SECRET = _resolve_secret()
_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "24"))


def _b64url_encode(raw: bytes) -> str:
    """Encode bytes using JWT base64url format.

    Args:
        raw: Bytes to encode.

    Returns:
        Base64url text without padding.
    """
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    """Decode JWT base64url text.

    Args:
        value: Base64url segment without padding.

    Returns:
        Decoded bytes.

    Raises:
        binascii.Error: If the segment is not valid base64url text.
    """
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _json_segment(payload: dict[str, Any]) -> str:
    """Serialize a JWT header or payload segment.

    Args:
        payload: JSON-serializable JWT segment.

    Returns:
        Base64url-encoded JSON segment.
    """
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64url_encode(raw)


def _sign(signing_input: str) -> str:
    """Create an HS256 JWT signature.

    Args:
        signing_input: Header and payload segments joined by a dot.

    Returns:
        Base64url-encoded signature.
    """
    signature = hmac.new(
        _SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(signature)


def _fallback_encode(payload: dict[str, Any]) -> str:
    """Encode a payload as an HS256 JWT without third-party dependencies.

    Args:
        payload: JWT claims to encode.

    Returns:
        Signed JWT string.
    """
    header = _json_segment({"alg": JWT_ALGO, "typ": "JWT"})
    body = _json_segment(payload)
    signing_input = f"{header}.{body}"
    return f"{signing_input}.{_sign(signing_input)}"


def _fallback_decode(token: str) -> dict[str, Any]:
    """Decode and verify an HS256 JWT without third-party dependencies.

    Args:
        token: JWT string to verify.

    Returns:
        Verified payload claims.

    Raises:
        JWTError: If the token is malformed, expired, or has a bad signature.
    """
    try:
        header_segment, payload_segment, signature_segment = token.split(".", 2)
        signing_input = f"{header_segment}.{payload_segment}"
        expected_signature = _b64url_decode(_sign(signing_input))
        provided_signature = _b64url_decode(signature_segment)
        if not hmac.compare_digest(provided_signature, expected_signature):
            raise JWTError("Invalid token signature")

        header = json.loads(_b64url_decode(header_segment))
        if header.get("alg") != JWT_ALGO:
            raise JWTError("Unsupported JWT algorithm")

        payload = json.loads(_b64url_decode(payload_segment))
        exp = int(payload["exp"])
        if datetime.now(timezone.utc).timestamp() > exp:
            raise JWTError("Token expired")
        return payload
    except JWTError:
        raise
    except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise JWTError("Invalid token") from exc


def create_access_token(
    *,
    user_id: str,
    email: str | None,
    role: str,
    expires_in_hours: int | None = None,
    expires_in_seconds: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed access token.

    Args:
        user_id: User identifier to place in the subject claim.
        email: User email claim.
        role: User role claim.
        expires_in_hours: Optional lifetime override in hours.
        expires_in_seconds: Optional lifetime override in seconds for tests.
        extra_claims: Additional claims merged into the payload.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    if expires_in_seconds is not None:
        exp = now + timedelta(seconds=expires_in_seconds)
    else:
        exp = now + timedelta(hours=expires_in_hours or _EXPIRE_HOURS)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    if _jose_jwt is not None:
        return _jose_jwt.encode(payload, _SECRET, algorithm=JWT_ALGO)
    return _fallback_encode(payload)


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify and decode an access token.

    Args:
        token: JWT string to verify.

    Returns:
        Verified payload claims.

    Raises:
        JWTError: If verification fails.
    """
    if _jose_jwt is not None:
        return _jose_jwt.decode(token, _SECRET, algorithms=[JWT_ALGO])
    return _fallback_decode(token)
