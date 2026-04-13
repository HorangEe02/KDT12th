"""
main.py
헬창지피티(HelChangGPT) FastAPI 백엔드 서버

Stage 1 엔드포인트:
  POST /api/v1/profile/analyze-text       — 자연어 텍스트 분석
  POST /api/v1/profile/analyze-inbody     — 인바디 이미지 분석
  POST /api/v1/profile/build              — 통합 프로필 생성
  POST /api/v1/profile/calculate-metrics  — 신체 지표 계산

실행:
  uvicorn api.main:app --reload --port 8000
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# src 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.profile.profile_ner import extract_entities_rule_based
from src.profile.goal_classifier import classify_goal_rule_based
from src.profile.keyword_extractor import extract_keywords
from src.profile.body_calculator import calculate_all_metrics
from src.profile.health_analyzer import analyze_health_risks, calculate_profile_confidence
from src.profile.profile_builder import build_user_profile
from src.utils.llm_client import LLMClient, AVAILABLE_MODELS, DEFAULT_MODEL_ASSIGNMENTS

app = FastAPI(
    title="헬창지피티 (HelChangGPT) API",
    description="AI 기반 맞춤형 피트니스 토탈 코칭 서비스",
    version="1.0.0",
)

# CORS 설정 (React 프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ngrok/외부 접속 허용 (프로덕션에서는 특정 도메인만 허용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════
# Request / Response 모델
# ═══════════════════════════════════════

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=5, description="사용자 자연어 입력 텍스트")


class MetricsRequest(BaseModel):
    weight_kg: float = Field(..., gt=20, lt=300)
    height_cm: float = Field(..., gt=100, lt=250)
    age: int = Field(..., gt=5, lt=120)
    gender: str = Field(..., pattern="^(남성|여성)$")
    exercise_frequency: int = Field(default=3, ge=0, le=7)
    goal_type: str = Field(default="체중관리")
    body_fat_percent: Optional[float] = None
    visceral_fat_level: Optional[int] = None
    waist_hip_ratio: Optional[float] = None
    skeletal_muscle_mass_kg: Optional[float] = None


class ProfileBuildRequest(BaseModel):
    natural_text: Optional[str] = None
    inbody_data: Optional[dict] = None


# ═══════════════════════════════════════
# Stage 1 엔드포인트
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# 인증 + 어드민 시스템 (JSON 파일 기반)
# ═══════════════════════════════════════

import hashlib
import json as _json

USERS_DIR = Path(os.path.join(os.path.dirname(__file__), "..", "data", "users"))
USERS_DIR.mkdir(parents=True, exist_ok=True)


class AuthRequest(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=4)


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _load_user(user_id: str) -> dict | None:
    f = USERS_DIR / f"{user_id}.json"
    if not f.exists():
        return None
    with open(f, "r", encoding="utf-8") as fp:
        return _json.load(fp)


def _save_user(data: dict):
    f = USERS_DIR / f"{data['user_id']}.json"
    with open(f, "w", encoding="utf-8") as fp:
        _json.dump(data, fp, ensure_ascii=False, indent=2)


def _user_response(data: dict) -> dict:
    return {
        "user_id": data["user_id"],
        "nickname": data["nickname"],
        "role": data.get("role", "user"),
        "is_active": data.get("is_active", True),
        "joined_at": data.get("joined_at", ""),
        "last_active_at": data.get("last_active_at", ""),
    }


def _check_admin(admin_id: str):
    data = _load_user(admin_id)
    if not data or data.get("role") != "admin":
        raise HTTPException(403, "관리자 권한이 필요합니다")


# ── 기본 어드민 계정 자동 생성 ──
_admin_file = USERS_DIR / "admin.json"
if not _admin_file.exists():
    _save_user({
        "user_id": "admin",
        "nickname": "관리자",
        "password_hash": _hash_password("helchang2026!"),
        "role": "admin",
        "is_active": True,
        "joined_at": datetime.now().isoformat(),
        "last_active_at": datetime.now().isoformat(),
    })


@app.post("/api/v1/auth/signup")
async def auth_signup(req: AuthRequest):
    user_id = req.nickname.lower().replace(" ", "_")
    if _load_user(user_id):
        raise HTTPException(400, "이미 존재하는 닉네임이에요. 다른 닉네임을 사용해주세요.")

    user_data = {
        "user_id": user_id,
        "nickname": req.nickname,
        "password_hash": _hash_password(req.password),
        "role": "user",
        "is_active": True,
        "joined_at": datetime.now().isoformat(),
        "last_active_at": datetime.now().isoformat(),
    }
    _save_user(user_data)
    return {"user": _user_response(user_data)}


@app.post("/api/v1/auth/login")
async def auth_login(req: AuthRequest):
    user_id = req.nickname.lower().replace(" ", "_")
    user_data = _load_user(user_id)

    if not user_data:
        raise HTTPException(401, "존재하지 않는 닉네임이에요. 회원가입을 먼저 해주세요.")
    if not user_data.get("is_active", True):
        raise HTTPException(403, "비활성화된 계정이에요. 관리자에게 문의해주세요.")
    if user_data["password_hash"] != _hash_password(req.password):
        raise HTTPException(401, "비밀번호가 틀렸어요. 다시 확인해주세요.")

    user_data["last_active_at"] = datetime.now().isoformat()
    _save_user(user_data)
    return {"user": _user_response(user_data)}


# ═══════════════════════════════════════
# 어드민 전용 API
# ═══════════════════════════════════════

@app.get("/api/v1/admin/users")
async def admin_list_users(admin_id: str = "admin"):
    """전체 사용자 목록 (어드민 전용)"""
    _check_admin(admin_id)
    users = []
    for f in sorted(USERS_DIR.glob("*.json")):
        data = _json.load(open(f, encoding="utf-8"))
        info = _user_response(data)
        # 측정 횟수 추가
        history_file = Path(os.path.join(os.path.dirname(__file__), "..", "data", "user_profiles", data["user_id"], "history.json"))
        if history_file.exists():
            h = _json.load(open(history_file, encoding="utf-8"))
            info["measurement_count"] = len(h.get("measurements", []))
        else:
            info["measurement_count"] = 0
        users.append(info)
    return {"users": users, "total": len(users)}


@app.get("/api/v1/admin/users/{user_id}")
async def admin_get_user(user_id: str, admin_id: str = "admin"):
    """사용자 상세 정보 (어드민 전용)"""
    _check_admin(admin_id)
    data = _load_user(user_id)
    if not data:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")
    info = _user_response(data)
    # 히스토리 추가
    history_file = Path(os.path.join(os.path.dirname(__file__), "..", "data", "user_profiles", user_id, "history.json"))
    if history_file.exists():
        info["history"] = _json.load(open(history_file, encoding="utf-8"))
    return info


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|user)$")


@app.put("/api/v1/admin/users/{user_id}/role")
async def admin_update_role(user_id: str, req: RoleUpdateRequest, admin_id: str = "admin"):
    """사용자 역할 변경 (어드민 전용)"""
    _check_admin(admin_id)
    data = _load_user(user_id)
    if not data:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")
    data["role"] = req.role
    _save_user(data)
    return {"message": f"{data['nickname']}의 역할을 '{req.role}'(으)로 변경했습니다", "user": _user_response(data)}


@app.put("/api/v1/admin/users/{user_id}/reset-password")
async def admin_reset_password(user_id: str, admin_id: str = "admin"):
    """비밀번호 초기화 — 'reset1234'로 설정 (어드민 전용)"""
    _check_admin(admin_id)
    data = _load_user(user_id)
    if not data:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")
    new_pw = "reset1234"
    data["password_hash"] = _hash_password(new_pw)
    _save_user(data)
    return {"message": f"{data['nickname']}의 비밀번호를 '{new_pw}'(으)로 초기화했습니다"}


@app.put("/api/v1/admin/users/{user_id}/toggle-active")
async def admin_toggle_active(user_id: str, admin_id: str = "admin"):
    """계정 활성/비활성 전환 (어드민 전용)"""
    _check_admin(admin_id)
    if user_id == "admin":
        raise HTTPException(400, "관리자 계정은 비활성화할 수 없습니다")
    data = _load_user(user_id)
    if not data:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")
    data["is_active"] = not data.get("is_active", True)
    _save_user(data)
    status = "활성화" if data["is_active"] else "비활성화"
    return {"message": f"{data['nickname']} 계정을 {status}했습니다", "user": _user_response(data)}


@app.delete("/api/v1/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin_id: str = "admin"):
    """계정 삭제 (어드민 전용)"""
    _check_admin(admin_id)
    if user_id == "admin":
        raise HTTPException(400, "관리자 계정은 삭제할 수 없습니다")
    user_file = USERS_DIR / f"{user_id}.json"
    if not user_file.exists():
        raise HTTPException(404, "사용자를 찾을 수 없습니다")
    data = _json.load(open(user_file, encoding="utf-8"))
    user_file.unlink()
    return {"message": f"{data.get('nickname', user_id)} 계정을 삭제했습니다"}


@app.get("/api/v1/admin/stats")
async def admin_stats(admin_id: str = "admin"):
    """시스템 통계 (어드민 전용)"""
    _check_admin(admin_id)

    # 사용자 통계
    user_files = list(USERS_DIR.glob("*.json"))
    total_users = len(user_files)
    today = datetime.now().strftime("%Y-%m-%d")
    active_today = 0
    admin_count = 0
    for f in user_files:
        d = _json.load(open(f, encoding="utf-8"))
        if d.get("last_active_at", "").startswith(today):
            active_today += 1
        if d.get("role") == "admin":
            admin_count += 1

    # 데이터 통계
    data_root = Path(os.path.join(os.path.dirname(__file__), ".."))
    nutrition_file = data_root / "data" / "nutrition" / "foods.json"
    exercise_file = data_root / "data" / "exercises" / "exercise_db.json"

    nutrition_count = 0
    if nutrition_file.exists():
        nutrition_count = len(_json.load(open(nutrition_file, encoding="utf-8")))

    exercise_count = 0
    if exercise_file.exists():
        ex_data = _json.load(open(exercise_file, encoding="utf-8"))
        exercise_count = ex_data.get("total_count", len(ex_data.get("exercises", [])))

    # 인바디 측정 수
    profiles_dir = data_root / "data" / "user_profiles"
    total_measurements = 0
    if profiles_dir.exists():
        for hf in profiles_dir.rglob("history.json"):
            h = _json.load(open(hf, encoding="utf-8"))
            total_measurements += len(h.get("measurements", []))

    return {
        "users": {"total": total_users, "admins": admin_count, "active_today": active_today},
        "data": {"nutrition_items": nutrition_count, "exercises": exercise_count, "inbody_measurements": total_measurements},
    }


# ═══════════════════════════════════════
# 회원 관리 API (어드민 전용 확장)
# ═══════════════════════════════════════

DATA_ROOT = Path(os.path.join(os.path.dirname(__file__), ".."))
PROFILES_DIR = DATA_ROOT / "data" / "user_profiles"


class ProfileUpdateRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal_type: Optional[str] = None
    constraints: Optional[list[str]] = None
    experience_level: Optional[str] = None
    exercise_frequency: Optional[int] = None
    admin_memo: Optional[str] = None


@app.get("/api/v1/admin/members")
async def admin_list_members(
    admin_id: str = "admin",
    search: str = "",
    role_filter: str = "",
    active_filter: str = "",
    sort_by: str = "joined_at",
    sort_order: str = "desc",
):
    """
    회원 목록 (검색/필터/정렬 지원)

    - search: 닉네임 검색
    - role_filter: admin | user
    - active_filter: active | inactive
    - sort_by: joined_at | last_active_at | nickname | measurement_count
    - sort_order: asc | desc
    """
    _check_admin(admin_id)

    members = []
    for f in USERS_DIR.glob("*.json"):
        d = _json.load(open(f, encoding="utf-8"))

        # 검색 필터
        if search and search.lower() not in d.get("nickname", "").lower():
            continue
        if role_filter and d.get("role") != role_filter:
            continue
        if active_filter == "active" and not d.get("is_active", True):
            continue
        if active_filter == "inactive" and d.get("is_active", True):
            continue

        # 측정 횟수
        history_file = PROFILES_DIR / d["user_id"] / "history.json"
        mc = 0
        if history_file.exists():
            mc = len(_json.load(open(history_file, encoding="utf-8")).get("measurements", []))

        profile = d.get("profile", {})

        members.append({
            **_user_response(d),
            "measurement_count": mc,
            "profile": profile,
            "admin_memo": d.get("admin_memo", ""),
        })

    # 정렬
    reverse = sort_order == "desc"
    if sort_by == "measurement_count":
        members.sort(key=lambda m: m.get("measurement_count", 0), reverse=reverse)
    elif sort_by == "nickname":
        members.sort(key=lambda m: m.get("nickname", ""), reverse=reverse)
    elif sort_by == "last_active_at":
        members.sort(key=lambda m: m.get("last_active_at", ""), reverse=reverse)
    else:
        members.sort(key=lambda m: m.get("joined_at", ""), reverse=reverse)

    return {"members": members, "total": len(members)}


@app.get("/api/v1/admin/members/{user_id}/detail")
async def admin_member_detail(user_id: str, admin_id: str = "admin"):
    """회원 상세 정보 (프로필 + 인바디 + 식단/운동/일지 이력)"""
    _check_admin(admin_id)

    data = _load_user(user_id)
    if not data:
        raise HTTPException(404, "회원을 찾을 수 없습니다")

    result = {**_user_response(data), "profile": data.get("profile", {}), "admin_memo": data.get("admin_memo", "")}

    user_dir = PROFILES_DIR / user_id

    # 인바디 이력
    history_file = user_dir / "history.json"
    if history_file.exists():
        h = _json.load(open(history_file, encoding="utf-8"))
        result["inbody_history"] = h.get("measurements", [])
    else:
        result["inbody_history"] = []

    # 식단/운동/일지 이력
    for key, filename in [("diet_history", "diet_history.json"), ("workout_history", "workout_history.json"), ("diary_history", "diary_history.json")]:
        fp = user_dir / filename
        result[key] = _json.load(open(fp, encoding="utf-8")) if fp.exists() else []

    # 활동 로그
    log_file = user_dir / "activity_log.json"
    result["activity_log"] = _json.load(open(log_file, encoding="utf-8")) if log_file.exists() else []

    return result


@app.put("/api/v1/admin/members/{user_id}/profile")
async def admin_update_member_profile(user_id: str, req: ProfileUpdateRequest, admin_id: str = "admin"):
    """회원 프로필 수정 (어드민)"""
    _check_admin(admin_id)

    data = _load_user(user_id)
    if not data:
        raise HTTPException(404, "회원을 찾을 수 없습니다")

    # profile 필드 업데이트
    if "profile" not in data:
        data["profile"] = {}

    profile = data["profile"]
    for field in ["age", "gender", "height_cm", "weight_kg", "goal_type", "constraints", "experience_level", "exercise_frequency"]:
        val = getattr(req, field, None)
        if val is not None:
            profile[field] = val

    if req.admin_memo is not None:
        data["admin_memo"] = req.admin_memo

    data["profile"] = profile
    _save_user(data)

    return {"message": f"{data['nickname']}의 프로필을 수정했습니다", "profile": profile}


# ── 본인 탈퇴 ──

class WithdrawRequest(BaseModel):
    user_id: str
    password: str
    delete_data: bool = False  # True면 측정 데이터도 삭제


@app.post("/api/v1/auth/withdraw")
async def auth_withdraw(req: WithdrawRequest):
    """본인 계정 탈퇴"""
    data = _load_user(req.user_id)
    if not data:
        raise HTTPException(404, "계정을 찾을 수 없습니다")
    if data.get("role") == "admin":
        raise HTTPException(400, "관리자 계정은 탈퇴할 수 없습니다")
    if data["password_hash"] != _hash_password(req.password):
        raise HTTPException(401, "비밀번호가 틀렸습니다")

    # 계정 파일 삭제
    user_file = USERS_DIR / f"{req.user_id}.json"
    user_file.unlink(missing_ok=True)

    # 측정 데이터 삭제 (선택)
    if req.delete_data:
        import shutil
        user_profile_dir = PROFILES_DIR / req.user_id
        if user_profile_dir.exists():
            shutil.rmtree(user_profile_dir)

    return {"message": "계정이 탈퇴 처리되었습니다. 이용해 주셔서 감사합니다."}


# ── 활동 로그 기록 유틸 ──

def _log_activity(user_id: str, action: str, detail: str = ""):
    """사용자 활동을 기록합니다."""
    user_dir = PROFILES_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    log_file = user_dir / "activity_log.json"

    logs = []
    if log_file.exists():
        logs = _json.load(open(log_file, encoding="utf-8"))

    logs.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "detail": detail,
    })

    # 최근 200건만 보관
    logs = logs[-200:]

    with open(log_file, "w", encoding="utf-8") as f:
        _json.dump(logs, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════
# AI 채팅 (프로필 대화형 입력/수정)
# ═══════════════════════════════════════

class ChatRequest(BaseModel):
    user_id: str = "default"
    message: str
    model: str = "exaone3.5:7.8b"


CHAT_SYSTEM_PROMPT = """당신은 헬창지피티의 AI 피트니스 코치입니다. 사용자와 대화하면서 신체 정보를 수집하고 운동/건강 상담을 합니다.

