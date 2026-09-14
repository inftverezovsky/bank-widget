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
poetry install
```

## Тестирование

Для тестирования используется `pytest`.

Запуск всех тестов:

```bash
pytest
```

Тесты разделены по модулям:

- `tests/test_masks.py` — функции из `masks.py`;
- `tests/test_widget.py` — функции из `widget.py`;
- `tests/test_processing.py` — функции из `processing.py`;
- `tests/conftest.py` — общие фикстуры с тестовыми данными.

В тестах используются фикстуры `pytest` и параметризация `pytest.mark.parametrize` для проверки разных номеров карт и счетов, дат, статусов операций и ошибочных входных данных.

Покрытие запускается автоматически вместе с `pytest` через `pytest-cov`. Минимально допустимое покрытие в настройках проекта — 80%.

Результат контрольного запуска:

```text
47 passed
TOTAL: 36 statements, 0 missed, 14 branches, 0 partial
Coverage: 100%
```

HTML-отчет покрытия находится в папке `htmlcov/`. Основной файл отчета — `htmlcov/index.html`.

## Проверка качества кода

```bash
flake8 src tests
mypy src tests
isort --check-only src tests
```

Эти же проверки вместе с `pytest` выполняются автоматически в GitHub Actions для feature-ветки и pull request в `develop`.

## Именование

Имена переменных записаны в `snake_case`. Однобуквенные пользовательские имена переменных не используются.
