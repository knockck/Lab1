"""Сущности-фигуры графического редактора.

Shape — абстрактный базовый класс. Конкретные фигуры по-своему вычисляют
площадь и периметр, перемещаются, масштабируются и проверяют попадание
точки в фигуру (полиморфизм).
"""

from __future__ import annotations

import copy
import math
from abc import ABC, abstractmethod

from exceptions import InvalidShapeError, UnknownShapeTypeError
from .primitives import Point, Style, compact, to_number


def _positive(value, name: str) -> float:
    value = to_number(value, name)
    if value <= 0:
        raise InvalidShapeError(f"{name} должна быть больше нуля (получено {compact(value)})")
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
                raise InvalidShapeError(
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
            raise InvalidShapeError("Коэффициент масштабирования должен быть больше нуля")
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
            raise UnknownShapeTypeError(type_name)
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


class Rectangle(Shape):
    """Прямоугольник, заданный левым верхним углом, шириной и высотой."""

    TITLE = "Прямоугольник"

    def __init__(self, top_left: Point, width: float, height: float, **common):
        self.top_left = top_left
        self.width = width
        self.height = height
        super().__init__(**common)

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value) -> None:
        self._width = _positive(value, "Ширина")

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value) -> None:
        self._height = _positive(value, "Высота")

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

    def move(self, dx: float, dy: float) -> None:
        self.top_left = self.top_left.moved(dx, dy)

    def scale(self, factor: float) -> None:
        factor = self.check_factor(factor)
        self.width *= factor
        self.height *= factor

    def bounding_box(self) -> tuple[Point, Point]:
        return self.top_left, self.top_left.moved(self.width, self.height)

    def geometry_to_dict(self) -> dict:
        return {"x": compact(self.top_left.x), "y": compact(self.top_left.y),
                "width": compact(self.width), "height": compact(self.height)}

    @classmethod
    def build(cls, data: dict, **common) -> Rectangle:
        geometry = data["geometry"]
        return cls(Point(geometry["x"], geometry["y"]),
                   geometry["width"], geometry["height"], **common)


class Ellipse(Shape):
    """Эллипс, заданный центром и двумя полуосями."""

    TITLE = "Эллипс"

    def __init__(self, center: Point, rx: float, ry: float, **common):
        self.center = center
        self.rx = rx
        self.ry = ry
        super().__init__(**common)

    @property
    def rx(self) -> float:
        return self._rx

    @rx.setter
    def rx(self, value) -> None:
        self._rx = _positive(value, "Полуось rx")

    @property
    def ry(self) -> float:
        return self._ry

    @ry.setter
    def ry(self, value) -> None:
        self._ry = _positive(value, "Полуось ry")

    def area(self) -> float:
        return math.pi * self.rx * self.ry

    def perimeter(self) -> float:
        # Приближённая формула Рамануджана
        a, b = self.rx, self.ry
        return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))

    def move(self, dx: float, dy: float) -> None:
        self.center = self.center.moved(dx, dy)

    def scale(self, factor: float) -> None:
        factor = self.check_factor(factor)
        self.rx *= factor
        self.ry *= factor

    def bounding_box(self) -> tuple[Point, Point]:
        return self.center.moved(-self.rx, -self.ry), self.center.moved(self.rx, self.ry)

    def contains_point(self, point: Point) -> bool:
        # Точная проверка по уравнению эллипса вместо ограничивающего прямоугольника
        dx = (point.x - self.center.x) / self.rx
        dy = (point.y - self.center.y) / self.ry
        return dx * dx + dy * dy <= 1

    def geometry_to_dict(self) -> dict:
        return {"cx": compact(self.center.x), "cy": compact(self.center.y),
                "rx": compact(self.rx), "ry": compact(self.ry)}

    @classmethod
    def build(cls, data: dict, **common) -> Ellipse:
        geometry = data["geometry"]
        return cls(Point(geometry["cx"], geometry["cy"]),
                   geometry["rx"], geometry["ry"], **common)


