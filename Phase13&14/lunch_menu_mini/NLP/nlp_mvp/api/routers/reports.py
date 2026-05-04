"""
/nlp/reports/* 라우터 — NLG 주간 영양 리포트.

- GET  /nlp/reports/weekly/{user_id}
- POST /nlp/reports/weekly/{user_id}/regenerate
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from nlp_mvp.api.rate_limit import rate_limit
from nlp_mvp.api.schemas import WeeklyReportOut
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp/reports", tags=["nlp-reports"])


# =============================================================================
# 싱글톤
# =============================================================================
_generator = None


def get_generator():
    """ReportGenerator 싱글톤.

    Phase 14: provider/모델은 factory.get_report_client() 가 결정.
    LLM_PROVIDER_REPORT env (gemini|ollama) 와 GEMINI_MODEL_REPORT /
    OLLAMA_MODEL_REPORT 를 읽음. PUT /nlp/settings/model (role=report)
    이 env 를 덮어쓰고 set_generator(None) 으로 캐시 drop 하면 다음 요청에
    새 provider/모델로 재생성된다.
    """
    global _generator
    if _generator is None:
        from nlp_mvp.nlg_report.generator import ReportGenerator
        from nlp_mvp.shared.llm.factory import get_report_client

        _generator = ReportGenerator(llm_client=get_report_client())
    return _generator


def set_generator(gen) -> None:
    global _generator
    _generator = gen


# =============================================================================
# 공용 내부 헬퍼
# =============================================================================
def _to_schema(result) -> WeeklyReportOut:
    return WeeklyReportOut(
        user_id=result.user_id,
        week_start=result.week_start,
        week_label=result.week_label,
        text=result.nlg_text,
        facts=result.facts or {},
        generation_method=result.generation_method,  # type: ignore[arg-type]
        generated_at=result.generated_at,
        validation=result.validation or {},
    )


def _run(user_id: str, force: bool) -> WeeklyReportOut:
    try:
        gen = get_generator()
    except Exception as e:
        logger.exception("generator init failed")
        raise HTTPException(status_code=503, detail=f"report generator unavailable: {e}")

    try:
        if force:
            result = gen.generate(user_id=user_id, save=True)
        else:
            result = gen.get_or_generate(user_id=user_id)
    except Exception as e:
        logger.exception(f"reports.weekly failed: {e}")
        raise HTTPException(status_code=500, detail="report generation failed")

    return _to_schema(result)


# =============================================================================
# GET /nlp/reports/weekly/{user_id}
# =============================================================================
@router.get("/weekly/{user_id}", response_model=WeeklyReportOut)
@rate_limit("20/minute")  # #5 — 캐시 hit 포함이라 넉넉히
def weekly(
    request: Request,
    user_id: str,
    regenerate: bool = Query(default=False),
) -> WeeklyReportOut:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="invalid user_id")
    return _run(user_id=user_id, force=regenerate)


# =============================================================================
# POST /nlp/reports/weekly/{user_id}/regenerate
# =============================================================================
@router.post("/weekly/{user_id}/regenerate", response_model=WeeklyReportOut)
@rate_limit("3/minute")  # #5 — LLM 전체 재생성이라 강하게 제한
def regenerate(request: Request, user_id: str) -> WeeklyReportOut:
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="invalid user_id")
    return _run(user_id=user_id, force=True)
