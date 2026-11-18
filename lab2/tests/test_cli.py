import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from runpy import run_module
from tempfile import TemporaryDirectory
from unittest.mock import patch

from lab2.cli import main


class ConsoleTests(unittest.TestCase):
    def run_menu(self, inputs):
        output = StringIO()
        with patch("builtins.input", side_effect=inputs):
            with redirect_stdout(output):
                main()
        return output.getvalue()

    def test_menu_checks_valid_and_invalid_input(self):
        output = self.run_menu(
            (" 1 ", r"C:\test.txt", "1", r"C:test.txt", "?", "0")
        )
        self.assertIn("Путь корректен.", output)
        self.assertIn("Путь некорректен.", output)
        self.assertIn("Выберите 1, 2 или 0.", output)
        self.assertIn("Работа завершена.", output)

    def test_menu_searches_file_and_handles_errors(self):
        with TemporaryDirectory() as tmp:
            text_file = Path(tmp) / "test file.txt"
            empty_file = Path(tmp) / "empty.txt"
            wrong_encoding = Path(tmp) / "wrong.txt"
            text_file.write_text(r"C:\test.txt", encoding="utf-8")
            empty_file.touch()
            wrong_encoding.write_bytes(b"\xffinvalid")
            output = self.run_menu((
                "2", f'"{text_file}"', "2", str(empty_file),
                "2", str(wrong_encoding), "2", str(Path(tmp) / "missing.txt"),
                "0",
            ))
        self.assertIn("Найдено вхождений: 1", output)
        self.assertIn(r"Строка 1, столбец 1: C:\test.txt", output)
        self.assertIn("Найдено вхождений: 0", output)
        self.assertIn("Ошибка чтения:", output)
        self.assertIn("Ошибка открытия файла:", output)

    def test_menu_handles_keyboard_interrupt_and_end_of_input(self):
        for error in (KeyboardInterrupt, EOFError):
            with self.subTest(error=error):
                output = self.run_menu(error)
                self.assertIn("Работа завершена.", output)

    def test_module_entry_point(self):
        with patch("lab2.cli.main") as entry_point:
            run_module("lab2", run_name="__main__")
        entry_point.assert_called_once_with()
