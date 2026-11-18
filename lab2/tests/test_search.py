import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from lab2.search import PathMatch, find_in_file, find_paths


class PathSearchTests(unittest.TestCase):
    def test_find_preserves_positions_and_order(self):
        lines = [
            'Файл: "C:\\Program Files\\App\\LICENSE"\r\n',
            "   E:\\Мои документы\\отчёт.txt\n",
            "Копии: D:\\a.txt, (\\\\nas\\share\\file)\n",
            "Файл: D:\\a.txt;\n",
        ]
        self.assertEqual(
            list(find_paths(lines)),
            [
                PathMatch(r"C:\Program Files\App\LICENSE", 1, 8),
                PathMatch(r"E:\Мои документы\отчёт.txt", 2, 4),
                PathMatch(r"D:\a.txt", 3, 8),
                PathMatch(r"\\nas\share\file", 3, 19),
                PathMatch(r"D:\a.txt", 4, 7),
            ],
        )

    def test_rejects_invalid_tokens_and_prefixes(self):
        lines = [
            r'Ошибки: "C:\Program Files\AUX.txt" D:\bad?.txt C:\ok|bad',
            r'Ошибки: C:relative.txt xC:\file.txt C:\dir.\file.txt',
            r'Ошибки: \\?\C:\secret.txt C:\folder\ C:\file.txt.',
            r'Незакрытая кавычка: "C:\Program Files\file.txt',
            "",
        ]
        self.assertEqual(list(find_paths(lines)), [])

    def test_preserves_quoted_punctuation_and_allows_wrapped_path(self):
        line = r'Имена: "C:\file," D:\file(1).txt [E:\readme]'
        self.assertEqual(
            [match.path for match in find_paths([line])],
            [r"C:\file,", r"D:\file(1).txt", r"E:\readme"],
        )

    def test_reads_supported_encodings(self):
        line = "Файл: C:\\Учёба\\отчёт.txt\n"
        for encoding in ("utf-8", "utf-8-sig", "utf-16"):
            with self.subTest(encoding=encoding), TemporaryDirectory() as tmp:
                file_path = Path(tmp) / "test.txt"
                file_path.write_bytes(line.encode(encoding))
                self.assertEqual(
                    list(find_in_file(file_path)),
                    [PathMatch(r"C:\Учёба\отчёт.txt", 1, 7)],
                )

    def test_propagates_reading_errors(self):
        with TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "test.txt"
            with self.assertRaises(FileNotFoundError):
                list(find_in_file(file_path))
            file_path.write_bytes(b"\xffinvalid")
            with self.assertRaises(UnicodeDecodeError):
                list(find_in_file(file_path))
