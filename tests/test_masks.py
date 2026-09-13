"""Тесты функций маскировки банковских реквизитов."""

import unittest

from src.masks import get_mask_account, get_mask_card_number


class TestMasks(unittest.TestCase):
    """Проверки функций модуля masks."""

    def test_get_mask_card_number(self) -> None:
        """Номер карты из 16 символов маскируется по заданному формату."""
        result = get_mask_card_number("7000792289606361")
        self.assertEqual(result, "7000 79** **** 6361")

    def test_get_mask_card_number_invalid_length(self) -> None:
        """Номер карты длиной не 16 символов вызывает ошибку."""
        with self.assertRaises(ValueError):
            get_mask_card_number("700079228960636")

    def test_get_mask_account(self) -> None:
        """У номера счета остаются видимыми только последние 4 символа."""
        result = get_mask_account("73654108430135874305")
        self.assertEqual(result, "**4305")

    def test_get_mask_account_minimum_length(self) -> None:
        """Строка счета длиной 4 символа также обрабатывается корректно."""
        result = get_mask_account("4305")
        self.assertEqual(result, "**4305")

    def test_get_mask_account_too_short(self) -> None:
        """Номер счета короче 4 символов вызывает ошибку."""
        with self.assertRaises(ValueError):
            get_mask_account("305")


if __name__ == "__main__":
    unittest.main()
