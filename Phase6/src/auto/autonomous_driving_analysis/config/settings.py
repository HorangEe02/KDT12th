"""
자율주행 AI 분야 취업 동향 분석 - 설정 파일
프로젝트 전체에서 사용하는 설정값과 API 키를 중앙 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ============================================================
# 경로 설정
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_CHARTS_DIR = BASE_DIR / "outputs" / "charts"
OUTPUT_REPORTS_DIR = BASE_DIR / "outputs" / "reports"
URL_LIST_DIR = BASE_DIR / "url_list"

# 디렉토리 자동 생성
for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUT_CHARTS_DIR, OUTPUT_REPORTS_DIR, URL_LIST_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# Naver OpenAPI 설정
# ============================================================
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ============================================================
# 잡플래닛 로그인 설정
# ============================================================
JOBPLANET_USER_ID = os.getenv("JOBPLANET_USER_ID", "")
JOBPLANET_PASSWORD = os.getenv("JOBPLANET_PASSWORD", "")

# ============================================================
# 크롤링 대상 기업 리스트
# ============================================================
TARGET_COMPANIES = {
    "현대모비스": {"jobplanet_id": "59aborz", "category": "대기업_부품"},
    "네이버랩스": {"jobplanet_id": "366rwz", "category": "IT_대기업"},
    "오토노머스에이투지": {"jobplanet_id": "2bnbqz", "category": "스타트업"},
    "라이드플럭스": {"jobplanet_id": "3f5rz", "category": "스타트업"},
    "HL만도": {"jobplanet_id": "59abrz", "category": "대기업_부품"},
    "현대오토에버": {"jobplanet_id": "59abnz", "category": "대기업_IT"},
    "42dot": {"jobplanet_id": "2c9gtz", "category": "스타트업"},
    "소네트": {"jobplanet_id": "3k7az", "category": "스타트업"},
    "서울로보틱스": {"jobplanet_id": "2dpqrz", "category": "스타트업"},
    "모라이": {"jobplanet_id": "2fhvaz", "category": "스타트업"},
}

# ============================================================
# Naver OpenAPI 검색 키워드
# ============================================================
NAVER_KEYWORDS = [
    "자율주행 취업 준비",
    "자율주행 개발자 채용",
    "ADAS 엔지니어 취업",
    "자율주행 신입 채용",
    "ROS 개발자 취업",
    "자율주행 자격증",
    "자율주행 포트폴리오",
    "자율주행 인턴",
    "LiDAR 개발자",
    "컴퓨터비전 자율주행",
    "자율주행 경진대회",
    "SLAM 취업",
    "자율주행 교육과정",
    "자율주행 석사 취업",
    "자율주행 스타트업 채용",
]

# ============================================================
# 사람인 검색 키워드
# ============================================================
SARAMIN_KEYWORDS = [
    "자율주행",
    "자율주행 AI",
    "ADAS",
    "자율주행 Python",
    "자율주행 엔지니어",
    "자율주행 인지",
    "자율주행 판단",
    "자율주행 제어",
    "ROS 개발",
    "LiDAR",
    "자율주행 시뮬레이션",
]

# ============================================================
# 기술스택 키워드
# ============================================================
TECH_STACK_KEYWORDS = [
    "Python", "C++", "C", "Java", "ROS", "ROS2",
    "PyTorch", "TensorFlow", "OpenCV", "SLAM",
    "LiDAR", "RADAR", "카메라", "센서퓨전",
    "AUTOSAR", "MATLAB", "Simulink", "Linux",
    "Docker", "Git", "딥러닝", "머신러닝",
    "컴퓨터비전", "영상처리", "포인트클라우드",
    "CUDA", "CAN", "V2X", "HD맵",
    "시뮬레이션", "CARLA", "SQL", "AWS", "GCP", "Kubernetes",
]

# ============================================================
# 자격증 키워드
# ============================================================
CERTIFICATE_KEYWORDS = [
    "정보처리기사", "빅데이터분석기사", "ADsP", "SQLD",
    "전자기사", "임베디드기사", "운전면허",
    "정보처리산업기사", "리눅스마스터", "네트워크관리사",
]

# ============================================================
# 불용어 리스트
# ============================================================
STOPWORDS = [
    "있는", "하는", "대한", "위한", "통해", "이런", "그런", "저런",
    "것은", "수행", "관련", "경우", "이상", "이하", "등의", "및",
    "또는", "그리고", "하여", "대해", "함께", "가능", "필요", "사용",
    "있음", "없음", "합니다", "입니다", "됩니다", "것이", "으로",
    "에서", "까지", "부터", "에게", "보다", "같은", "때문", "위해",
    "따라", "대로", "만큼", "처럼", "뿐만", "아니라", "하고",
    "되는", "하면", "이를", "그것", "저것", "여기", "거기",
]

# ============================================================
# 크롤링 설정
# ============================================================
CRAWL_DELAY_MIN = 2  # 최소 딜레이 (초)
CRAWL_DELAY_MAX = 5  # 최대 딜레이 (초)
API_CALL_DELAY = 0.1  # API 호출 간 딜레이 (초)
MAX_RETRIES = 3  # 최대 재시도 횟수

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ============================================================
# 한글 폰트 설정
# ============================================================
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]

FONT_PATH = None
for fp in FONT_CANDIDATES:
    if os.path.exists(fp):
        FONT_PATH = fp
        break

# ============================================================
# 워드클라우드 마스크 이미지 경로
# ============================================================
WORDCLOUD_MASK_PATHS = {
    "m1": str(BASE_DIR.parent.parent / "m1.png"),
    "m2": str(BASE_DIR.parent.parent / "m2.png"),
    "car": str(BASE_DIR.parent.parent / "car.png"),
}

# ============================================================
# 기술스택 카테고리 분류
# ============================================================
TECH_CATEGORIES = {
    "프로그래밍언어": ["Python", "C++", "C", "Java", "CUDA"],
    "프레임워크": ["ROS", "ROS2", "PyTorch", "TensorFlow", "OpenCV", "AUTOSAR", "CARLA"],
    "도구": ["MATLAB", "Simulink", "Linux", "Docker", "Git", "SQL", "AWS", "GCP", "Kubernetes"],
    "도메인지식": [
        "SLAM", "LiDAR", "RADAR", "카메라", "센서퓨전",
        "딥러닝", "머신러닝", "컴퓨터비전", "영상처리",
        "포인트클라우드", "CAN", "V2X", "HD맵", "시뮬레이션",
    ],
}

# ============================================================
# 직무 분류
# ============================================================
JOB_CATEGORIES = {
    "인지": ["센서처리", "객체인식", "LiDAR처리", "카메라처리", "센서퓨전", "영상처리"],
    "판단": ["경로계획", "의사결정", "행동계획", "예측", "강화학습"],
    "제어": ["차량제어", "모션제어", "종횡방향제어", "PID", "MPC"],
    "인프라": ["MLOps", "데이터파이프라인", "시뮬레이션", "클라우드", "DevOps"],
    "데이터": ["데이터수집", "데이터라벨링", "데이터분석", "HD맵", "어노테이션"],
}