규칙:
1. 친근한 반말과 존댓말을 상황에 맞게 섞어 사용하세요.
2. 사용자가 신체 정보(나이, 키, 체중, 목표 등)를 알려주면, 응답 끝에 아래 형식으로 추출된 데이터를 추가하세요:
   [PROFILE_UPDATE] {"age": 25, "gender": "남성", "height_cm": 178, "weight_kg": 82}
3. 신체 정보가 없는 일반 대화는 자연스럽게 응답하세요.
4. 운동이나 건강에 대한 질문에 전문적으로 답변하세요.
5. 200자 이내로 간결하게 답변하세요."""


@app.post("/api/v1/chat")
async def chat_with_ai(req: ChatRequest):
    """AI와 대화하면서 프로필 정보를 입력/수정합니다."""
    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

        # 사용자 현재 프로필 로드
        user_data = _load_user(req.user_id)
        profile_context = ""
        if user_data and user_data.get("profile"):
            p = user_data["profile"]
            profile_context = f"\n현재 사용자 프로필: {_json.dumps(p, ensure_ascii=False)}"

        response = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT + profile_context},
                {"role": "user", "content": req.message},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        reply = response.choices[0].message.content

        # 프로필 업데이트 감지
        profile_update = None
        if "[PROFILE_UPDATE]" in reply:
            parts = reply.split("[PROFILE_UPDATE]")
            reply = parts[0].strip()
            try:
                update_json = parts[1].strip()
                if update_json.startswith("{"):
                    profile_update = _json.loads(update_json.split("}")[0] + "}")
            except:
                pass

        # NER 폴백: LLM이 태그를 안 붙였어도 규칙 기반으로 추출 시도
        if not profile_update:
            from src.profile.profile_ner import extract_entities_rule_based
            entities = extract_entities_rule_based(req.message)
            extracted = {}
            if entities.age: extracted["age"] = entities.age
            if entities.gender: extracted["gender"] = entities.gender
            if entities.height_cm: extracted["height_cm"] = entities.height_cm
            if entities.weight_kg: extracted["weight_kg"] = entities.weight_kg
            if entities.exercise_frequency: extracted["exercise_frequency"] = entities.exercise_frequency
            if extracted:
                profile_update = extracted

        # 프로필 저장
        if profile_update and user_data:
            if "profile" not in user_data:
                user_data["profile"] = {}
            for k, v in profile_update.items():
                if v is not None:
                    user_data["profile"][k] = v
            _save_user(user_data)

        return {
            "reply": reply,
            "profile_update": profile_update,
            "current_profile": user_data.get("profile", {}) if user_data else {},
        }

    except Exception as e:
        # Ollama 미연결 시 간단 응답
        return {
            "reply": f"안녕하세요! 저는 헬창지피티 AI 코치예요. 현재 AI 서버(Ollama)에 연결할 수 없어서 간단히 답변드릴게요. 신체 정보를 알려주시면 기록해드려요! (오류: {str(e)[:30]})",
            "profile_update": None,
            "current_profile": {},
        }


# ── 사용자 프로필 조회/저장 ──

@app.get("/api/v1/profile/{user_id}")
async def get_user_profile(user_id: str):
    """사용자 프로필 + 인바디 이력 조회"""
    user_data = _load_user(user_id)
    if not user_data:
        return {"profile": {}, "inbody_history": [], "has_data": False}

    profile = user_data.get("profile", {})

    # 인바디 이력
    history_file = PROFILES_DIR / user_id / "history.json"
    inbody_history = []
    if history_file.exists():
        h = _json.load(open(history_file, encoding="utf-8"))
        inbody_history = h.get("measurements", [])

    # BMI/BMR 계산 (프로필에 키/체중 있을 때)
    calculated = {}
    if profile.get("height_cm") and profile.get("weight_kg"):
        from src.profile.body_calculator import calculate_all_metrics
        metrics = calculate_all_metrics(
            weight_kg=profile["weight_kg"],
            height_cm=profile["height_cm"],
            age=profile.get("age", 30),
            gender=profile.get("gender", "남성"),
            exercise_frequency=profile.get("exercise_frequency", 3),
            goal_type=profile.get("goal_type", "체중관리"),
        )
        calculated = {
            "bmi": metrics.bmi, "bmi_category": metrics.bmi_category,
            "bmr_kcal": metrics.bmr_kcal, "tdee_kcal": metrics.tdee_kcal,
            "recommended_intake_kcal": metrics.recommended_intake_kcal,
            "ideal_weight_kg": metrics.ideal_weight_kg,
        }

    return {
        "profile": profile,
        "calculated": calculated,
        "inbody_history": inbody_history,
        "has_data": bool(profile),
        "nickname": user_data.get("nickname", ""),
    }


class SaveProfileRequest(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    goal_type: Optional[str] = None
    constraints: Optional[list[str]] = None
    experience_level: Optional[str] = None
    exercise_frequency: Optional[int] = None


@app.post("/api/v1/profile/save")
async def save_user_profile(req: SaveProfileRequest):
    """사용자 프로필 저장 (폼 입력)"""
    user_data = _load_user(req.user_id)
    if not user_data:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")

    if "profile" not in user_data:
        user_data["profile"] = {}

    p = user_data["profile"]
    for field in ["name", "age", "gender", "height_cm", "weight_kg", "body_fat_percent", "goal_type", "constraints", "experience_level", "exercise_frequency"]:
        val = getattr(req, field, None)
        if val is not None:
            p[field] = val

    user_data["profile"] = p
    _save_user(user_data)

    _log_activity(req.user_id, "프로필 수정", f"폼 입력으로 프로필 업데이트")

    return {"message": "프로필이 저장되었습니다", "profile": p}


@app.get("/")
async def root():
    return {
        "service": "헬창지피티 (HelChangGPT)",
        "version": "1.0.0",
        "description": "AI가 설계하는 나만의 피트니스 라이프 코치",
        "endpoints": {
            "analyze_text": "POST /api/v1/profile/analyze-text",
            "analyze_inbody": "POST /api/v1/profile/analyze-inbody",
            "build_profile": "POST /api/v1/profile/build",
            "calculate_metrics": "POST /api/v1/profile/calculate-metrics",
        },
    }


@app.post("/api/v1/profile/analyze-text")
async def analyze_text(request: TextAnalysisRequest):
    """
    자연어 텍스트를 분석하여 NER, 목표 분류, 키워드 추출 결과를 반환합니다.
    """
    text = request.text

    # NER
    entities = extract_entities_rule_based(text)

    # 목표 분류
    goal_result = classify_goal_rule_based(text)

    # 키워드 추출
    keyword_result = extract_keywords(text, top_n=5)

    return {
        "entities": {
            "age": entities.age,
            "gender": entities.gender,
            "height_cm": entities.height_cm,
            "weight_kg": entities.weight_kg,
            "body_fat_percent": entities.body_fat_percent,
            "exercise_frequency": entities.exercise_frequency,
            "constraints": entities.constraints,
            "preferred_exercises": entities.preferred_exercises,
            "experience_level": entities.experience_level,
        },
        "goal_classification": {
            "goal_type": goal_result.goal_type.value,
            "confidence": goal_result.confidence,
            "method": goal_result.method,
            "reason": goal_result.reason,
        },
        "keywords": keyword_result.keywords,
        "keyword_model": keyword_result.model_used,
    }


@app.post("/api/v1/profile/analyze-inbody")
async def analyze_inbody(
    image: UploadFile = File(...),
    model: str = "gemma4:e4b",
    provider: str = "ollama",
    api_key: Optional[str] = None,
):
    """
    인바디 이미지를 분석하여 체성분 데이터를 추출합니다.

    - provider="ollama" (기본): 로컬 Ollama 비전 모델 사용 (gemma4 등)
    - provider="openai": OpenAI API 사용 (API 키 필요)
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    # 임시 파일에 이미지 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        content = await image.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if provider == "ollama":
            from src.profile.inbody_parser import parse_inbody_with_ollama
            result = parse_inbody_with_ollama(
                image_path=tmp_path,
                model=model,
            )
        else:
            effective_api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not effective_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="OpenAI provider 사용 시 API 키가 필요합니다.",
                )
            from src.profile.inbody_parser import parse_inbody_with_openai
            result = parse_inbody_with_openai(
                image_path=tmp_path,
                api_key=effective_api_key,
                model=model,
            )
        return {
            "inbody_data": result.raw,
            "parse_method": result.parse_method,
            "parse_confidence": result.parse_confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인바디 파싱 실패: {str(e)}")
    finally:
        os.unlink(tmp_path)


@app.get("/api/v1/models")
async def list_models():
    """사용 가능한 LLM 모델 목록과 작업별 기본 배정을 반환합니다."""
    models = {}
    for key, config in AVAILABLE_MODELS.items():
        models[key] = {
            "display_name": config.display_name,
            "provider": config.provider.value,
            "supports_vision": config.supports_vision,
            "supports_korean": config.supports_korean,
            "size_gb": config.size_gb,
            "recommended_for": config.recommended_for,
            "description": config.description,
        }
    return {
        "models": models,
        "default_assignments": DEFAULT_MODEL_ASSIGNMENTS,
    }


@app.post("/api/v1/profile/calculate-metrics")
async def calculate_metrics(request: MetricsRequest):
    """
    신체 정보를 바탕으로 BMI, BMR, TDEE 등 건강 지표를 계산합니다.
    """
    metrics = calculate_all_metrics(
        weight_kg=request.weight_kg,
        height_cm=request.height_cm,
        age=request.age,
        gender=request.gender,
        exercise_frequency=request.exercise_frequency,
        goal_type=request.goal_type,
        body_fat_percent=request.body_fat_percent,
        visceral_fat_level=request.visceral_fat_level,
        waist_hip_ratio=request.waist_hip_ratio,
        skeletal_muscle_mass_kg=request.skeletal_muscle_mass_kg,
    )

    return {
        "bmi": metrics.bmi,
        "bmi_category": metrics.bmi_category,
        "bmr_kcal": metrics.bmr_kcal,
        "tdee_kcal": metrics.tdee_kcal,
        "recommended_intake_kcal": metrics.recommended_intake_kcal,
        "ideal_weight_kg": metrics.ideal_weight_kg,
        "ideal_weight_range": list(metrics.ideal_weight_range),
        "body_fat_category": metrics.body_fat_category,
        "visceral_fat_risk": metrics.visceral_fat_risk,
        "smi": metrics.smi,
        "sarcopenia_risk": metrics.sarcopenia_risk,
    }


@app.post("/api/v1/profile/build")
async def build_profile(request: ProfileBuildRequest):
    """
    모든 분석 결과를 통합하여 최종 사용자 프로필을 생성합니다.
    """
    if not request.natural_text and not request.inbody_data:
        raise HTTPException(
            status_code=400,
            detail="natural_text 또는 inbody_data 중 하나 이상 필요합니다.",
        )

    profile = build_user_profile(
        inbody_data=request.inbody_data,
        natural_text=request.natural_text,
    )

    return profile


# ═══════════════════════════════════════
# 인바디 파일 업로드 (이미지/CSV/PDF/Word/Excel)
# ═══════════════════════════════════════

@app.post("/api/v1/inbody/upload")
async def upload_inbody_file(
    file: UploadFile = File(...),
    user_id: str = "default",
    model: str = "gemma4:e4b",
):
    """
    인바디 파일을 업로드하여 파싱 + 분석 + 저장합니다.
    지원 포맷: PNG/JPG (이미지), CSV, PDF, Word(.docx), Excel(.xlsx)
    """
    from src.profile.inbody_parser import parse_inbody_auto
    from src.profile.inbody_analyzer import analyze_inbody
    from src.profile.user_history import save_measurement

    ext = Path(file.filename).suffix.lower()
    allowed = {".png", ".jpg", ".jpeg", ".csv", ".pdf", ".docx", ".xlsx", ".xls"}
    if ext not in allowed:
        raise HTTPException(400, f"지원하지 않는 파일: {ext} (지원: {', '.join(allowed)})")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 이미지 파일이면 모델 파라미터 전달
        if ext in (".png", ".jpg", ".jpeg"):
            inbody = parse_inbody_auto(tmp_path, model=model)
        else:
            inbody = parse_inbody_auto(tmp_path)

        # 분석
        analysis = analyze_inbody(inbody)

        # 저장
        save_result = save_measurement(user_id, inbody)

        return {
            "inbody_data": inbody.raw,
            "parse_method": inbody.parse_method,
            "parse_confidence": inbody.parse_confidence,
            "validation": inbody.validation,
            "analysis": {
                "body_shape": analysis.body_shape,
                "body_shape_description": analysis.body_shape_description,
                "bmi_status": analysis.bmi_status,
                "body_fat_status": analysis.body_fat_status,
                "combined_assessment": analysis.combined_assessment,
                "visceral_fat_risk": analysis.visceral_fat_risk,
                "sarcopenia_risk": analysis.sarcopenia_risk,
                "ecw_status": analysis.ecw_status,
                "overall_grade": analysis.overall_grade,
                "inbody_score": analysis.inbody_score,
                "praise_points": analysis.praise_points,
                "improvement_points": analysis.improvement_points,
                "action_items": analysis.action_items,
                "coaching_messages": analysis.coaching_messages,
                "muscle_balance": analysis.muscle_balance,
                "trend_summary": analysis.trend_summary,
            },
            "save_result": save_result,
        }
    except Exception as e:
        raise HTTPException(500, f"파싱/분석 실패: {str(e)}")
    finally:
        os.unlink(tmp_path)


# ═══════════════════════════════════════
# 보고서 다운로드
# ═══════════════════════════════════════

@app.get("/api/v1/report/download")
async def download_report(
    user_id: str = "default",
    format: str = Query("pdf", regex="^(csv|pdf|docx|xlsx|json)$"),
):
    """
    최신 인바디 분석 보고서를 지정 포맷으로 다운로드합니다.
    지원 포맷: csv, pdf, docx, xlsx, json
    """
    from src.profile.user_history import get_history
    from src.profile.inbody_parser import InBodyData, _build_inbody_data
    from src.profile.inbody_analyzer import analyze_inbody
    from src.profile.report_generator import export_report

    history = get_history(user_id)
    measurements = history.get("measurements", [])

    if not measurements:
        raise HTTPException(404, f"사용자 '{user_id}'의 측정 데이터가 없습니다.")

    latest = measurements[-1]
    inbody = _build_inbody_data(latest["data"], latest.get("parse_method", "history"))
    analysis = analyze_inbody(inbody)

    result = export_report(inbody, analysis, format=format)

    if format == "json":
        return result

    mime_types = {
        "csv": "text/csv",
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    filename = f"helchanggpt_report_{user_id}_{datetime.now().strftime('%Y%m%d')}.{format}"

    return StreamingResponse(
        result,
        media_type=mime_types[format],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════
# 사용자 히스토리
# ═══════════════════════════════════════

@app.get("/api/v1/user/{user_id}/history")
async def get_user_history(user_id: str):
    """사용자의 인바디 측정 이력을 반환합니다."""
    from src.profile.user_history import get_history
    return get_history(user_id)


@app.get("/api/v1/user/{user_id}/trend")
async def get_user_trend(user_id: str):
    """사용자의 신체변화 추이 데이터를 반환합니다."""
    from src.profile.user_history import get_trend_data
    return get_trend_data(user_id)


@app.get("/api/v1/users")
async def list_all_users():
    """저장된 사용자 목록을 반환합니다."""
    from src.profile.user_history import list_users
    return {"users": list_users()}


# ═══════════════════════════════════════
# Stage 2: 식단 생성
# ═══════════════════════════════════════

class DietRequest(BaseModel):
    user_profile: dict
    model: str = "exaone3.5:7.8b"
    prompt_type: str = "few_shot"
    temperature: float = 0.7


class DietDemoRequest(BaseModel):
    target_kcal: int = 1800
    goal_type: str = "체지방감소"


@app.post("/api/v1/diet/generate")
async def generate_diet(request: DietRequest):
    """
    사용자 프로필 기반 맞춤 식단을 LLM으로 생성합니다.
    Ollama 로컬 모델을 사용합니다.
    """
    from src.diet.macro_calculator import calculate_macro_targets
    from src.diet.diet_generator import generate_diet_plan
    from src.diet.diet_analyzer import analyze_diet_plan

    profile = request.user_profile
    calc = profile.get("calculated", {})
    nlp = profile.get("nlp_analysis", {})
    basic = profile.get("basic", {})

    # 탄단지 목표 계산
    macro = calculate_macro_targets(
        total_kcal=calc.get("recommended_intake_kcal", 2000),
        goal_type=nlp.get("goal_type", "체중관리"),
        constraints=nlp.get("constraints", []),
        weight_kg=basic.get("weight_kg"),
    )

    # 식단 생성
    result = generate_diet_plan(
        user_profile=profile,
        macro_targets=macro,
        model=request.model,
        prompt_type=request.prompt_type,
        temperature=request.temperature,
    )

    if not result.success:
        raise HTTPException(500, f"식단 생성 실패: {result.error}")

    # 식단 분석
    analysis = analyze_diet_plan(
        meal_plan=result.meal_plan,
        macro_targets=macro,
        constraints=nlp.get("constraints"),
        weight_kg=basic.get("weight_kg"),
    )

    return {
        "meal_plan": result.meal_plan,
        "macro_targets": {
            "total_kcal": macro.total_kcal,
            "carb_ratio": macro.carb_ratio,
            "protein_ratio": macro.protein_ratio,
            "fat_ratio": macro.fat_ratio,
            "carb_g": macro.carb_g,
            "protein_g": macro.protein_g,
            "fat_g": macro.fat_g,
            "description": macro.description,
            "notes": macro.notes,
        },
        "analysis": {
            "calorie_diff": analysis.calorie_diff,
            "calorie_accuracy_pct": analysis.calorie_accuracy_pct,
            "macro_accuracy": analysis.macro_accuracy,
            "constraint_warnings": analysis.constraint_warnings,
            "keywords": analysis.keywords,
            "summary": analysis.summary,
            "overall_score": analysis.overall_score,
            "grade": analysis.grade,
        },
        "generation_info": {
            "model": result.model,
            "prompt_type": result.prompt_type,
            "temperature": result.temperature,
            "latency_sec": result.latency_sec,
        },
    }


@app.post("/api/v1/diet/demo")
async def generate_diet_demo(request: DietDemoRequest):
    """LLM 없이 데모 식단을 생성합니다."""
    from src.diet.diet_generator import generate_demo_meal_plan
    from src.diet.macro_calculator import calculate_macro_targets
    from src.diet.diet_analyzer import analyze_diet_plan

    macro = calculate_macro_targets(request.target_kcal, request.goal_type)
    meal_plan = generate_demo_meal_plan(request.target_kcal, request.goal_type)
    analysis = analyze_diet_plan(meal_plan, macro)

    return {
        "meal_plan": meal_plan,
        "analysis": {
            "summary": analysis.summary,
            "keywords": analysis.keywords,
            "overall_score": analysis.overall_score,
            "grade": analysis.grade,
        },
    }


@app.post("/api/v1/diet/calculate-macros")
async def calculate_macros(
    total_kcal: int = 2000,
    goal_type: str = "체중관리",
    constraints: str = "",
    weight_kg: float = 70,
):
    """목표 칼로리와 유형에 따른 탄단지 비율을 계산합니다."""
    from src.diet.macro_calculator import calculate_macro_targets

    constraint_list = [c.strip() for c in constraints.split(",") if c.strip()]
    macro = calculate_macro_targets(total_kcal, goal_type, constraint_list, weight_kg)

    return {
        "total_kcal": macro.total_kcal,
        "carb": {"ratio_pct": macro.carb_ratio, "grams": macro.carb_g},
        "protein": {"ratio_pct": macro.protein_ratio, "grams": macro.protein_g},
        "fat": {"ratio_pct": macro.fat_ratio, "grams": macro.fat_g},
        "description": macro.description,
        "notes": macro.notes,
    }


@app.get("/api/v1/diet/search-food")
async def search_food_nutrition(query: str, top_n: int = 5):
    """식품 영양성분을 검색합니다."""
    from src.diet.nutrition_db import search_food
    return {"query": query, "results": search_food(query, top_n)}


# ── 시간대별 식단 생성 ──

class ScheduledDietRequest(BaseModel):
    user_profile: dict
    wake_time: str = "07:00"
    sleep_time: str = "23:00"
    workout_time: Optional[str] = "18:00"
    workout_duration_min: int = 60
    work_start: str = "09:00"
    work_end: str = "18:00"
    is_workout_day: bool = True
    schedule_note: str = ""
    model: str = "exaone3.5:7.8b"
    temperature: float = 0.7


@app.post("/api/v1/diet/generate-scheduled")
async def generate_scheduled_diet(request: ScheduledDietRequest):
    """
    사용자 일정에 맞춘 시간대별 식단을 생성합니다.
    운동 전후 간식, 끼니별 추천 시간, 대체 메뉴를 포함합니다.
    """
    from src.diet.meal_scheduler import UserSchedule, create_meal_schedule, schedule_to_prompt_context, get_meal_calorie_allocation
    from src.diet.macro_calculator import calculate_macro_targets
    from src.diet.diet_generator import generate_diet_plan
    from src.diet.diet_analyzer import analyze_diet_plan

    profile = request.user_profile
    calc = profile.get("calculated", {})
    nlp = profile.get("nlp_analysis", {})
    basic = profile.get("basic", {})

    # 스케줄 생성
    schedule = UserSchedule(
        wake_time=request.wake_time,
        sleep_time=request.sleep_time,
        workout_time=request.workout_time,
        workout_duration_min=request.workout_duration_min,
        work_start=request.work_start,
        work_end=request.work_end,
        is_workout_day=request.is_workout_day,
        schedule_note=request.schedule_note,
    )

    meal_schedule = create_meal_schedule(schedule, nlp.get("goal_type", "체중관리"))
    schedule_context = schedule_to_prompt_context(meal_schedule)

    # 탄단지 계산
    macro = calculate_macro_targets(
        total_kcal=calc.get("recommended_intake_kcal", 2000),
        goal_type=nlp.get("goal_type", "체중관리"),
        constraints=nlp.get("constraints", []),
        weight_kg=basic.get("weight_kg"),
    )

    # 끼니별 칼로리 배분
    calorie_allocation = get_meal_calorie_allocation(meal_schedule, macro.total_kcal)

    # LLM 식단 생성 (scheduled 프롬프트)
    result = generate_diet_plan(
        user_profile=profile,
        macro_targets=macro,
        model=request.model,
        prompt_type="scheduled",
        temperature=request.temperature,
    )

    # 식단 분석
    meal_plan = result.meal_plan if result.success else {}
    analysis = None
    if result.success:
        analysis = analyze_diet_plan(
            meal_plan=meal_plan,
            macro_targets=macro,
            constraints=nlp.get("constraints"),
            weight_kg=basic.get("weight_kg"),
        )

    return {
        "meal_plan": meal_plan,
        "schedule": {
            "slots": [
                {
                    "meal_key": s.meal_key,
                    "meal_name": s.meal_name,
                    "recommended_time": s.recommended_time,
                    "time_window": s.time_window,
                    "calorie_target": calorie_allocation.get(s.meal_key, 0),
                    "calorie_ratio_pct": round(s.calorie_ratio * 100, 1),
                    "timing_reason": s.timing_reason,
                    "nutrition_focus": s.nutrition_focus,
                    "is_optional": s.is_optional,
                }
                for s in meal_schedule.slots
            ],
            "is_workout_day": meal_schedule.is_workout_day,
            "notes": meal_schedule.notes,
        },
        "analysis": {
            "summary": analysis.summary if analysis else "",
            "overall_score": analysis.overall_score if analysis else 0,
            "constraint_warnings": analysis.constraint_warnings if analysis else [],
        } if analysis else None,
        "generation_info": {
            "model": result.model,
            "success": result.success,
            "latency_sec": result.latency_sec,
            "error": result.error if not result.success else None,
        },
    }


# ── 일정 변동 대응 ──

class DietAdjustRequest(BaseModel):
    meal_plan: dict
    change_text: str                # "오늘 야근이라 저녁 10시에 먹어야 해요"
    total_kcal: int = 1800
    user_profile: Optional[dict] = None
    use_llm: bool = False
    model: str = "exaone3.5:7.8b"


@app.post("/api/v1/diet/adjust")
async def adjust_diet(request: DietAdjustRequest):
    """
    일정 변동에 따라 식단을 동적으로 조정합니다.

    지원 시나리오:
    - "야근이라 저녁 늦어요" → 저녁 경량화 + 점심 보강
    - "아침 못 먹었어요" → 나머지 끼니에 칼로리 재배분
    - "점심에 회식" → 회식 칼로리 추정 + 다른 끼니 절약
    - "오늘 운동 안 해요" → 운동 간식 제거 + 칼로리 감소
    - "메뉴 바꿔줘" → 동일 칼로리 대체 메뉴 제안
    - "치킨 먹었어요" → 내일 칼로리 보정 제안
    """
    from src.diet.diet_adjuster import detect_schedule_change, adjust_diet_plan, adjust_with_llm

    # 변동 감지
    change = detect_schedule_change(request.change_text)

    if not change:
        return {
            "detected_change": None,
            "message": "일정 변동을 인식하지 못했습니다. 좀 더 구체적으로 입력해주세요.",
            "examples": [
                "야근이라 저녁 10시에 먹어야 해요",
                "아침 못 먹었어요",
                "점심에 회식이 있어요",
                "오늘 운동 안 해요",
                "점심 메뉴 바꿔줘",
                "어제 치킨 먹었어요",
            ],
        }

    # 규칙 기반 조정
    result = adjust_diet_plan(
        meal_plan=request.meal_plan,
        change=change,
        total_kcal=request.total_kcal,
    )

    # LLM 기반 재생성 (선택)
    llm_adjusted = None
    if request.use_llm and request.user_profile:
        llm_adjusted = adjust_with_llm(
            meal_plan=request.meal_plan,
            change_text=request.change_text,
            user_profile=request.user_profile,
            model=request.model,
        )

    return {
        "detected_change": {
            "type": change.change_type,
            "details": change.details,
            "original_text": change.original_text,
        },
        "adjustment": {
            "changes_made": result.changes_made,
            "calorie_rebalance": result.calorie_rebalance,
            "warnings": result.warnings,
        },
        "adjusted_plan": result.adjusted_plan,
        "llm_adjusted_plan": llm_adjusted,
    }


# ── 외식 칼로리 조회 ──

@app.get("/api/v1/diet/eating-out")
async def get_eating_out_info(query: str = "회식"):
    """외식/회식 메뉴의 추정 칼로리를 조회합니다."""
    from src.diet.eating_out_db import estimate_eating_out_calories, list_eating_out_categories

    if query == "all":
        return {"categories": list_eating_out_categories()}

    result = estimate_eating_out_calories(query)
    return {"query": query, **result}


# ── 3일치 식단 생성 + 대체 음식 + 알레르기 제외 ──

class MultiDayDietRequest(BaseModel):
    user_id: str = "default"
    days: int = 3
    model: str = "exaone3.5:7.8b"
    temperature: float = 0.7
    allergies: list[str] = []          # 알레르기 식품
    excluded_foods: list[str] = []     # 추가 제외 식품


@app.post("/api/v1/diet/generate-multiday")
async def generate_multiday_diet(request: MultiDayDietRequest):
    """3일치 맞춤 식단 생성 (알레르기/제외 식품 반영 + 대체 음식 포함)"""
    from src.diet.macro_calculator import calculate_macro_targets
    from src.diet.diet_analyzer import analyze_diet_plan

    # 사용자 프로필 로드
    user_data = _load_user(request.user_id)
    profile = user_data.get("profile", {}) if user_data else {}

    goal = profile.get("goal_type", "체중관리")
    constraints = profile.get("constraints", [])
    weight = profile.get("weight_kg", 70)
    height = profile.get("height_cm", 170)
    age = profile.get("age", 30)
    gender = profile.get("gender", "남성")
    freq = profile.get("exercise_frequency", 3)

    # 매크로 계산
    from src.profile.body_calculator import calculate_all_metrics
    metrics = calculate_all_metrics(weight, height, age, gender, freq, goal)
    macro = calculate_macro_targets(metrics.recommended_intake_kcal, goal, constraints, weight)

    # 제외 식품 문자열
    all_excluded = request.allergies + request.excluded_foods
    excluded_str = ", ".join(all_excluded) if all_excluded else "없음"
    allergy_str = ", ".join(request.allergies) if request.allergies else "없음"

    # LLM 프롬프트
    prompt = f"""당신은 스포츠 영양학 전문가입니다.

[사용자 정보]
- {age}세 {gender}, {height}cm {weight}kg
- 목표: {goal}, 제약: {', '.join(constraints) or '없음'}
- 목표 칼로리: {macro.total_kcal}kcal
- 탄단지: 탄{macro.carb_g}g / 단{macro.protein_g}g / 지{macro.fat_g}g

[제외 식품 — 절대 포함 금지]
- 알레르기: {allergy_str}
- 추가 제외: {excluded_str}

[생성 규칙]
1. {request.days}일치 식단을 만드세요 (day1, day2, day3).
2. 매일 아침/점심/저녁/간식 4끼.
3. 각 음식: name, amount, calories_kcal, carb_g, protein_g, fat_g.
4. 각 음식에 alternatives 배열로 대체 음식 2개를 제안하세요.
5. 한국인 식단 기준, 하루마다 다른 메뉴 구성.
6. 제외 식품은 대체 음식에도 절대 포함하지 마세요.
7. 각 끼니에 tip 포함.

JSON만 반환:
{{
  "days": {{
    "day1": {{
      "date_label": "1일차",
      "meals": {{
        "breakfast": {{ "menu_name": "...", "foods": [{{"name":"...","amount":"...","calories_kcal":0,"carb_g":0,"protein_g":0,"fat_g":0,"alternatives":["대체1","대체2"]}}], "tip": "..." }},
        "lunch": {{ ... }}, "dinner": {{ ... }}, "snack": {{ ... }}
      }}
    }},
    "day2": {{ ... }}, "day3": {{ ... }}
  }}
}}"""

    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        import time
        start = time.time()

        response = client.chat.completions.create(
            model=request.model, messages=[{"role": "user", "content": prompt}],
            temperature=request.temperature, max_tokens=4000,
        )
        latency = round(time.time() - start, 2)
        content = response.choices[0].message.content.strip()

        if "```json" in content: content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            for p in content.split("```"):
                if p.strip().startswith("{"): content = p; break

        meal_data = _json.loads(content.strip())

        return {
            "meal_plan": meal_data,
            "macro_targets": {"total_kcal": macro.total_kcal, "carb_g": macro.carb_g, "protein_g": macro.protein_g, "fat_g": macro.fat_g,
                              "carb_ratio": macro.carb_ratio, "protein_ratio": macro.protein_ratio, "fat_ratio": macro.fat_ratio},
            "excluded_foods": all_excluded,
            "allergies": request.allergies,
            "model": request.model,
            "latency_sec": latency,
            "days": request.days,
        }
    except Exception as e:
        raise HTTPException(500, f"식단 생성 실패: {str(e)}")


# ── 식단 챗봇 ──

class DietChatRequest(BaseModel):
    user_id: str = "default"
    message: str
    model: str = "exaone3.5:7.8b"
    current_meal_plan: Optional[dict] = None  # 현재 식단 (변경용)


DIET_CHAT_SYSTEM = """당신은 헬창지피티의 AI 영양사입니다. 사용자와 대화하면서 맞춤 식단을 생성하고 수정합니다.

규칙:
1. 사용자 프로필(나이, 키, 체중, 목표, 제약)을 참고해 답변하세요.
2. "식단 짜줘", "뭐 먹을까" → 맞춤 식단을 JSON으로 생성하세요.
3. "점심 바꿔줘", "닭가슴살 말고" → 해당 끼니만 대체 메뉴를 제안하세요.
4. "회식이야", "야근이야" → 일정에 맞게 식단을 조정하세요.
5. "알레르기가 있어", "견과류 못 먹어" → 해당 식품 제외하고 재생성하세요.
6. 식단을 생성할 때 자연어 답변 후 반드시 [MEAL_PLAN] 태그를 넣고 그 뒤에 아래 JSON 형식을 따르세요.
7. 100자 이내 간결한 자연어 답변 후, JSON 추가. 장황하게 설명하지 마세요.
8. JSON 코드블록(```json)을 자연어에 섞지 마세요. JSON은 [MEAL_PLAN] 뒤에만.

[MEAL_PLAN] 뒤에 넣을 JSON 형식 (반드시 이 구조):
```
{
  "day1": {
    "label": "1일차",
    "meals": {
      "breakfast": {"menu": "메뉴명", "calories": 400, "protein": 30, "carbs": 40, "fat": 15, "items": ["재료1", "재료2"]},
      "lunch": {"menu": "메뉴명", "calories": 500, "protein": 40, "carbs": 50, "fat": 20, "items": ["재료1"]},
      "dinner": {"menu": "메뉴명", "calories": 450, "protein": 35, "carbs": 45, "fat": 18, "items": ["재료1"]},
      "snack": {"menu": "메뉴명", "calories": 200, "protein": 15, "carbs": 20, "fat": 8, "items": ["재료1"]}
    },
    "total_calories": 1550
  }
}
```
- 1~3일치 식단을 day1, day2, day3 키로
- 각 끼니는 breakfast, lunch, dinner, snack
- calories, protein, carbs, fat은 숫자(단위: kcal, g)"""


@app.post("/api/v1/diet/chat")
async def diet_chat(req: DietChatRequest):
    """식단 관련 AI 챗봇"""
    user_data = _load_user(req.user_id)
    profile = user_data.get("profile", {}) if user_data else {}

    profile_ctx = f"\n사용자: {profile.get('age','?')}세 {profile.get('gender','?')}, {profile.get('height_cm','?')}cm {profile.get('weight_kg','?')}kg, 목표: {profile.get('goal_type','?')}, 제약: {profile.get('constraints', [])}"

    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

        messages = [{"role": "system", "content": DIET_CHAT_SYSTEM + profile_ctx}]
        if req.current_meal_plan:
            messages.append({"role": "system", "content": f"현재 식단: {_json.dumps(req.current_meal_plan, ensure_ascii=False)[:1000]}"})
        messages.append({"role": "user", "content": req.message})

        response = client.chat.completions.create(
            model=req.model, messages=messages, temperature=0.7, max_tokens=4096,
        )

        reply = response.choices[0].message.content
        meal_plan_update = None

        # --- [MEAL_PLAN] 태그 기반 파싱 ---
        if "[MEAL_PLAN]" in reply:
            parts = reply.split("[MEAL_PLAN]")
            reply = parts[0].strip()
            try:
                json_str = parts[1].strip()
                if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str: json_str = json_str.split("```")[1].split("```")[0]
                meal_plan_update = _json.loads(json_str.strip())
            except: pass

        # --- 태그 없이 JSON 코드블록이 있는 경우 ---
        if meal_plan_update is None and "```json" in reply:
            try:
                before_json = reply.split("```json")[0].strip()
                json_block = reply.split("```json")[1].split("```")[0]
                parsed = _json.loads(json_block.strip())
                if isinstance(parsed, dict) and ("day1" in parsed or "meals" in parsed or "breakfast" in str(parsed)):
                    meal_plan_update = parsed
                    reply = before_json if before_json else "식단을 만들었어요! 🍽️"
            except: pass

        # --- reply에서 JSON 코드블록 정제 ---
        import re
        reply = re.sub(r'```json\s*[\s\S]*?```', '', reply).strip()
        reply = reply.replace("[MEAL_PLAN]", "").strip()
        if not reply:
            reply = "맞춤 식단을 만들었어요! 🍽️ 식단 보기에서 확인하세요."

        # 일정 변동 감지 (회식/야근 등)
        schedule_change = None
        from src.diet.diet_adjuster import detect_schedule_change
        change = detect_schedule_change(req.message)
        if change:
            schedule_change = {"type": change.change_type, "details": change.details}

        return {"reply": reply, "meal_plan_update": meal_plan_update, "schedule_change": schedule_change, "profile": profile}

    except Exception as e:
        return {"reply": f"AI 서버에 연결할 수 없어요. ({str(e)[:30]})\n\n일단 기본적인 도움을 드릴게요:\n- \"식단 짜줘\" → 맞춤 식단 생성\n- \"회식이야\" → 식단 조정\n- \"견과류 알레르기\" → 제외 식단",
                "meal_plan_update": None, "schedule_change": None, "profile": {}}


# ═══════════════════════════════════════
# Stage 3: 운동 루틴
# ═══════════════════════════════════════

class WorkoutRequest(BaseModel):
    user_profile: dict
    frequency: Optional[int] = None
    model: str = "exaone3.5:7.8b"
    temperature: float = 0.7


class WorkoutDemoRequest(BaseModel):
    frequency: int = 3
    goal_type: str = "체지방감소"
    experience: str = "입문"
    constraints: list[str] = []


@app.post("/api/v1/workout/generate")
async def generate_workout(request: WorkoutRequest):
    """사용자 프로필 기반 주간 운동 루틴을 LLM으로 생성합니다."""
    from src.workout.workout_generator import generate_workout_plan
    from src.workout.workout_analyzer import analyze_workout_plan

    result = generate_workout_plan(
        user_profile=request.user_profile,
        frequency=request.frequency,
        model=request.model,
        temperature=request.temperature,
    )

    if not result.success:
        raise HTTPException(500, f"운동 루틴 생성 실패: {result.error}")

    nlp = request.user_profile.get("nlp_analysis", {})
    analysis = analyze_workout_plan(
        workout_plan=result.workout_plan,
        goal_type=nlp.get("goal_type", "체중관리"),
        experience=nlp.get("experience_level", "입문"),
        constraints=nlp.get("constraints"),
    )

    return {
        "workout_plan": result.workout_plan,
        "analysis": {
            "balance_score": analysis.balance_score,
            "muscle_coverage": analysis.muscle_coverage,
            "cardio_ratio": analysis.cardio_ratio,
            "strength_ratio": analysis.strength_ratio,
            "ratio_assessment": analysis.ratio_assessment,
            "volume_assessment": analysis.volume_assessment,
            "constraint_warnings": analysis.constraint_warnings,
            "overall_score": analysis.overall_score,
            "grade": analysis.grade,
            "improvements": analysis.improvements,
            "disclaimer": analysis.disclaimer,
        },
        "generation_info": {
            "model": result.model,
            "latency_sec": result.latency_sec,
        },
    }


@app.post("/api/v1/workout/demo")
async def generate_workout_demo(request: WorkoutDemoRequest):
    """LLM 없이 데모 운동 루틴을 생성합니다."""
    from src.workout.workout_generator import generate_demo_workout_plan
    from src.workout.workout_analyzer import analyze_workout_plan

    plan = generate_demo_workout_plan(
        frequency=request.frequency,
        goal_type=request.goal_type,
        experience=request.experience,
        constraints=request.constraints,
    )

    analysis = analyze_workout_plan(
        workout_plan=plan,
        goal_type=request.goal_type,
        experience=request.experience,
        constraints=request.constraints,
    )

    return {
        "workout_plan": plan,
        "analysis": {
            "balance_score": analysis.balance_score,
            "overall_score": analysis.overall_score,
            "grade": analysis.grade,
            "improvements": analysis.improvements,
            "disclaimer": analysis.disclaimer,
        },
    }


@app.get("/api/v1/workout/search")
async def search_exercise(
    query: str,
    method: str = "bm25",
    top_k: int = 5,
    constraints: str = "",
):
    """운동을 검색합니다. method: bm25 | embedding | filter"""
    from src.workout.exercise_search import search_exercises

    constraint_list = [c.strip() for c in constraints.split(",") if c.strip()]
    results = search_exercises(query, method, top_k, constraint_list or None)

    return {
        "query": query,
        "method": method,
        "results": [
            {
                "name": r.name,
                "score": r.score,
                "method": r.method,
                "target_muscle": r.exercise_data.get("target_muscle"),
                "difficulty": r.exercise_data.get("difficulty"),
                "equipment": r.exercise_data.get("equipment"),
                "description": r.exercise_data.get("description", "")[:100],
            }
            for r in results
        ],
    }


# ── 운동 챗봇 + 7일 계획 ──

class WorkoutChatRequest(BaseModel):
    user_id: str = "default"
    message: str
    model: str = "exaone3.5:7.8b"
    current_plan: Optional[dict] = None


WORKOUT_CHAT_SYSTEM = """당신은 헬창지피티의 AI 트레이너입니다. 사용자와 대화하면서 운동 루틴을 설계하고 조정합니다.

규칙:
1. 사용자 프로필(나이, 키, 체중, 목표, 제약, 주당 운동 횟수)을 참고하세요.
2. "운동 계획 짜줘" → 월~일 7일 스케줄을 만드세요.
   - **반드시 사용자의 주당 운동 횟수를 정확히 지키세요.**
   - 사용자가 주 7회이면 7일 모두 운동일로 설정하세요 (휴식일 없음).
   - 사용자가 주 6회이면 6일 운동 + 1일 휴식으로 설정하세요.
   - 사용자가 주 5회이면 5일 운동 + 2일 휴식으로 설정하세요.
   - 사용자의 운동 횟수를 임의로 줄이지 마세요.
3. "오늘 뭐 하지?" → 오늘의 운동 상세 루틴을 추천하세요.
4. "무릎이 아파", "오늘은 하체 싫어" → 해당 부위 제외하고 대체 루틴 제안.
5. "30분밖에 없어" → 시간에 맞는 단축 루틴 제안.
6. 운동 계획을 만들 때 자연어 답변 후 반드시 [WORKOUT_PLAN] 태그를 넣고 그 뒤에 아래 JSON 형식을 따르세요.
7. 모든 루틴에 "이 루틴은 참고용이며, 본인 체력에 맞게 조정하세요"를 포함하세요.
8. 200자 이내 자연어 답변 후, 필요시 JSON 추가.
9. JSON 코드블록(```json)을 자연어 답변에 섞지 마세요. JSON은 반드시 [WORKOUT_PLAN] 태그 뒤에만 넣으세요.

[WORKOUT_PLAN] 뒤에 넣을 JSON 형식 (반드시 이 구조를 따르세요):
```
{
  "weekly_plan": {
    "day1": {"day_label": "월요일", "focus": "가슴 + 삼두", "estimated_time_min": 50, "estimated_calories": 300, "main_workout": {"exercises": [{"name": "벤치프레스", "target_muscle": "가슴", "sets": 4, "reps": "8~12", "rest_sec": 90, "intensity": "중", "description": "설명", "alternatives": ["대체운동"], "caution": ""}]}, "tip": "팁"},
    "day2": {"day_label": "화요일", "focus": "등 + 이두", ...},
    "day3": {"day_label": "수요일", "focus": "하체", ...}
  },
  "rest_days": ["목요일", "일요일"]
}
```
- day_label은 반드시 "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일" 중 하나
- 운동일은 day1, day2, day3... 순서로
- rest_days는 쉬는 날의 요일 배열"""


def _parse_workout_from_text(text: str, frequency: int = 3) -> dict | None:
    """LLM이 [WORKOUT_PLAN] JSON 없이 마크다운 텍스트만 반환했을 때,
    텍스트에서 요일별 운동 정보를 추출하여 프론트엔드 구조로 변환합니다."""
    import re

    day_map = {
        "월": "월요일", "화": "화요일", "수": "수요일", "목": "목요일",
        "금": "금요일", "토": "토요일", "일": "일요일",
    }
    # 요일 패턴으로 텍스트 분할
    day_pattern = r'\*{0,2}(월|화|수|목|금|토|일)(?:요일)?\s*[\(\（]([^)\）]+)[\)\）]\*{0,2}'
    matches = list(re.finditer(day_pattern, text))

    if len(matches) < 2:
        return None  # 요일 패턴 부족 → 변환 불가

    weekly_plan = {}
    rest_days = []
    day_counter = 1

    for idx, match in enumerate(matches):
        day_short = match.group(1)
        focus = match.group(2).strip()
        day_label = day_map.get(day_short, day_short + "요일")

        # 이 요일의 텍스트 범위: 현재 매치 ~ 다음 매치
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        section = text[start:end]

        # 운동 항목 추출: "- **운동명**: 세트 x 횟수" 패턴
        exercise_pattern = r'[-•]\s*\*{0,2}([^*:]+?)\*{0,2}\s*[:：]\s*(\d+)\s*세트\s*[*xX×]\s*(\S+)'
        exercises = []
        for ex_match in re.finditer(exercise_pattern, section):
            exercises.append({
                "name": ex_match.group(1).strip(),
                "target_muscle": focus.split("+")[0].strip() if "+" in focus else focus,
                "sets": int(ex_match.group(2)),
                "reps": ex_match.group(3).strip(),
                "rest_sec": 60,
                "intensity": "중",
                "description": "",
                "alternatives": [],
                "caution": "",
            })

        # 간단한 패턴도 시도: "- **운동명**: 세트 * 횟수"
        if not exercises:
            simple_pattern = r'[-•]\s*\*{0,2}([^*:\n]+?)\*{0,2}\s*[:：]\s*(.+?)(?:\n|$)'
            for ex_match in re.finditer(simple_pattern, section):
                name = ex_match.group(1).strip()
                detail = ex_match.group(2).strip()
                if len(name) > 1 and name not in ("웜업", "쿨다운", "워밍업", "마무리"):
                    sets_match = re.search(r'(\d+)\s*세트', detail)
                    reps_match = re.search(r'(\d+(?:~\d+)?)\s*(?:회|회씩|초)', detail)
                    exercises.append({
                        "name": name,
                        "target_muscle": focus.split("+")[0].strip() if "+" in focus else focus,
                        "sets": int(sets_match.group(1)) if sets_match else 3,
                        "reps": reps_match.group(0) if reps_match else "10~12",
                        "rest_sec": 60,
                        "intensity": "중",
                        "description": detail,
                        "alternatives": [],
                        "caution": "",
                    })

        if exercises:
            weekly_plan[f"day{day_counter}"] = {
                "day_label": day_label,
                "focus": focus,
                "estimated_time_min": max(len(exercises) * 10 + 10, 40),
                "estimated_calories": len(exercises) * 60 + 50,
                "main_workout": {"exercises": exercises},
                "tip": "운동 전 충분한 수분 섭취를 잊지 마세요!",
            }
            day_counter += 1
        else:
            rest_days.append(day_label)

    if not weekly_plan:
        return None

    # 운동일이 아닌 요일은 rest_days에 추가
    workout_day_labels = {v["day_label"] for v in weekly_plan.values()}
    for dl in ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]:
        if dl not in workout_day_labels and dl not in rest_days:
            rest_days.append(dl)

    return {
        "weekly_plan": weekly_plan,
        "rest_days": rest_days,
    }


DAY_LABEL_MAP = {
    "월": "월요일", "화": "화요일", "수": "수요일", "목": "목요일",
    "금": "금요일", "토": "토요일", "일": "일요일",
    "월요일": "월요일", "화요일": "화요일", "수요일": "수요일", "목요일": "목요일",
    "금요일": "금요일", "토요일": "토요일", "일요일": "일요일",
    "monday": "월요일", "tuesday": "화요일", "wednesday": "수요일",
    "thursday": "목요일", "friday": "금요일", "saturday": "토요일", "sunday": "일요일",
}
ALL_DAY_LABELS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _normalize_workout_plan(raw: dict) -> dict:
    """LLM이 반환한 다양한 JSON 구조를 프론트엔드 기대 형식으로 정규화합니다."""
    if not isinstance(raw, dict):
        return raw

    # 이미 올바른 구조: weekly_plan.day1.day_label 존재
    wp = raw.get("weekly_plan", {})
    if wp and isinstance(wp, dict):
        first_val = next(iter(wp.values()), None)
        if isinstance(first_val, dict) and "day_label" in first_val:
            # day_label 정규화 (월→월요일)
            for k, v in wp.items():
                label = v.get("day_label", "")
                v["day_label"] = DAY_LABEL_MAP.get(label, label)
                # exercises가 main_workout 안에 있는지 확인
                if "exercises" in v and "main_workout" not in v:
                    v["main_workout"] = {"exercises": v.pop("exercises")}
            return raw

    # 구조 A: 요일이 키인 경우 {"월요일": {...}, "화요일": {...}}
    day_entries = {}
    for key, val in raw.items():
        if key in DAY_LABEL_MAP and isinstance(val, dict):
            day_entries[DAY_LABEL_MAP[key]] = val

    # 구조 B: weekly_plan 안에 요일 키 {"weekly_plan": {"월요일": {...}}}
    if not day_entries and wp:
        for key, val in wp.items():
            if key in DAY_LABEL_MAP and isinstance(val, dict):
                day_entries[DAY_LABEL_MAP[key]] = val

    # 구조 C: 배열 형태 {"schedule": [{...}, ...]} 또는 직접 배열
    if not day_entries:
        schedule = raw.get("schedule", raw.get("days", raw.get("plan", [])))
        if isinstance(schedule, list):
            for item in schedule:
                if isinstance(item, dict):
                    day_name = item.get("day", item.get("day_label", item.get("요일", "")))
                    if day_name and day_name in DAY_LABEL_MAP:
                        day_entries[DAY_LABEL_MAP[day_name]] = item

    if not day_entries:
        return raw  # 변환 불가 — 원본 반환

    # 정규화된 weekly_plan 빌드
    normalized_wp = {}
    rest_days = []
    day_counter = 1

    for day_label in ALL_DAY_LABELS:
        if day_label in day_entries:
            entry = day_entries[day_label]
            # exercises 정규화
            exercises = entry.get("exercises", [])
            if not exercises:
                mw = entry.get("main_workout", {})
                exercises = mw.get("exercises", []) if isinstance(mw, dict) else []
            # 각 운동 항목 보정
            normalized_exercises = []
            for ex in exercises:
                if isinstance(ex, str):
                    normalized_exercises.append({"name": ex, "target_muscle": "", "sets": 3, "reps": "10~12", "rest_sec": 60, "intensity": "중", "description": "", "alternatives": [], "caution": ""})
                elif isinstance(ex, dict):
                    normalized_exercises.append({
                        "name": ex.get("name", ex.get("운동", ex.get("exercise", "운동"))),
                        "target_muscle": ex.get("target_muscle", ex.get("부위", ex.get("muscle", ""))),
                        "sets": ex.get("sets", ex.get("세트", 3)),
                        "reps": str(ex.get("reps", ex.get("횟수", ex.get("반복", "10~12")))),
                        "rest_sec": ex.get("rest_sec", ex.get("휴식", 60)),
                        "intensity": ex.get("intensity", ex.get("강도", "중")),
                        "description": ex.get("description", ex.get("설명", "")),
                        "alternatives": ex.get("alternatives", ex.get("대체", [])),
                        "caution": ex.get("caution", ex.get("주의", "")),
                    })

            day_key = f"day{day_counter}"
            normalized_wp[day_key] = {
                "day_label": day_label,
                "focus": entry.get("focus", entry.get("부위", entry.get("target", "전신"))),
                "estimated_time_min": entry.get("estimated_time_min", entry.get("time", entry.get("시간", 50))),
                "estimated_calories": entry.get("estimated_calories", entry.get("calories", entry.get("칼로리", 300))),
                "main_workout": {"exercises": normalized_exercises},
                "tip": entry.get("tip", entry.get("팁", "운동 전 충분한 수분 섭취를 잊지 마세요!")),
            }
            day_counter += 1
        else:
            rest_days.append(day_label)

    return {
        "weekly_plan": normalized_wp,
        "rest_days": raw.get("rest_days", rest_days),
    }


@app.post("/api/v1/workout/chat")
async def workout_chat(req: WorkoutChatRequest):
    """운동 관련 AI 챗봇"""
    user_data = _load_user(req.user_id)
    profile = user_data.get("profile", {}) if user_data else {}

    freq = profile.get("exercise_frequency", 3)
    constraints = profile.get("constraints", [])
    profile_ctx = f"\n사용자: {profile.get('age','?')}세 {profile.get('gender','?')}, {profile.get('height_cm','?')}cm {profile.get('weight_kg','?')}kg"
    profile_ctx += f"\n목표: {profile.get('goal_type','?')}, 경험: {profile.get('experience_level','?')}"
    profile_ctx += f"\n★★★ 주당 운동 횟수: 정확히 {freq}회 (이 횟수를 반드시 지켜서 계획을 세우세요) ★★★"
    if constraints:
        profile_ctx += f"\n제약사항: {', '.join(constraints)} (해당 부위 운동 시 대체 운동 필수)"

    try:
        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

        messages = [{"role": "system", "content": WORKOUT_CHAT_SYSTEM + profile_ctx}]
        if req.current_plan:
            messages.append({"role": "system", "content": f"현재 운동 계획: {_json.dumps(req.current_plan, ensure_ascii=False)[:1500]}"})
        messages.append({"role": "user", "content": req.message})

        response = client.chat.completions.create(
            model=req.model, messages=messages, temperature=0.7, max_tokens=4096,
        )

        reply = response.choices[0].message.content
        workout_plan_update = None

        # --- [WORKOUT_PLAN] 태그 기반 파싱 ---
        if "[WORKOUT_PLAN]" in reply:
            parts = reply.split("[WORKOUT_PLAN]")
            reply = parts[0].strip()
            try:
                json_str = parts[1].strip()
                if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str: json_str = json_str.split("```")[1].split("```")[0]
                workout_plan_update = _json.loads(json_str.strip())
            except: pass

        # --- 태그 없이 JSON이 포함된 경우 추가 파싱 ---
        if workout_plan_update is None and "```json" in reply:
            try:
                before_json = reply.split("```json")[0].strip()
                json_block = reply.split("```json")[1].split("```")[0]
                parsed = _json.loads(json_block.strip())
                if isinstance(parsed, dict) and ("weekly_plan" in parsed or "day1" in parsed or "day_label" in parsed):
                    workout_plan_update = parsed
                    reply = before_json if before_json else "운동 계획을 만들었어요! 💪"
            except: pass

        # --- JSON 없이 마크다운 텍스트만 있을 때: 텍스트에서 운동 플랜 자동 구성 ---
        if workout_plan_update is None and ("월" in reply or "화" in reply) and ("세트" in reply or "회" in reply):
            workout_plan_update = _parse_workout_from_text(reply, freq)

        # --- reply에서 남은 마크다운/JSON 코드블록 정제 ---
        import re
        # ```json ... ``` 블록 제거
        reply = re.sub(r'```json\s*[\s\S]*?```', '', reply).strip()
        # ``` ... ``` 블록 중 JSON 형태인 것 제거
        def _remove_json_codeblocks(text):
            parts = text.split('```')
            result = []
            for i, part in enumerate(parts):
                if i % 2 == 1:  # 코드블록 내부
                    stripped = part.strip()
                    if stripped.startswith('{') or stripped.startswith('['):
                        continue  # JSON 블록 제거
                    else:
                        result.append(part)  # 비-JSON 코드블록 유지
                else:
                    result.append(part)
            return ''.join(result)
        reply = _remove_json_codeblocks(reply)
        # [WORKOUT_PLAN] 잔여 태그 제거
        reply = reply.replace("[WORKOUT_PLAN]", "").strip()
        # 빈 응답 방지
        if not reply:
            reply = "운동 계획을 만들었어요! 💪 옆의 루틴 패널에서 확인하세요."

        # --- LLM JSON을 프론트엔드 기대 구조로 정규화 ---
        if workout_plan_update:
            workout_plan_update = _normalize_workout_plan(workout_plan_update)

        return {"reply": reply, "workout_plan_update": workout_plan_update, "profile": profile, "frequency": freq}

    except Exception as e:
        return {
            "reply": f"AI 서버에 연결할 수 없어요. ({str(e)[:30]})\n\n이런 것들을 물어볼 수 있어요:\n• \"일주일 운동 계획 짜줘\"\n• \"오늘 상체 운동 추천\"\n• \"30분 운동 루틴\"\n• \"무릎 아파서 하체 운동 대체\"",
            "workout_plan_update": None, "profile": profile, "frequency": profile.get("exercise_frequency", 3),
        }


# ═══════════════════════════════════════
# Stage 4: 감성 분석 & 피드백
# ═══════════════════════════════════════

class FeedbackRequest(BaseModel):
    diary_entries: list[dict]                  # [{"date": "...", "text": "...", "exercises_done": [...], "duration_min": N}]
    planned_frequency: int = 3
    mode: str = "coach"                        # coach | friend | drill | cheerleader | scientist
    use_llm: bool = False
    model: str = "exaone3.5:7.8b"
    user_profile: Optional[dict] = None


@app.post("/api/v1/feedback/analyze")
async def analyze_and_feedback(request: FeedbackRequest):
    """
    운동 일지를 감성 분석하고, 선택한 모드에 맞는 피드백을 생성합니다.

    피드백 모드:
    - coach: 전문 트레이너 (체계적, 데이터 기반)
    - friend: 운동 친구 (편한 반말, 공감)
    - drill: 드릴교관 (엄격하지만 애정)
    - cheerleader: 응원단 (무조건 긍정, 에너지)
    - scientist: 과학자 (데이터, 논문 근거)
    """
    from src.feedback.sentiment_analyzer import analyze_weekly_sentiment
    from src.feedback.weekly_summarizer import build_weekly_summary
    from src.feedback.feedback_generator import generate_feedback_rule_based, generate_feedback_with_llm

    # 1. 감성 분석
    sentiment_data = analyze_weekly_sentiment(
        request.diary_entries,
        use_llm=request.use_llm,
    )

    # 2. 주간 요약
    weekly_summary = build_weekly_summary(
        request.diary_entries,
        request.planned_frequency,
    )

    # 3. 피드백 생성
    if request.use_llm:
        feedback = generate_feedback_with_llm(
            sentiment_data=sentiment_data,
            weekly_summary=weekly_summary,
            user_profile=request.user_profile,
            mode_id=request.mode,
            model=request.model,
        )
    else:
        feedback = generate_feedback_rule_based(
            sentiment_data=sentiment_data,
            weekly_summary=weekly_summary,
            mode_id=request.mode,
        )

    return {
        "sentiment_analysis": sentiment_data,
        "weekly_summary": weekly_summary,
        "feedback": {
            "main_message": feedback.main_message,
            "praise_points": feedback.praise_points,
            "improvement_suggestions": feedback.improvement_suggestions,
            "next_week_tips": feedback.next_week_tips,
            "encouragement_quote": feedback.encouragement_quote,
            "mode": feedback.mode,
            "mode_name": feedback.mode_name,
            "mode_emoji": feedback.mode_emoji,
            "model_used": feedback.model_used,
        },
    }


@app.get("/api/v1/feedback/modes")
async def list_feedback_modes():
    """사용 가능한 피드백 모드 목록을 반환합니다."""
    from src.feedback.feedback_modes import list_modes
    return {"modes": list_modes()}


# ═══════════════════════════════════════
# 운동 일기 저장 + 성장 기록 + 목표 달성률
# ═══════════════════════════════════════

class DiaryEntry(BaseModel):
    user_id: str = "default"
    text: str
    exercises_done: list[str] = []
    duration_min: int = 0
    mood: Optional[str] = None  # 선택: 사용자 자가 기분 평가


@app.post("/api/v1/diary/save")
async def save_diary_entry(entry: DiaryEntry):
    """운동 일기를 저장합니다."""
    user_dir = PROFILES_DIR / entry.user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    diary_file = user_dir / "diary_history.json"

    diaries = []
    if diary_file.exists():
        diaries = _json.load(open(diary_file, encoding="utf-8"))

    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "text": entry.text,
        "exercises_done": entry.exercises_done,
        "duration_min": entry.duration_min,
        "mood": entry.mood,
    }
    diaries.append(new_entry)

    with open(diary_file, "w", encoding="utf-8") as f:
        _json.dump(diaries, f, ensure_ascii=False, indent=2)

    _log_activity(entry.user_id, "운동 일기 작성", f"{entry.duration_min}분, {len(entry.exercises_done)}종목")

    return {"message": "일기가 저장되었습니다", "total_entries": len(diaries), "entry": new_entry}


@app.get("/api/v1/diary/{user_id}/history")
async def get_diary_history(user_id: str):
    """저장된 운동 일기 전체 조회."""
    diary_file = PROFILES_DIR / user_id / "diary_history.json"
    if not diary_file.exists():
        return {"entries": [], "total": 0}
    diaries = _json.load(open(diary_file, encoding="utf-8"))
    return {"entries": diaries, "total": len(diaries)}


@app.get("/api/v1/diary/{user_id}/growth")
async def get_growth_stats(user_id: str):
    """성장 기록 + 목표 달성률 분석."""
    user_data = _load_user(user_id)
    profile = user_data.get("profile", {}) if user_data else {}
    goal_type = profile.get("goal_type", "체중관리")
    target_freq = profile.get("exercise_frequency", 3)

    # 일기 이력 로드
    diary_file = PROFILES_DIR / user_id / "diary_history.json"
    diaries = []
    if diary_file.exists():
        diaries = _json.load(open(diary_file, encoding="utf-8"))

    # 인바디 이력
    history_file = PROFILES_DIR / user_id / "history.json"
    inbody = []
    if history_file.exists():
        h = _json.load(open(history_file, encoding="utf-8"))
        inbody = h.get("measurements", [])

    # 주별 통계
    from collections import defaultdict
    weekly = defaultdict(lambda: {"count": 0, "total_min": 0, "exercises": set()})
    for d in diaries:
        # ISO week
        from datetime import datetime as dt
        try:
            date = dt.fromisoformat(d["timestamp"]) if "timestamp" in d else dt.strptime(d["date"], "%Y-%m-%d")
            week_key = f"{date.isocalendar()[0]}-W{date.isocalendar()[1]:02d}"
        except:
            week_key = "unknown"
        weekly[week_key]["count"] += 1
        weekly[week_key]["total_min"] += d.get("duration_min", 0)
        for ex in d.get("exercises_done", []):
            weekly[week_key]["exercises"].add(ex)

    # 주별 달성률
    weekly_stats = []
    for week, data in sorted(weekly.items()):
        rate = min(round(data["count"] / max(target_freq, 1) * 100), 100)
        weekly_stats.append({
            "week": week,
            "sessions": data["count"],
            "target": target_freq,
            "completion_rate": rate,
            "total_min": data["total_min"],
            "exercises": sorted(data["exercises"]),
        })

    # 전체 통계
    total_sessions = len(diaries)
    total_weeks = max(len(weekly_stats), 1)
    total_minutes = sum(d.get("duration_min", 0) for d in diaries)
    avg_weekly_rate = round(sum(w["completion_rate"] for w in weekly_stats) / total_weeks) if weekly_stats else 0

    # 목표 진행 상황 메시지
    if avg_weekly_rate >= 90:
        goal_message = f"🏆 대단해요! 평균 달성률 {avg_weekly_rate}%로 목표를 꾸준히 달성하고 있어요!"
    elif avg_weekly_rate >= 60:
        goal_message = f"💪 잘하고 있어요! 평균 달성률 {avg_weekly_rate}%, 조금만 더 하면 완벽해요!"
    elif avg_weekly_rate >= 30:
        goal_message = f"🌱 시작이 반이에요! 평균 달성률 {avg_weekly_rate}%, 조금씩 늘려가 봐요!"
    else:
        goal_message = f"🔥 지금 시작하면 돼요! 목표 주 {target_freq}회, 하나씩 채워가 봐요!"

    return {
        "goal_type": goal_type,
        "target_frequency": target_freq,
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "total_weeks_tracked": total_weeks,
        "avg_weekly_completion_rate": avg_weekly_rate,
        "weekly_stats": weekly_stats,
        "inbody_count": len(inbody),
        "goal_message": goal_message,
        "streak": _calculate_streak(diaries),
    }


def _calculate_streak(diaries: list) -> dict:
    """연속 운동일 계산."""
    if not diaries:
        return {"current": 0, "best": 0}

    from datetime import datetime as dt, timedelta
    dates = set()
    for d in diaries:
        try:
            date = dt.fromisoformat(d["timestamp"]).date() if "timestamp" in d else dt.strptime(d["date"], "%Y-%m-%d").date()
            dates.add(date)
        except: pass

    if not dates:
        return {"current": 0, "best": 0}

    sorted_dates = sorted(dates)
    best_streak = 1
    current_streak = 1

    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i-1]).days <= 2:  # 이틀 이내면 연속
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 1

    # 현재 진행 중인 스트릭 (마지막 운동이 2일 이내)
    today = dt.now().date()
    if (today - sorted_dates[-1]).days <= 2:
        active_streak = current_streak
    else:
        active_streak = 0

    return {"current": active_streak, "best": best_streak}


