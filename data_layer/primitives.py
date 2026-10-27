"""Базовые примитивы графического редактора: точка, цвет и стиль отрисовки."""

from __future__ import annotations

import math
import re

from exceptions import InvalidColorError, InvalidShapeError


def to_number(value, name: str) -> float:
    """Приводит значение к числу.

    Бросает встроенные исключения:
    TypeError  — если передан объект неподходящего типа;
    ValueError — если строку нельзя прочитать как число.
    """
    if isinstance(value, bool):
        raise TypeError(f"{name}: ожидалось число, получено логическое значение")
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip().replace(",", "."))
        except ValueError:
            raise ValueError(f"{name}: «{value}» не является числом") from None
    else:
        raise TypeError(f"{name}: ожидалось число, получено {type(value).__name__}")
    if not math.isfinite(number):
        raise ValueError(f"{name}: значение должно быть конечным числом")
    return number


def compact(number: float):
    """Возвращает int, если число целое (чтобы в файлах было 10, а не 10.0)."""
    return int(number) if float(number).is_integer() else round(number, 3)


class Point:
    """Точка на холсте (координаты в пикселях)."""

    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value) -> None:
        self._x = to_number(value, "x")

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value) -> None:
        self._y = to_number(value, "y")

    def moved(self, dx: float, dy: float) -> Point:
        """Возвращает новую точку, сдвинутую на (dx, dy)."""
        return Point(self.x + dx, self.y + dy)

    def distance_to(self, other: Point) -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def to_dict(self) -> dict:
        return {"x": compact(self.x), "y": compact(self.y)}

    @classmethod
    def from_dict(cls, data: dict) -> Point:
        return cls(data["x"], data["y"])

    def __eq__(self, other) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)

    def __repr__(self) -> str:
        return f"Point({compact(self.x)}, {compact(self.y)})"

    def __str__(self) -> str:
        return f"({compact(self.x)}; {compact(self.y)})"


class Color:
    """Цвет в модели RGBA (каждая компонента 0..255)."""

    NAMED = {
        "black": "#000000", "черный": "#000000", "чёрный": "#000000",
        "white": "#FFFFFF", "белый": "#FFFFFF",
        "red": "#FF0000", "красный": "#FF0000",
        "green": "#008000", "зеленый": "#008000", "зелёный": "#008000",
        "blue": "#0000FF", "синий": "#0000FF",
        "yellow": "#FFFF00", "желтый": "#FFFF00", "жёлтый": "#FFFF00",
        "orange": "#FFA500", "оранжевый": "#FFA500",
        "gray": "#808080", "серый": "#808080",
        "brown": "#8B4513", "коричневый": "#8B4513",
        "skyblue": "#87CEEB", "голубой": "#87CEEB",
    }
    _HEX_PATTERN = re.compile(r"^#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?$")

    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        self._r = self._check_component(r)
        self._g = self._check_component(g)
        self._b = self._check_component(b)
        self._a = self._check_component(a)

    @staticmethod
    def _check_component(value) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
            raise InvalidColorError(value)
        return value

    # Свойства только для чтения: цвет неизменяемый (как строка или число)
    @property
    def r(self) -> int:
        return self._r

    @property
    def g(self) -> int:
        return self._g

    @property
    def b(self) -> int:
        return self._b

    @property
    def a(self) -> int:
        return self._a

    @classmethod
    def from_hex(cls, text: str) -> Color:
        """Создаёт цвет из строки вида #RRGGBB или #RRGGBBAA."""
        match = cls._HEX_PATTERN.match(str(text).strip())
        if match is None:
            raise InvalidColorError(text)
        rgb, alpha = match.groups()
        return cls(int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16),
                   int(alpha, 16) if alpha else 255)

    @classmethod
    def parse(cls, text: str) -> Color:
        """Создаёт цвет из HEX-строки или названия цвета."""
        text = str(text).strip()
        return cls.from_hex(cls.NAMED.get(text.lower(), text))

    def to_hex(self) -> str:
        result = f"#{self._r:02X}{self._g:02X}{self._b:02X}"
        if self._a != 255:
            result += f"{self._a:02X}"
        return result

    def __eq__(self, other) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return (self._r, self._g, self._b, self._a) == (other.r, other.g, other.b, other.a)

    def __hash__(self) -> int:
        return hash((self._r, self._g, self._b, self._a))

    def __repr__(self) -> str:
        return f"Color.from_hex('{self.to_hex()}')"

    def __str__(self) -> str:
        return self.to_hex()


class Style:
    """Стиль отрисовки фигуры: цвет контура, цвет заливки, толщина линии."""

    def __init__(self, stroke: Color | None = None, fill: Color | None = None,
                 stroke_width: float = 1):
        self.stroke = stroke if stroke is not None else Color(0, 0, 0)
        self.fill = fill  # None — фигура без заливки
        self.stroke_width = stroke_width

    @property
    def stroke_width(self) -> float:
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, value) -> None:
        value = to_number(value, "толщина линии")
        if value < 0:
            raise InvalidShapeError("Толщина линии не может быть отрицательной")
        self._stroke_width = value

    def copy(self) -> Style:
        return Style(self.stroke, self.fill, self.stroke_width)

    def to_dict(self) -> dict:
        return {
            "stroke": self.stroke.to_hex(),
            "fill": self.fill.to_hex() if self.fill is not None else None,
            "stroke_width": compact(self.stroke_width),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Style:
        fill = data.get("fill")
        return cls(
            stroke=Color.from_hex(data["stroke"]),
            fill=Color.from_hex(fill) if fill else None,
            stroke_width=data.get("stroke_width", 1),
        )

    def __str__(self) -> str:
        fill = self.fill.to_hex() if self.fill is not None else "нет"
        return f"контур {self.stroke}, заливка {fill}, толщина {compact(self.stroke_width)}"
