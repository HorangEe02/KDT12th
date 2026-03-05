"""
=============================================================
의료 AI 분야 취업 동향 분석 - 설정 파일
=============================================================
프로젝트 전체에서 사용하는 설정값과 API 키를 중앙 관리
=============================================================
"""

import os
import random
import time
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ============================================================
# Naver OpenAPI 설정
# ============================================================
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ============================================================
# 잡플래닛 로그인 정보
# ============================================================
JOBPLANET_USER_ID = os.getenv("JOBPLANET_USER_ID", "")
JOBPLANET_PASSWORD = os.getenv("JOBPLANET_PASSWORD", "")

# ============================================================
# 크롤링 대상 기업 리스트 (의료 AI 특화)
# ============================================================
TARGET_COMPANIES = {
    "뷰노": {
        "company_id": "329047",
        "category": "스타트업_의료영상",
        "비고": "의료영상 AI 진단",
    },
    "루닛": {
        "company_id": "325870",
        "category": "스타트업_의료영상",
        "비고": "흉부 X-ray AI",
    },
    "딥노이드": {
        "company_id": "62240",
        "category": "스타트업_의료영상",
        "비고": "의료영상 딥러닝",
    },
    "제이엘케이": {
        "company_id": "327410",
        "category": "스타트업_의료AI",
        "비고": "뇌졸중 AI 진단",
    },
    "셀바스AI": {
        "company_id": "79634",
        "category": "중소기업_AI",
        "비고": "음성인식/필기인식 AI + 헬스케어",
    },
    "라인웍스": {
        "company_id": "390283",
        "category": "스타트업_디지털헬스",
        "비고": "의료 자연어처리",
    },
    "메디컬에이아이": {
        "company_id": "389808",
        "category": "스타트업_의료AI",
        "비고": "심전도 AI 분석",
    },
    "닥터나우": {
        "company_id": "377124",
        "category": "스타트업_원격의료",
        "비고": "원격 진료 플랫폼",
    },
    "인피니트헬스케어": {
        "company_id": "57691",
        "category": "중소기업_PACS",
        "비고": "PACS/의료정보 시스템",
    },
    "카카오헬스케어": {
        "company_id": "405810",
        "category": "대기업_헬스케어",
        "비고": "디지털 헬스케어 플랫폼",
    },
    "네이버클라우드(의료)": {
        "company_id": "42216",
        "category": "대기업_클라우드",
        "비고": "클라우드 기반 의료 AI",
    },
    "솔트룩스": {
        "company_id": "71198",
        "category": "중소기업_AI",
        "비고": "AI 플랫폼(의료/산업 적용)",
    },
}

# ============================================================
# Naver OpenAPI 검색 키워드 (블로그/뉴스 분리)
# ============================================================
# 블로그 검색 키워드 (취준 동향, 준비 내용 중심)
NAVER_BLOG_KEYWORDS = [
    "의료 AI 취업 준비",
    "의료 AI 개발자 취업",
    "헬스케어 AI 취업",
    "의료영상 AI 개발자",
    "디지털헬스 취업",
    "의료 데이터 분석가",
    "의료 AI 신입 채용",
    "의료 AI 자격증",
    "의료 AI 포트폴리오",
    "의료 AI 인턴",
    "의료AI Python 개발",
    "헬스케어 데이터 자격증",
    "의료 AI 석사 취업",
    "의료 AI 교육과정",
    "의료 영상 AI 취업",
    "DICOM 개발자",
    "바이오헬스 AI 취업",
    "의료 AI 논문 취업",
    "FDA SaMD 인허가",
    "의료 AI 스타트업 취업",
    "임상시험 SAS 통계",
    "의료 SPSS 데이터분석",
]

# 뉴스 검색 키워드 (산업 트렌드, 채용 현황 중심)
NAVER_NEWS_KEYWORDS = [
    "의료 AI 채용",
    "헬스케어 AI 인력",
    "의료 AI 스타트업 채용",
    "디지털 헬스케어 채용",
    "의료 AI 산업 전망",
    "헬스케어 데이터 채용",
    "의료AI 연봉",
    "의료 AI 인력 수요",
    "의료 AI 개발자 부족",
    "의료 AI 기술 인재",
    "의료 데이터 사이언티스트",
    "의료 AI 투자",
    "헬스케어 AI 시장",
    "의료 AI 규제",
    "의료 AI 인허가",
]

# 전체 키워드 (하위 호환용)
NAVER_KEYWORDS = NAVER_BLOG_KEYWORDS + NAVER_NEWS_KEYWORDS

