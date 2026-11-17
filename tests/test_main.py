"""Проверки настоящего консольного диалога с изолированным чтением файлов."""

import runpy
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

import src.main as app

ROOT = Path(__file__).resolve().parents[1]


def transaction(**changes: Any) -> dict[str, Any]:
    """Создать синтетическую JSON-операцию для проверки интерфейса."""
    operation: dict[str, Any] = {
        "id": 1,
        "state": "EXECUTED",
        "date": "2019-07-03T18:35:29.512364",
        "description": "Перевод организации",
        "operationAmount": {"amount": "100.50", "currency": {"code": "RUB", "name": "руб."}},
        "from": "Visa Classic 7000792289606361",
        "to": "Счет 73654108430135874305",
    }
    operation.update(changes)
    return operation


def run_dialog(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    answers: list[str],
    data: Any,
    reader_name: str = "load_transactions",
) -> tuple[str, Mock]:
    """Запустить настоящий main, заменив только ввод и чтение исходного файла."""
    reader = Mock(return_value=data)
    user_input = Mock(side_effect=answers)
    for name in ("load_transactions", "read_csv_transactions", "read_excel_transactions"):
        if name != reader_name:
            monkeypatch.setattr(app, name, Mock(side_effect=AssertionError(f"Не выбранный источник: {name}")))
    monkeypatch.setattr(app, reader_name, reader)
    monkeypatch.setattr("builtins.input", user_input)

    app.main()

    assert user_input.call_count == len(answers)
    return capsys.readouterr().out, reader


def test_main_json_displays_filtered_masked_operations(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Обычный JSON-сценарий вызывает реальный фильтр и маскирует реквизиты."""
    data = [transaction(), transaction(state="CANCELED", description="Отмененная операция")]
    text, reader = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "нет", "нет", "нет"], data)

    reader.assert_called_once_with(ROOT / "data" / "operations.json")
    assert "Добро пожаловать" in text
    assert "Для обработки выбран JSON-файл." in text
    assert 'Операции отфильтрованы по статусу "EXECUTED"' in text
    assert "Всего банковских операций в выборке: 1" in text
    assert "03.07.2019 Перевод организации" in text
    assert "Visa Classic 7000 79** **** 6361 -> Счет **4305" in text
    assert "Сумма: 100.50 руб." in text
    assert "Отмененная операция" not in text
    assert "7000792289606361" not in text
    assert "73654108430135874305" not in text


def test_main_retries_invalid_status_and_strips_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Неизвестный и пустой статусы повторяют запрос без потери данных."""
    answers = ["1", "test", "", " eXeCuTeD ", "нет", "нет", "нет"]
    text, _ = run_dialog(monkeypatch, capsys, answers, [transaction()])

    assert 'Статус операции "test" недоступен.' in text
    assert 'Статус операции "" недоступен.' in text
    assert 'Операции отфильтрованы по статусу "EXECUTED"' in text
    assert "Всего банковских операций в выборке: 1" in text


@pytest.mark.parametrize("state", ["executed", "Executed", "EXECUTED", "cAnCeLeD", "pending"])
def test_main_supports_every_status_case_insensitively(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], state: str
) -> None:
    """Каждый разрешенный статус выбирается независимо от регистра ввода."""
    data = [transaction(state=value, description=f"Операция {value}") for value in ("EXECUTED", "CANCELED", "PENDING")]
    text, _ = run_dialog(monkeypatch, capsys, ["1", state, "нет", "нет", "нет"], data)

    assert f'Операции отфильтрованы по статусу "{state.upper()}"' in text
    assert f"03.07.2019 Операция {state.upper()}" in text
    assert "Всего банковских операций в выборке: 1" in text


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        ("по возрастанию", ["Первая", "Средняя", "Последняя"]),
        ("возрастание", ["Первая", "Средняя", "Последняя"]),
        ("ПО УБЫВАНИЮ", ["Последняя", "Средняя", "Первая"]),
        ("убывание", ["Последняя", "Средняя", "Первая"]),
    ],
)
def test_main_sorts_dates_in_both_directions(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], direction: str, expected: list[str]
) -> None:
    """Даты сортируются реальной функцией processing, а не порядком загрузки."""
    data = [
        transaction(date="2020-01-01T00:00:00Z", description="Последняя"),
        transaction(date="2018-01-01T00:00:00Z", description="Первая"),
        transaction(date="2019-01-01T00:00:00Z", description="Средняя"),
    ]
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", " Да ", direction, "нет", "нет"], data)

    positions = [text.index(description) for description in expected]
    assert positions == sorted(positions)
    assert [operation["description"] for operation in data] == ["Последняя", "Первая", "Средняя"]


