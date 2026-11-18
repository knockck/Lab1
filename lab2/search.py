"""Поиск полных путей и их позиций в строках текстового файла."""

import re
from codecs import BOM_UTF16_BE, BOM_UTF16_LE
from dataclasses import dataclass
from io import TextIOWrapper
from pathlib import Path
from typing import Iterable, Iterator

from .windows_paths import is_valid_path

# Незакрытая кавычка поглощает остаток строки, чтобы не искать внутри неё.
TOKEN = re.compile(r'"(?P<quoted>[^"]*)"|"[^"]*$|(?P<bare>[^\s"]+)')
WRAPPERS = {"(": ")", "[": "]", "{": "}", "<": ">"}


@dataclass(frozen=True)
class PathMatch:
    path: str
    line: int
    column: int


def find_paths(lines: Iterable[str]) -> Iterator[PathMatch]:
    """Вернуть вхождения по порядку с номерами строк и столбцов от 1."""
    for line_number, line in enumerate(lines, start=1):
        line = line.rstrip("\r\n")
        whole_line = line.strip(" \t")
        if is_valid_path(whole_line):
            indentation = len(line) - len(line.lstrip(" \t"))
            yield PathMatch(whole_line, line_number, indentation + 1)
            continue

        for token in TOKEN.finditer(line):
            quoted = token.group("quoted")
            bare = token.group("bare")
            if quoted is not None:
                candidate = quoted
                start = token.start("quoted")
            elif bare is not None:
                candidate = bare.rstrip(",;")
                start = token.start("bare")
                closing = WRAPPERS.get(candidate[:1])
                if closing is not None and candidate.endswith(closing):
                    candidate = candidate[1:-1]
                    start += 1
            else:
                continue

            if is_valid_path(candidate):
                yield PathMatch(candidate, line_number, start + 1)


def find_in_file(file_path: Path) -> Iterator[PathMatch]:
    """Прочитать UTF-8 или UTF-16 с BOM, не загружая весь файл в память."""
    with file_path.open("rb") as stream:
        has_utf16_bom = stream.peek(2).startswith((BOM_UTF16_LE, BOM_UTF16_BE))
        encoding = "utf-16" if has_utf16_bom else "utf-8-sig"
        with TextIOWrapper(stream, encoding=encoding) as lines:
            yield from find_paths(lines)
