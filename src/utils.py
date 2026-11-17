"""Загрузка финансовых транзакций из JSON."""

import json
import logging
from pathlib import Path
from typing import Any, cast

LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "utils.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
file_handler = next(
    (
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == LOG_PATH
    ),
    None,
)
if file_handler is None:
    file_handler = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
    logger.addHandler(file_handler)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)


def load_transactions(path: str | Path) -> list[dict[str, Any]]:
    """Прочитать UTF-8 JSON со списком словарей транзакций.

    Отсутствующий, нечитаемый, поврежденный файл или неверная структура
    дают пустой список. Содержимое операций и пути в лог не попадают.
    """
    try:
        with Path(path).open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        logger.error("Не удалось прочитать JSON-файл: %s", type(error).__name__)
        return []

    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        logger.error("JSON должен содержать список словарей")
        return []
    logger.debug("JSON-файл успешно прочитан; количество операций: %d", len(data))
    return cast(list[dict[str, Any]], data)
