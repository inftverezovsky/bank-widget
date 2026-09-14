"""Тесты функций из модуля generators."""

from typing import Any

import pytest

from src.generators import (
    MAX_CARD_NUMBER,
    card_number_generator,
    filter_by_currency,
    transaction_descriptions,
)


@pytest.mark.parametrize(
    ("currency", "expected_ids"),
    [
        ("USD", [939719570, 142264268, 895315941]),
        ("RUB", [873106923, 594226727]),
        ("EUR", []),
    ],
)
def test_filter_by_currency(
    transactions: list[dict[str, Any]], currency: str, expected_ids: list[int]
) -> None:
    """Фильтр возвращает только транзакции в указанной валюте."""
    result = list(filter_by_currency(transactions, currency))

    assert [transaction["id"] for transaction in result] == expected_ids


def test_filter_by_currency_returns_iterator(transactions: list[dict[str, Any]]) -> None:
    """Функция возвращает итератор, из которого можно получать значения через next."""
    usd_transactions = filter_by_currency(transactions, "USD")

    first_transaction = next(usd_transactions)
    second_transaction = next(usd_transactions)

    assert first_transaction["id"] == 939719570
    assert second_transaction["id"] == 142264268


@pytest.mark.parametrize("source_transactions", [[], [{}]])
def test_filter_by_currency_without_matches(source_transactions: list[dict[str, Any]]) -> None:
    """Пустые и неполные входные данные не создают совпадений."""
    assert list(filter_by_currency(source_transactions, "USD")) == []


def test_filter_by_currency_skips_malformed_currency_data() -> None:
    """Записи с некорректной структурой данных валюты пропускаются."""
    source_transactions: list[dict[str, Any]] = [
        {"operationAmount": "wrong"},
        {"operationAmount": {"currency": "wrong"}},
        {"operationAmount": {"currency": {"code": "USD"}}, "id": 1},
    ]

    assert list(filter_by_currency(source_transactions, "USD")) == [source_transactions[2]]


def test_transaction_descriptions(transactions: list[dict[str, Any]]) -> None:
    """Генератор возвращает описания транзакций в исходном порядке."""
    assert list(transaction_descriptions(transactions)) == [
        "Перевод организации",
        "Перевод со счета на счет",
        "Перевод со счета на счет",
        "Перевод с карты на карту",
        "Перевод организации",
    ]


@pytest.mark.parametrize("source_transactions", [[], [{"id": 1}], [{"description": None}]])
def test_transaction_descriptions_empty_or_invalid(
    source_transactions: list[dict[str, Any]],
) -> None:
    """Пустой список и записи без строкового описания не дают значений."""
    assert list(transaction_descriptions(source_transactions)) == []


@pytest.mark.parametrize(
    ("start", "stop", "expected_numbers"),
    [
        (
            1,
            5,
            [
                "0000 0000 0000 0001",
                "0000 0000 0000 0002",
                "0000 0000 0000 0003",
                "0000 0000 0000 0004",
                "0000 0000 0000 0005",
            ],
        ),
        (9998, 10000, ["0000 0000 0000 9998", "0000 0000 0000 9999", "0000 0000 0001 0000"]),
        (MAX_CARD_NUMBER, MAX_CARD_NUMBER, ["9999 9999 9999 9999"]),
    ],
)
def test_card_number_generator(
    start: int, stop: int, expected_numbers: list[str]
) -> None:
    """Генератор формирует номера карт в правильном формате и диапазоне."""
    assert list(card_number_generator(start, stop)) == expected_numbers


def test_card_number_generator_empty_range() -> None:
    """Если start больше stop, генератор завершается без значений."""
    assert list(card_number_generator(5, 1)) == []


@pytest.mark.parametrize(
    ("start", "stop"),
    [
        (0, 5),
        (-1, 5),
        (1, MAX_CARD_NUMBER + 1),
    ],
)
def test_card_number_generator_invalid_bounds(start: int, stop: int) -> None:
    """Значения вне допустимого диапазона вызывают ValueError."""
    with pytest.raises(ValueError):
        list(card_number_generator(start, stop))