# ============================================================
# 검색 키워드별 색상 맵 (시각화 일관성용)
# ============================================================
KEYWORD_COLOR_MAP = {
    # 블로그 키워드 - 파란 계열
    "의료 AI 취업 준비": "#1f77b4",
    "의료 AI 개발자 취업": "#2986cc",
    "헬스케어 AI 취업": "#3498db",
    "의료영상 AI 개발자": "#5dade2",
    "디지털헬스 취업": "#85c1e9",
    "의료 데이터 분석가": "#0b5394",
    "의료 AI 신입 채용": "#6fa8dc",
    "의료 AI 자격증": "#073763",
    "의료 AI 포트폴리오": "#4a86c8",
    "의료 AI 인턴": "#7fb3e0",
    "의료AI Python 개발": "#1a5276",
    "헬스케어 데이터 자격증": "#2e86c1",
    "의료 AI 석사 취업": "#21618c",
    "의료 AI 교육과정": "#2874a6",
    "의료 영상 AI 취업": "#1b4f72",
    "DICOM 개발자": "#154360",
    "바이오헬스 AI 취업": "#1a73b5",
    "의료 AI 논문 취업": "#3c8dbc",
    "FDA SaMD 인허가": "#4592af",
    "의료 AI 스타트업 취업": "#5ba3c9",
    "임상시험 SAS 통계": "#0e4d7a",
    "의료 SPSS 데이터분석": "#2471a3",
    # 뉴스 키워드 - 주황/빨강 계열
    "의료 AI 채용": "#e74c3c",
    "헬스케어 AI 인력": "#e67e22",
    "의료 AI 스타트업 채용": "#f39c12",
    "디지털 헬스케어 채용": "#d35400",
    "의료 AI 산업 전망": "#c0392b",
    "헬스케어 데이터 채용": "#e57e25",
    "의료AI 연봉": "#f1c40f",
    "의료 AI 인력 수요": "#d4551a",
    "의료 AI 개발자 부족": "#cb4335",
    "의료 AI 기술 인재": "#e08e4a",
    "의료 데이터 사이언티스트": "#f0b92d",
    "의료 AI 투자": "#b7352d",
    "헬스케어 AI 시장": "#d68910",
    "의료 AI 규제": "#a93226",
    "의료 AI 인허가": "#ba4a00",
}

# ============================================================
# 원티드 검색 키워드
# ============================================================
WANTED_KEYWORDS = [
    "의료 AI",
    "헬스케어",
    "의료영상",
    "디지털헬스",
    "바이오 AI",
]

# ============================================================
# 사람인 검색 키워드
# ============================================================
SARAMIN_KEYWORDS = [
    "의료 AI",
    "의료 인공지능",
    "헬스케어 AI",
    "의료영상 분석",
    "디지털헬스",
    "헬스케어 Python",
    "의료 데이터",
    "바이오 AI",
    "의료 딥러닝",
    "의료 머신러닝",
    "PACS 개발",
    "EMR 개발",
]

# ============================================================
# 크롤링 딜레이 설정
# ============================================================
CRAWL_DELAY_MIN = 2  # 최소 딜레이 (초)
CRAWL_DELAY_MAX = 5  # 최대 딜레이 (초)
API_CALL_DELAY = 0.1  # API 호출 간 딜레이 (초)


def random_delay(min_sec=None, max_sec=None):
    """랜덤 딜레이 적용"""
    min_sec = min_sec or CRAWL_DELAY_MIN
    max_sec = max_sec or CRAWL_DELAY_MAX
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


# ============================================================
# 저장 경로 상수
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUTS_CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
OUTPUTS_REPORTS_DIR = os.path.join(BASE_DIR, "outputs", "reports")
URL_LIST_DIR = os.path.join(BASE_DIR, "url_list")

# 디렉토리 자동 생성
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUTS_CHARTS_DIR, OUTPUTS_REPORTS_DIR, URL_LIST_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# User-Agent 설정
# ============================================================
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

# ============================================================
# 기술스택 키워드 사전 (의료 AI 특화)
# ============================================================
TECH_STACK_KEYWORDS = [
    "Python", "R", "PyTorch", "TensorFlow", "Keras",
    "OpenCV", "scikit-learn", "pandas", "NumPy", "SciPy",
    "딥러닝", "머신러닝", "컴퓨터비전", "자연어처리", "NLP",
    "의료영상", "DICOM", "PACS", "HL7", "FHIR",
    "CT", "MRI", "X-ray", "병리", "내시경",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "SQL", "MongoDB", "PostgreSQL",
    "Git", "Linux", "MLOps", "Kubeflow", "MLflow",
    "SAS", "SPSS", "통계분석", "생존분석", "임상시험", "FDA", "MFDS",
    "논문", "SCI", "특허",
    "Java", "C++", "JavaScript", "React", "FastAPI", "Django",
]

# ============================================================
# 자격증 키워드 사전 (의료 AI 특화)
# ============================================================
CERTIFICATE_KEYWORDS = [
    "정보처리기사", "빅데이터분석기사", "ADsP", "ADP",
    "SQLD", "SQLP", "의공기사", "방사선사", "임상병리사",
    "AWS 자격증", "GCP 자격증", "데이터분석준전문가",
]

# ============================================================
# 의료 도메인 키워드
# ============================================================
MEDICAL_DOMAIN_KEYWORDS = {
    "영상의학": ["CT", "MRI", "X-ray", "초음파", "의료영상", "방사선"],
    "병리": ["조직검사", "세포검사", "디지털병리", "병리", "슬라이드"],
    "임상": ["EMR", "임상시험", "바이오마커", "임상데이터", "전자의무기록"],
    "인허가": ["FDA", "MFDS", "SaMD", "CE마킹", "인허가", "510(k)"],
    "유전체": ["유전체", "오믹스", "NGS", "게노믹스", "바이오인포매틱스"],
}

# ============================================================
# 한글 폰트 경로 후보
# ============================================================
KOREAN_FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]

# ============================================================
# 워드클라우드 마스크 이미지 경로
# ============================================================
WORDCLOUD_MASK_PATH = os.path.join(
    os.path.dirname(BASE_DIR), "cross.png"
)
