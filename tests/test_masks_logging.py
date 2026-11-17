"""Проверки файлового логирования masks в изолированных процессах."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def run_masks(project: Path, code: str) -> subprocess.CompletedProcess[str]:
    """Запустить реальный модуль вне корня проекта без общих хендлеров."""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=project.parent,
        env={**os.environ, "PYTHONPATH": str(project), "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=20,
    )


def read_log(project: Path) -> str:
    """Прочитать созданный модулем файл и проверить формат каждой записи."""
    log_path = project / "logs" / "masks.log"
    assert log_path.is_file(), "masks должен записывать события в logs/masks.log в корне проекта"
    content = log_path.read_text(encoding="utf-8")
    assert content, "Журнал не должен быть пустым после вызова функции"
    for line in content.splitlines():
        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - src\.masks - (DEBUG|INFO|ERROR) - .+",
            line,
        ), line
    return content


class TestMasksLogging(unittest.TestCase):
    """Проверить реальные файлы журналов без общего состояния логеров."""

    def setUp(self) -> None:
        """Скопировать текущие байты masks в отдельный временный проект."""
        temporary_directory = tempfile.TemporaryDirectory(prefix="masks-")
        self.addCleanup(temporary_directory.cleanup)
        self.project = Path(temporary_directory.name) / "project"
        source = self.project / "src"
        source.mkdir(parents=True)
        package = Path(__file__).resolve().parents[1] / "src"
        shutil.copyfile(package / "__init__.py", source / "__init__.py")
        shutil.copyfile(package / "masks.py", source / "masks.py")

    def test_card_success_is_logged_without_payment_details(self) -> None:
        """Записать успех и DEBUG без исходного номера или его маски."""
        run_masks(
            self.project,
            "from src.masks import get_mask_card_number; "
            "assert get_mask_card_number('7000792289606361') == '7000 79** **** 6361'",
        )

        content = read_log(self.project)
        assert " - DEBUG - " in content
        assert " - INFO - " in content
        assert "get_mask_card_number" in content
        assert "7000792289606361" not in content
        assert "7000 79** **** 6361" not in content
        assert not (self.project.parent / "logs").exists()

    def test_card_errors_are_logged_without_changing_exceptions(self) -> None:
        """Сохранить ValueError/TypeError и записать ERROR без реквизитов."""
        cases = [
            ("'987654321098765'", "ValueError", "Номер карты должен содержать ровно 16 символов"),
            ("None", "TypeError", "object of type 'NoneType' has no len()"),
        ]
        for argument, exception, message in cases:
            with self.subTest(argument=argument):
                run_masks(
                    self.project,
                    "from src.masks import get_mask_card_number\n"
                    "try:\n"
                    f"    get_mask_card_number({argument})\n"
                    f"except {exception} as error:\n"
                    f"    assert str(error) == {message!r}\n"
                    "else:\n"
                    "    raise AssertionError('Ожидалось исключение')\n",
                )

                content = read_log(self.project)
                assert " - ERROR - " in content
                assert "get_mask_card_number" in content
                assert "987654321098765" not in content
                assert " - INFO - " not in content

    def test_account_success_is_logged_without_payment_details(self) -> None:
        """Записать успех маскирования счета без номера и его маски."""
        run_masks(
            self.project,
            "from src.masks import get_mask_account; "
            "assert get_mask_account('73654108430135874305') == '**4305'",
        )

        content = read_log(self.project)
        assert " - DEBUG - " in content
        assert " - INFO - " in content
        assert "get_mask_account" in content
        assert "73654108430135874305" not in content
        assert "**4305" not in content

    def test_account_errors_are_logged_without_changing_exceptions(self) -> None:
        """Сохранить ошибки счета и не записать неуспех как INFO."""
        cases = [
            ("'987'", "ValueError", "Номер счета должен содержать не менее 4 символов"),
            ("None", "TypeError", "object of type 'NoneType' has no len()"),
        ]
        for argument, exception, message in cases:
            with self.subTest(argument=argument):
                run_masks(
                    self.project,
                    "from src.masks import get_mask_account\n"
                    "try:\n"
                    f"    get_mask_account({argument})\n"
                    f"except {exception} as error:\n"
                    f"    assert str(error) == {message!r}\n"
                    "else:\n"
                    "    raise AssertionError('Ожидалось исключение')\n",
                )

                content = read_log(self.project)
                assert " - ERROR - " in content
                assert "get_mask_account" in content
                assert " - INFO - " not in content
                messages = "\n".join(line.split(" - ", 3)[3] for line in content.splitlines())
                assert "987" not in messages

    def test_reload_preserves_log_without_duplicate_handlers(self) -> None:
        """Повторная загрузка не стирает записи и не удваивает сообщения."""
        result = run_masks(
            self.project,
            "import importlib, logging\n"
            "from src import masks\n"
            "masks.logger.info('before_reload')\n"
            "importlib.reload(masks)\n"
            "importlib.reload(masks)\n"
            "masks.logger.info('after_reload')\n"
            "print(sum(isinstance(handler, logging.FileHandler) for handler in masks.logger.handlers))\n",
        )

        content = (self.project / "logs" / "masks.log").read_text(encoding="utf-8")
        assert content.count("before_reload") == 1
        assert content.count("after_reload") == 1
        assert result.stdout.strip() == "1"
        read_log(self.project)

    def test_new_process_overwrites_previous_run(self) -> None:
        """Новый процесс удаляет старые записи, а не дописывает журнал."""
        run_masks(
            self.project,
            "from src.masks import get_mask_card_number; get_mask_card_number('7000792289606361')",
        )
        assert "get_mask_card_number" in read_log(self.project)

        run_masks(
            self.project,
            "from src.masks import get_mask_account; get_mask_account('73654108430135874305')",
        )
        content = read_log(self.project)
        assert "get_mask_account" in content
        assert "get_mask_card_number" not in content
        assert content.count(" - INFO - ") == 1

    def test_existing_string_validation_is_unchanged(self) -> None:
        """Не вводить запрет нецифровых строк, отсутствующий в старом API."""
        run_masks(
            self.project,
            "from src.masks import get_mask_card_number, get_mask_account; "
            "assert get_mask_card_number('abcdefghijklmnop') == 'abcd ef** **** mnop'; "
            "assert get_mask_account('ABCD') == '**ABCD'",
        )
        content = read_log(self.project)
        assert content.count(" - INFO - ") == 2
        assert "abcdefghijklmnop" not in content
        assert "ABCD" not in content