def test_main_retries_invalid_yes_no_and_sort_direction(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ошибочные ответы на дополнительные вопросы не принимаются за отказ."""
    answers = ["1", "EXECUTED", "может быть", "yes", "как-нибудь", "по возрастанию", "", "no", "нет"]
    text, _ = run_dialog(monkeypatch, capsys, answers, [transaction()])

    assert text.count("Введите Да или Нет.") == 2
    assert "Введите по возрастанию или по убыванию." in text
    assert "Всего банковских операций в выборке: 1" in text


def test_main_combines_rubles_and_literal_description_search(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Два дополнительных фильтра применяются последовательно к текущей выборке."""
    data = [
        transaction(description="Открытие [вклада]"),
        transaction(description="Открытие вклада"),
        transaction(
            description="Валютный [вклад]",
            operationAmount={"amount": "130", "currency": {"code": "USD"}},
        ),
    ]
    answers = ["1", "EXECUTED", "нет", "да", "ДА", "[ВКЛАД"]
    text, _ = run_dialog(monkeypatch, capsys, answers, data)

    assert "Всего банковских операций в выборке: 1" in text
    assert "03.07.2019 Открытие [вклада]" in text
    assert "03.07.2019 Открытие вклада" not in text
    assert "Валютный [вклад]" not in text


@pytest.mark.parametrize(
    ("data", "answers"),
    [
        ([], ["1", "EXECUTED", "нет", "нет", "нет"]),
        ([transaction()], ["1", "CANCELED", "нет", "нет", "нет"]),
        ([transaction()], ["1", "EXECUTED", "нет", "нет", "да", "несуществующая категория"]),
        (
            [transaction(operationAmount={"amount": "130", "currency": {"code": "USD"}})],
            ["1", "EXECUTED", "нет", "да", "нет"],
        ),
    ],
    ids=["empty-source", "state-filter", "search-filter", "currency-filter"],
)
def test_main_reports_empty_selection(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], data: list[dict[str, Any]], answers: list[str]
) -> None:
    """Пустой исходный список и пустые результаты фильтров имеют понятный вывод."""
    text, _ = run_dialog(monkeypatch, capsys, answers, data)

    assert "Не найдено ни одной транзакции, подходящей под ваши условия фильтрации" in text
    assert "Сумма:" not in text


def test_main_keeps_original_foreign_currency_without_network(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Консольный просмотр не зависит от ключей и внешнего API валют."""
    network = Mock(side_effect=AssertionError("Просмотр не должен обращаться к сети"))
    monkeypatch.setattr("socket.socket.connect", network)
    data = [transaction(operationAmount={"amount": "130", "currency": {"code": "USD"}})]
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "нет", "нет", "нет"], data)

    assert "Сумма: 130 USD" in text
    network.assert_not_called()


@pytest.mark.parametrize("sender", [None, "", float("nan")])
def test_main_deposit_without_sender_has_no_arrow(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], sender: Any
) -> None:
    """Пустое поле отправителя для открытия вклада не требует маскировки."""
    operation = transaction(description="Открытие вклада")
    if sender is None:
        operation.pop("from")
    else:
        operation["from"] = sender
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "нет", "нет", "нет"], [operation])

    assert "Открытие вклада\nСчет **4305\nСумма: 100.50 руб." in text
    assert " -> " not in text
    assert "nan" not in text.lower()


def test_main_handles_malformed_rows_without_exposing_requisites(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Некорректные значения дают безопасные заглушки, а не исходные реквизиты."""
    invalid = transaction(
        date=float("nan"),
        description=float("nan"),
        operationAmount={"amount": float("nan"), "currency": None},
        to="Некорректный счет 12345678901234567890",
    )
    invalid["from"] = "7000792289606361"
    data = [None, {}, "bad", invalid, transaction()]
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "да", "по возрастанию", "нет", "нет"], data)

    assert "Всего банковских операций в выборке: 2" in text
    assert "Дата не указана Без описания" in text
    assert "Реквизиты скрыты -> Реквизиты скрыты" in text
    assert "Сумма: не указана валюта не указана" in text
    assert "nan" not in text.lower()
    assert "12345678901234567890" not in text
    assert "7000792289606361" not in text


