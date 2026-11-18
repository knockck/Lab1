import unittest

from lab2.windows_paths import is_valid_path


class WindowsPathTests(unittest.TestCase):
    def test_absolute_drive_paths(self):
        for value in (
            r"C:\report.txt",
            r"d:\Учёба\Лабораторная работа\Отчёт.docx",
            r"Z:\Program Files\App\LICENSE",
            r"E:\.env",
            r"G:\data\new (final) #2.tar.gz",
            r"C:\folder\..\file.txt",
            r"C:\.\folder\file.txt",
            r"C:/Folder\test.txt",
            r"C:\files\COM10.txt",
            r"C:\files\summary.CON",
            r"C:\files\ком1.txt",
            r"C:\files\LPT0",
        ):
            with self.subTest(value=value):
                self.assertTrue(is_valid_path(value))

    def test_absolute_unc_paths(self):
        for value in (
            r"\\server\share\readme",
            r"\\my-host.example.org\Общие документы\отчёт.docx",
            r"\\192.168.1.20\C$\archive\backup.zip",
            r"\\nas_1\share\..\file",
            "//server/share/folder/sample.txt",
        ):
            with self.subTest(value=value):
                self.assertTrue(is_valid_path(value))

    def test_rejects_relative_incomplete_and_special_paths(self):
        for value in (
            "",
            "file.txt",
            r"dir\file.txt",
            r"\dir\file.txt",
            r"C:file.txt",
            "C:",
            "C:\\",
            "C:/data/",
            r"\\server",
            r"\\server\share",
            "\\\\server\\share\\",
            r"\\?\C:\file.txt",
            r"\\.\C:\file.txt",
            r"\\.\COM1",
            r"file://C:/file.txt",
            r"1:\file.txt",
            r"С:\file.txt",
            r"C:\dir\\file.txt",
            r"C:\dir\.",
            r"C:\dir\..",
            r"\\bad host\share\file",
            r"\\server\.\file",
        ):
            with self.subTest(value=value):
                self.assertFalse(is_valid_path(value))

    def test_rejects_forbidden_characters_and_endings(self):
        for char in '<>:"|?*\x00\t\n\x1f\ud800':
            with self.subTest(char=repr(char)):
                self.assertFalse(is_valid_path(fr"C:\dir\a{char}b.txt"))

        for value in (
            "C:\\file.txt.",
            "C:\\file.txt ",
            r"C:\dir.\file",
            r"C:\dir \file",
            '"C:\\file.txt"',
            " C:\\file.txt",
            "C:\\file.txt\n",
            r"C:\file.txt:stream",
        ):
            with self.subTest(value=value):
                self.assertFalse(is_valid_path(value))

    def test_rejects_reserved_names_regardless_of_case_or_extension(self):
        for name in ("CON", "prn.txt", "AuX", "NUL.tar.gz", "NUL .txt"):
            with self.subTest(name=name):
                self.assertFalse(is_valid_path(fr"C:\dir\{name}"))
                self.assertFalse(is_valid_path(fr"C:\{name}\file.txt"))

        for digit in "123456789¹²³":
            with self.subTest(digit=digit):
                self.assertFalse(is_valid_path(fr"C:\COM{digit}.txt"))
                self.assertFalse(is_valid_path(fr"\\srv\share\lpt{digit}"))

    def test_component_length_counts_utf16_units(self):
        prefix = "C:\\"
        self.assertTrue(is_valid_path(prefix + "a" * 255))
        self.assertFalse(is_valid_path(prefix + "a" * 256))
        self.assertTrue(is_valid_path(prefix + "🔹" * 127 + "a"))
        self.assertFalse(is_valid_path(prefix + "🔹" * 128))
        self.assertTrue(is_valid_path(prefix + ("a" * 150 + "\\") * 2 + "b"))
