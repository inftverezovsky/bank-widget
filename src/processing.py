"""Функции для работы со списком банковских операций."""

from typing import Any


def filter_by_state(
    operations: list[dict[str, Any]], state: str = "EXECUTED"
) -> list[dict[str, Any]]:
    """Вернуть новый список операций с указанным статусом.

    Args:
        operations: Список словарей с данными банковских операций.
        state: Статус операции для фильтрации. По умолчанию ``EXECUTED``.

    Returns:
        Новый список операций, у которых значение ключа ``state``
        совпадает с переданным статусом.
    """
    return [operation for operation in operations if operation.get("state") == state]


def sort_by_date(
    operations: list[dict[str, Any]], descending: bool = True
) -> list[dict[str, Any]]:
    """Вернуть новый список операций, отсортированный по дате.

    Args:
        operations: Список словарей с данными банковских операций.
        descending: Порядок сортировки. При ``True`` операции сортируются
            от новых к старым, при ``False`` — от старых к новым.

    Returns:
        Новый список операций, отсортированный по значению ключа ``date``.

    Raises:
        KeyError: Если хотя бы в одной операции отсутствует ключ ``date``.
    """
    return sorted(
        operations,
        key=lambda operation: str(operation["date"]),
        reverse=descending,
    )
