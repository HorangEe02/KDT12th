"""
표준 메뉴 로딩 추상 + 3종 구현체.

- SyntheticMenuLoader: 합성 100건 (테스트용)
- NutritionDBLoader:   Mini nutrition_info 테이블 (실제)
- FileMenuLoader:      CSV/JSON 파일
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from sqlalchemy import text

from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


class StandardMenuLoader(ABC):
    """표준 메뉴 로딩 추상."""

    @abstractmethod
    def load(self) -> list[dict[str, Any]]:
        """
        Returns:
            [{"id": "kimchi_jjigae", "name": "김치찌개", "category": "한식"}, ...]
        """


class SyntheticMenuLoader(StandardMenuLoader):
    """§14.A 부록의 합성 100건."""

    def load(self) -> list[dict[str, Any]]:
        from nlp_mvp.menu_normalizer._synthetic_menus import SYNTHETIC_STANDARD_MENUS
        logger.info(f"Loaded {len(SYNTHETIC_STANDARD_MENUS)} synthetic menus")
        return list(SYNTHETIC_STANDARD_MENUS)


class NutritionDBLoader(StandardMenuLoader):
    """Mini nutrition_info 테이블 (또는 동등 테이블)."""

    def __init__(
        self,
        table: str = "nutrition_info",
        id_col: str = "id",
        name_col: str = "food_name",
    ):
        self.table = table
        self.id_col = id_col
        self.name_col = name_col

    def load(self) -> list[dict[str, Any]]:
        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(
                    text(f"SELECT {self.id_col}, {self.name_col} FROM {self.table}")
                ).fetchall()
            menus = [{"id": str(r[0]), "name": r[1]} for r in rows if r[1]]
            logger.info(f"Loaded {len(menus)} menus from {self.table}")
            return menus
        except Exception as e:
            logger.warning(f"Failed to load from {self.table}: {e}")
            return []


class FileMenuLoader(StandardMenuLoader):
    """CSV/JSON 파일 로더."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            logger.warning(f"File not found: {self.path}")
            return []

        if self.path.suffix == ".csv":
            import csv
            with open(self.path, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            logger.info(f"Loaded {len(rows)} rows from {self.path}")
            return rows
        elif self.path.suffix == ".json":
            import json
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} entries from {self.path}")
            return data
        else:
            raise ValueError(f"Unsupported format: {self.path.suffix}")
