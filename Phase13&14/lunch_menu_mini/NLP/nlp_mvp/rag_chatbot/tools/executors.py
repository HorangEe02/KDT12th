"""
Tool executors — thin HTTP wrappers around lunch-optimizer endpoints.

Each executor method maps 1:1 to a tool in `definitions.py`. Errors are
caught and returned as dicts so the chat loop can surface them to the LLM
without crashing.
"""
from __future__ import annotations

import os
from typing import Any, Callable

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


DEFAULT_LUNCH_API = os.getenv("LUNCH_API_BASE", "http://localhost:8000/api")
HTTP_TIMEOUT = 10.0


class ToolExecutionError(RuntimeError):
    """Raised when a tool cannot be executed."""


class ToolExecutor:
    """
    Executes the 8 Mini tool functions against the lunch-optimizer API.

    Construction:
        executor = ToolExecutor(base_url="http://lunch-api:8000/api")
        result = executor.execute("get_current_weather", {})
    """

    def __init__(
        self,
        base_url: str = DEFAULT_LUNCH_API,
        http_get: Callable | None = None,
        http_post: Callable | None = None,
        http_patch: Callable | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        # Injectable transport — tests pass mocks, production uses requests
        self._http_get = http_get
        self._http_post = http_post
        self._http_patch = http_patch

    # -------------------------------------------------------------------------
    # Dispatch
    # -------------------------------------------------------------------------
    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a tool call by name; returns `{ok, data|error, tool}` dict."""
        method = getattr(self, f"tool_{name}", None)
        if method is None:
            return {
                "ok": False,
                "tool": name,
                "error": f"unknown tool: {name}",
            }
        try:
            data = method(**(args or {}))
            return {"ok": True, "tool": name, "data": data}
        except ToolExecutionError as e:
            return {"ok": False, "tool": name, "error": str(e)}
        except TypeError as e:
            # Usually: missing required kwarg or wrong type
            return {
                "ok": False,
                "tool": name,
                "error": f"invalid arguments: {e}",
            }
        except Exception as e:
            logger.exception(f"tool {name} failed: {e}")
            return {"ok": False, "tool": name, "error": str(e)}

    # -------------------------------------------------------------------------
    # HTTP helpers (lazy requests import for optional dep)
    # -------------------------------------------------------------------------
    def _get(self, path: str, params: dict | None = None) -> Any:
        if self._http_get is not None:
            return self._http_get(path, params)
        import requests
        url = f"{self.base_url}{path}"
        r = requests.get(url, params=params or {}, timeout=HTTP_TIMEOUT)
        if not r.ok:
            raise ToolExecutionError(f"GET {path} → {r.status_code}: {r.text[:120]}")
        return r.json()

    def _post(self, path: str, body: dict | None = None) -> Any:
        if self._http_post is not None:
            return self._http_post(path, body)
        import requests
        url = f"{self.base_url}{path}"
        r = requests.post(url, json=body or {}, timeout=HTTP_TIMEOUT)
        if not r.ok:
            raise ToolExecutionError(f"POST {path} → {r.status_code}: {r.text[:120]}")
        return r.json()

    def _patch(self, path: str, body: dict | None = None) -> Any:
        if self._http_patch is not None:
            return self._http_patch(path, body)
        import requests
        url = f"{self.base_url}{path}"
        r = requests.patch(url, json=body or {}, timeout=HTTP_TIMEOUT)
        if not r.ok:
            raise ToolExecutionError(f"PATCH {path} → {r.status_code}: {r.text[:120]}")
        return r.json()

    # =========================================================================
    # Tool implementations — one method per entry in definitions.TOOL_DEFINITIONS
    # =========================================================================
    def tool_get_lunch_recommendations(
        self,
        team_id: str = "team1",
        user_id: str = "user1",
        top_n: int = 5,
    ) -> Any:
        return self._get(
            "/recommend",
            {"team_id": team_id, "user_id": user_id, "top_n": int(top_n)},
        )

    def tool_get_current_weather(self) -> Any:
        return self._get("/weather/current")

    def tool_get_nutrition_diagnosis(self, user_id: str = "user1") -> Any:
        return self._get("/nutrition/diagnosis", {"user_id": user_id})

    def tool_get_restaurant_info(self, restaurant_id: str) -> Any:
        if not restaurant_id:
            raise ToolExecutionError("restaurant_id is required")
        basic = self._get(f"/restaurants/{restaurant_id}")
        # Best-effort enrichment with nutrition if available
        try:
            nut = self._get(f"/nutrition/restaurant/{restaurant_id}")
            basic["nutrition"] = nut
        except ToolExecutionError:
            basic["nutrition"] = None
        return basic

    def tool_cast_vote(self, user_id: str, restaurant_id: str) -> Any:
        if not user_id or not restaurant_id:
            raise ToolExecutionError("user_id and restaurant_id are required")
        return self._post(
            "/vote/cast",
            {"user_id": user_id, "restaurant_id": restaurant_id},
        )

    def tool_get_vote_status(self, team_id: str = "team1") -> Any:
        return self._get("/vote/status", {"team_id": team_id})

    def tool_record_meal(
        self,
        user_id: str,
        restaurant_id: str,
        menu_name: str | None = None,
        satisfaction: int | None = None,
    ) -> Any:
        if not user_id or not restaurant_id:
            raise ToolExecutionError("user_id and restaurant_id are required")
        body: dict[str, Any] = {
            "user_id": user_id,
            "restaurant_id": restaurant_id,
        }
        if menu_name is not None:
            body["menu_name"] = menu_name
        if satisfaction is not None:
            body["satisfaction"] = int(satisfaction)
        return self._post("/nutrition/meal", body)

    def tool_get_visit_history(
        self, team_id: str = "team1", days: int = 10
    ) -> Any:
        return self._get(
            "/history/visits", {"team_id": team_id, "days": int(days)}
        )


__all__ = ["ToolExecutor", "ToolExecutionError"]
