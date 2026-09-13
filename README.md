# Bank Widget Homework

Домашнее задание по виджету банковских операций клиента.

## Реализовано

- `src/masks.py` — маскировка номера банковской карты и счета.
- `src/widget.py` — обработка строки с названием карты/счета и номером через `mask_account_card()`.
- `src/widget.py` — преобразование ISO-даты в формат `ДД.ММ.ГГГГ` через `get_date()`.
- `.gitignore` — исключения для Python, IDE, виртуальных окружений, тестовых и временных файлов.
- Git-репозиторий с историей разработки из трех и более логичных коммитов.
- Автоматические тесты в `tests/`.

## Примеры

```python
from src.widget import get_date, mask_account_card

print(mask_account_card("Visa Platinum 7000792289606361"))
# Visa Platinum 7000 79** **** 6361

print(mask_account_card("Счет 73654108430135874305"))
# Счет **4305

print(get_date("2024-03-11T02:26:18.671407"))
# 11.03.2024
```

## Проверка

```bash
python -m unittest discover -s tests -v
git status
```

Дополнительно, если зависимости установлены через Poetry:

```bash
poetry install --with lint
poetry run flake8 src tests
poetry run black --check src tests
poetry run isort --check-only src tests
poetry run mypy src tests
```
