"""Консольная программа для работы с банковскими транзакциями."""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.file_readers import read_csv_transactions, read_excel_transactions
from src.processing import filter_by_state, sort_by_date
from src.search import process_bank_search
from src.utils import load_transactions
from src.widget import get_date, mask_account_card

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _ask_yes_no(prompt: str) -> bool:
    """Повторять вопрос до получения однозначного согласия или отказа."""
    while True:
        answer = input(prompt).strip().casefold()
        if answer in {"да", "yes"}:
            return True
        if answer in {"нет", "no"}:
            return False
        print("Введите Да или Нет.")


def _ask_descending() -> bool:
    """Запросить направление сортировки с проверкой пользовательского ввода."""
    while True:
        answer = input("Отсортировать по возрастанию или по убыванию? ").strip().casefold()
        if answer in {"по возрастанию", "возрастанию", "возрастание"}:
            return False
        if answer in {"по убыванию", "убыванию", "убывание"}:
            return True
        print("Введите по возрастанию или по убыванию.")


def _ask_state() -> str:
    """Получить один из разрешенных статусов независимо от регистра ввода."""
    while True:
        entered_state = input(
            "Введите статус, по которому необходимо выполнить фильтрацию.\n"
            "Доступные для фильтровки статусы: EXECUTED, CANCELED, PENDING\n"
        ).strip()
        state = entered_state.upper()
        if state in {"EXECUTED", "CANCELED", "PENDING"}:
            return state
        print(f'Статус операции "{entered_state}" недоступен.')


def _text(value: object) -> str:
    """Вернуть текстовое значение, не превращая None и NaN в строки."""
    text = value.strip() if isinstance(value, str) else ""
    return "" if text.casefold() in {"nan", "nat"} else text


def _hide_long_numbers(text: str) -> str:
    """Скрыть длинные номера, ошибочно попавшие в описание или название карты."""
    return re.sub(r"\d(?:[\s-]*\d){11,}", "****", text)


def _prepare_operations(data: object) -> list[dict[str, Any]]:
    """Скопировать записи с безопасными строками для фильтрации и сортировки."""
    if not isinstance(data, list):
        return []
    operations = []
    for item in data:
        if not isinstance(item, dict) or not item:
            continue
        operation = item.copy()
        operation["state"] = _text(item.get("state")).upper()
        operation["date"] = _text(item.get("date"))
        operation["description"] = _text(item.get("description")) or "Без описания"
        operations.append(operation)
    return operations


def _amount_and_currency(operation: dict[str, Any]) -> tuple[str, str]:
    """Извлечь исходную сумму и код валюты без сетевой конвертации."""
    details = operation.get("operationAmount")
    if isinstance(details, dict):
        currency = details.get("currency")
        currency = currency if isinstance(currency, dict) else {}
        code = _text(currency.get("code")).upper()
        value = details.get("amount")
    else:
        code = _text(operation.get("currency_code")).upper()
        value = operation.get("amount")
    if len(code) != 3 or not code.isascii() or not code.isalpha():
        code = ""
    amount = "не указана"
    if isinstance(value, (str, int, float, Decimal)) and not isinstance(value, bool):
        try:
            if Decimal(str(value)).is_finite():
                amount = str(value).strip()
        except InvalidOperation:
            pass
    return amount, code


def _masked_details(value: object) -> str:
    """Скрыть реквизиты, не раскрывая исходную строку при ошибке маскировки."""
    text = _text(value)
    if not text:
        return "Реквизиты не указаны"
    try:
        return _hide_long_numbers(mask_account_card(text))
    except ValueError:
        return "Реквизиты скрыты"


def _print_operation(operation: dict[str, Any]) -> None:
    """Распечатать одну операцию, в том числе вклад без отправителя."""
    try:
        date = get_date(operation["date"])
    except ValueError:
        date = "Дата не указана"
    print(f"\n{date} {_hide_long_numbers(operation['description'])}")
    recipient = _masked_details(operation.get("to"))
    if _text(operation.get("from")):
        print(f"{_masked_details(operation['from'])} -> {recipient}")
    else:
        print(recipient)
    amount, currency = _amount_and_currency(operation)
    currency = "руб." if currency == "RUB" else currency or "валюта не указана"
    print(f"Сумма: {amount} {currency}")


def main() -> None:
    """Запустить диалог выбора и отображения банковских операций."""
    print("Привет! Добро пожаловать в программу работы с банковскими транзакциями.")
    print(
        "Выберите необходимый пункт меню:\n"
        "1. Получить информацию о транзакциях из JSON-файла\n"
        "2. Получить информацию о транзакциях из CSV-файла\n"
        "3. Получить информацию о транзакциях из XLSX-файла"
    )
    sources = {
        "1": ("JSON", "operations.json", load_transactions),
        "2": ("CSV", "transactions.csv", read_csv_transactions),
        "3": ("XLSX", "transactions_excel.xlsx", read_excel_transactions),
    }
    while True:
        choice = input("Ваш выбор: ").strip()
        if choice in sources:
            break
        print("Выберите пункт 1, 2 или 3.")
    format_name, filename, reader = sources[choice]
    try:
        operations = _prepare_operations(reader(DATA_DIR / filename))
    except (OSError, ValueError, ImportError):
        print("Не удалось прочитать файл транзакций. Проверьте файл и установленные зависимости.")
        return
    print(f"Для обработки выбран {format_name}-файл.")
    state = _ask_state()
    operations = filter_by_state(operations, state)
    print(f'Операции отфильтрованы по статусу "{state}"')
    if _ask_yes_no("Отсортировать операции по дате? Да/Нет: "):
        operations = sort_by_date(operations, descending=_ask_descending())
    if _ask_yes_no("Выводить только рублевые транзакции? Да/Нет: "):
        operations = [operation for operation in operations if _amount_and_currency(operation)[1] == "RUB"]
    if _ask_yes_no("Отфильтровать список транзакций по определенному слову в описании? Да/Нет: "):
        operations = process_bank_search(operations, input("Введите слово для поиска: ").strip())
    print("Распечатываю итоговый список транзакций...")
    if not operations:
        print("Не найдено ни одной транзакции, подходящей под ваши условия фильтрации.")
        return
    print(f"Всего банковских операций в выборке: {len(operations)}")
    for operation in operations:
        _print_operation(operation)


if __name__ == "__main__":
    main()