class Circle(Ellipse):
    """Круг — частный случай эллипса с равными полуосями."""

    TITLE = "Круг"

    def __init__(self, center: Point, radius: float, **common):
        super().__init__(center, radius, radius, **common)

    @property
    def radius(self) -> float:
        return self.rx

    def perimeter(self) -> float:
        # Для круга есть точная формула — переопределяем метод родителя
        return 2 * math.pi * self.radius

    def geometry_to_dict(self) -> dict:
        return {"cx": compact(self.center.x), "cy": compact(self.center.y),
                "r": compact(self.radius)}

    @classmethod
    def build(cls, data: dict, **common) -> Circle:
        geometry = data["geometry"]
        return cls(Point(geometry["cx"], geometry["cy"]), geometry["r"], **common)


class Line(Shape):
    """Отрезок между двумя точками."""

    TITLE = "Линия"
    HIT_TOLERANCE = 3  # на каком расстоянии от линии точка считается попаданием

    def __init__(self, start: Point, end: Point, **common):
        if start == end:
            raise InvalidShapeError("Начало и конец линии не должны совпадать")
        self.start = start
        self.end = end
        super().__init__(**common)

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def area(self) -> float:
        return 0.0

    def perimeter(self) -> float:
        return self.length()

    def move(self, dx: float, dy: float) -> None:
        self.start = self.start.moved(dx, dy)
        self.end = self.end.moved(dx, dy)

    def scale(self, factor: float) -> None:
        factor = self.check_factor(factor)
        dx, dy = self.end.x - self.start.x, self.end.y - self.start.y
        self.end = self.start.moved(dx * factor, dy * factor)

    def bounding_box(self) -> tuple[Point, Point]:
        return (Point(min(self.start.x, self.end.x), min(self.start.y, self.end.y)),
                Point(max(self.start.x, self.end.x), max(self.start.y, self.end.y)))

    def contains_point(self, point: Point) -> bool:
        # Расстояние от точки до отрезка
        dx, dy = self.end.x - self.start.x, self.end.y - self.start.y
        t = ((point.x - self.start.x) * dx + (point.y - self.start.y) * dy) / (dx ** 2 + dy ** 2)
        t = max(0.0, min(1.0, t))
        nearest = Point(self.start.x + t * dx, self.start.y + t * dy)
        tolerance = max(self.HIT_TOLERANCE, self.style.stroke_width / 2)
        return nearest.distance_to(point) <= tolerance

    def geometry_to_dict(self) -> dict:
        return {"x1": compact(self.start.x), "y1": compact(self.start.y),
                "x2": compact(self.end.x), "y2": compact(self.end.y)}

    @classmethod
    def build(cls, data: dict, **common) -> Line:
        geometry = data["geometry"]
        return cls(Point(geometry["x1"], geometry["y1"]),
                   Point(geometry["x2"], geometry["y2"]), **common)


