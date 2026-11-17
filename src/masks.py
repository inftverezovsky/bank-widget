"""Функции для маскировки банковских реквизитов."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_directory = Path(__file__).resolve().parents[1] / "logs"
log_directory.mkdir(parents=True, exist_ok=True)
log_path = log_directory / "masks.log"
# Повторная загрузка модуля не должна стирать журнал текущего процесса.
file_handler = next(
    (
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_path
    ),
    None,
)
if file_handler is None:
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    logger.addHandler(file_handler)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)


def get_mask_card_number(card_number: str) -> str:
    """Вернуть маску номера банковской карты.

    Отображаются первые 6 и последние 4 цифры номера карты.
    Ожидается строка длиной 16 символов.

    Пример:
        7000792289606361 -> 7000 79** **** 6361

    Raises:
        ValueError: Если длина номера карты не равна 16 символам.
    """
    logger.debug("get_mask_card_number: начало маскирования номера карты")
    try:
        if len(card_number) != 16:
            raise ValueError("Номер карты должен содержать ровно 16 символов")

        masked_number = f"{card_number[:4]} {card_number[4:6]}** **** {card_number[-4:]}"
    except (TypeError, ValueError):
        logger.error("get_mask_card_number: не удалось замаскировать номер карты")
        raise
    logger.info("get_mask_card_number: номер карты успешно замаскирован")
    return masked_number


def get_mask_account(account_number: str) -> str:
    """Вернуть маску номера банковского счета.

    Отображаются только последние 4 символа номера счета,
    перед которыми добавляются две звездочки.

    Пример:
        73654108430135874305 -> **4305

    Raises:
        ValueError: Если номер счета короче 4 символов.
    """
    logger.debug("get_mask_account: начало маскирования номера счета")
    try:
        if len(account_number) < 4:
            raise ValueError("Номер счета должен содержать не менее 4 символов")

        masked_number = f"**{account_number[-4:]}"
    except (TypeError, ValueError):
        logger.error("get_mask_account: не удалось замаскировать номер счета")
        raise
    logger.info("get_mask_account: номер счета успешно замаскирован")
    return masked_number
