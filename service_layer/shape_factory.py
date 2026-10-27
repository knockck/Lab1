"""Фабрика фигур: создаёт сущности по названию типа и параметрам из интерфейса.

Интерфейс не знает о классах сущностей: он спрашивает у фабрики список
типов и их параметры, а затем передаёт введённые значения обратно.
"""

from __future__ import annotations

from typing import Callable, NamedTuple

from data_layer import (Circle, Ellipse, Line, Point, Polygon, Rectangle, Shape, Style,
                        TextLabel)


class Param(NamedTuple):
    """Описание параметра фигуры: имя, подсказка и вид значения."""

    name: str
    prompt: str
    kind: str        # "number" | "point" | "points" | "text"
    default: object = None


class ShapeKind(NamedTuple):
    title: str
    params: list[Param]
    build: Callable[[dict, Style], Shape]


def _point(value) -> Point:
    x, y = value
    return Point(x, y)


class ShapeFactory:
    """Создание фигур по описанию типа."""

    KINDS: dict[str, ShapeKind] = {
        "rectangle": ShapeKind("Прямоугольник", [
            Param("top_left", "Левый верхний угол", "point"),
            Param("width", "Ширина", "number"),
            Param("height", "Высота", "number"),
        ], lambda p, s: Rectangle(_point(p["top_left"]), p["width"], p["height"], style=s)),
        "ellipse": ShapeKind("Эллипс", [
            Param("center", "Центр", "point"),
            Param("rx", "Полуось rx", "number"),
            Param("ry", "Полуось ry", "number"),
        ], lambda p, s: Ellipse(_point(p["center"]), p["rx"], p["ry"], style=s)),
        "circle": ShapeKind("Круг", [
            Param("center", "Центр", "point"),
            Param("radius", "Радиус", "number"),
        ], lambda p, s: Circle(_point(p["center"]), p["radius"], style=s)),
        "line": ShapeKind("Линия", [
            Param("start", "Начало", "point"),
            Param("end", "Конец", "point"),
        ], lambda p, s: Line(_point(p["start"]), _point(p["end"]), style=s)),
        "polygon": ShapeKind("Многоугольник", [
            Param("points", "Вершины", "points"),
        ], lambda p, s: Polygon([_point(item) for item in p["points"]], style=s)),
        "text": ShapeKind("Текст", [
            Param("position", "Позиция", "point"),
            Param("text", "Текст", "text"),
            Param("font_size", "Размер шрифта", "number", 14),
        ], lambda p, s: TextLabel(_point(p["position"]), p["text"], p["font_size"], style=s)),
    }

    def kinds(self) -> list[tuple[str, str]]:
        """Список (ключ, название) доступных типов фигур."""
        return [(key, kind.title) for key, kind in self.KINDS.items()]

    def params(self, kind: str) -> list[Param]:
        return list(self._kind(kind).params)

    def create(self, kind: str, params: dict, style: Style) -> Shape:
        return self._kind(kind).build(params, style)

    def _kind(self, kind: str) -> ShapeKind:
        if kind not in self.KINDS:
            raise ValueError(f"Неизвестный тип фигуры: {kind!r}")
        return self.KINDS[kind]
