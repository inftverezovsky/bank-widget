"""Functions for filtering and sorting banking operations."""

from typing import Any


def filter_by_state(
    operations: list[dict[str, Any]], state: str = "EXECUTED"
) -> list[dict[str, Any]]:
    """Return operations whose ``state`` value matches the requested state.

    Args:
        operations: Banking operations represented as dictionaries.
        state: Operation state to keep. Defaults to ``"EXECUTED"``.

    Returns:
        A new list containing only operations with the requested state.
    """
    return [operation for operation in operations if operation.get("state") == state]
