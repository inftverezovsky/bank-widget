# Bank Widget

Учебный проект для работы с банковскими операциями.

## Возможности

В проекте реализованы функции для:

- маскировки номера карты и счета;
- форматирования даты;
- фильтрации операций по статусу;
- сортировки операций по дате;
- фильтрации транзакций по валюте;
- последовательного получения описаний транзакций;
- генерации номеров банковских карт.

## Установка

```bash
git clone https://github.com/inftverezovsky/bank-widget.git
cd bank-widget
poetry install
```

## Модуль `generators`

В `src/generators.py` находятся три функции для последовательной обработки данных.

### `filter_by_currency`

Возвращает итератор с транзакциями, валюта которых совпадает с переданным кодом.

```python
from src.generators import filter_by_currency

usd_transactions = filter_by_currency(transactions, "USD")

for transaction in usd_transactions:
    print(transaction)
```

### `transaction_descriptions`

По очереди возвращает описания транзакций.

```python
from src.generators import transaction_descriptions

descriptions = transaction_descriptions(transactions)

for description in descriptions:
    print(description)
```

### `card_number_generator`

Генерирует номера карт в диапазоне от `start` до `stop` включительно и форматирует их как `XXXX XXXX XXXX XXXX`.

```python
from src.generators import card_number_generator

for card_number in card_number_generator(1, 5):
    print(card_number)
```

Результат:

```text
0000 0000 0000 0001
0000 0000 0000 0002
0000 0000 0000 0003
0000 0000 0000 0004
0000 0000 0000 0005
```

## Тестирование

Для тестирования используется `pytest`.

```bash
pytest
```

Тесты разделены по модулям:

- `tests/test_masks.py` — функции из `masks.py`;
- `tests/test_widget.py` — функции из `widget.py`;
- `tests/test_processing.py` — функции из `processing.py`;
- `tests/test_generators.py` — функции из `generators.py`;
- `tests/conftest.py` — общие фикстуры с тестовыми данными.

В тестах используются фикстуры `pytest` и параметризация `pytest.mark.parametrize`. Проверяются корректные данные, пустые наборы, отсутствующие совпадения, крайние значения диапазона карт и ошибочные границы.

Покрытие запускается вместе с `pytest` через `pytest-cov`. Минимально допустимое покрытие проекта — 80%.

Результат контрольного запуска:

```text
65 passed
TOTAL: 61 statements, 0 missed, 30 branches, 0 partial
Coverage: 100%
```

HTML-отчет покрытия находится в папке `htmlcov/`. Основной файл отчета — `htmlcov/index.html`.

## Проверка качества кода

```bash
flake8 src tests
mypy src tests
isort --check-only src tests
```

Эти проверки вместе с `pytest` выполняются автоматически в GitHub Actions для feature-веток и pull request в `develop`.

## Именование

Имена функций и переменных соответствуют PEP 8 и записаны в `snake_case`.
