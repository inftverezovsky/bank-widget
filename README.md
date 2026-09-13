# Bank Widget

Учебный проект для работы с банковскими операциями.

## Возможности

В проекте реализованы функции для:

- маскировки номера карты и счета;
- форматирования даты;
- фильтрации операций по статусу;
- сортировки операций по дате.

## Установка

```bash
git clone https://github.com/inftverezovsky/bank-widget.git
cd bank-widget
poetry install --with lint
```

## Примеры использования

```python
from src.processing import filter_by_state, sort_by_date

operations = [
    {"id": 1, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
    {"id": 2, "state": "CANCELED", "date": "2018-09-12T21:27:25.241689"},
]

print(filter_by_state(operations))
print(filter_by_state(operations, "CANCELED"))
print(sort_by_date(operations))
print(sort_by_date(operations, False))
```

Также в проекте есть функции `mask_account_card()` и `get_date()` из прошлой домашней работы.

## Проверка кода

Тесты:

```bash
python -m unittest discover -s tests -v
```

Flake8 и mypy:

```bash
poetry run flake8 src tests
poetry run mypy src tests
```

Результат последней проверки:

- flake8 — 0 ошибок;
- mypy — `Success: no issues found in 8 source files`.

Проверки также запускаются автоматически через GitHub Actions.

## Именование

Имена переменных записаны в `snake_case`. Однобуквенные имена переменных не используются.