class Polygon(Shape):
    """Многоугольник, заданный списком вершин."""

    TITLE = "Многоугольник"

    def __init__(self, points: list[Point], **common):
        points = list(points)
        if len(points) < 3:
            raise InvalidShapeError(
                f"У многоугольника должно быть не меньше 3 вершин (получено {len(points)})")
        self._points = points
        if math.isclose(self.area(), 0.0, abs_tol=1e-9):
            raise InvalidShapeError("Вершины многоугольника лежат на одной прямой")
        super().__init__(**common)

    @property
    def points(self) -> tuple[Point, ...]:
        return tuple(self._points)

    def _edges(self):
        return zip(self._points, self._points[1:] + self._points[:1])

    def area(self) -> float:
        # Формула площади Гаусса («шнурования»)
        total = sum(a.x * b.y - b.x * a.y for a, b in self._edges())
        return abs(total) / 2

    def perimeter(self) -> float:
        return sum(a.distance_to(b) for a, b in self._edges())

    def centroid(self) -> Point:
        count = len(self._points)
        return Point(sum(p.x for p in self._points) / count,
                     sum(p.y for p in self._points) / count)

    def move(self, dx: float, dy: float) -> None:
        self._points = [point.moved(dx, dy) for point in self._points]

    def scale(self, factor: float) -> None:
        factor = self.check_factor(factor)
        center = self.centroid()
        self._points = [Point(center.x + (p.x - center.x) * factor,
                              center.y + (p.y - center.y) * factor) for p in self._points]

    def bounding_box(self) -> tuple[Point, Point]:
        xs = [p.x for p in self._points]
        ys = [p.y for p in self._points]
        return Point(min(xs), min(ys)), Point(max(xs), max(ys))

    def contains_point(self, point: Point) -> bool:
        # Метод трассировки луча: считаем пересечения луча вправо с рёбрами
        inside = False
        for a, b in self._edges():
            if (a.y > point.y) != (b.y > point.y):
                x_cross = a.x + (point.y - a.y) * (b.x - a.x) / (b.y - a.y)
                if point.x < x_cross:
                    inside = not inside
        return inside

    def geometry_to_dict(self) -> dict:
        return {"points": [point.to_dict() for point in self._points]}

    def geometry_text(self) -> str:
        return "вершины " + ", ".join(str(point) for point in self._points)

    @classmethod
    def build(cls, data: dict, **common) -> Polygon:
        return cls([Point.from_dict(item) for item in data["geometry"]["points"]], **common)


class TextLabel(Shape):
    """Текстовая надпись на холсте."""

    TITLE = "Текст"
    CHAR_WIDTH = 0.6  # средняя ширина символа относительно размера шрифта

    def __init__(self, position: Point, text: str, font_size: float = 14,
                 font_family: str = "Arial", **common):
        self.position = position
        self.text = text
        self.font_size = font_size
        self.font_family = font_family
        super().__init__(**common)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value) -> None:
        value = str(value)
        if not value.strip():
            raise InvalidShapeError("Текст надписи не может быть пустым")
        self._text = value

    @property
    def font_size(self) -> float:
        return self._font_size

    @font_size.setter
    def font_size(self, value) -> None:
        self._font_size = _positive(value, "Размер шрифта")

    def _size(self) -> tuple[float, float]:
        return len(self.text) * self.font_size * self.CHAR_WIDTH, self.font_size

    def area(self) -> float:
        width, height = self._size()
        return width * height

    def perimeter(self) -> float:
        width, height = self._size()
        return 2 * (width + height)

    def move(self, dx: float, dy: float) -> None:
        self.position = self.position.moved(dx, dy)

    def scale(self, factor: float) -> None:
        self.font_size *= self.check_factor(factor)

    def bounding_box(self) -> tuple[Point, Point]:
        width, height = self._size()
        return self.position, self.position.moved(width, height)

    def geometry_to_dict(self) -> dict:
        return {"x": compact(self.position.x), "y": compact(self.position.y)}

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["text"] = {"content": self.text, "font_family": self.font_family,
                        "font_size": compact(self.font_size)}
        return data

    def geometry_text(self) -> str:
        return (f"«{self.text}» в точке {self.position}, "
                f"шрифт {self.font_family} {compact(self.font_size)}")

    @classmethod
    def build(cls, data: dict, **common) -> TextLabel:
        geometry, text = data["geometry"], data["text"]
        return cls(Point(geometry["x"], geometry["y"]), text["content"],
                   text.get("font_size", 14), text.get("font_family", "Arial"), **common)


# Реестр типов фигур: имя класса -> класс (используется при чтении из файла)
SHAPE_TYPES: dict[str, type[Shape]] = {
    cls.__name__: cls for cls in (Rectangle, Ellipse, Circle, Line, Polygon, TextLabel)
}
