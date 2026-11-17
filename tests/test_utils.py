"""Проверки чтения JSON и безопасного логирования."""

import importlib
import json
import logging
import re
from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest

from src.utils import load_transactions


def test_load_transactions_reads_real_utf8_file(tmp_path: Path) -> None:
    """Прочитать реальный UTF-8 JSON без изменения операций."""
    expected: list[dict[str, Any]] = [{"id": 1, "description": "Перевод организации"}, {}]
    path = tmp_path / "operations.json"
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")

    assert load_transactions(path) == expected


@pytest.mark.parametrize("error", [FileNotFoundError, PermissionError, IsADirectoryError])
def test_load_transactions_returns_empty_on_file_error(error: type[OSError]) -> None:
    """Ошибки файловой системы не должны прерывать загрузку."""
    failed_open = Mock(side_effect=error("private-path"))
    with patch("src.utils.Path.open", failed_open):
        assert load_transactions("missing.json") == []
    failed_open.assert_called_once_with(encoding="utf-8")


@pytest.mark.parametrize("content", ["", " \n\t", "{broken", '[{"id": 1}'])
def test_load_transactions_returns_empty_for_malformed_json(content: str) -> None:
    """Пустой или синтаксически неверный JSON дает пустой список."""
    with patch("src.utils.Path.open", mock_open(read_data=content)):
        assert load_transactions("invalid.json") == []


@pytest.mark.parametrize("payload", [{}, None, True, 42, "transactions", [1], [{"id": 1}, None]])
def test_load_transactions_rejects_wrong_structure(payload: Any) -> None:
    """Принимать только список словарей, без частичной загрузки."""
    with patch("src.utils.Path.open", mock_open(read_data=json.dumps(payload))):
        assert load_transactions("wrong-structure.json") == []


def test_load_transactions_writes_safe_module_log(tmp_path: Path) -> None:
    """Писать успех и ошибки в отдельный файл, не раскрывая данные."""
    path = tmp_path / "sensitive-filename.json"
    path.write_text('[{"description": "private-transaction", "apikey": "private-key"}]', encoding="utf-8")
    assert load_transactions(path)
    assert load_transactions(tmp_path / "private-missing.json") == []
    path.write_text("null", encoding="utf-8")
    assert load_transactions(path) == []

    logger = logging.getLogger("src.utils")
    handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).name == "utils.log"
    ]
    assert len(handlers) == 1
    handler = handlers[0]
    handler.flush()
    assert logger.level == logging.DEBUG
    assert handler.mode == "w"
    assert Path(handler.baseFilename) == Path(__file__).resolve().parents[1] / "logs" / "utils.log"
    contents = Path(handler.baseFilename).read_text(encoding="utf-8")
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*src\.utils.*DEBUG", contents)
    assert "ERROR" in contents
    for secret in ("private-transaction", "private-key", "sensitive-filename", "private-missing"):
        assert secret not in contents


def test_reloading_utils_does_not_duplicate_or_truncate_log() -> None:
    """Повторный импорт сохраняет единственный handler и уже записанный лог."""
    import src.utils as utils

    logger = logging.getLogger("src.utils")
    with patch("src.utils.Path.open", mock_open(read_data="[]")):
        load_transactions("empty.json")
    handlers_before = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).name == "utils.log"
    ]
    assert len(handlers_before) == 1
    handler = handlers_before[0]
    logger.debug("reload-sentinel")
    handler.flush()
    importlib.reload(utils)
    handlers_after = [
        item
        for item in logger.handlers
        if isinstance(item, logging.FileHandler) and Path(item.baseFilename).name == "utils.log"
    ]
    assert handlers_after == handlers_before
    assert "reload-sentinel" in Path(handler.baseFilename).read_text(encoding="utf-8")


def test_load_transactions_rejects_invalid_utf8(tmp_path: Path) -> None:
    """Поврежденная кодировка обрабатывается как ошибка чтения."""
    path = tmp_path / "broken-encoding.json"
    path.write_bytes(b"\xff\xfeinvalid")
    assert load_transactions(path) == []


def test_load_transactions_reads_coursework_fixture() -> None:
    """Прочитать оригинальный учебный JSON из data без сетевых запросов."""
    path = Path(__file__).resolve().parents[1] / "data" / "operations.json"
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert expected
    assert load_transactions(str(path)) == expected


def test_load_transactions_accepts_empty_list() -> None:
    """Пустой список является корректным содержимым JSON."""
    with patch("src.utils.Path.open", mock_open(read_data="[]")):
        assert load_transactions("empty.json") == []
