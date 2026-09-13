"""Тесты функций модуля masks."""

import pytest

from src.masks import get_mask_account, get_mask_card_number


def test_get_mask_card_number(card_number: str) -> None:
    """Проверить обычное маскирование номера карты."""
    assert get_mask_card_number(card_number) == "7000 79** **** 6361"


@pytest.mark.parametrize(
    ("card_number", "expected"),
    [
        ("1596837868705199", "1596 83** **** 5199"),
        ("0000000000000000", "0000 00** **** 0000"),
        ("9999999999999999", "9999 99** **** 9999"),
    ],
)
def test_get_mask_card_number_different_values(card_number: str, expected: str) -> None:
    """Проверить несколько корректных номеров карт."""
    assert get_mask_card_number(card_number) == expected


@pytest.mark.parametrize(
    "card_number",
    ["", "1234", "700079228960636", "70007922896063611"],
)
def test_get_mask_card_number_invalid_length(card_number: str) -> None:
    """Проверить ошибку при пустом или некорректном номере карты."""
    with pytest.raises(ValueError):
        get_mask_card_number(card_number)


def test_get_mask_account(account_number: str) -> None:
    """Проверить обычное маскирование номера счета."""
    assert get_mask_account(account_number) == "**4305"


@pytest.mark.parametrize(
    ("account_number", "expected"),
    [
        ("4305", "**4305"),
        ("64686473678894779589", "**9589"),
        ("00000000", "**0000"),
    ],
)
def test_get_mask_account_different_lengths(account_number: str, expected: str) -> None:
    """Проверить счета различной допустимой длины."""
    assert get_mask_account(account_number) == expected


@pytest.mark.parametrize("account_number", ["", "1", "12", "123"])
def test_get_mask_account_too_short(account_number: str) -> None:
    """Проверить ошибку для слишком короткого счета."""
    with pytest.raises(ValueError):
        get_mask_account(account_number)
