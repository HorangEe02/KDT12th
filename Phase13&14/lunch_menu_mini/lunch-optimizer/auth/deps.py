"""FastAPI Depends 의존성: JWT → User 객체.

사용 예:
    @router.get("/api/admin/users")
    def list_users(admin: User = Depends(require_admin)):
        ...

    @router.get("/api/auth/me")
    def me(user: User = Depends(get_current_user)):
        return user.to_dict()
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from auth.jwt_utils import JWTError, decode_access_token
from database.connection import get_session
from database.models import User

# tokenUrl 은 Swagger UI 의 "Authorize" 다이얼로그가 호출할 경로 (실제 엔드포인트와 일치 필요).
# auto_error=False → Authorization 헤더가 없어도 None 반환 (optional_current_user 용).
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


def _resolve_user_from_token(token: Optional[str]) -> Optional[User]:
    """토큰 → User. 토큰 없거나 잘못되면 None."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    with get_session() as session:
        user = session.get(User, user_id)
        if user is None or not user.is_active:
            return None
        # detached copy — 세션 닫힌 후에도 속성 접근 가능하도록 dict 직렬화 후 ORM 인스턴스 재구성은 과함.
        # 대신 lazy load 가 필요한 속성만 강제 평가.
        _ = user.email, user.role, user.name, user.team_id, user.avatar_emoji
        session.expunge(user)
        return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """JWT 필수. 401 if invalid/missing."""
    user = _resolve_user_from_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """JWT 선택. 게스트도 허용 (None 반환)."""
    return _resolve_user_from_token(token)


def require_admin(user: User = Depends(get_current_user)) -> User:
    """role==admin 필수. 403 otherwise."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return user
