"""Генераторы для последовательной обработки банковских транзакций."""

from collections.abc import Iterator
from typing import Any


MIN_CARD_NUMBER = 1
MAX_CARD_NUMBER = 9_999_999_999_999_999


def filter_by_currency(
    transactions: list[dict[str, Any]], currency: str
) -> Iterator[dict[str, Any]]:
    """Выдавать по очереди транзакции в указанной валюте.

    Args:
        transactions: Список словарей с банковскими транзакциями.
        currency: Код валюты, например ``USD`` или ``RUB``.

    Yields:
        Транзакции, у которых код валюты совпадает с ``currency``.
    """
    for transaction in transactions:
        operation_amount = transaction.get("operationAmount")
        if not isinstance(operation_amount, dict):
            continue

        currency_data = operation_amount.get("currency")
        if not isinstance(currency_data, dict):
            continue

        if currency_data.get("code") == currency:
            yield transaction


def transaction_descriptions(transactions: list[dict[str, Any]]) -> Iterator[str]:
    """Выдавать описания транзакций по одному.

    Args:
        transactions: Список словарей с банковскими транзакциями.

    Yields:
        Строковое описание очередной транзакции.
    """
    for transaction in transactions:
        description = transaction.get("description")
        if isinstance(description, str):
            yield description


def card_number_generator(start: int, stop: int) -> Iterator[str]:
    """Генерировать номера банковских карт в заданном диапазоне.

    Диапазон включает оба переданных значения.

    Args:
        start: Первый номер диапазона.
        stop: Последний номер диапазона.

    Yields:
        Номер карты в формате ``XXXX XXXX XXXX XXXX``.

    Raises:
        ValueError: Если границы выходят за допустимый диапазон номеров карт.
    """
    if start < MIN_CARD_NUMBER or stop > MAX_CARD_NUMBER:
        raise ValueError("Диапазон номера карты должен быть от 1 до 9999999999999999")

    for card_number in range(start, stop + 1):
        card_number_text = f"{card_number:016d}"
        yield " ".join(
            card_number_text[index : index + 4] for index in range(0, 16, 4)
        )
