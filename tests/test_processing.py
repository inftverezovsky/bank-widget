"""Тесты функций модуля processing."""

from typing import Any

import pytest

from src.processing import filter_by_state, sort_by_date


@pytest.mark.parametrize(
    ("state", "expected_ids"),
    [
        ("EXECUTED", [41428829, 939719570]),
        ("CANCELED", [594226727, 615064591]),
        ("PENDING", [100000001]),
        ("UNKNOWN", []),
    ],
)
def test_filter_by_state(
    operations: list[dict[str, Any]], state: str, expected_ids: list[int]
) -> None:
    """Проверить фильтрацию по разным значениям state."""
    result = filter_by_state(operations, state)
    assert [operation["id"] for operation in result] == expected_ids


def test_filter_by_state_default(operations: list[dict[str, Any]]) -> None:
    """Проверить значение EXECUTED по умолчанию."""
    result = filter_by_state(operations)
    assert [operation["id"] for operation in result] == [41428829, 939719570]
    assert result is not operations


@pytest.mark.parametrize(
    ("descending", "expected_ids"),
    [
        (True, [100000001, 41428829, 615064591, 594226727, 939719570]),
        (False, [939719570, 594226727, 615064591, 41428829, 100000001]),
    ],
)
def test_sort_by_date(
    operations: list[dict[str, Any]], descending: bool, expected_ids: list[int]
) -> None:
    """Проверить сортировку по убыванию и возрастанию даты."""
    original_ids = [operation["id"] for operation in operations]
    result = sort_by_date(operations, descending)

    assert [operation["id"] for operation in result] == expected_ids
    assert [operation["id"] for operation in operations] == original_ids
    assert result is not operations


def test_sort_by_date_same_dates(same_date_operations: list[dict[str, Any]]) -> None:
    """Проверить стабильный порядок операций с одинаковыми датами."""
    result = sort_by_date(same_date_operations)
    assert [operation["id"] for operation in result] == [1, 2]


def test_sort_by_date_nonstandard_date() -> None:
    """Проверить сортировку нестандартных строковых значений date."""
    operations = [
        {"id": 1, "state": "EXECUTED", "date": "2024-1-2"},
        {"id": 2, "state": "EXECUTED", "date": "2024-01-10"},
    ]

    result = sort_by_date(operations, descending=False)
    assert [operation["id"] for operation in result] == [2, 1]


def test_sort_by_date_missing_date() -> None:
    """Проверить исключение, если в операции отсутствует ключ date."""
    operations = [{"id": 1, "state": "EXECUTED"}]

    with pytest.raises(KeyError):
        sort_by_date(operations)
