"""Тесты функций модуля widget."""

import unittest

from src.widget import get_date, mask_account_card


class TestMaskAccountCard(unittest.TestCase):
    """Проверки маскировки карты и счета по одной входной строке."""

    def test_mask_card(self) -> None:
        """Название карты сохраняется, а номер маскируется как карта."""
        result = mask_account_card("Visa Platinum 7000792289606361")
        self.assertEqual(result, "Visa Platinum 7000 79** **** 6361")

    def test_mask_account(self) -> None:
        """Счет определяется по названию и маскируется отдельным способом."""
        result = mask_account_card("Счет 73654108430135874305")
        self.assertEqual(result, "Счет **4305")

    def test_all_examples(self) -> None:
        """Примеры из задания обрабатываются без ошибок."""
        cases = {
            "Maestro 1596837868705199": "Maestro 1596 83** **** 5199",
            "Счет 64686473678894779589": "Счет **9589",
            "MasterCard 7158300734726758": "MasterCard 7158 30** **** 6758",
            "Счет 35383033474447895560": "Счет **5560",
            "Visa Classic 6831982476737658": "Visa Classic 6831 98** **** 7658",
            "Visa Platinum 8990922113665229": "Visa Platinum 8990 92** **** 5229",
            "Visa Gold 5999414228426353": "Visa Gold 5999 41** **** 6353",
            "Счет 73654108430135874305": "Счет **4305",
        }

        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(mask_account_card(source), expected)

    def test_empty_input(self) -> None:
        """Пустой ввод отклоняется."""
        with self.assertRaises(ValueError):
            mask_account_card("")

    def test_input_without_number(self) -> None:
        """Строка без отдельного номера отклоняется."""
        with self.assertRaises(ValueError):
            mask_account_card("Maestro")

    def test_extra_text_after_number(self) -> None:
        """Лишняя подстрока после номера не принимается как корректный ввод."""
        with self.assertRaises(ValueError):
            mask_account_card("Visa Platinum 7000792289606361 extra")


class TestGetDate(unittest.TestCase):
    """Проверки преобразования даты."""

    def test_get_date(self) -> None:
        """Дата из примера преобразуется в ДД.ММ.ГГГГ."""
        result = get_date("2024-03-11T02:26:18.671407")
        self.assertEqual(result, "11.03.2024")

    def test_get_date_other_valid_iso(self) -> None:
        """Другие корректные ISO-строки также обрабатываются."""
        result = get_date("2025-12-01T23:59:59+03:00")
        self.assertEqual(result, "01.12.2025")

    def test_get_date_empty_input(self) -> None:
        """Пустая дата отклоняется."""
        with self.assertRaises(ValueError):
            get_date("")

    def test_get_date_invalid_iso(self) -> None:
        """Некорректная ISO-дата отклоняется."""
        with self.assertRaises(ValueError):
            get_date("11.03.2024")


if __name__ == "__main__":
    unittest.main()
