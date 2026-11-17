"""Офлайн-тесты рублевых сумм и HTTP-конвертации валют."""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

from src.external_api import get_transaction_amount

INVALID_AMOUNTS: tuple[object, ...] = (None, True, {}, [], "not-a-number", "nan", "inf", float("-inf"), 10**1000)
INVALID_CURRENCIES: tuple[object, ...] = ("GBP", "", None, {}, [])


@pytest.fixture(autouse=True)
def offline_http() -> Iterator[Mock]:
    """Запретить реальный HTTP во всех тестах этого модуля."""
    with patch("requests.get", side_effect=AssertionError("Unexpected HTTP request")) as request:
        yield request


@pytest.mark.parametrize("amount", ["123.45", "0", 0, 987, 12.5])
def test_rub_amount_does_not_use_http_or_dotenv(amount: Any, offline_http: Mock) -> None:
    """Рубли возвращаются как float без сети и без API-ключа."""
    transaction = {"operationAmount": {"amount": amount, "currency": {"code": "RUB"}}}
    with patch("dotenv.load_dotenv") as load_env:
        result = get_transaction_amount(transaction)
    assert result == float(amount)
    assert isinstance(result, float)
    offline_http.assert_not_called()
    load_env.assert_not_called()


@pytest.mark.parametrize("currency", ["USD", "EUR"])
def test_foreign_amount_uses_conversion_endpoint(currency: str, offline_http: Mock) -> None:
    """Передать сумму, валюты и ключ в HTTP и прочитать рублевый result."""
    transaction = {"operationAmount": {"amount": "100.50", "currency": {"code": currency}}}
    response = Mock(spec=requests.Response)
    response.json.return_value = {"success": True, "result": 9876.5}
    offline_http.side_effect = None
    offline_http.return_value = response
    with patch.dict(os.environ, {"EXCHANGE_RATE_API_KEY": "test-only-not-a-real-api-key"}):
        with patch("dotenv.load_dotenv") as load_env:
            result = get_transaction_amount(transaction)
    assert result == 9876.5
    assert isinstance(result, float)
    offline_http.assert_called_once_with(
        "https://api.apilayer.com/exchangerates_data/convert",
        params={"from": currency, "to": "RUB", "amount": 100.5},
        headers={"apikey": "test-only-not-a-real-api-key"},
        timeout=10,
    )
    response.raise_for_status.assert_called_once_with()
    response.close.assert_called_once_with()
    load_env.assert_called_once_with(Path(__file__).resolve().parents[1] / ".env", override=False)


@pytest.mark.parametrize("api_key", [None, "", "   "])
def test_missing_key_stops_before_http(api_key: str | None, offline_http: Mock) -> None:
    """При отсутствии ключа выдавать понятную ошибку без запроса."""
    transaction = {"operationAmount": {"amount": "10", "currency": {"code": "USD"}}}
    environment = {} if api_key is None else {"EXCHANGE_RATE_API_KEY": api_key}
    with patch.dict(os.environ, environment, clear=True), patch("dotenv.load_dotenv"):
        with pytest.raises(ValueError, match="EXCHANGE_RATE_API_KEY"):
            get_transaction_amount(transaction)
    offline_http.assert_not_called()


