"""Чтение финансовых операций из табличных файлов."""

import csv
from pathlib import Path
from typing import Any, cast
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

import pandas as pd


def read_csv_transactions(path: str | Path) -> list[dict[str, Any]]:
    """Прочитать операции из UTF-8 CSV с разделителем ; и необязательным BOM.

    Args:
        path: Путь к CSV-файлу в виде строки или объекта Path.

    Returns:
        Список словарей с исходными заголовками и строковыми значениями.
        Пустой файл или файл только с заголовками дает пустой список.

    Raises:
        OSError: Файл отсутствует или недоступен для чтения.
        ValueError: Ошибка кодировки, кавычек, заголовков или числа столбцов.
    """
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=";", strict=True)
            fields = reader.fieldnames
            if fields and (len(fields) != len(set(fields)) or any(not field.strip() for field in fields)):
                raise ValueError(f"Некорректные заголовки CSV-файла {path}")
            transactions: list[dict[str, Any]] = []
            for row in reader:
                if None in row or None in row.values():
                    raise ValueError(f"Некорректное число столбцов CSV-файла {path}, строка {reader.line_num}")
                transactions.append(row)
            return transactions
    except (csv.Error, UnicodeDecodeError) as error:
        raise ValueError(f"Некорректный CSV-файл {path}: {error}") from error


def read_excel_transactions(path: str | Path) -> list[dict[str, Any]]:
    """Прочитать операции из первого листа XLSX через pandas и openpyxl.

    Args:
        path: Путь к XLSX-файлу в виде строки или объекта Path.

    Returns:
        Список словарей с исходными заголовками. Номера from/to остаются
        строками, отсутствующие значения заменяются на пустые строки.
        Корректная книга без операций дает пустой список.

    Raises:
        OSError: Файл отсутствует или недоступен для чтения.
        ValueError: Файл поврежден, не является XLSX или не содержит листов.
    """
    try:
        frame = pd.read_excel(path, engine="openpyxl", dtype={"from": str, "to": str}, keep_default_na=False)
    except (BadZipFile, KeyError, ParseError, ValueError) as error:
        raise ValueError(f"Некорректный Excel-файл {path}: {error}") from error
    frame = frame.astype(object).where(frame.notna(), "")
    return cast(list[dict[str, Any]], frame.to_dict(orient="records"))
