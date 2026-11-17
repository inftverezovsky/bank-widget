"""Тесты чтения финансовых операций из CSV и Excel."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch
from zipfile import ZipFile

import pandas as pd
import pytest

from src.file_readers import read_csv_transactions, read_excel_transactions


def test_read_csv_preserves_fields_and_account_numbers(tmp_path: Path) -> None:
    """Прочитать разделитель ;, кириллицу и номера без потери ведущих нулей."""
    path = tmp_path / "transactions.csv"
    path.write_text(
        "id;state;date;amount;currency_name;currency_code;from;to;description\n"
        "1;EXECUTED;2023-09-05T11:30:32Z;100.50;Ruble;RUB;"
        '00123456789012345678;Счет 00987654321098765432;"Перевод; себе"\n',
        encoding="utf-8-sig",
    )

    assert read_csv_transactions(path) == [
        {
            "id": "1",
            "state": "EXECUTED",
            "date": "2023-09-05T11:30:32Z",
            "amount": "100.50",
            "currency_name": "Ruble",
            "currency_code": "RUB",
            "from": "00123456789012345678",
            "to": "Счет 00987654321098765432",
            "description": "Перевод; себе",
        }
    ]


def test_read_csv_uses_mocked_file() -> None:
    """Подменить только файловый ввод через Mock и patch."""
    source = StringIO(
        "id;state;date;amount;currency_name;currency_code;from;to;description\n"
        "2;EXECUTED;2023-01-01T00:00:00Z;0;Ruble;RUB;;Счет 0001;Открытие вклада\n"
    )
    open_mock = Mock(return_value=source)

    with patch("src.file_readers.Path.open", open_mock):
        transactions = read_csv_transactions("transactions.csv")

    assert transactions[0]["id"] == "2"
    assert transactions[0]["amount"] == "0"
    assert transactions[0]["from"] == ""
    assert transactions[0]["to"] == "Счет 0001"
    open_mock.assert_called_once_with(encoding="utf-8-sig", newline="")
    assert source.closed


def test_read_csv_reads_actual_course_file() -> None:
    """Прочитать все операции из исходного учебного CSV."""
    path = Path(__file__).resolve().parents[1] / "data" / "transactions.csv"

    transactions = read_csv_transactions(path)

    assert len(transactions) == 1000
    assert transactions[0] == {
        "id": "650703",
        "state": "EXECUTED",
        "date": "2023-09-05T11:30:32Z",
        "amount": "16210",
        "currency_name": "Sol",
        "currency_code": "PEN",
        "from": "Счет 58803664561298323391",
        "to": "Счет 39745660563456619397",
        "description": "Перевод организации",
    }
    assert transactions[-1]["id"] == "4699552"
    assert all(isinstance(row["from"], str) and isinstance(row["to"], str) for row in transactions)
    assert all(set(row) == set(transactions[0]) for row in transactions)


def test_read_csv_rejects_unclosed_quotes(tmp_path: Path) -> None:
    """Не выдавать поврежденную строку за успешно прочитанную операцию."""
    path = tmp_path / "broken.csv"
    path.write_text(
        "id;state;date;amount;currency_name;currency_code;from;to;description\n"
        '1;EXECUTED;2023-01-01T00:00:00Z;10;Ruble;RUB;;Счет 0001;"нет конца\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=path.name):
        read_csv_transactions(path)


@pytest.mark.parametrize("row", ["1;10;extra\n", "1\n"])
def test_read_csv_rejects_wrong_column_count(tmp_path: Path, row: str) -> None:
    """Не терять лишние значения и не дополнять обрезанные строки молча."""
    path = tmp_path / "columns.csv"
    path.write_text("id;amount\n" + row, encoding="utf-8")

    with pytest.raises(ValueError, match=r"columns.csv.*2"):
        read_csv_transactions(path)


@pytest.mark.parametrize("header", ["id;id", ";amount", "id;   "])
def test_read_csv_rejects_ambiguous_headers(tmp_path: Path, header: str) -> None:
    """Не перезаписывать поля при повторяющихся или пустых заголовках."""
    path = tmp_path / "headers.csv"
    path.write_text(header + "\n1;2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="headers.csv"):
        read_csv_transactions(path)


def test_read_csv_reports_invalid_encoding(tmp_path: Path) -> None:
    """Показать путь поврежденного файла вместо безымянной ошибки декодирования."""
    path = tmp_path / "encoding.csv"
    path.write_bytes(b"id;amount\n1;\xff\n")

    with pytest.raises(ValueError, match=path.name):
        read_csv_transactions(path)


@pytest.mark.parametrize("content", ["", "\ufeff", "\n\n", "id;amount\n"])
def test_read_csv_returns_empty_list_without_transactions(tmp_path: Path, content: str) -> None:
    """Отличать успешно прочитанный пустой CSV от ошибки чтения."""
    path = tmp_path / "empty.csv"
    path.write_text(content, encoding="utf-8")

    assert read_csv_transactions(str(path)) == []


def test_read_csv_reports_missing_file(tmp_path: Path) -> None:
    """Не скрывать отсутствие CSV-файла за пустым списком."""
    with pytest.raises(FileNotFoundError, match="missing.csv"):
        read_csv_transactions(tmp_path / "missing.csv")


def test_read_csv_preserves_permission_error() -> None:
    """Сохранить ошибку доступа, подменив файловую границу через Mock и patch."""
    error = PermissionError("Нет доступа к transactions.csv")
    open_mock = Mock(side_effect=error)

    with patch("src.file_readers.Path.open", open_mock):
        with pytest.raises(PermissionError) as raised:
            read_csv_transactions("transactions.csv")

    assert raised.value is error


def test_read_excel_reads_actual_course_file() -> None:
    """Прочитать все операции из исходного учебного XLSX."""
    path = Path(__file__).resolve().parents[1] / "data" / "transactions_excel.xlsx"

    transactions = read_excel_transactions(path)

    assert len(transactions) == 1000
    assert transactions[0] == {
        "id": 650703,
        "state": "EXECUTED",
        "date": "2023-09-05T11:30:32Z",
        "amount": 16210,
        "currency_name": "Sol",
        "currency_code": "PEN",
        "from": "Счет 58803664561298323391",
        "to": "Счет 39745660563456619397",
        "description": "Перевод организации",
    }
    assert transactions[-1]["id"] == 4699552
    assert all(set(row) == set(transactions[0]) for row in transactions)


def test_read_excel_preserves_account_numbers(tmp_path: Path) -> None:
    """Не преобразовывать текстовые номера в числа при чтении XLSX."""
    path = tmp_path / "accounts.xlsx"
    transaction = {"id": 1, "amount": 0, "from": "00123456789012345678", "to": "00000000000000000001"}
    pd.DataFrame([transaction]).to_excel(path, index=False, engine="openpyxl")

    assert read_excel_transactions(str(path)) == [transaction]


def test_read_excel_preserves_text_and_blank_cells(tmp_path: Path) -> None:
    """Не считать текст NA/null пропусками; пустые ячейки вернуть как строки."""
    path = tmp_path / "blanks.xlsx"
    transaction = {"id": 1, "amount": 0, "from": "", "to": "Счет 0001", "description": "NA", "currency_name": "null"}
    pd.DataFrame([transaction]).to_excel(path, index=False, engine="openpyxl")

    assert read_excel_transactions(path) == [transaction]


def test_read_excel_normalizes_missing_values_with_mock() -> None:
    """С Mock и patch проверить настоящую обработку DataFrame, NaN, NA и NaT."""
    frame = pd.DataFrame(
        {
            "id": [1, 2],
            "amount": [12.5, float("nan")],
            "from": ["0001", pd.NA],
            "to": ["Счет 0002", "Счет 0003"],
            "description": [None, None],
            "date": [pd.NaT, pd.NaT],
        }
    )
    original = frame.copy(deep=True)
    read_mock = Mock(return_value=frame)

    with patch("src.file_readers.pd.read_excel", read_mock):
        transactions = read_excel_transactions("transactions.xlsx")

    assert transactions == [
        {"id": 1, "amount": 12.5, "from": "0001", "to": "Счет 0002", "description": "", "date": ""},
        {"id": 2, "amount": "", "from": "", "to": "Счет 0003", "description": "", "date": ""},
    ]
    assert json.loads(json.dumps(transactions, allow_nan=False)) == transactions
    assert type(transactions[0]["id"]) is int
    read_mock.assert_called_once_with(
        "transactions.xlsx", engine="openpyxl", dtype={"from": str, "to": str}, keep_default_na=False
    )
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("damage", ["empty", "not_zip", "missing_content_types", "invalid_xml"])
def test_read_excel_reports_corrupt_workbook(tmp_path: Path, damage: str) -> None:
    """Поврежденная книга должна давать явную ошибку с путем, а не пустой список."""
    path = tmp_path / "broken.xlsx"
    if damage == "empty":
        path.write_bytes(b"")
    elif damage == "not_zip":
        path.write_bytes(b"not an Excel workbook")
    else:
        with ZipFile(path, "w") as archive:
            if damage == "invalid_xml":
                archive.writestr("[Content_Types].xml", "<broken")

    with pytest.raises(ValueError, match="broken.xlsx") as raised:
        read_excel_transactions(path)

    assert raised.value.__cause__ is not None


def test_read_excel_includes_path_in_parser_error() -> None:
    """Дополнить ошибку pandas именем исходной книги, сохранив причину."""
    error = ValueError("Worksheet index 0 is invalid, 0 worksheets found")
    read_mock = Mock(side_effect=error)

    with patch("src.file_readers.pd.read_excel", read_mock):
        with pytest.raises(ValueError, match="no_sheets.xlsx") as raised:
            read_excel_transactions("no_sheets.xlsx")

    assert raised.value.__cause__ is error


@pytest.mark.parametrize("columns", [[], ["id", "amount", "from", "to"]])
def test_read_excel_returns_empty_list_without_transactions(tmp_path: Path, columns: list[str]) -> None:
    """Корректная пустая книга и книга только с заголовками дают пустой список."""
    path = tmp_path / "empty.xlsx"
    pd.DataFrame(columns=columns).to_excel(path, index=False, engine="openpyxl")

    assert read_excel_transactions(path) == []


def test_read_excel_reports_missing_file(tmp_path: Path) -> None:
    """Не скрывать отсутствие Excel-файла за пустым списком."""
    with pytest.raises(FileNotFoundError, match="missing.xlsx"):
        read_excel_transactions(tmp_path / "missing.xlsx")


def test_read_excel_preserves_permission_error() -> None:
    """Ошибки доступа не должны становиться успешным чтением или ошибкой формата."""
    error = PermissionError("Нет доступа к transactions.xlsx")
    read_mock = Mock(side_effect=error)

    with patch("src.file_readers.pd.read_excel", read_mock):
        with pytest.raises(PermissionError) as raised:
            read_excel_transactions("transactions.xlsx")

    assert raised.value is error


def test_read_excel_reads_first_sheet(tmp_path: Path) -> None:
    """Не смешивать основной лист с дополнительными листами книги."""
    path = tmp_path / "sheets.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"id": 1, "amount": 10}]).to_excel(writer, sheet_name="Operations", index=False)
        pd.DataFrame([{"id": 2, "amount": 20}]).to_excel(writer, sheet_name="Other", index=False)

    assert read_excel_transactions(path) == [{"id": 1, "amount": 10}]


def test_actual_course_files_contain_same_transactions() -> None:
    """Сверить все 1000 записей учебных файлов, включая пустые поля и счета."""
    data = Path(__file__).resolve().parents[1] / "data"
    csv_transactions = read_csv_transactions(data / "transactions.csv")
    excel_transactions = read_excel_transactions(data / "transactions_excel.xlsx")

    assert len(csv_transactions) == len(excel_transactions) == 1000
    assert [{key: str(value) for key, value in row.items()} for row in excel_transactions] == csv_transactions
    assert all(isinstance(row["from"], str) and isinstance(row["to"], str) for row in excel_transactions)
    assert json.loads(json.dumps(excel_transactions, allow_nan=False)) == excel_transactions
