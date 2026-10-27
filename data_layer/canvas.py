"""Сущность «Холст» — параметры рисунка."""

from __future__ import annotations

import copy

from .primitives import Color, Point, compact, to_number


class Canvas:
    """Холст: название рисунка, размеры, цвет фона и активный слой."""

    def __init__(self, title: str = "Без названия", width: float = 800, height: float = 600,
                 background: Color | None = None, active_layer: str = ""):
        self.title = title
        self.width = width
        self.height = height
        self.background = background if background is not None else Color(255, 255, 255)
        self.active_layer = active_layer

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value) -> None:
        self._title = str(value).strip() or "Без названия"

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value) -> None:
        self._width = self._check_size(value, "Ширина холста")

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value) -> None:
        self._height = self._check_size(value, "Высота холста")

    @staticmethod
    def _check_size(value, name: str) -> float:
        value = to_number(value, name)
        if value <= 0:
            raise ValueError(f"{name} должна быть больше нуля")
        return value

    def contains_box(self, top_left: Point, bottom_right: Point) -> bool:
        """Целиком ли прямоугольная область лежит на холсте."""
        return (top_left.x >= 0 and top_left.y >= 0
                and bottom_right.x <= self.width and bottom_right.y <= self.height)

    def clone(self) -> Canvas:
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "width": compact(self.width),
            "height": compact(self.height),
            "background": self.background.to_hex(),
            "active_layer": self.active_layer,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Canvas:
        return cls(data.get("title", "Без названия"), data["width"], data["height"],
                   Color.from_hex(data.get("background", "#FFFFFF")),
                   data.get("active_layer") or "")

    def __str__(self) -> str:
        return (f"Рисунок «{self.title}» {compact(self.width)}x{compact(self.height)}, "
                f"фон {self.background}")