@pytest.mark.parametrize("data", [None, {}, "bad", 123])
def test_main_handles_nonlist_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], data: Any
) -> None:
    """Некорректный контейнер файла не передается напрямую обработчикам списка."""
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "нет", "нет", "нет"], data)

    assert "Не найдено ни одной транзакции" in text


@pytest.mark.parametrize("amount", [None, [], {"amount": None}, {"amount": "bad", "currency": []}])
def test_main_handles_broken_amount_objects(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], amount: Any
) -> None:
    """Поврежденный объект суммы не приводит к падению или печати его содержимого."""
    data = [transaction(operationAmount=amount, to=float("nan"))]
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "нет", "нет", "нет"], data)

    assert "Сумма: не указана валюта не указана" in text
    assert "Реквизиты не указаны" in text


def flat_transaction(currency: str = "RUB", **changes: Any) -> dict[str, Any]:
    """Создать строку CSV/XLSX с плоскими полями суммы и валюты."""
    operation = transaction(date="2023-09-05T11:00:00Z")
    operation.pop("operationAmount")
    operation.update(amount="130", currency_code=currency, currency_name="Рубль")
    operation.update(changes)
    return operation


@pytest.mark.parametrize(
    ("choice", "format_name", "reader_name", "filename"),
    [
        ("1", "JSON", "load_transactions", "operations.json"),
        ("2", "CSV", "read_csv_transactions", "transactions.csv"),
        ("3", "XLSX", "read_excel_transactions", "transactions_excel.xlsx"),
    ],
)
def test_main_selects_each_reader_from_project_root(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    choice: str,
    format_name: str,
    reader_name: str,
    filename: str,
) -> None:
    """Каждый пункт меню читает свой файл независимо от текущего каталога."""
    monkeypatch.chdir(tmp_path)
    for name in ("load_transactions", "read_csv_transactions", "read_excel_transactions"):
        monkeypatch.setattr(app, name, Mock(side_effect=AssertionError(f"Не выбранный источник: {name}")))
    data = [transaction()] if choice == "1" else [flat_transaction("EUR")]
    text, reader = run_dialog(monkeypatch, capsys, [choice, "EXECUTED", "нет", "нет", "нет"], data, reader_name)

    reader.assert_called_once_with(ROOT / "data" / filename)
    assert f"Для обработки выбран {format_name}-файл." in text
    assert "Всего банковских операций в выборке: 1" in text
    if choice != "1":
        assert "05.09.2023 Перевод организации" in text
        assert "Сумма: 130 EUR" in text


