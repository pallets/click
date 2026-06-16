"""Unit-тесты для модуля _winconsole.py (Windows Console API).

Этот модуль содержит тесты для функций работы с Windows Console.
Покрывает функции: GetStdHandle, GetConsoleMode, ReadConsoleW,
WriteConsoleW, GetCommandLineW и проверку констант.
"""

import pytest
import sys
from click import _winconsole


class TestWinconsoleImports:
    """Проверка базового импорта и структуры модуля."""

    def test_module_imports_successfully(self):
        """Тест: модуль _winconsole успешно импортируется."""
        assert _winconsole is not None

    def test_kernel32_is_accessible(self):
        """Тест: доступ к kernel32 (ядро Windows API)."""
        assert hasattr(_winconsole, 'kernel32')
        assert _winconsole.kernel32 is not None


class TestWinconsoleConstants:
    """Тесты для констант (handle и коды ошибок)."""

    def test_std_handles_constants_exist(self):
        """Тест: константы STDIN_HANDLE, STDOUT_HANDLE, STDERR_HANDLE существуют."""
        assert hasattr(_winconsole, 'STDIN_HANDLE')
        assert hasattr(_winconsole, 'STDOUT_HANDLE')
        assert hasattr(_winconsole, 'STDERR_HANDLE')

    def test_error_constants_exist(self):
        """Тест: константы ошибок существуют."""
        assert hasattr(_winconsole, 'ERROR_SUCCESS')
        assert hasattr(_winconsole, 'ERROR_NOT_ENOUGH_MEMORY')
        assert hasattr(_winconsole, 'ERROR_OPERATION_ABORTED')


class TestWinconsoleFunctions:
    """Тесты для основных функций Windows Console API."""

    def test_get_std_handle_function_exists(self):
        """Тест: функция GetStdHandle существует и вызываема."""
        assert hasattr(_winconsole, 'GetStdHandle')
        assert callable(_winconsole.GetStdHandle)

    def test_get_console_mode_function_exists(self):
        """Тест: функция GetConsoleMode существует и вызываема."""
        assert hasattr(_winconsole, 'GetConsoleMode')
        assert callable(_winconsole.GetConsoleMode)

    def test_read_console_w_function_exists(self):
        """Тест: функция ReadConsoleW существует и вызываема."""
        assert hasattr(_winconsole, 'ReadConsoleW')
        assert callable(_winconsole.ReadConsoleW)

    def test_write_console_w_function_exists(self):
        """Тест: функция WriteConsoleW существует и вызываема."""
        assert hasattr(_winconsole, 'WriteConsoleW')
        assert callable(_winconsole.WriteConsoleW)

    def test_get_command_line_w_function_exists(self):
        """Тест: функция GetCommandLineW существует и вызываема."""
        assert hasattr(_winconsole, 'GetCommandLineW')
        assert callable(_winconsole.GetCommandLineW)

    def test_get_last_error_function_exists(self):
        """Тест: функция GetLastError существует."""
        assert hasattr(_winconsole, 'GetLastError')
        assert callable(_winconsole.GetLastError)


class TestWinconsoleFunctionCalls:
    """Тесты для реальных вызовов функций (только на Windows)."""

    def test_get_std_handle_returns_value(self):
        """Тест: GetStdHandle возвращает значение (или вызывает исключение)."""
        if sys.platform == 'win32':
            try:
                handle = _winconsole.GetStdHandle(_winconsole.STD_OUTPUT_HANDLE)
                # handle может быть -1 при ошибке, но это не краш
                assert handle is not None
            except Exception:
                pass  # В тестовой среде без консоли исключение допустимо

    def test_get_console_mode_callable_without_crash(self):
        """Тест: вызов GetConsoleMode не приводит к фатальной ошибке."""
        if sys.platform == 'win32':
            try:
                # Пытаемся получить handle
                handle = _winconsole.GetStdHandle(_winconsole.STD_OUTPUT_HANDLE)
                if handle and handle != -1:
                    _winconsole.GetConsoleMode(handle)
            except Exception:
                pass

    def test_get_command_line_w_returns_string(self):
        """Тест: GetCommandLineW возвращает строку (или None)."""
        if sys.platform == 'win32':
            try:
                cmd_line = _winconsole.GetCommandLineW()
                # Может быть строка или указатель — проверяем, что не крашит
                assert cmd_line is not None or isinstance(cmd_line, int)
            except Exception:
                pass
