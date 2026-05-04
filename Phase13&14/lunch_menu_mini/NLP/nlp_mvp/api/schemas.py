"""
FastAPI Pydantic v2 스키마.

모든 라우터의 요청/응답 바디를 여기 한 곳에 정의한다.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Meta
# =============================================================================
class HealthOut(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    version: str = "0.5.0"
    modules: dict[str, str] = Field(default_factory=dict)


class ErrorOut(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None


# =============================================================================
# Settings / Models (M9)
# =============================================================================
class OllamaModelOut(BaseModel):
    """Single LLM model entry. 'OllamaModelOut' 이름은 backward-compat 유지."""
    name: str
    size: str = ""
    modified: str = ""
    provider: Literal["ollama", "gemini"] = "ollama"


class ModelListOut(BaseModel):
    models: list[OllamaModelOut] = Field(default_factory=list)
    host: str = ""
    active_chat: str = ""
    active_report: str = ""
    # Phase 14: 활성 provider 표시 (UI 뱃지용)
    active_chat_provider: Literal["ollama", "gemini"] = "ollama"
    active_report_provider: Literal["ollama", "gemini"] = "ollama"
    active_tools_provider: Literal["ollama", "gemini"] = "ollama"
    active_tools: str = ""


class SettingsOut(BaseModel):
    chat_model: str
    report_model: str
    tools_model: str = ""
    host: str
    language: Literal["en", "ko", "both"] = "both"
    chat_provider: Literal["ollama", "gemini"] = "ollama"
    report_provider: Literal["ollama", "gemini"] = "ollama"
    tools_provider: Literal["ollama", "gemini"] = "ollama"


class SettingsUpdateIn(BaseModel):
    model: str = Field(min_length=1, max_length=200)
    # Phase 14: "tools" role 추가, "all" = chat+report+tools
    role: Literal["chat", "report", "tools", "both", "all"] = "chat"
    # 명시적 provider 변경 (없으면 model 접두사로 추론)
    provider: Optional[Literal["ollama", "gemini"]] = None


class SettingsUpdateOut(BaseModel):
    status: Literal["ok", "error"]
    role: str
    model: str
    chat_model: str
    report_model: str
    tools_model: str = ""
    chat_provider: Literal["ollama", "gemini"] = "ollama"
    report_provider: Literal["ollama", "gemini"] = "ollama"
    tools_provider: Literal["ollama", "gemini"] = "ollama"
    detail: Optional[str] = None


# =============================================================================
# Sentiment
# =============================================================================
class SentimentOut(BaseModel):
    restaurant_id: str
    score: Optional[float] = Field(None, description="[-1, +1]. None if insufficient.")
    pos_ratio: float = 0.0
    neu_ratio: float = 0.0
    neg_ratio: float = 0.0
    review_count: int = 0
    updated_at: Optional[str] = None


class SentimentTopItem(BaseModel):
    restaurant_id: str
    name: Optional[str] = None
    score: float
    pos_ratio: float
    review_count: int


class SentimentRefreshIn(BaseModel):
    limit: int = Field(default=20, ge=1, le=500)
    source: Literal["synthetic", "aihub", "kakao_public"] = "synthetic"
    min_reviews: int = Field(default=5, ge=1, le=100)
    skip_model_load: bool = False


class SentimentRefreshOut(BaseModel):
    queued: bool
    limit: int
    source: str
    message: str


# =============================================================================
# Menu normalize
# =============================================================================
class MenuNormalizeIn(BaseModel):
    raw_name: str = Field(min_length=1, max_length=200)


class MenuNormalizeOut(BaseModel):
    raw: str
    cleaned: str
    matched_id: Optional[str] = None
    matched_name: Optional[str] = None
    confidence: float = 0.0
    method: Literal["rule", "levenshtein", "embedding", "none", "error"]
    latency_ms: int = 0


class MenuStatsOut(BaseModel):
    total: int
    by_method: dict[str, int]
    hit_rate: float  # (rule + lev + emb) / total


# =============================================================================
# Nutrition natural-language parse
# =============================================================================
class NutritionParseIn(BaseModel):
    user_id: str = Field(default="user1", min_length=1, max_length=50)
    text: str = Field(min_length=1, max_length=1000)
    base_date: Optional[str] = None
    locale: str = Field(default="ko-KR", max_length=20)


class NutritionParsedItem(BaseModel):
    raw_name: str
    normalized_name: Optional[str] = None
    quantity: float = 1.0
    unit: str = "serving"
    confidence: float = 0.0
    needs_review: bool = True


class NutritionParseParserInfo(BaseModel):
    method: str
    confidence: float = 0.0


class NutritionParseOut(BaseModel):
    user_id: str
    raw_text: str
    meal_date: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack", "unknown"] = "unknown"
    restaurant_hint: Optional[str] = None
    satisfaction: Optional[int] = None
    items: list[NutritionParsedItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    parser: NutritionParseParserInfo


# =============================================================================
# Chatbot
# =============================================================================
class ChatIn(BaseModel):
    user_id: int = Field(ge=1)
    query: str = Field(min_length=1, max_length=1000)
    top_k_meal: int = Field(default=5, ge=1, le=20)
    top_k_nutrition: int = Field(default=5, ge=1, le=20)
    top_k_restaurant: int = Field(default=5, ge=1, le=20)
    # 다중 식사 시간 — None 이면 query 자연어에서 추출 시도
    meal_type: Optional[str] = Field(
        default=None,
        pattern="^(breakfast|lunch|dinner|any)$",
        description="식사 시간 — breakfast/lunch/dinner/any. 지정 시 query 앞에 [아침]/[점심]/[저녁] prefix가 자동 부착됨.",
    )


class ChatRecommendation(BaseModel):
    name: str
    reason: Optional[str] = None
    category: Optional[str] = None


class ChatOut(BaseModel):
    response: str
    recommendations: list[ChatRecommendation] = Field(default_factory=list)
    latency_ms: int = 0
    validation: dict[str, Any] = Field(default_factory=dict)
    context_summary: dict[str, int] = Field(default_factory=dict)


class ChatResetIn(BaseModel):
    user_id: int = Field(ge=1)


class ChatResetOut(BaseModel):
    user_id: int
    reset: bool


# =============================================================================
# Weekly NLG report
# =============================================================================
class WeeklyReportOut(BaseModel):
    user_id: str
    week_start: str
    week_label: str
    text: str
    facts: dict[str, Any] = Field(default_factory=dict)
    generation_method: Literal["llm", "template", "minimal"] = "minimal"
    generated_at: str
    validation: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Research v2 (Phase 6) — placeholders + actual response shapes
# =============================================================================
class V2AspectSentiment(BaseModel):
    aspect: str
    sentiment: Literal["positive", "neutral", "negative"]
    confidence: float = 0.0
    score: float = 0.0  # signed sentiment score in [-1, 1]


class V2ABSAOut(BaseModel):
    restaurant_id: str
    aspects: list[V2AspectSentiment] = Field(default_factory=list)
    backend: Literal["trained", "dummy", "seeded"] = "dummy"


class V2NEREntity(BaseModel):
    type: str
    value: str
    start_token: int
    end_token: int


class V2MenuExtractIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class V2MenuExtractOut(BaseModel):
    text: str
    entities: list[V2NEREntity] = Field(default_factory=list)
    backend: Literal["trained", "rule_based"] = "rule_based"


class V2RecommendItem(BaseModel):
    menu: str
    restaurant: Optional[str] = None
    score: float = 0.0
    similar_user_count: int = 0
    reason: Optional[str] = None


class V2RecommendOut(BaseModel):
    user_id: str
    recommendations: list[V2RecommendItem] = Field(default_factory=list)
    backend: Literal["embedding_cf", "popular", "random"] = "popular"


# =============================================================================
# Tool Calling (Phase 7)
# =============================================================================
class ToolChatIn(BaseModel):
    user_id: str = Field(default="user1", max_length=50)
    query: str = Field(min_length=1, max_length=1000)
    temperature: float = Field(default=0.2, ge=0.0, le=1.5)
    max_iterations: int = Field(default=3, ge=1, le=6)
    # 다중 식사 시간 — None 이면 query 안에서 LLM 이 추론
    meal_type: Optional[str] = Field(
        default=None,
        pattern="^(breakfast|lunch|dinner|any)$",
        description="식사 시간 — breakfast/lunch/dinner/any.",
    )


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ToolResultRecord(BaseModel):
    ok: bool
    tool: str
    data: Optional[Any] = None
    error: Optional[str] = None


class ToolChatOut(BaseModel):
    response: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    tool_results: list[ToolResultRecord] = Field(default_factory=list)
    iterations: int = 0
    latency_ms: int = 0
    fallback_used: bool = False


__all__ = [
    "HealthOut",
    "ErrorOut",
    "SentimentOut",
    "SentimentTopItem",
    "SentimentRefreshIn",
    "SentimentRefreshOut",
    "MenuNormalizeIn",
    "MenuNormalizeOut",
    "MenuStatsOut",
    "ChatIn",
    "ChatRecommendation",
    "ChatOut",
    "ChatResetIn",
    "ChatResetOut",
    "WeeklyReportOut",
    "OllamaModelOut",
    "ModelListOut",
    "SettingsOut",
    "SettingsUpdateIn",
    "SettingsUpdateOut",
    "V2AspectSentiment",
    "V2ABSAOut",
    "V2NEREntity",
    "V2MenuExtractIn",
    "V2MenuExtractOut",
    "V2RecommendItem",
    "V2RecommendOut",
    "ToolChatIn",
    "ToolCallRecord",
    "ToolResultRecord",
    "ToolChatOut",
]
