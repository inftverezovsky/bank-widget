"""Тесты поиска в описаниях банковских операций."""

from typing import Any

from src.search import process_bank_operations, process_bank_search


def test_search_finds_substring_ignoring_case_without_changing_data() -> None:
    """Поиск сохраняет исходные словари и порядок совпадений."""
    transactions = [
        {"id": 1, "description": "Перевод организации"},
        {"id": 2, "description": "Открытие вклада"},
        {"id": 3, "description": "ПЕРЕВОД со счета на счет"},
    ]

    result = process_bank_search(transactions, "пЕрЕвОд")

    assert result == [transactions[0], transactions[2]]
    assert result is not transactions
    assert result[0] is transactions[0]
    assert len(transactions) == 3


def test_search_skips_missing_or_nontext_descriptions() -> None:
    """Пустые и поврежденные записи не прерывают поиск."""
    transactions: list[Any] = [{}, {"description": None}, {"description": float("nan")}, None, "bad"]
    match = {"description": "Перевод"}
    transactions.append(match)

    assert process_bank_search(transactions, "перевод") == [match]
    assert process_bank_search(transactions, "") == [match]


def test_search_treats_regexp_symbols_as_literal_characters() -> None:
    """Пользовательский текст не становится регулярным выражением."""
    transactions = [{"description": "Платеж [ЖКХ] (a+b).*"}, {"description": "Платеж ЖКХ"}]

    assert process_bank_search(transactions, "[жкх] (a+b).*") == [transactions[0]]
    assert process_bank_search(transactions, "[") == [transactions[0]]
    assert process_bank_search(transactions, "несуществующий") == []
    assert process_bank_search([], "перевод") == []


def test_operations_counts_exact_categories_including_zero() -> None:
    """Подсчет сохраняет запрошенные категории, включая отсутствующие."""
    transactions = [
        {"description": "Перевод организации"},
        {"description": "Открытие вклада"},
        {"description": "Перевод организации"},
        {"description": "Перевод организации срочно"},
        {"description": "перевод организации"},
    ]
    categories = ["Перевод организации", "Открытие вклада", "Отмена", "Перевод организации"]

    assert process_bank_operations(transactions, categories) == {
        "Перевод организации": 2,
        "Открытие вклада": 1,
        "Отмена": 0,
    }


def test_operations_ignores_invalid_descriptions() -> None:
    """Невалидные описания не превращаются в названия категорий."""
    transactions: list[Any] = [
        {},
        None,
        {"description": None},
        {"description": float("nan")},
        {"description": ["Перевод"]},
        {"description": "Перевод"},
    ]

    assert process_bank_operations(transactions, ["Перевод", "nan"]) == {"Перевод": 1, "nan": 0}
    assert process_bank_operations([], ["Перевод"]) == {"Перевод": 0}
    assert process_bank_operations(transactions, []) == {}
