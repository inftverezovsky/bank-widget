"""Тесты функций модуля widget."""

from typing import Any

import pytest

from src.widget import get_date, mask_account_card


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Maestro 1596837868705199", "Maestro 1596 83** **** 5199"),
        ("MasterCard 7158300734726758", "MasterCard 7158 30** **** 6758"),
        ("Visa Platinum 8990922113665229", "Visa Platinum 8990 92** **** 5229"),
        ("Счет 73654108430135874305", "Счет **4305"),
        ("СЧЕТ 64686473678894779589", "СЧЕТ **9589"),
    ],
)
def test_mask_account_card(source: str, expected: str) -> None:
    """Проверить распознавание карт и счетов разных типов."""
    assert mask_account_card(source) == expected


@pytest.mark.parametrize(
    "invalid_value",
    ["", "   ", "Maestro", "Visa Platinum abc", "Visa 1234", "Счет 123", 123],
)
def test_mask_account_card_invalid_input(invalid_value: Any) -> None:
    """Проверить обработку некорректных входных данных."""
    with pytest.raises(ValueError):
        mask_account_card(invalid_value)


@pytest.mark.parametrize(
    ("date_string", "expected"),
    [
        ("2024-03-11T02:26:18.671407", "11.03.2024"),
        ("2025-12-01T23:59:59+03:00", "01.12.2025"),
        ("2000-01-01T00:00:00", "01.01.2000"),
        ("2024-02-29", "29.02.2024"),
    ],
)
def test_get_date(date_string: str, expected: str) -> None:
    """Проверить преобразование разных корректных ISO-дат."""
    assert get_date(date_string) == expected


@pytest.mark.parametrize("invalid_value", ["", "   ", "11.03.2024", "not-a-date", 123])
def test_get_date_invalid_input(invalid_value: Any) -> None:
    """Проверить обработку пустых и некорректных дат."""
    with pytest.raises(ValueError):
        get_date(invalid_value)
