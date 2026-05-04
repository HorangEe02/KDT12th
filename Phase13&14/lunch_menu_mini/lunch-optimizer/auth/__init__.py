"""Phase 13&14: 자체 JWT + bcrypt RBAC 인증 모듈.

핵심 책임:
  - 비밀번호 해싱 (bcrypt cost=12)
  - JWT 발급/검증 (HS256)
  - FastAPI Depends 의존성: get_current_user, require_admin

사용 예:
    from auth import (
        hash_password, verify_password,
        create_access_token, decode_access_token,
        get_current_user, require_admin,
    )
"""
from auth.passwords import hash_password, verify_password
from auth.jwt_utils import create_access_token, decode_access_token, JWTError
from auth.deps import (
    get_current_user,
    require_admin,
    optional_current_user,
    oauth2_scheme,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
    "get_current_user",
    "require_admin",
    "optional_current_user",
    "oauth2_scheme",
]
