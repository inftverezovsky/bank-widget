# Bank Widget Homework

Домашнее задание по созданию функций маскировки банковской карты и счета.

## Структура

- `src/` — исходный код.
- `tests/` — тесты.
- `.flake8` — настройки Flake8.
- `pyproject.toml` — настройки Poetry, Black, isort и mypy.

## Установка зависимостей

```bash
poetry install --with lint
```

## Проверки перед сдачей

```bash
poetry run flake8 src tests
poetry run black --check src tests
poetry run isort --check-only src tests
poetry run mypy src tests
python -m unittest discover -s tests -v
```

Если Black или isort сообщат о необходимости форматирования, выполните:

```bash
poetry run black src tests
poetry run isort src tests
```
