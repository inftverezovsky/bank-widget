"""Получение рублевой суммы транзакции."""

import math
import os
from pathlib import Path
from typing import Any

import dotenv
import requests

API_URL = "https://api.apilayer.com/exchangerates_data/convert"
REQUEST_TIMEOUT = 10


def _finite_amount(value: object) -> float:
    """Преобразовать числовую сумму в конечный float, исключая bool."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Некорректная сумма")
    amount = float(value)
    if not math.isfinite(amount):
        raise ValueError("Сумма должна быть конечным числом")
    return amount


def get_transaction_amount(transaction: dict[str, Any]) -> float:
    """Вернуть сумму operationAmount в RUB как float.

    Рубли не требуют сети. Для USD/EUR используется текущий курс Exchange
    Rates Data API; EXCHANGE_RATE_API_KEY читается из окружения или .env.
    Неверная транзакция, валюта или отсутствующий ключ вызывают ValueError.
    Ошибки HTTP, таймаут и неверный ответ API вызывают RuntimeError.
    """
    try:
        operation_amount = transaction["operationAmount"]
        amount = _finite_amount(operation_amount["amount"])
        currency = operation_amount["currency"]["code"]
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValueError("Некорректные данные транзакции") from None

    if not isinstance(currency, str) or currency not in ("RUB", "USD", "EUR"):
        raise ValueError("Неподдерживаемая валюта транзакции")
    if currency == "RUB":
        return amount

    dotenv.load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError("Не задан EXCHANGE_RATE_API_KEY в .env или окружении")
    request_params: dict[str, str | float] = {"from": currency, "to": "RUB", "amount": amount}
    try:
        response = requests.get(
            API_URL,
            params=request_params,
            headers={"apikey": api_key},
            timeout=REQUEST_TIMEOUT,
        )
        try:
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise ValueError
            return _finite_amount(payload["result"])
        finally:
            response.close()
    except (requests.RequestException, KeyError, TypeError, ValueError, OverflowError):
        raise RuntimeError("Не удалось выполнить конвертацию валюты") from None
