"""Функции для отображения банковских реквизитов и даты операции."""

from datetime import datetime

from src.masks import get_mask_account, get_mask_card_number


def mask_account_card(account_card_info: str) -> str:
    """Вернуть название карты/счета и замаскированный номер.

    Функция принимает одну строку целиком. Название может состоять из
    нескольких слов, поэтому отделение номера выполняется справа только
    по последнему пробелу.

    Примеры:
        Visa Platinum 7000792289606361 -> Visa Platinum 7000 79** **** 6361
        Счет 73654108430135874305 -> Счет **4305

    Raises:
        ValueError: Если строка пустая, не содержит название и номер
            либо номер содержит не только цифры.
    """
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
    """Преобразовать дату из ISO-формата в формат ``ДД.ММ.ГГГГ``.

    Пример:
        2024-03-11T02:26:18.671407 -> 11.03.2024

    Raises:
        ValueError: Если дата не передана или имеет некорректный ISO-формат.
    """
    if not isinstance(date_string, str) or not date_string.strip():
        raise ValueError("Необходимо передать дату в ISO-формате")

    try:
        parsed_date = datetime.fromisoformat(date_string.strip())
    except ValueError as error:
        raise ValueError("Некорректная дата в ISO-формате") from error

    return parsed_date.strftime("%d.%m.%Y")
