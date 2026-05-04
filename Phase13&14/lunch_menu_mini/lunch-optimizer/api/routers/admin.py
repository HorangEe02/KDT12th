"""/api/admin/* 라우터 — 관리자 전용 사용자 CRUD.

가드:
  - 모든 엔드포인트가 require_admin Depends 를 통과해야 동작.
  - last admin 보호: 마지막 admin 강등/비활성 거부.
  - self-DELETE 보호: 본인 계정 비활성/강등 거부.

Pagination: offset/limit (기본 20, 최대 100).
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import hash_password, require_admin
from database.connection import get_session
from database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


# -----------------------------------------------------------------------------
# Pydantic 스키마
# -----------------------------------------------------------------------------
class UserPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = Field(None, max_length=120)
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    is_active: Optional[bool] = None
    team_id: Optional[str] = Field(None, max_length=50)
    avatar_emoji: Optional[str] = Field(None, max_length=10)
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[dict]


# -----------------------------------------------------------------------------
# 헬퍼
# -----------------------------------------------------------------------------
def _user_response(user: User) -> dict:
    payload = user.to_dict()
    payload.pop("password_hash", None)
    return payload


def _count_admins(session, exclude_user_id: Optional[str] = None) -> int:
    q = session.query(User).filter(User.role == "admin", User.is_active.is_(True))
    if exclude_user_id is not None:
        q = q.filter(User.id != exclude_user_id)
    return q.count()


# -----------------------------------------------------------------------------
# 엔드포인트
# -----------------------------------------------------------------------------
@router.get("/users", response_model=UserListResponse)
def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, pattern="^(admin|user)$"),
    is_active: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, max_length=100, description="이름/이메일 부분 검색"),
    admin: User = Depends(require_admin),
) -> UserListResponse:
    with get_session() as session:
        query = session.query(User)
        if role is not None:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active.is_(is_active))
        if q:
            like = f"%{q.strip()}%"
            query = query.filter((User.name.like(like)) | (User.email.like(like)))

        total = query.count()
        items = (
            query.order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return UserListResponse(
            total=total,
            offset=offset,
            limit=limit,
            items=[_user_response(u) for u in items],
        )


@router.get("/users/{user_id}")
def get_user(user_id: str, admin: User = Depends(require_admin)) -> dict:
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return _user_response(user)


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    body: UserPatch,
    admin: User = Depends(require_admin),
) -> dict:
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # last admin 보호
        if (body.role is not None and body.role != "admin" and user.role == "admin"
                and _count_admins(session, exclude_user_id=user.id) == 0):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="마지막 관리자는 강등할 수 없습니다.",
            )
        if (body.is_active is False and user.role == "admin"
                and _count_admins(session, exclude_user_id=user.id) == 0):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="마지막 관리자는 비활성화할 수 없습니다.",
            )

        # self 비활성 거부
        if body.is_active is False and user.id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="본인 계정은 비활성화할 수 없습니다.",
            )

        for field in ("name", "email", "role", "is_active", "team_id", "avatar_emoji"):
            value = getattr(body, field)
            if value is not None:
                if field == "email" and value:
                    value = value.strip().lower()
                setattr(user, field, value)

        if body.new_password:
            user.password_hash = hash_password(body.new_password)

        session.commit()
        session.refresh(user)
        logger.info("admin.update_user: admin=%s target=%s fields=%s",
                    admin.id, user.id, body.model_dump(exclude_none=True).keys())
        return _user_response(user)


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: str,
    admin: User = Depends(require_admin),
) -> dict:
    """soft-delete (is_active=False). 데이터 보존."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        if user.id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="본인 계정은 비활성화할 수 없습니다.",
            )
        if (user.role == "admin"
                and _count_admins(session, exclude_user_id=user.id) == 0):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="마지막 관리자는 비활성화할 수 없습니다.",
            )
        user.is_active = False
        session.commit()
        session.refresh(user)
        logger.info("admin.deactivate_user: admin=%s target=%s", admin.id, user.id)
        return _user_response(user)


@router.post("/users/{user_id}/restore")
def restore_user(
    user_id: str,
    admin: User = Depends(require_admin),
) -> dict:
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        user.is_active = True
        session.commit()
        session.refresh(user)
        logger.info("admin.restore_user: admin=%s target=%s", admin.id, user.id)
        return _user_response(user)


# 외래키로 user_id 를 참조할 가능성이 있는 테이블들 — 영구 삭제 시 함께 정리.
_USER_FK_TABLES = (
    "buddy_joins",
    "buddy_posts",
    "vetoes",
    "votes",
    "vote_sessions",
    "meal_history",
    "visit_history",
    "chat_messages",
)


@router.delete("/users/{user_id}/permanent")
def hard_delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
) -> dict:
    """영구 삭제 — DB row 와 모든 의존 데이터를 cascade 삭제.

    가드:
      - 본인 계정 영구 삭제 거부 (400)
      - 마지막 admin 영구 삭제 거부 (409)
      - 미존재 사용자 (404)

    cascade: votes/buddy_*/vote_*/meal_history/visit_history/chat_messages 등
             user_id 컬럼이 있는 테이블에서 해당 row 삭제 후 users 행 삭제.
             컬럼이 없는 테이블은 silently 스킵 (raw SQL try/except).
    """
    from sqlalchemy import text

    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인 계정은 영구 삭제할 수 없습니다.",
        )

    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        if (
            user.role == "admin"
            and _count_admins(session, exclude_user_id=user.id) == 0
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="마지막 관리자는 영구 삭제할 수 없습니다.",
            )

        snapshot = _user_response(user)
        deleted_counts: dict[str, int] = {}

        # 의존 row 삭제 (foreign key 무시 가능하도록 raw SQL try/except)
        for tbl in _USER_FK_TABLES:
            try:
                result = session.execute(
                    text(f"DELETE FROM {tbl} WHERE user_id = :uid"),
                    {"uid": user_id},
                )
                deleted_counts[tbl] = result.rowcount or 0
            except Exception:
                # 컬럼 없거나 테이블 없음 — 무시
                session.rollback()

        # User row 삭제 (relationship cascade 도 함께 작동)
        session.delete(user)
        session.commit()

        logger.warning(
            "admin.hard_delete_user: admin=%s target=%s cascaded=%s",
            admin.id, user_id, deleted_counts,
        )
        return {
            "ok": True,
            "permanently_deleted": True,
            "user": snapshot,
            "cascaded": deleted_counts,
        }


@router.get("/stats")
def stats(admin: User = Depends(require_admin)) -> dict:
    """대시보드 헤더용 요약."""
    with get_session() as session:
        total = session.query(User).count()
        active = session.query(User).filter(User.is_active.is_(True)).count()
        admins = (
            session.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        return {
            "total_users": total,
            "active_users": active,
            "active_admins": admins,
        }
