"""Сущности-фигуры графического редактора.

Shape — абстрактный базовый класс. Конкретные фигуры по-своему вычисляют
площадь и периметр, перемещаются, масштабируются и проверяют попадание
точки в фигуру (полиморфизм).
"""

from __future__ import annotations

import copy
import math
from abc import ABC, abstractmethod

from .primitives import Point, Style, compact, to_number


def _positive(value, name: str) -> float:
    value = to_number(value, name)
    if value <= 0:
        raise ValueError(f"{name} должна быть больше нуля (получено {compact(value)})")
    return value


class Shape(ABC):
    """Абстрактная фигура на холсте.

    id назначает репозиторий при добавлении фигуры, layer — имя слоя,
    которому принадлежит фигура, z_index — порядок отрисовки внутри слоя.
    """

    TITLE = "Фигура"   # название типа для пользователя

    def __init__(self, style: Style | None = None, name: str = "", visible: bool = True,
                 shape_id: int | None = None, layer: str = "", z_index: int = 0):
        self.id = shape_id
        self.style = style if style is not None else Style()
        self.name = name
        self.visible = bool(visible)
        self.layer = layer
        self.z_index = int(z_index)

    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, value) -> None:
        if value is not None:
            value = int(value)
            if value <= 0:
                raise ValueError(
                    f"Идентификатор фигуры должен быть положительным (получено {value})")
        self._id = value

    @property
    def name(self) -> str:
        return self._name or f"{self.TITLE} {self.id or ''}".strip()

    @name.setter
    def name(self, value) -> None:
        self._name = str(value).strip()

    # ---- абстрактные методы: каждая фигура реализует их по-своему ----
    @abstractmethod
    def area(self) -> float:
        """Площадь фигуры."""

    @abstractmethod
    def perimeter(self) -> float:
        """Периметр (длина контура) фигуры."""

    @abstractmethod
    def move(self, dx: float, dy: float) -> None:
        """Сдвигает фигуру на (dx, dy)."""

    @abstractmethod
    def scale(self, factor: float) -> None:
        """Масштабирует фигуру относительно её опорной точки."""

    @abstractmethod
    def bounding_box(self) -> tuple[Point, Point]:
        """Ограничивающий прямоугольник: (левый верхний, правый нижний)."""

    @abstractmethod
    def geometry_to_dict(self) -> dict:
        """Геометрические параметры фигуры в виде словаря."""

    @classmethod
    @abstractmethod
    def build(cls, data: dict, **common) -> Shape:
        """Создаёт фигуру своего класса из словаря."""

    # ---- общие методы ----
    def contains_point(self, point: Point) -> bool:
        """Попадает ли точка в фигуру (по умолчанию — в ограничивающий прямоугольник)."""
        top_left, bottom_right = self.bounding_box()
        return (top_left.x <= point.x <= bottom_right.x
                and top_left.y <= point.y <= bottom_right.y)

    @staticmethod
    def check_factor(factor) -> float:
        factor = to_number(factor, "коэффициент масштабирования")
        if factor <= 0:
            raise ValueError("Коэффициент масштабирования должен быть больше нуля")
        return factor

    def clone(self) -> Shape:
        """Полная независимая копия фигуры."""
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return {
            "type": type(self).__name__,
            "id": self.id,
            "name": self.name,
            "visible": self.visible,
            "style": self.style.to_dict(),
            "geometry": self.geometry_to_dict(),
        }

    @staticmethod
    def from_dict(data: dict, layer: str = "", z_index: int = 0) -> Shape:
        """Создаёт фигуру нужного класса по полю "type"."""
        type_name = data["type"]
        shape_class = SHAPE_TYPES.get(type_name)
        if shape_class is None:
            raise ValueError(f"Неизвестный тип фигуры: {type_name!r}")
        return shape_class.build(
            data,
            style=Style.from_dict(data["style"]),
            name=data.get("name", ""),
            visible=data.get("visible", True),
            shape_id=data.get("id"),
            layer=layer,
            z_index=z_index,
        )

    def geometry_text(self) -> str:
        return ", ".join(f"{key}={value}" for key, value in self.geometry_to_dict().items())

    def __str__(self) -> str:
        hidden = "" if self.visible else " [скрыта]"
        return (f"#{self.id} {self.TITLE} «{self.name}»{hidden}: {self.geometry_text()}; "
                f"S = {self.area():.2f}, P = {self.perimeter():.2f}")

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.id} layer={self.layer!r}>"


# Реестр типов фигур: имя класса -> класс (используется при чтении из файла)
SHAPE_TYPES: dict[str, type[Shape]] = {}
