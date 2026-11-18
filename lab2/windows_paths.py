"""Проверка синтаксиса полных путей к файлам Windows."""

import re

SEPARATOR = r"[\\/]"
DRIVE = rf"[A-Za-z]:{SEPARATOR}"
HOST_LABEL = r"\w(?:[\w-]*\w)?"
HOST = rf"{HOST_LABEL}(?:\.{HOST_LABEL})*"
INVALID_NAME_CHARS = r'<>:"/\\|?*\x00-\x1f\ud800-\udfff'
NAME = rf"[^{INVALID_NAME_CHARS}]{{0,254}}[^{INVALID_NAME_CHARS} .]"
UNC = rf"{SEPARATOR}{{2}}{HOST}{SEPARATOR}{NAME}{SEPARATOR}"

RESERVED = r"(?ai:CON|PRN|AUX|NUL|(?:COM|LPT)[1-9¹²³])"
# Зарезервированное имя нельзя использовать с расширением и без него.
COMPONENT = rf"(?!{RESERVED}[ ]*(?:\.|{SEPARATOR}|\Z)){NAME}"
DIRECTORY = rf"(?:{COMPONENT}|\.{{1,2}})"
PATH_PATTERN = re.compile(
    rf"(?:{DRIVE}|{UNC})(?:{DIRECTORY}{SEPARATOR})*{COMPONENT}"
)

MAX_COMPONENT_UNITS = 255


def is_valid_path(value: str) -> bool:
    """Проверить путь без обращения к файловой системе."""
    if PATH_PATTERN.fullmatch(value) is None:
        return False

    # Дополнительный символ Unicode может занимать две единицы UTF-16.
    components = re.split(SEPARATOR, value)
    return all(
        len(component.encode("utf-16-le")) // 2 <= MAX_COMPONENT_UNITS
        for component in components
    )
