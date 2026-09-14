"""Общие фикстуры для тестов проекта."""

from typing import Any

import pytest


@pytest.fixture
def card_number() -> str:
    """Вернуть корректный номер карты для тестов."""
    return "7000792289606361"


@pytest.fixture
def account_number() -> str:
    """Вернуть корректный номер счета для тестов."""
    return "73654108430135874305"


@pytest.fixture
def operations() -> list[dict[str, Any]]:
    """Вернуть набор операций с разными статусами и датами."""
    return [
        {"id": 41428829, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
        {"id": 939719570, "state": "EXECUTED", "date": "2018-06-30T02:08:58.425572"},
        {"id": 594226727, "state": "CANCELED", "date": "2018-09-12T21:27:25.241689"},
        {"id": 615064591, "state": "CANCELED", "date": "2018-10-14T08:21:33.419441"},
        {"id": 100000001, "state": "PENDING", "date": "2020-01-01T00:00:00"},
    ]


@pytest.fixture
def same_date_operations() -> list[dict[str, Any]]:
    """Вернуть операции с одинаковыми датами."""
    return [
        {"id": 1, "state": "EXECUTED", "date": "2024-01-01T12:00:00"},
        {"id": 2, "state": "CANCELED", "date": "2024-01-01T12:00:00"},
    ]
