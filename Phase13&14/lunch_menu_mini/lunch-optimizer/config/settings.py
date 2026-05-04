"""
Mini lunch-optimizer — 전역 설정 모듈.

공용 `Mini/.env` 를 자동 로드하며, 환경 변수를 타입 안전하게 노출합니다.
모든 하위 모듈은 `from config.settings import settings` 로 접근합니다.

로드 우선순위:
    1. 프로세스 환경 변수
    2. Mini/.env (공용, 상위 경로)
    3. lunch-optimizer/.env (local override, 선택)
    4. 본 파일의 기본값
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# =============================================================================
# .env 로드 (상위 → 하위 순서, 하위가 우선)
# =============================================================================
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MINI_ROOT = _PROJECT_ROOT.parent

# 1. 공용 Mini/.env
_parent_env = _MINI_ROOT / ".env"
if _parent_env.exists():
    load_dotenv(_parent_env, override=False)

# 2. 하위 lunch-optimizer/.env (선택적 override)
_local_env = _PROJECT_ROOT / ".env"
if _local_env.exists():
    load_dotenv(_local_env, override=True)


# =============================================================================
# 설정 유틸
# =============================================================================
def _get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


# =============================================================================
# 설정 데이터 클래스
# =============================================================================
@dataclass(frozen=True)
class KakaoSettings:
    """카카오 로컬 API."""
    api_key: str = field(default_factory=lambda: _get_env("KAKAO_REST_API_KEY"))
    js_key: str = field(default_factory=lambda: _get_env("NEXT_PUBLIC_KAKAO_MAP_KEY"))
    base_url: str = "https://dapi.kakao.com"
    category_search_path: str = "/v2/local/search/category.json"
    keyword_search_path: str = "/v2/local/search/keyword.json"
    default_category_code: str = "FD6"  # 음식점
    # KA 헤더에 사용할 origin. Kakao Developers 콘솔 "Web 플랫폼 → 사이트 도메인"
    # 에 동일한 값이 등록되어 있어야 합니다.
    ka_origin: str = field(
        default_factory=lambda: _get_env("KAKAO_KA_ORIGIN", "http://localhost:3000")
    )

    @property
    def has_key(self) -> bool:
        return bool(self.api_key and "your_" not in self.api_key)

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"KakaoAK {self.api_key}"}

    @property
    def request_headers(self) -> dict[str, str]:
        """
        Kakao 로컬 API 요청에 필요한 전체 헤더.

        2025년 이후 카카오 정책 변경으로 서버 사이드에서도 KA(Kakao Agent)
        헤더가 필수입니다. KA 헤더의 origin 값은 Kakao Developers 콘솔에
        등록된 Web 도메인과 일치해야 합니다.

        인증 키는 **JavaScript 키**를 사용합니다.
        REST API 키는 KA origin 기반 도메인 검증과 호환되지 않으며,
        JavaScript 키 + KA 헤더가 카카오 현행 인증 체계입니다.
        """
        import platform
        import urllib.parse
        # JavaScript 키 우선, 없으면 REST API 키 fallback
        key = self.js_key or self.api_key
        origin_encoded = urllib.parse.quote(self.ka_origin, safe="")
        ka = (
            f"sdk/2.7.4 os/javascript sdk_type/javascript "
            f"lang/ko-KR device/{platform.system()} "
            f"origin/{origin_encoded}"
        )
        return {
            "Authorization": f"KakaoAK {key}",
            "KA": ka,
        }


@dataclass(frozen=True)
class DataGoKrSettings:
    """공공데이터포털 (기상청·식약처 등 공용 인증키)."""
    encoded_key: str = field(default_factory=lambda: _get_env("DATA_GO_KR_API_KEY_ENCODED"))
    decoded_key: str = field(default_factory=lambda: _get_env("DATA_GO_KR_API_KEY_DECODED"))

    @property
    def has_key(self) -> bool:
        return bool(self.decoded_key and "your_" not in self.decoded_key)


@dataclass(frozen=True)
class WeatherSettings:
    """기상청 단기예보 API."""
    base_url: str = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
    ultra_ncst_path: str = "/getUltraSrtNcst"
    vilage_fcst_path: str = "/getVilageFcst"


@dataclass(frozen=True)
class AirQualitySettings:
    """에어코리아 대기질 API."""
    base_url: str = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc"
    realtime_path: str = "/getMsrstnAcctoRltmMesureDnsty"
    station_name: str = field(
        default_factory=lambda: _get_env("NEAREST_STATION_NAME", "종로구")
    )


@dataclass(frozen=True)
class FoodSafetySettings:
    """식품안전나라 영양성분 DB API (I2790)."""
    base_url: str = "https://openapi.foodsafetykorea.go.kr/api"
    service_id: str = "I2790"
    api_key: str = field(
        default_factory=lambda: (
            _get_env("FOOD_SAFETY_API_KEY")
            or _get_env("DATA_GO_KR_API_KEY_DECODED")
        )
    )

    @property
    def has_key(self) -> bool:
        return bool(self.api_key and "your_" not in self.api_key)


@dataclass(frozen=True)
class NutritionProviderSettings:
    """영양 정보 collector provider 라우팅.

    provider 값:
      - "data_go_kr" (기본): apis.data.go.kr 식약처 영양 API 우선,
        실패 시 (fallback_to_food_safety) 식품안전나라 폴백.
      - "food_safety": 식품안전나라(openapi.foodsafetykorea.go.kr) 만 사용.
      - "auto": data.go.kr 시도 후 폴백 (data_go_kr 와 동일).
    """
    provider: str = field(
        default_factory=lambda: _get_env("NUTRITION_PROVIDER", "data_go_kr")
    )
    fallback_to_food_safety: bool = field(
        default_factory=lambda: _get_env("NUTRITION_FALLBACK_FOOD_SAFETY", "1")
        not in {"0", "false", "False", ""}
    )
    data_go_kr_url: str = field(
        default_factory=lambda: _get_env(
            "DATA_GO_KR_NUTRITION_URL",
            "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01",
        )
    )
    data_go_kr_name_param: str = field(
        default_factory=lambda: _get_env("DATA_GO_KR_NUTRITION_NAME_PARAM", "FOOD_NM_KR")
    )


@dataclass(frozen=True)
class OfficeSettings:
    """사무실 위치 및 검색 반경."""
    lat: float = field(default_factory=lambda: _get_float("OFFICE_LAT", 37.5665))
    lng: float = field(default_factory=lambda: _get_float("OFFICE_LNG", 126.9780))
    search_radius_m: int = field(default_factory=lambda: _get_int("SEARCH_RADIUS", 500))


@dataclass(frozen=True)
class DatabaseSettings:
    """DB 연결 설정."""
    url: str = field(default_factory=lambda: _get_env(
        "DB_URL", "sqlite:///./lunch-optimizer/database/mini.db"
    ))
    echo: bool = False

    @property
    def sqlite_path(self) -> Optional[Path]:
        if self.url.startswith("sqlite:///"):
            return Path(self.url.replace("sqlite:///", "")).resolve()
        return None


@dataclass(frozen=True)
class APISettings:
    """FastAPI 서버."""
    host: str = field(default_factory=lambda: _get_env("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _get_int("API_PORT", 8000))
    cors_origins: list[str] = field(
        default_factory=lambda: _get_env(
            "CORS_ORIGINS",
            ",".join(
                [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://localhost:3002",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:3001",
                    "http://127.0.0.1:3002",
                    "http://127.0.0.1:5173",
                ]
            ),
        ).split(",")
    )


@dataclass(frozen=True)
class LoggingSettings:
    level: str = field(default_factory=lambda: _get_env("LOG_LEVEL", "INFO"))
    file: str = field(default_factory=lambda: _get_env("LOG_FILE", "./logs/mini.log"))


@dataclass(frozen=True)
class Settings:
    """전역 설정 컨테이너."""
    project_root: Path = field(default_factory=lambda: _PROJECT_ROOT)
    mini_root: Path = field(default_factory=lambda: _MINI_ROOT)
    kakao: KakaoSettings = field(default_factory=KakaoSettings)
    datago: DataGoKrSettings = field(default_factory=DataGoKrSettings)
    weather: WeatherSettings = field(default_factory=WeatherSettings)
    air_quality: AirQualitySettings = field(default_factory=AirQualitySettings)
    food_safety: FoodSafetySettings = field(default_factory=FoodSafetySettings)
    nutrition_provider: NutritionProviderSettings = field(
        default_factory=NutritionProviderSettings
    )
    office: OfficeSettings = field(default_factory=OfficeSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    api: APISettings = field(default_factory=APISettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)


# =============================================================================
# 모듈 싱글톤
# =============================================================================
settings = Settings()


if __name__ == "__main__":
    # 빠른 점검 (민감 키는 마스킹)
    print(f"Project root: {settings.project_root}")
    print(f"Mini root: {settings.mini_root}")
    print(f"Kakao API key: {'✓ loaded' if settings.kakao.has_key else '✗ missing'}")
    print(f"DataGoKr key:  {'✓ loaded' if settings.datago.has_key else '✗ missing'}")
    print(f"Office:        ({settings.office.lat}, {settings.office.lng}) r={settings.office.search_radius_m}m")
    print(f"DB URL:        {settings.db.url}")
    print(f"API:           {settings.api.host}:{settings.api.port}")
