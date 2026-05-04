"""
nlp_mvp.shared.ollama_client 스모크 테스트.

실제 Ollama 서버를 필요로 하지 않도록 HTTP 계층을 mocking 한다.
서버 통합 테스트는 별도 `tests/integration/` 에 둘 수 있다 (향후).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nlp_mvp.shared.ollama_client import (
    DEFAULT_HOST,
    DEFAULT_MODEL,
    OllamaClient,
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
    get_default_client,
)


@pytest.fixture(autouse=True)
def _force_http_fallback(monkeypatch):
    """
    모든 테스트에서 SDK 경로 대신 HTTP fallback 을 강제한다.
    (SDK 설치 여부에 관계없이 동일 동작)
    """
    import nlp_mvp.shared.ollama_client as oc
    monkeypatch.setattr(oc, "_OLLAMA_SDK_AVAILABLE", False)
    yield


class TestInit:
    def test_defaults(self):
        client = OllamaClient()
        assert client.host == DEFAULT_HOST or client.host.startswith("http")
        assert client.model == DEFAULT_MODEL or client.model

    def test_overrides(self):
        client = OllamaClient(
            host="http://test:1234",
            model="my-model",
            timeout=5.0,
            max_retries=0,
        )
        assert client.host == "http://test:1234"
        assert client.model == "my-model"
        assert client.timeout == 5.0
        assert client.max_retries == 0


class TestChatHttp:
    def _mock_response(self, content: str, status: int = 200):
        mock = MagicMock()
        mock.status_code = status
        mock.ok = 200 <= status < 300
        mock.json.return_value = {"message": {"role": "assistant", "content": content}}
        mock.text = content
        return mock

    def test_successful_chat(self):
        client = OllamaClient(max_retries=0)
        with patch("requests.post") as mock_post:
            mock_post.return_value = self._mock_response("안녕하세요!")
            result = client.chat([{"role": "user", "content": "hi"}])
        assert result == "안녕하세요!"

    def test_model_not_found(self):
        client = OllamaClient(max_retries=0)
        with patch("requests.post") as mock_post:
            mock_post.return_value = self._mock_response("model not found", status=404)
            with pytest.raises(OllamaModelNotFoundError):
                client.chat([{"role": "user", "content": "hi"}])

    def test_http_error_raises_ollama_error(self):
        client = OllamaClient(max_retries=0)
        with patch("requests.post") as mock_post:
            mock_post.return_value = self._mock_response("server error", status=500)
            with pytest.raises(OllamaError):
                client.chat([{"role": "user", "content": "hi"}])

    def test_connection_error_retries(self):
        import requests
        client = OllamaClient(max_retries=1, retry_backoff=0.01)
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("boom")
            with pytest.raises(OllamaConnectionError):
                client.chat([{"role": "user", "content": "hi"}])
        # 초기 + 재시도 = 2회
        assert mock_post.call_count == 2

    def test_generate_wraps_chat(self):
        client = OllamaClient(max_retries=0)
        with patch("requests.post") as mock_post:
            mock_post.return_value = self._mock_response("response text")
            result = client.generate("prompt")
        assert result == "response text"


class TestPing:
    def test_ping_success(self):
        client = OllamaClient()
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, ok=True, json=lambda: {"models": []}
            )
            mock_get.return_value.raise_for_status = lambda: None
            assert client.ping() is True

    def test_ping_failure(self):
        client = OllamaClient()
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("connection refused")
            assert client.ping() is False


class TestAvailableModels:
    def test_parses_models(self):
        client = OllamaClient()
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.raise_for_status = lambda: None
            mock_resp.json.return_value = {
                "models": [{"name": "qwen2.5:7b"}, {"name": "gemma2:9b"}]
            }
            mock_get.return_value = mock_resp
            models = client.available_models()
        assert "qwen2.5:7b" in models
        assert "gemma2:9b" in models


class TestSingleton:
    def test_get_default_client_reuses(self):
        import nlp_mvp.shared.ollama_client as oc
        oc._default_client = None  # reset
        c1 = get_default_client()
        c2 = get_default_client()
        assert c1 is c2
