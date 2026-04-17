import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
POI_CACHE_DIR = DATA_DIR / "poi_cache"
MODELS_DIR = PROJECT_ROOT / "models"
ASSETS_DIR = PROJECT_ROOT / "assets"
ASSETS_CSS_DIR = ASSETS_DIR / "css"
ASSETS_IMAGES_DIR = ASSETS_DIR / "images"
TESTS_DIR = PROJECT_ROOT / "tests"

load_dotenv(PROJECT_ROOT / ".env")

TOUR_API_KEY = os.getenv("TOUR_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
MID_WEATHER_API_KEY = os.getenv("MID_WEATHER_API_KEY", "")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_JAVASCRIPT_KEY = os.getenv("KAKAO_JAVASCRIPT_KEY", "")
KAKAO_MOBILITY_API_KEY = os.getenv("KAKAO_MOBILITY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# -- Ollama (로컬 LLM) --
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "gemma4:e4b")
OLLAMA_TOOL_MODEL = os.getenv("OLLAMA_TOOL_MODEL", "gemma4:e4b")
OLLAMA_FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL", "gemma4:e2b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3:latest")

try:
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
except ValueError:
    OLLAMA_TEMPERATURE = 0.7
try:
    OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "800"))
except ValueError:
    OLLAMA_MAX_TOKENS = 800
try:
    OLLAMA_REQUEST_TIMEOUT = int(os.getenv("OLLAMA_REQUEST_TIMEOUT", "60"))
except ValueError:
    OLLAMA_REQUEST_TIMEOUT = 60

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
WIN_RATE_MODEL_PATH = MODELS_DIR / "win_rate_model.pkl"

# -- Firebase / GCP (Phase 5 배포) --
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", FIREBASE_PROJECT_ID)
GCP_REGION = os.getenv("GCP_REGION", "asia-northeast3")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")
GCS_RAG_BLOB = os.getenv("GCS_RAG_BLOB", "rag/chroma_snapshot.tar.gz")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# -- Gemini API (Ollama fallback) --
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash-lite")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# 배포 환경 여부 (Cloud Run 자동 설정 환경변수)
IS_CLOUD_RUN = bool(os.getenv("K_SERVICE"))

KBO_TEAMS = [
    "LG 트윈스",
    "KIA 타이거즈",
    "삼성 라이온즈",
    "두산 베어스",
    "KT 위즈",
    "SSG 랜더스",
    "롯데 자이언츠",
    "한화 이글스",
    "NC 다이노스",
    "키움 히어로즈",
]

TEAMS = ["LG", "KT", "SSG", "두산", "KIA", "NC", "삼성", "롯데", "한화", "키움"]

HOME_STADIUM = {
    "LG": "잠실",
    "두산": "잠실",
    "키움": "고척",
    "SSG": "문학",
    "KT": "수원",
    "한화": "대전",
    "삼성": "대구",
    "KIA": "광주",
    "NC": "창원",
    "롯데": "사직",
}

CONTENT_TYPE = {
    "tour": 12,
    "stay": 32,
    "food": 39,
}
CONTENT_TYPE_REVERSE = {v: k for k, v in CONTENT_TYPE.items()}

TOUR_API_BASE = "https://apis.data.go.kr/B551011/KorService2"
WEATHER_API_BASE = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
MID_WEATHER_API_BASE = "https://apis.data.go.kr/1360000/MidFcstInfoService"

SCHEDULE_CSV = DATA_DIR / "kbo_schedule_2026.csv"
STADIUMS_CSV = DATA_DIR / "stadiums.csv"
TEAM_STATS_CSV = DATA_DIR / "team_stats_10yr.csv"

SEASON_START = "2026-03-28"
SEASON_END = "2026-09-30"
ALL_STAR_BREAK = ("2026-07-10", "2026-07-15")

DEFAULT_CACHE_TTL = 3600
DEFAULT_API_TIMEOUT = 10