# ═══════════════════════════════════════
# 식단 저장/조회/삭제
# ═══════════════════════════════════════

class DietSaveRequest(BaseModel):
    user_id: str = "default"
    meal_plan: dict
    macro_targets: Optional[dict] = None
    allergies: list[str] = []
    excluded_foods: list[str] = []
    title: Optional[str] = None

@app.post("/api/v1/diet/save")
async def save_diet_plan(req: DietSaveRequest):
    """생성된 식단 계획을 저장합니다."""
    user_dir = PROFILES_DIR / req.user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    diet_file = user_dir / "diet_history.json"

    history = []
    if diet_file.exists():
        history = _json.load(open(diet_file, encoding="utf-8"))

    days_count = len(req.meal_plan.get("days", {})) if req.meal_plan else 0
    new_entry = {
        "id": f"diet_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "saved_at": datetime.now().isoformat(),
        "title": req.title or f"{days_count}일치 맞춤 식단",
        "meal_plan": req.meal_plan,
        "macro_targets": req.macro_targets,
        "allergies": req.allergies,
        "excluded_foods": req.excluded_foods,
        "days_count": days_count,
    }
    history.append(new_entry)

    with open(diet_file, "w", encoding="utf-8") as f:
        _json.dump(history, f, ensure_ascii=False, indent=2)

    _log_activity(req.user_id, "식단 저장", f"{days_count}일치 식단")
    return {"message": "식단이 저장되었습니다", "total": len(history), "entry": new_entry}


