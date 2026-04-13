"""
README.md → PDF 변환 스크립트
헬창지피티 프로젝트 소개서 PDF 생성
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── 한글 폰트 등록 ───
FONT_PATHS = [
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "AppleSD"),
    ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", "AppleGothic"),
]

FONT_NAME = "Helvetica"
for path, name in FONT_PATHS:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            FONT_NAME = name
            break
        except:
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                FONT_NAME = name
                break
            except:
                continue

# ─── 색상 팔레트 ───
NEON = HexColor("#2e7d32")
DARK_BG = HexColor("#1a1a1a")
LIGHT_BG = HexColor("#f5f5f0")
CARD_BG = HexColor("#e8e8e3")
TEXT = HexColor("#1a1a1a")
TEXT_SUB = HexColor("#5a5a5a")
BORDER = HexColor("#c8c8c8")
WHITE = white

# ─── 스타일 ───
def make_style(name, size, color=TEXT, bold=False, align=TA_LEFT, space_before=0, space_after=4, leading=None):
    return ParagraphStyle(
        name, fontName=FONT_NAME, fontSize=size, textColor=color,
        alignment=align, spaceBefore=space_before, spaceAfter=space_after,
        leading=leading or size * 1.5,
        wordWrap='CJK',
    )

S_TITLE = make_style("Title", 22, NEON, bold=True, align=TA_CENTER, space_after=2)
S_SUBTITLE = make_style("Subtitle", 11, TEXT_SUB, align=TA_CENTER, space_after=12)
S_H1 = make_style("H1", 16, NEON, bold=True, space_before=18, space_after=6)
S_H2 = make_style("H2", 13, DARK_BG, bold=True, space_before=14, space_after=4)
S_H3 = make_style("H3", 11, NEON, bold=True, space_before=10, space_after=3)
S_BODY = make_style("Body", 9, TEXT, space_after=4, leading=14)
S_BODY_SUB = make_style("BodySub", 8, TEXT_SUB, space_after=3, leading=12)
S_BULLET = make_style("Bullet", 9, TEXT, space_after=2, leading=13)
S_CODE = make_style("Code", 8, HexColor("#333333"), space_after=2, leading=11)
S_FOOTER = make_style("Footer", 7, TEXT_SUB, align=TA_CENTER)
S_CELL = make_style("Cell", 8, TEXT, leading=11)
S_CELL_HEADER = make_style("CellH", 8, WHITE, bold=True, leading=11)

def build_table(headers, rows, col_widths=None):
    """표를 생성합니다."""
    w = A4[0] - 40*mm
    if not col_widths:
        n = len(headers)
        col_widths = [w / n] * n

    data = [[Paragraph(h, S_CELL_HEADER) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), S_CELL) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NEON),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, CARD_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    return t

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8, spaceAfter=8)

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_NAME, 7)
    canvas.setFillColor(TEXT_SUB)
    canvas.drawCentredString(A4[0]/2, 15*mm, f"- {doc.page} -")
    # 헤더
    canvas.setFont(FONT_NAME, 7)
    canvas.setFillColor(NEON)
    canvas.drawString(20*mm, A4[1] - 12*mm, "HelChangGPT v1.1")
    canvas.setFillColor(TEXT_SUB)
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 12*mm, "AI Fitness Life Coach")
    canvas.restoreState()


def main():
    out = os.path.join(os.path.dirname(__file__), "HelChangGPT_프로젝트_소개서.pdf")
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=20*mm,
    )
    W = A4[0] - 40*mm  # 사용 가능 폭
    story = []

    # ════════════ 표지 ════════════
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("헬창지피티 (HelChangGPT)", S_TITLE))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("AI가 설계하는 나만의 피트니스 라이프 코치", make_style("st2", 13, TEXT_SUB, align=TA_CENTER, space_after=8)))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="40%", thickness=1.5, color=NEON, spaceBefore=0, spaceAfter=12))
    story.append(Paragraph("K-Digital Training 빅데이터 분석가 교육과정", S_BODY_SUB))
    story.append(Paragraph("자연어처리 미니프로젝트 | v1.1", make_style("st3", 9, TEXT_SUB, align=TA_CENTER, space_after=4)))
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph(
        "사용자가 자연어로 신체 정보와 운동 목표를 입력하면,<br/>"
        "4단계 NLP 파이프라인(프로필 분석 → 식단 생성 → 운동 루틴 → 동기부여 피드백)을 통해<br/>"
        "개인 맞춤형 건강 관리를 제공하는 AI 피트니스 코칭 웹 서비스",
        make_style("intro", 9, TEXT_SUB, align=TA_CENTER, space_after=4, leading=15)
    ))
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("2026-04-10 | 프로젝트 폴더 구조 소개서", S_FOOTER))
    story.append(PageBreak())

    # ════════════ 기술 스택 ════════════
    story.append(Paragraph("1. 기술 스택", S_H1))
    story.append(build_table(
        ["구분", "기술"],
        [
            ["Frontend", "React 18 + Tailwind CSS (Neon Kinetic), CSS 변수 기반 다크/라이트 테마"],
            ["Backend", "Python FastAPI (50+ 엔드포인트)"],
            ["LLM", "Ollama (EXAONE 3.5, Qwen 3.5, Gemma 4)"],
            ["NLP", "KcBERT, KeyBERT, BM25, sentence-transformers"],
            ["i18n", "경량 딕셔너리 기반 다국어 (한/영/일)"],
            ["배포", "ngrok HTTPS 터널링"],
            ["데이터", "식품안전나라 API (1,146건), 운동 DB (24종), JSON 사용자 데이터"],
        ],
        [W*0.15, W*0.85]
    ))
    story.append(hr())

    # ════════════ 프로젝트 구조 ════════════
    story.append(Paragraph("2. 프로젝트 폴더 구조", S_H1))
    tree = """helchanggpt/
