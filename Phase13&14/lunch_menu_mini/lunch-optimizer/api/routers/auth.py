"""/api/auth/* 라우터 — 회원가입 · 로그인 · 본인 정보 · 비밀번호 변경.

설계 원칙:
  - 비밀번호는 절대 평문으로 저장하지 않음 (bcrypt cost=12).
  - 응답에서 password_hash 노출 금지.
  - 이메일 enumeration 방지: 로그인 실패 메시지를 "이메일 또는 비밀번호 불일치" 로 통일.
  - 토큰은 Authorization: Bearer <token> 헤더로 사용.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database.connection import get_session
from database.models import Team, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# -----------------------------------------------------------------------------
# Pydantic 스키마
# -----------------------------------------------------------------------------
class RegisterIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=50)
    team_id: str = Field("team1", max_length=50)
    avatar_emoji: str = Field("🧑‍💻", max_length=10)


class LoginIn(BaseModel):
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordIn(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# -----------------------------------------------------------------------------
# 헬퍼
# -----------------------------------------------------------------------------
def _normalize_email(raw: str) -> str:
    email = raw.strip().lower()
    # Optional dependency 없이 라우터가 항상 등록되도록, MVP에서는 보수적인
    # 문법 검증만 수행한다. MX/전달성 검증은 네트워크 호출을 만들지 않는다.
    if not _EMAIL_RE.match(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="올바르지 않은 이메일 형식입니다.",
        )
    return email


def _ensure_team(session, team_id: str) -> None:
    """팀이 없으면 자동 생성 (기존 /api/users 패턴 유지)."""
    if session.get(Team, team_id) is None:
        session.add(Team(id=team_id, name=team_id))
        session.flush()


def _generate_user_id(email: str) -> str:
    """이메일 local-part 기반 식별자 + 짧은 uuid 으로 충돌 회피."""
    local = re.split(r"[^a-zA-Z0-9_.-]", email.split("@")[0])[0][:30] or "user"
    return f"{local.lower()}-{uuid.uuid4().hex[:8]}"


def _user_response(user: User) -> dict:
    """민감 필드를 제거한 사용자 응답."""
    payload = user.to_dict()
    payload.pop("password_hash", None)
    return payload


# -----------------------------------------------------------------------------
# 엔드포인트
# -----------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn) -> TokenResponse:
    email = _normalize_email(body.email)
    pw_hash = hash_password(body.password)
    user_id = _generate_user_id(email)

    with get_session() as session:
        # 이메일 중복 체크
        existing = session.query(User).filter(User.email == email).first()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 등록된 이메일입니다.",
            )
        _ensure_team(session, body.team_id)

        user = User(
            id=user_id,
            email=email,
            password_hash=pw_hash,
            role="user",
            name=body.name,
            team_id=body.team_id,
            avatar_emoji=body.avatar_emoji,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.refresh(user)
        # detached 직전 상태 캡처
        user_payload = _user_response(user)
        token = create_access_token(
            user_id=user.id, email=user.email, role=user.role
        )
        session.commit()
        logger.info("auth.register: user_id=%s email=%s", user.id, email)
        return TokenResponse(access_token=token, user=user_payload)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginIn) -> TokenResponse:
    email = body.email.strip().lower()

    with get_session() as session:
        user: Optional[User] = (
            session.query(User).filter(User.email == email).first()
        )
        # 동일 메시지로 enumeration 방지
        invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다.",
        )
        if user is None or not user.is_active:
            raise invalid
        if not verify_password(body.password, user.password_hash):
            raise invalid

        user.last_login_at = datetime.utcnow()
        session.flush()
        session.refresh(user)
        user_payload = _user_response(user)
        token = create_access_token(
            user_id=user.id, email=user.email, role=user.role
        )
        session.commit()
        logger.info("auth.login: user_id=%s", user.id)
        return TokenResponse(access_token=token, user=user_payload)


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return _user_response(user)


@router.post("/change-password")
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
) -> dict:
    with get_session() as session:
        db_user = session.get(User, user.id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        if not verify_password(body.old_password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 일치하지 않습니다.",
            )
        db_user.password_hash = hash_password(body.new_password)
        session.commit()
        logger.info("auth.change_password: user_id=%s", user.id)
        return {"ok": True}