@app.get("/api/v1/diet/{user_id}/history")
async def get_diet_history(user_id: str):
    """저장된 식단 이력을 조회합니다."""
    diet_file = PROFILES_DIR / user_id / "diet_history.json"
    if not diet_file.exists():
        return {"entries": [], "total": 0}
    history = _json.load(open(diet_file, encoding="utf-8"))
    return {"entries": history, "total": len(history)}


@app.delete("/api/v1/diet/{user_id}/{diet_id}")
async def delete_diet_plan(user_id: str, diet_id: str):
    """저장된 식단을 삭제합니다."""
    diet_file = PROFILES_DIR / user_id / "diet_history.json"
    if not diet_file.exists():
        raise HTTPException(404, "식단 이력이 없습니다")
    history = _json.load(open(diet_file, encoding="utf-8"))
    history = [e for e in history if e.get("id") != diet_id]
    with open(diet_file, "w", encoding="utf-8") as f:
        _json.dump(history, f, ensure_ascii=False, indent=2)
    return {"message": "삭제되었습니다", "total": len(history)}


# ═══════════════════════════════════════
# 운동 루틴 저장/조회/삭제
# ═══════════════════════════════════════

class WorkoutSaveRequest(BaseModel):
    user_id: str = "default"
    workout_plan: dict
    title: Optional[str] = None

