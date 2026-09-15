"""Тесты логирования в консоль и файл, результатов и исключений."""

from datetime import datetime, timezone
from inspect import signature, unwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from src.decorators import log


@pytest.mark.parametrize("use_file", [False, True], ids=["console", "file"])
def test_log_success(use_file: bool, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить начало, успешный результат и конец в обоих назначениях."""
    log_path = tmp_path / "success.log"
    calls: list[tuple[int, int]] = []

    @log(filename=str(log_path) if use_file else None)
    def add_numbers(left: int, right: int) -> int:
        """Сложить два числа и зафиксировать количество вызовов."""
        calls.append((left, right))
        return left + right

    assert add_numbers(1, right=2) == 3
    assert calls == [(1, 2)]
    captured = capsys.readouterr()
    assert captured.err == ""
    if use_file:
        assert captured.out == ""
        output = log_path.read_text(encoding="utf-8")
    else:
        assert not log_path.exists()
        output = captured.out

    lines = output.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("add_numbers start. Time: ")
    assert "Inputs: (1,), {'right': 2}" in lines[0]
    assert lines[1] == "add_numbers ok. Result: 3"
    assert lines[2].startswith("add_numbers end. Time: ")
    assert "error:" not in output


@pytest.mark.parametrize("use_file", [False, True], ids=["console", "file"])
@pytest.mark.parametrize("error_type", [ValueError, TypeError, ZeroDivisionError])
def test_log_error(
    use_file: bool,
    error_type: type[Exception],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Проверить тип, текст, аргументы ошибки и повторное исключение."""
    log_path = tmp_path / "error.log"
    original_error = error_type("некорректные данные")
    calls: list[tuple[int, int]] = []

    @log(filename=str(log_path) if use_file else None)
    def failing_function(left: int, right: int) -> None:
        """Завершить вызов заранее подготовленным исключением."""
        calls.append((left, right))
        raise original_error

    with pytest.raises(error_type) as error_info:
        failing_function(1, right=0)

    assert error_info.value is original_error
    assert calls == [(1, 0)]
    captured = capsys.readouterr()
    assert captured.err == ""
    if use_file:
        assert captured.out == ""
        output = log_path.read_text(encoding="utf-8")
    else:
        assert not log_path.exists()
        output = captured.out

    lines = output.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("failing_function start. Time: ")
    assert lines[1] == (
        f"failing_function error: {error_type.__name__}. "
        "Inputs: (1,), {'right': 0}. Error: 'некорректные данные'"
    )
    assert lines[2].startswith("failing_function end. Time: ")
    assert " ok" not in output
    assert error_info.traceback[-1].name == "failing_function"


def test_log_without_filename(capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить вывод в консоль при использовании @log() без аргументов."""

    @log()
    def greet(*, name: str = "Мир") -> str:
        """Вернуть приветствие с именованным аргументом."""
        return f"Привет, {name}!"

    assert greet(name="Даниил") == "Привет, Даниил!"
    output = capsys.readouterr().out
    assert "Inputs: (), {'name': 'Даниил'}" in output
    assert "greet ok. Result: 'Привет, Даниил!'" in output


@pytest.mark.parametrize("result", [None, False, 0, "", [1, 2], {"state": "EXECUTED"}])
def test_log_preserves_return_value(result: object, capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить возврат исходного объекта, включая пустые значения."""

    @log()
    def get_result() -> object:
        """Вернуть переданный тесту объект без преобразования."""
        return result

    assert get_result() is result
    output = capsys.readouterr().out
    assert "Inputs: (), {}" in output
    assert f"get_result ok. Result: {result!r}" in output


def test_log_preserves_metadata() -> None:
    """Проверить имя, документацию, аннотации и сигнатуру функции."""

    def multiply(left: int, right: int = 2) -> int:
        """Умножить два числа."""
        return left * right

    decorated = log()(multiply)
    assert decorated.__name__ == multiply.__name__
    assert decorated.__doc__ == multiply.__doc__
    assert decorated.__annotations__ == multiply.__annotations__
    assert signature(decorated) == signature(multiply)
    assert unwrap(decorated) is multiply


def test_log_appends_to_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить сохранение старого содержимого и последовательных вызовов."""
    log_path = tmp_path / "history.txt"
    log_path.write_text("Предыдущая запись\n", encoding="utf-8")

    @log(filename=str(log_path))
    def double(number: int) -> int:
        """Удвоить число."""
        return number * 2

    assert double(2) == 4
    assert double(5) == 10
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 7
    assert lines[0] == "Предыдущая запись"
    assert "Inputs: (2,), {}" in lines[1]
    assert lines[2] == "double ok. Result: 4"
    assert "Inputs: (5,), {}" in lines[4]
    assert lines[5] == "double ok. Result: 10"
    assert capsys.readouterr().out == ""


def test_log_creates_file_on_call(tmp_path: Path) -> None:
    """Проверить создание файла при первом вызове и запись кириллицы."""
    log_path = tmp_path / "журнал.txt"

    @log(filename=str(log_path))
    def echo(text: str) -> str:
        """Вернуть текст без изменения."""
        return text

    assert not log_path.exists()
    assert echo("Готово") == "Готово"
    output = log_path.read_text(encoding="utf-8")
    assert "Inputs: ('Готово',), {}" in output
    assert "echo ok. Result: 'Готово'" in output


def test_log_forwards_variadic_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить передачу произвольных позиционных и именованных аргументов."""

    @log()
    def collect(*numbers: int, **options: str) -> tuple[tuple[int, ...], dict[str, str]]:
        """Вернуть все полученные аргументы."""
        return numbers, options

    assert collect(1, 2, 3, mode="sum") == ((1, 2, 3), {"mode": "sum"})
    assert "Inputs: (1, 2, 3), {'mode': 'sum'}" in capsys.readouterr().out


def test_log_records_start_and_end_times(capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить отдельные временные метки начала и завершения в UTC."""
    started_at = datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc)
    finished_at = datetime(2026, 9, 15, 10, 0, 2, tzinfo=timezone.utc)

    @log()
    def complete() -> str:
        """Вернуть признак успешного выполнения."""
        return "done"

    with patch("src.decorators.datetime") as mocked_datetime:
        mocked_datetime.now.side_effect = [started_at, finished_at]
        assert complete() == "done"

    assert mocked_datetime.now.call_count == 2
    assert all(call.args == (timezone.utc,) for call in mocked_datetime.now.call_args_list)
    assert capsys.readouterr().out.splitlines() == [
        "complete start. Time: 2026-09-15T10:00:00+00:00. Inputs: (), {}",
        "complete ok. Result: 'done'",
        "complete end. Time: 2026-09-15T10:00:02+00:00",
    ]


def test_log_keeps_functions_independent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Проверить, что разные декорированные функции не смешивают логи."""
    first_path = tmp_path / "first.log"
    second_path = tmp_path / "second.log"

    @log(filename=str(first_path))
    def first() -> int:
        """Вернуть результат первой функции."""
        return 1

    @log(filename=str(second_path))
    def second() -> int:
        """Вернуть результат второй функции."""
        return 2

    assert first() == 1
    assert second() == 2
    first_output = first_path.read_text(encoding="utf-8")
    second_output = second_path.read_text(encoding="utf-8")
    assert "first ok. Result: 1" in first_output
    assert "second" not in first_output
    assert "second ok. Result: 2" in second_output
    assert "first" not in second_output
    assert capsys.readouterr().out == ""