@pytest.mark.parametrize(
    ("stage", "error"),
    [("request", requests.Timeout), ("request", requests.ConnectionError), ("status", requests.HTTPError)],
)
def test_http_errors_are_sanitized(stage: str, error: type[requests.RequestException], offline_http: Mock) -> None:
    """Таймауты, соединение и HTTP-ошибки не раскрывают ответ или ключ."""
    transaction = {"operationAmount": {"amount": "10", "currency": {"code": "EUR"}}}
    response = Mock(spec=requests.Response)
    failure = error("private-api-key private-response")
    offline_http.side_effect = failure if stage == "request" else None
    offline_http.return_value = response
    if stage == "status":
        response.raise_for_status.side_effect = failure
    with patch.dict(os.environ, {"EXCHANGE_RATE_API_KEY": "test-only-not-a-real-api-key"}):
        with patch("dotenv.load_dotenv"), pytest.raises(RuntimeError, match="конвертац") as caught:
            get_transaction_amount(transaction)
    assert "private" not in str(caught.value)
    assert caught.value.__suppress_context__
    response.json.assert_not_called()
    if stage == "status":
        response.close.assert_called_once_with()


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"success": False, "result": 100},
        {"success": 1, "result": 100},
        {"result": 100},
        {"success": True},
        {"success": True, "result": None},
        {"success": True, "result": True},
        {"success": True, "result": "private-invalid-result"},
        {"success": True, "result": "nan"},
        {"success": True, "result": "inf"},
        {"success": True, "result": {}},
    ],
)
def test_invalid_api_payload_is_rejected(payload: Any, offline_http: Mock) -> None:
    """Не подменять ошибку API или некорректный result денежной суммой."""
    transaction = {"operationAmount": {"amount": "10", "currency": {"code": "USD"}}}
    response = Mock(spec=requests.Response)
    response.json.return_value = payload
    offline_http.side_effect = None
    offline_http.return_value = response
    with patch.dict(os.environ, {"EXCHANGE_RATE_API_KEY": "test-only-not-a-real-api-key"}):
        with patch("dotenv.load_dotenv"), pytest.raises(RuntimeError, match="конвертац") as caught:
            get_transaction_amount(transaction)
    assert "private" not in str(caught.value)
    response.close.assert_called_once_with()


def test_invalid_api_json_is_rejected(offline_http: Mock) -> None:
    """Ответ, который нельзя разобрать как JSON, дает контролируемую ошибку."""
    transaction = {"operationAmount": {"amount": "10", "currency": {"code": "USD"}}}
    response = Mock(spec=requests.Response)
    response.json.side_effect = ValueError("private-response")
    offline_http.side_effect = None
    offline_http.return_value = response
    with patch.dict(os.environ, {"EXCHANGE_RATE_API_KEY": "test-only-not-a-real-api-key"}):
        with patch("dotenv.load_dotenv"), pytest.raises(RuntimeError, match="конвертац"):
            get_transaction_amount(transaction)
    response.close.assert_called_once_with()


@pytest.mark.parametrize(
    "transaction",
    [
        None,
        [],
        {},
        {"operationAmount": None},
        {"operationAmount": {}},
        {"operationAmount": {"amount": "10"}},
        {"operationAmount": {"amount": "10", "currency": None}},
        {"operationAmount": {"amount": "10", "currency": {}}},
        *[
            {"operationAmount": {"amount": amount, "currency": {"code": "RUB"}}}
            for amount in INVALID_AMOUNTS
        ],
        *[
            {"operationAmount": {"amount": "10", "currency": {"code": currency}}}
            for currency in INVALID_CURRENCIES
        ],
    ],
)
def test_invalid_transaction_fails_before_http(transaction: Any, offline_http: Mock) -> None:
    """Некорректная операция не должна уходить в сеть."""
    with patch("dotenv.load_dotenv") as load_env:
        with pytest.raises(ValueError, match="транзакц"):
            get_transaction_amount(transaction)
    offline_http.assert_not_called()
    load_env.assert_not_called()


@pytest.mark.parametrize("environment_key", [None, "test-only-process-key"])
def test_real_dotenv_loading_keeps_environment_priority(
    tmp_path: Path, environment_key: str | None, offline_http: Mock
) -> None:
    """Прочитать настоящий временный .env, не заменяя заданный ключ окружения."""
    (tmp_path / ".env").write_text("EXCHANGE_RATE_API_KEY=test-only-file-key\n", encoding="utf-8")
    transaction = {"operationAmount": {"amount": "0", "currency": {"code": "USD"}}}
    response = Mock(spec=requests.Response)
    response.json.return_value = {"success": True, "result": 0}
    offline_http.side_effect = None
    offline_http.return_value = response
    environment = {} if environment_key is None else {"EXCHANGE_RATE_API_KEY": environment_key}
    with patch.dict(os.environ, environment, clear=True):
        with patch("src.external_api.__file__", str(tmp_path / "src" / "external_api.py")):
            assert get_transaction_amount(transaction) == 0.0
    expected_key = environment_key or "test-only-file-key"
    assert offline_http.call_args.kwargs["headers"] == {"apikey": expected_key}
