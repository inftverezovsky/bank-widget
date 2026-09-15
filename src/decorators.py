"""Декоратор для логирования вызовов синхронных функций."""

from datetime import datetime, timezone
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

Parameters = ParamSpec("Parameters")
ReturnValue = TypeVar("ReturnValue")


def log(
    filename: str | None = None,
) -> Callable[[Callable[Parameters, ReturnValue]], Callable[Parameters, ReturnValue]]:
    """Логировать начало, результат или ошибку и завершение вызова.

    Args:
        filename: Путь к файлу для дозаписи логов в UTF-8. Если не указан
            или равен None, сообщения выводятся в консоль.

    Returns:
        Декоратор, сохраняющий сигнатуру и результат исходной функции.

    Raises:
        Exception: Исключение исходной функции после записи информации
            об ошибке. Возникает при вызове декорированной функции.
        OSError: Если при вызове не удалось открыть файл или записать лог.

    Notes:
        Время записывается в ISO-формате с часовым поясом UTC.
        Исключения функции не подавляются: после записи ошибки они
        передаются вызывающему коду. Каталог для файла должен существовать.
        Аргументы и результаты попадают в лог без маскировки, поэтому
        декоратор не следует применять к функциям с секретными данными.
    """

    def write_log(message: str) -> None:
        """Вывести сообщение в консоль или дописать его в выбранный файл.

        Args:
            message: Текст одной записи лога.

        Returns:
            None. Сообщение записывается с завершающим переводом строки.

        Raises:
            OSError: Если открыть файл или записать сообщение не удалось.
        """
        if filename is None:
            print(message)
        else:
            with open(filename, "a", encoding="utf-8") as log_file:
                log_file.write(f"{message}\n")

    def decorator(function: Callable[Parameters, ReturnValue]) -> Callable[Parameters, ReturnValue]:
        """Обернуть функцию логированием, сохранив ее метаданные.

        Args:
            function: Синхронная функция, вызовы которой нужно записывать.

        Returns:
            Обертка с теми же параметрами и типом результата.
        """

        @wraps(function)
        def wrapper(*args: Parameters.args, **kwargs: Parameters.kwargs) -> ReturnValue:
            """Вызвать функцию один раз и записать сведения о выполнении.

            Args:
                args: Позиционные аргументы исходной функции.
                kwargs: Именованные аргументы исходной функции.

            Returns:
                Результат исходной функции без преобразований.

            Raises:
                Exception: Исходное исключение после записи ошибки.
                OSError: Если запись лога не удалась.
            """
            started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            input_values = f"{args!r}, {kwargs!r}"
            write_log(f"{function.__name__} start. Time: {started_at}. Inputs: {input_values}")
            try:
                result = function(*args, **kwargs)
            except Exception as error:
                write_log(
                    f"{function.__name__} error: {type(error).__name__}. "
                    f"Inputs: {input_values}. Error: {str(error)!r}"
                )
                raise
            else:
                write_log(f"{function.__name__} ok. Result: {result!r}")
                return result
            finally:
                finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                write_log(f"{function.__name__} end. Time: {finished_at}")

        return wrapper

    return decorator