@app.post("/api/v1/workout/save")
async def save_workout_plan(req: WorkoutSaveRequest):
    """생성된 운동 계획을 저장합니다."""
    user_dir = PROFILES_DIR / req.user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    workout_file = user_dir / "workout_history.json"

    history = []
    if workout_file.exists():
        history = _json.load(open(workout_file, encoding="utf-8"))

    days_count = len(req.workout_plan.get("days", {})) if req.workout_plan else 0
    new_entry = {
        "id": f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "saved_at": datetime.now().isoformat(),
        "title": req.title or f"{days_count}일 운동 루틴",
        "workout_plan": req.workout_plan,
        "days_count": days_count,
    }
    history.append(new_entry)

    with open(workout_file, "w", encoding="utf-8") as f:
        _json.dump(history, f, ensure_ascii=False, indent=2)

    _log_activity(req.user_id, "운동 루틴 저장", f"{days_count}일 루틴")
    return {"message": "운동 계획이 저장되었습니다", "total": len(history), "entry": new_entry}


@app.get("/api/v1/workout/{user_id}/history")
async def get_workout_history(user_id: str):
    """저장된 운동 루틴 이력을 조회합니다."""
    workout_file = PROFILES_DIR / user_id / "workout_history.json"
    if not workout_file.exists():
        return {"entries": [], "total": 0}
    history = _json.load(open(workout_file, encoding="utf-8"))
    return {"entries": history, "total": len(history)}


@app.delete("/api/v1/workout/{user_id}/{workout_id}")
async def delete_workout_plan(user_id: str, workout_id: str):
    """저장된 운동 루틴을 삭제합니다."""
    workout_file = PROFILES_DIR / user_id / "workout_history.json"
    if not workout_file.exists():
        raise HTTPException(404, "운동 이력이 없습니다")
    history = _json.load(open(workout_file, encoding="utf-8"))
    history = [e for e in history if e.get("id") != workout_id]
    with open(workout_file, "w", encoding="utf-8") as f:
        _json.dump(history, f, ensure_ascii=False, indent=2)
    return {"message": "삭제되었습니다", "total": len(history)}


# ═══════════════════════════════════════
# Health Check
# ═══════════════════════════════════════

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
