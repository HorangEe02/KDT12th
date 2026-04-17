"""Firestore 클라이언트 — 사용자 뱃지·공유 계획·대화 히스토리 영속화.

lazy init + @lru_cache로 firebase_admin.App을 1회만 생성.
로컬 개발 시 서비스 계정 키(GOOGLE_APPLICATION_CREDENTIALS) 또는 ADC 자동 사용.
연결 실패 시 모든 메서드가 경고 로그 + 기본값 반환 (UX 차단 없음).
"""
from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from src import config

log = logging.getLogger(__name__)

COLLECTION_VISITED = "visited_stadiums"
COLLECTION_PLANS = "shared_plans"
COLLECTION_SESSIONS = "chat_sessions"


@lru_cache(maxsize=1)
def _get_client():
    """Firestore client lazy init. 실패 시 None 반환 (폴백)."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred_path = config.GOOGLE_APPLICATION_CREDENTIALS
            cred = None
            if cred_path and Path(cred_path).exists():
                cred = credentials.Certificate(cred_path)
                log.info("Firestore: 서비스 계정 키 사용 (%s)", cred_path)
            else:
                # Cloud Run에선 ADC(Application Default Credentials) 자동 사용
                try:
                    cred = credentials.ApplicationDefault()
                    log.info("Firestore: ADC 사용")
                except Exception as exc:
                    log.warning("Firestore 자격증명 없음: %s", exc)
                    return None

            firebase_admin.initialize_app(cred, {
                "projectId": config.FIREBASE_PROJECT_ID,
            })
        return firestore.client()
    except ImportError:
        log.warning("firebase-admin SDK 미설치 — Firestore 비활성")
        return None
    except Exception as exc:
        log.warning("Firestore 초기화 실패: %s", exc)
        return None


def health() -> bool:
    """Firestore 연결 가능 여부."""
    return _get_client() is not None


# =====================================================================
# 사용자 ID (브라우저 세션 UUID)
# =====================================================================

def get_or_create_user_id(session_state: dict) -> str:
    """session_state에서 user_id 가져오거나 생성."""
    uid = session_state.get("user_id")
    if not uid:
        uid = f"u_{uuid.uuid4().hex[:12]}"
        session_state["user_id"] = uid
    return uid


# =====================================================================
# 뱃지 (방문 구장)
# =====================================================================

def save_visited_stadiums(user_id: str, stadiums: list[str]) -> bool:
    client = _get_client()
    if client is None:
        return False
    try:
        doc_ref = client.collection(COLLECTION_VISITED).document(user_id)
        doc_ref.set({
            "user_id": user_id,
            "stadiums": list(stadiums),
            "count": len(stadiums),
        }, merge=True)
        log.info("방문 구장 저장: user=%s, count=%d", user_id, len(stadiums))
        return True
    except Exception as exc:
        log.warning("방문 구장 저장 실패: %s", exc)
        return False


def load_visited_stadiums(user_id: str) -> list[str]:
    client = _get_client()
    if client is None:
        return []
    try:
        doc = client.collection(COLLECTION_VISITED).document(user_id).get()
        if not doc.exists:
            return []
        data = doc.to_dict() or {}
        return list(data.get("stadiums") or [])
    except Exception as exc:
        log.warning("방문 구장 로드 실패: %s", exc)
        return []


# =====================================================================
# 공유 원정 계획
# =====================================================================

def save_shared_plan(filters: dict, author_id: str | None = None) -> str | None:
    """계획 Firestore에 저장 후 plan_id 반환."""
    client = _get_client()
    if client is None:
        return None
    try:
        plan_id = f"p_{uuid.uuid4().hex[:10]}"
        payload: dict[str, Any] = {
            "plan_id": plan_id,
            "author_id": author_id,
            "team": filters.get("team"),
            "budget": filters.get("budget"),
            "party": filters.get("party"),
            "transport": filters.get("transport"),
        }
        # date_range 직렬화 (tuple → [start, end])
        dr = filters.get("date_range")
        if isinstance(dr, (list, tuple)) and len(dr) == 2:
            payload["date_start"] = str(dr[0])
            payload["date_end"] = str(dr[1])

        client.collection(COLLECTION_PLANS).document(plan_id).set(payload)
        log.info("공유 계획 저장: %s", plan_id)
        return plan_id
    except Exception as exc:
        log.warning("공유 계획 저장 실패: %s", exc)
        return None


def load_shared_plan(plan_id: str) -> dict | None:
    client = _get_client()
    if client is None or not plan_id:
        return None
    try:
        doc = client.collection(COLLECTION_PLANS).document(plan_id).get()
        if not doc.exists:
            return None
        return doc.to_dict()
    except Exception as exc:
        log.warning("공유 계획 로드 실패 (%s): %s", plan_id, exc)
        return None


# =====================================================================
# 챗 세션 (옵션)
# =====================================================================

def save_chat_session(session_id: str, messages: list[dict]) -> bool:
    client = _get_client()
    if client is None:
        return False
    try:
        # 최근 50턴만 저장 (비용 절감)
        truncated = messages[-50:] if len(messages) > 50 else messages
        client.collection(COLLECTION_SESSIONS).document(session_id).set({
            "session_id": session_id,
            "turn_count": len(truncated),
            "messages": truncated,
        }, merge=True)
        return True
    except Exception as exc:
        log.warning("챗 세션 저장 실패: %s", exc)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(f"Firestore health: {health()}")
    if health():
        test_uid = "u_test_local"
        save_visited_stadiums(test_uid, ["잠실", "수원", "광주"])
        loaded = load_visited_stadiums(test_uid)
        print(f"저장 후 로드: {loaded}")

        pid = save_shared_plan({"team": "LG", "budget": 30, "party": "couple", "transport": "train",
                                "date_range": ("2026-04-20", "2026-04-22")})
        print(f"계획 ID: {pid}")
        if pid:
            plan = load_shared_plan(pid)
            print(f"계획 로드: {plan}")
