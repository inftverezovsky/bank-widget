"""Функции для маскировки реквизитов и работы с датой."""

from datetime import datetime

from src.masks import get_mask_account, get_mask_card_number


def mask_account_card(account_card_info: str) -> str:
    """Вернуть название карты или счета и замаскированный номер."""
    if not isinstance(account_card_info, str) or not account_card_info.strip():
        raise ValueError("Необходимо передать название карты или счета и номер")

    account_card_parts = account_card_info.strip().rsplit(maxsplit=1)
    if len(account_card_parts) != 2:
        raise ValueError("Строка должна содержать название карты или счета и номер")

    account_card_name, account_card_number = account_card_parts
    if not account_card_name.strip() or not account_card_number.isdigit():
        raise ValueError("Номер карты или счета должен состоять только из цифр")

    if account_card_name.casefold() == "счет":
        masked_number = get_mask_account(account_card_number)
    else:
        masked_number = get_mask_card_number(account_card_number)

    return f"{account_card_name} {masked_number}"


def get_date(date_string: str) -> str:
    """Преобразовать дату из ISO-формата в ДД.ММ.ГГГГ."""
    if not isinstance(date_string, str) or not date_string.strip():
        raise ValueError("Необходимо передать дату в ISO-формате")

    try:
        parsed_date = datetime.fromisoformat(date_string.strip())
    except ValueError as error:
        raise ValueError("Некорректная дата в ISO-формате") from error

    return parsed_date.strftime("%d.%m.%Y")