├── api/                  FastAPI 백엔드 서버
├── src/                  핵심 NLP/LLM 비즈니스 로직
│   ├── profile/            Stage 1: 프로필 분석
│   ├── diet/               Stage 2: 식단 생성
│   ├── workout/            Stage 3: 운동 루틴
│   ├── feedback/           Stage 4: 감성 분석 &amp; 피드백
│   └── utils/              공통 유틸리티
├── frontend/             React 프론트엔드
│   └── src/
│       ├── pages/          페이지 컴포넌트 (8개)
│       ├── components/     공통 컴포넌트 (4개)
│       ├── context/        전역 상태 (Auth, Settings)
│       └── i18n/           다국어 번역 딕셔너리
├── data/                 데이터 저장소
├── scripts/              데이터 수집 &amp; 실험 스크립트
├── docs/                 보고서 &amp; 기능 설명서
└── notebooks/            Jupyter 노트북 (실험용)"""
    for line in tree.split("\n"):
        story.append(Paragraph(line, S_CODE))
    story.append(hr())

    # ════════════ api/ ════════════
    story.append(Paragraph("3. api/ — FastAPI 백엔드 서버", S_H1))
    story.append(Paragraph("main.py 하나에 50+ 엔드포인트를 포함하는 FastAPI 메인 앱입니다.", S_BODY))
    apis = [
        "인증 — 회원가입, 로그인, 탈퇴",
        "프로필 — 저장, BMI/BMR/TDEE 계산, NLP 분석, AI 채팅",
        "인바디 — 다중 포맷 업로드(이미지/CSV/PDF/Word/Excel), 건강 분석",
        "식단 — AI 식단 생성, 3일치 생성, 일정 변동 대응, 저장/조회/삭제",
        "운동 — AI 루틴 생성, 운동 검색(BM25/임베딩/필터), 저장/조회/삭제",
        "피드백 — 감성 분석 + 5종 모드별 AI 피드백",
        "일기 — 저장, 이력 조회, 성장 통계",
        "어드민 — 사용자 관리, 시스템 통계, 역할/비밀번호/활성화 관리",
    ]
    for a in apis:
        story.append(Paragraph(f"&bull; {a}", S_BULLET))
    story.append(hr())

    # ════════════ src/ ════════════
    story.append(Paragraph("4. src/ — 핵심 NLP/LLM 비즈니스 로직", S_H1))
    story.append(Paragraph("4단계(기·승·전·결) 파이프라인의 핵심 모듈입니다.", S_BODY))

    # profile
    story.append(Paragraph("4-1. src/profile/ — Stage 1: 프로필 분석 (기-起)", S_H2))
    story.append(build_table(["파일", "설명"], [
        ["profile_ner.py", "정규식 기반 NER — 나이/성별/키/체중/운동빈도 추출 (정확도 100%)"],
        ["goal_classifier.py", "운동 목표 5클래스 분류 (규칙+LLM, F1=0.849)"],
        ["body_calculator.py", "Mifflin-St Jeor BMR, KSSO BMI 6단계, TDEE 계산"],
        ["inbody_parser.py", "인바디 다중 포맷 파싱 (이미지 비전/CSV/PDF/Word/Excel)"],
        ["inbody_analyzer.py", "체형 분석(C/I/D), 내장지방, 근감소증(SMI), ECW 비율"],
        ["health_analyzer.py", "대사증후군 스크리닝, 프로필 신뢰도 점수"],
        ["profile_builder.py", "전체 분석 통합 → 구조화된 프로필 생성"],
        ["report_generator.py", "PDF/Word/Excel/CSV/JSON 리포트 내보내기"],
        ["user_history.py", "사용자별 인바디 측정 이력 관리 (JSON)"],
        ["keyword_extractor.py", "KeyBERT 키워드 추출"],
        ["evaluation.py", "NER 정확도, 목표 F1, BMR 비교 평가"],
    ], [W*0.28, W*0.72]))

    # diet
    story.append(Paragraph("4-2. src/diet/ — Stage 2: 식단 생성 (승-承)", S_H2))
    story.append(build_table(["파일", "설명"], [
        ["macro_calculator.py", "목표별 탄단지 비율 계산 + 제약사항 보정"],
        ["nutrition_db.py", "식품 영양성분 DB (API 1,146건 + 기본 30종)"],
        ["diet_prompts.py", "LLM 프롬프트 4종 (Zero-shot/Few-shot/CoT/Scheduled)"],
        ["diet_generator.py", "LLM 식단 생성 + 프롬프트 비교 실험 실행기"],
        ["diet_analyzer.py", "칼로리 정확도, 매크로 검증, 제약사항 위반 체크"],
        ["diet_adjuster.py", "6가지 일정 변동 시나리오 감지 + 식단 재조정"],
        ["meal_scheduler.py", "시간대별 끼니 배정 (운동 전후 간식 포함)"],
        ["eating_out_db.py", "외식/회식 메뉴 칼로리 추정 DB (21종)"],
    ], [W*0.28, W*0.72]))

    # workout
    story.append(Paragraph("4-3. src/workout/ — Stage 3: 운동 루틴 (전-轉)", S_H2))
    story.append(build_table(["파일", "설명"], [
        ["workout_prompts.py", "면책 문구, 분할 추천 규칙, 유산소/근력 비율 기준"],
        ["workout_generator.py", "LLM 7일 운동 루틴 생성 + 데모 루틴 + 제약사항 반영"],
        ["exercise_search.py", "BM25 + 임베딩 + 필터 하이브리드 검색 + 제약 안전 필터링"],
        ["workout_analyzer.py", "근육군 균형 점수, 유산소 비율, 볼륨 평가"],
    ], [W*0.28, W*0.72]))

    # feedback
    story.append(Paragraph("4-4. src/feedback/ — Stage 4: 감성 분석 &amp; 피드백 (결-結)", S_H2))
    story.append(build_table(["파일", "설명"], [
        ["sentiment_analyzer.py", "키워드 기반 감성 분석 (긍정/부정/중립, 정확도 70%) + LLM 병행"],
        ["feedback_modes.py", "5종 피드백 모드 정의 (코치/친구/교관/매미킴/해병문학)"],
        ["feedback_generator.py", "규칙 기반 + LLM 기반 피드백 생성 (모드별 톤/스타일 적용)"],
        ["weekly_summarizer.py", "주간 요약 + 하이라이트 추출"],
    ], [W*0.28, W*0.72]))

    story.append(Paragraph("4-5. src/utils/ — 공통 유틸리티", S_H2))
    story.append(Paragraph("&bull; llm_client.py — Ollama/OpenAI 통합 클라이언트, 11개 모델 레지스트리, 기본 모델 할당", S_BULLET))
    story.append(hr())

    # ════════════ frontend/ ════════════
    story.append(Paragraph("5. frontend/ — React 프론트엔드", S_H1))
    story.append(Paragraph("Neon Kinetic 디자인 시스템을 적용한 React 18 + Tailwind CSS SPA입니다.", S_BODY))

    story.append(Paragraph("5-1. 페이지 컴포넌트 (8개)", S_H2))
    story.append(build_table(["파일", "설명"], [
        ["LoginPage.jsx", "로그인/회원가입 (다국어 지원)"],
        ["OnboardingPage.jsx", "내 몸 알기 — 4탭: 직접 입력, 인바디 업로드, AI 채팅, 프로필 보기"],
        ["DietPage.jsx", "오늘 뭐 먹지 — 3탭: AI 대화(+사이드 미리보기), 식단 보기, 저장 이력"],
        ["WorkoutPage.jsx", "오늘 뭐 하지 — 3탭: AI 트레이너, 상세 루틴 보기, 저장 이력"],
        ["DiaryPage.jsx", "운동 일기 — 3탭: 오늘의 일기(5종 피드백 모드), 성장 기록, 목표 달성률"],
        ["SettingsPage.jsx", "설정 — 언어(한/영/일), 테마(다크/라이트), AI 모델, 데이터 관리"],
        ["AdminPage.jsx", "시스템 관리 — 관리자 전용 대시보드"],
        ["MemberManagePage.jsx", "회원 관리 — 사용자 목록, 역할 변경, 비밀번호 초기화"],
    ], [W*0.28, W*0.72]))

    story.append(Paragraph("5-2. 공통 컴포넌트 / 전역 상태 / 다국어", S_H2))
    story.append(build_table(["파일", "설명"], [
        ["components/ModelSelector.jsx", "AI 모델 선택기 (6개 모델, 컴팩트/풀 모드)"],
        ["components/InBodyUploader.jsx", "인바디 파일 업로드 (이미지/CSV/PDF/Word/Excel)"],
        ["context/AuthContext.jsx", "인증 상태 (로그인/로그아웃/역할), localStorage 기반"],
        ["context/SettingsContext.jsx", "설정 상태 (테마/언어/모델) + t() 번역 함수"],
        ["i18n/translations.js", "한국어/영어/일본어 번역 딕셔너리 (~50키 x 3언어)"],
    ], [W*0.32, W*0.68]))
    story.append(hr())

    # ════════════ data/ ════════════
    story.append(Paragraph("6. data/ — 데이터 저장소", S_H1))
    story.append(build_table(["폴더", "설명"], [
        ["nutrition/", "식품 영양성분 DB — foods.json (1,146건, 식품안전나라 API)"],
        ["exercises/", "운동 DB — exercise_db.json (24종, 11개 근육군), MET 테이블 (30종)"],
        ["experiments/", "실험 결과 — experiment_results.json (NER/분류/감성/BMR/검색)"],
        ["user_samples/", "학습/평가 데이터 — 목표분류 train/val/test, KNHANES 통계"],
        ["diary_samples/", "일기 샘플 — diary_samples.json (데모/평가용)"],
        ["users/", "사용자 인증 — {user_id}.json (닉네임, 비밀번호 해시, 역할)"],
        ["user_profiles/", "사용자별 데이터 (프로필, 인바디, 식단, 운동, 일기 이력)"],
    ], [W*0.2, W*0.8]))
    story.append(hr())

    # ════════════ scripts/ ════════════
    story.append(Paragraph("7. scripts/ — 데이터 수집 &amp; 실험 스크립트", S_H1))
    story.append(build_table(["파일", "설명"], [
        ["fetch_nutrition_api.py", "식품안전나라 COOKRCP01 API 식품 데이터 수집"],
        ["build_exercise_db.py", "운동 DB + MET 테이블 구축"],
        ["process_knhanes.py", "국민건강영양조사(KNHANES) 통계 가공"],
        ["prepare_training_data.py", "목표분류/감성분석 학습 데이터 생성"],
        ["run_experiments.py", "4단계 전체 평가 실험 실행기"],
    ], [W*0.3, W*0.7]))
    story.append(hr())

    # ════════════ docs/ ════════════
    story.append(Paragraph("8. docs/ — 보고서 &amp; 기능 설명서", S_H1))
    story.append(build_table(["파일", "설명"], [
        ["final_report.md", "최종 보고서 — 10개 필수 섹션 (주제/모델/프롬프트/파라미터/결과/개선/한계점)"],
        ["experiment_report.md", "실험 결과 분석 — 4단계별 정량 평가 + v1.1 업데이트 내역"],
        ["feature_01_my_body.md", "기능 설명서: 내 몸 알기 (Stage 1)"],
        ["feature_02_diet.md", "기능 설명서: 오늘 뭐 먹지? (Stage 2)"],
        ["feature_03_workout.md", "기능 설명서: 오늘 뭐 하지? (Stage 3)"],
        ["feature_04_diary.md", "기능 설명서: 운동 일기 (Stage 4)"],
    ], [W*0.3, W*0.7]))
    story.append(hr())

    # ════════════ 실험 결과 ════════════
    story.append(Paragraph("9. 주요 실험 결과", S_H1))
    story.append(build_table(["단계", "NLP 기법", "정확도/점수"], [
        ["Stage 1 NER", "정규식 기반", "100% (21/21 필드)"],
        ["Stage 1 분류", "키워드 매칭", "85%, F1=0.849"],
        ["Stage 2 식단", "LLM Few-shot", "JSON 준수율 매우 높음"],
        ["Stage 3 검색", "BM25+필터 하이브리드", "자연어+정확 매칭 최적"],
        ["Stage 4 감성", "키워드 기반", "70% (LLM 병행 시 85%+)"],
    ], [W*0.2, W*0.35, W*0.45]))

    story.append(Spacer(1, 15*mm))
    story.append(HRFlowable(width="30%", thickness=1, color=NEON, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("최종 수정: 2026-04-10 | 헬창지피티 v1.1", S_FOOTER))

    # ─── 빌드 ───
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF 생성 완료: {out}")


if __name__ == "__main__":
    main()
