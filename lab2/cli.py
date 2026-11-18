"""Консольное меню лабораторной работы."""

from pathlib import Path

from .search import find_in_file
from .windows_paths import is_valid_path

MENU = "\n1. Проверить путь\n2. Найти пути в текстовом файле\n0. Выход"


def show_file_matches() -> None:
    file_name = input("Путь к текстовому файлу: ").strip()
    if file_name.startswith('"') and file_name.endswith('"'):
        file_name = file_name[1:-1]

    try:
        matches = list(find_in_file(Path(file_name)))
    except UnicodeDecodeError:
        print("Ошибка чтения: используйте UTF-8 или UTF-16 с BOM.")
        return
    except (OSError, ValueError) as error:
        print(f"Ошибка открытия файла: {error}")
        return

    print(f"Найдено вхождений: {len(matches)}")
    for match in matches:
        print(f"Строка {match.line}, столбец {match.column}: {match.path}")


def main() -> None:
    print("Лабораторная работа № 2 · Windows-пути · вариант 19")
    try:
        while True:
            print(MENU)
            choice = input("Ваш выбор: ").strip()
            if choice == "0":
                break
            if choice == "1":
                value = input("Полный путь Windows: ")
                if is_valid_path(value):
                    print("Путь корректен.")
                else:
                    print("Путь некорректен.")
            elif choice == "2":
                show_file_matches()
            else:
                print("Выберите 1, 2 или 0.")
    except (EOFError, KeyboardInterrupt):
        print()
    print("Работа завершена.")