def test_main_retries_invalid_source_choice(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Неверный пункт меню повторяет выбор источника, не переходя к статусам."""
    answers = ["", "4", "CSV", " 1 ", "EXECUTED", "нет", "нет", "нет"]
    text, reader = run_dialog(monkeypatch, capsys, answers, [transaction()])

    assert text.count("Выберите пункт 1, 2 или 3.") == 3
    reader.assert_called_once_with(ROOT / "data" / "operations.json")


@pytest.mark.parametrize("choice,reader_name", [("2", "read_csv_transactions"), ("3", "read_excel_transactions")])
def test_main_filters_rubles_in_flat_sources(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], choice: str, reader_name: str
) -> None:
    """Рублевый фильтр использует currency_code табличной схемы."""
    data = [
        flat_transaction("RUB", description="Рублевый вклад"),
        flat_transaction("USD", description="Долларовый вклад"),
    ]
    text, _ = run_dialog(monkeypatch, capsys, [choice, "EXECUTED", "нет", "да", "нет"], data, reader_name)

    assert "Всего банковских операций в выборке: 1" in text
    assert "Рублевый вклад" in text
    assert "Долларовый вклад" not in text
    assert "Сумма: 130 руб." in text


@pytest.mark.parametrize(
    ("choice", "reader_name", "error_type"),
    [
        ("1", "load_transactions", FileNotFoundError),
        ("1", "load_transactions", PermissionError),
        ("2", "read_csv_transactions", ValueError),
        ("3", "read_excel_transactions", ValueError),
        ("3", "read_excel_transactions", ImportError),
    ],
)
def test_main_reports_source_failure_without_raw_error_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    choice: str,
    reader_name: str,
    error_type: type[Exception],
) -> None:
    """Ошибка файла или зависимости завершает диалог без traceback и реквизитов."""
    reader = Mock(side_effect=error_type("Секретные реквизиты 7000792289606361"))
    monkeypatch.setattr(app, reader_name, reader)
    user_input = Mock(side_effect=[choice])
    monkeypatch.setattr("builtins.input", user_input)

    app.main()

    assert user_input.call_count == 1
    assert reader.call_count == 1
    text = capsys.readouterr().out
    assert "Не удалось прочитать файл транзакций." in text
    assert "7000792289606361" not in text
    assert "Всего банковских операций" not in text


def test_main_masks_long_numbers_in_malformed_labels_and_description(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ошибочно попавший в название номер не обходит маскировку последнего токена."""
    operation = transaction(description="Платеж по счету 12345678901234567890")
    operation["from"] = "Visa 7000792289606361 7000792289606361"
    text, _ = run_dialog(monkeypatch, capsys, ["1", "EXECUTED", "нет", "нет", "нет"], [operation])

    assert "12345678901234567890" not in text
    assert "7000792289606361" not in text
    assert "Платеж по счету ****" in text


def test_main_handles_textual_nan_fields_in_flat_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Строковые маркеры пропуска из CSV не изображают отправителя и валюту."""
    operation = flat_transaction("NaN", amount="NaN", date="NaT", description=None, to=float("nan"))
    operation["from"] = " NaN "
    text, _ = run_dialog(
        monkeypatch, capsys, ["2", "EXECUTED", "нет", "нет", "нет"], [operation], "read_csv_transactions"
    )

    assert "Дата не указана Без описания" in text
    assert "Реквизиты не указаны" in text
    assert " -> " not in text
    assert "Сумма: не указана валюта не указана" in text
    assert "nan" not in text.lower()


def test_main_script_entrypoint_starts_dialog(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Исполнение модуля как программы действительно запускает main."""
    monkeypatch.setattr("src.utils.load_transactions", Mock(return_value=[transaction()]))
    user_input = Mock(side_effect=["1", "EXECUTED", "нет", "нет", "нет"])
    monkeypatch.setattr("builtins.input", user_input)

    runpy.run_path(str(Path(app.__file__)), run_name="__main__")

    assert user_input.call_count == 5
    assert "Всего банковских операций в выборке: 1" in capsys.readouterr().out


def test_main_rejects_corrupt_xlsx_without_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Поврежденный архив XLSX проверяется через настоящий файловый reader."""
    (tmp_path / "transactions_excel.xlsx").write_bytes(b"not-an-xlsx-archive")
    monkeypatch.setattr(app, "DATA_DIR", tmp_path)
    monkeypatch.setattr("builtins.input", Mock(side_effect=["3"]))

    app.main()

    text = capsys.readouterr().out
    assert "Не удалось прочитать файл транзакций." in text
    assert "not-an-xlsx-archive" not in text
