# Bank Widget

Учебный проект виджета банковских операций клиента. Проект содержит функции для маскировки карт и счетов, форматирования даты, фильтрации операций по статусу и сортировки операций по дате.

## Возможности

- `get_mask_card_number()` — маскирует номер банковской карты.
- `get_mask_account()` — маскирует номер банковского счета.
- `mask_account_card()` — принимает одной строкой название карты/счета и номер, затем возвращает замаскированное значение.
- `get_date()` — преобразует дату из ISO-формата в `ДД.ММ.ГГГГ`.
- `filter_by_state()` — возвращает новый список операций с выбранным статусом. По умолчанию используется `EXECUTED`.
- `sort_by_date()` — возвращает новый список операций, отсортированный по дате. По умолчанию сортировка выполняется по убыванию.

## Установка

### Вариант с Poetry

```bash
git clone <URL-вашего-репозитория>
cd bank-widget
poetry install --with lint
```

### Без Poetry

Для запуска самих функций достаточно Python 3.12 или совместимой версии Python 3.

```bash
git clone <URL-вашего-репозитория>
cd bank-widget
```

## Использование маскировки и даты

```python
from src.widget import get_date, mask_account_card

print(mask_account_card("Visa Platinum 7000792289606361"))
# Visa Platinum 7000 79** **** 6361

print(mask_account_card("Счет 73654108430135874305"))
# Счет **4305

print(get_date("2024-03-11T02:26:18.671407"))
# 11.03.2024
```

## Фильтрация операций

```python
from src.processing import filter_by_state

operations = [
    {"id": 1, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
    {"id": 2, "state": "CANCELED", "date": "2018-09-12T21:27:25.241689"},
]

print(filter_by_state(operations))
# [{'id': 1, 'state': 'EXECUTED', 'date': '2019-07-03T18:35:29.512364'}]

print(filter_by_state(operations, "CANCELED"))
# [{'id': 2, 'state': 'CANCELED', 'date': '2018-09-12T21:27:25.241689'}]
```

## Сортировка операций

```python
from src.processing import sort_by_date

operations = [
    {"id": 1, "state": "EXECUTED", "date": "2018-06-30T02:08:58.425572"},
    {"id": 2, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
]

print(sort_by_date(operations))
# Сначала операция с датой 2019-07-03, затем 2018-06-30.

print(sort_by_date(operations, False))
# Сначала операция с датой 2018-06-30, затем 2019-07-03.
```

## Проверка проекта

Запуск тестов:

```bash
python -m unittest discover -s tests -v
```

Проверка стиля и типов:

```bash
poetry run flake8 src tests
poetry run mypy src tests
```

Также можно выполнить дополнительные проверки форматирования:

```bash
poetry run black --check src tests
poetry run isort --check-only src tests
```

### Результаты проверки качества кода

Проверка выполнена автоматически в GitHub Actions на Python 3.12:

- `flake8 src tests` — **0 ошибок**;
- `mypy src tests` — **Success: no issues found in 8 source files**.

Workflow `.github/workflows/code-quality.yml` автоматически запускает `flake8` и `mypy` для ветки домашней работы и pull request в `develop`.

## Именование

Переменные и параметры функций оформлены в стиле PEP 8: используются понятные имена в нижнем регистре с подчеркиваниями (`snake_case`), без однобуквенных пользовательских имен переменных.

## GitFlow

В проекте используются ветки:

- `main` — стабильная версия;
- `develop` — ветка разработки;
- `feature/homework_processing` — ветка текущей домашней работы.

Домашняя работа отправляется pull request из `feature/homework_processing` в `develop`.
