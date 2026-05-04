"""nlp_mvp.shared.logger 스모크 테스트."""
from __future__ import annotations

import logging

import pytest

from nlp_mvp.shared import logger as log_module
from nlp_mvp.shared.logger import (
    ROOT_LOGGER_NAME,
    configure,
    get_logger,
    set_level,
)


@pytest.fixture(autouse=True)
def _reset_logger_state():
    """각 테스트마다 로거 상태 초기화."""
    log_module._configured = False
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.handlers.clear()
    yield
    log_module._configured = False
    root.handlers.clear()


class TestConfigure:
    def test_first_call_sets_up_handlers(self):
        configure(level="DEBUG", log_file="none", console=True)
        root = logging.getLogger(ROOT_LOGGER_NAME)
        assert root.level == logging.DEBUG
        assert len(root.handlers) >= 1  # 최소 콘솔 핸들러

    def test_idempotent_without_force(self):
        configure(log_file="none")
        handlers_count = len(logging.getLogger(ROOT_LOGGER_NAME).handlers)
        configure(log_file="none")  # 재호출
        assert len(logging.getLogger(ROOT_LOGGER_NAME).handlers) == handlers_count

    def test_force_resets_handlers(self):
        configure(log_file="none")
        configure(log_file="none", force=True)
        root = logging.getLogger(ROOT_LOGGER_NAME)
        assert len(root.handlers) >= 1

    def test_file_handler_created(self, tmp_path):
        log_file = tmp_path / "test.log"
        configure(level="INFO", log_file=str(log_file), console=False)
        logger = get_logger(__name__)
        logger.info("hello from test")
        # flush
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        assert log_file.exists()
        assert "hello from test" in log_file.read_text(encoding="utf-8")

    def test_none_log_file_disables_file_handler(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LOG_FILE", raising=False)
        configure(log_file="none", console=True)
        handlers = logging.getLogger(ROOT_LOGGER_NAME).handlers
        from logging.handlers import RotatingFileHandler
        assert not any(isinstance(h, RotatingFileHandler) for h in handlers)


class TestGetLogger:
    def test_none_returns_root(self):
        logger = get_logger(None)
        assert logger.name == ROOT_LOGGER_NAME

    def test_module_name_namespaced(self):
        logger = get_logger("nlp_mvp.sentiment.crawler")
        assert logger.name == "nlp_mvp.sentiment.crawler"

    def test_external_name_prefixed(self):
        logger = get_logger("custom_module")
        assert logger.name == "nlp_mvp.custom_module"


class TestSetLevel:
    def test_changes_root_level(self):
        configure(level="INFO", log_file="none")
        set_level("DEBUG")
        assert logging.getLogger(ROOT_LOGGER_NAME).level == logging.DEBUG

    def test_invalid_level_falls_back_to_info(self):
        configure(level="INFO", log_file="none")
        set_level("NONSENSE")
        assert logging.getLogger(ROOT_LOGGER_NAME).level == logging.INFO
