"""Поиск и подсчет банковских операций по описанию."""

import re
from collections import Counter
from typing import Any


def process_bank_search(data: list[dict[str, Any]], search: str) -> list[dict[str, Any]]:
    """Вернуть операции с подстрокой в описании без учета регистра."""
    pattern = re.compile(re.escape(search), re.IGNORECASE)
    return [
        operation
        for operation in data
        if isinstance(operation, dict)
        and isinstance(operation.get("description"), str)
        and pattern.search(operation["description"])
    ]


def process_bank_operations(data: list[dict[str, Any]], categories: list[str]) -> dict[str, int]:
    """Подсчитать точные совпадения описаний, включая нули для отсутствующих категорий."""
    counts = Counter(
        operation["description"]
        for operation in data
        if isinstance(operation, dict) and isinstance(operation.get("description"), str)
    )
    return {category: counts[category] for category in categories}
