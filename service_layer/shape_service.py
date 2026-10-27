"""Бизнес-логика работы с фигурами."""

from __future__ import annotations

from data_layer import Color, Point, Shape, Style
from repository_layer import CanvasRepository, LayerRepository, ShapeRepository
from .history_service import HistoryService
from .shape_factory import ShapeFactory


class ShapeService:
    """Создание, изменение, поиск и порядок отрисовки фигур."""

    DUPLICATE_OFFSET = 20   # смещение копии относительно оригинала

    def __init__(self, shapes: ShapeRepository, layers: LayerRepository,
                 canvas: CanvasRepository, history: HistoryService,
                 factory: ShapeFactory | None = None):
        self._shapes = shapes
        self._layers = layers
        self._canvas = canvas
        self._history = history
        self.factory = factory if factory is not None else ShapeFactory()

    # ---- запросы ----
    def get(self, shape_id: int) -> Shape:
        return self._shapes.get(shape_id)

    def list_by_layer(self, layer_name: str) -> list[Shape]:
        """Фигуры слоя в порядке отрисовки (снизу вверх)."""
        return sorted(self._shapes.find_by_layer(layer_name), key=lambda shape: shape.z_index)

    def find_at(self, x: float, y: float) -> list[Shape]:
        """Видимые фигуры в точке (x, y): сначала верхняя."""
        point = Point(x, y)
        order = {layer.name: layer.order for layer in self._layers.get_all() if layer.visible}
        hits = [shape for shape in self._shapes.get_all()
                if shape.visible and shape.layer in order and shape.contains_point(point)]
        return sorted(hits, key=lambda s: (order[s.layer], s.z_index), reverse=True)

    def outside_canvas(self) -> list[Shape]:
        """Фигуры, которые хотя бы частично выходят за границы холста."""
        canvas = self._canvas.get()
        return [shape for shape in self._shapes.get_all()
                if not canvas.contains_box(*shape.bounding_box())]

    # ---- команды ----
    def create(self, kind: str, params: dict, stroke: str | None = None,
               fill: str | None = None, stroke_width: float = 1) -> Shape:
        """Создаёт фигуру в активном слое поверх остальных фигур слоя."""
        with self._history.track():
            layer = self._layers.get(self._canvas.get().active_layer)
            layer.check_editable()
            style = self.make_style(stroke, fill, stroke_width)
            shape = self.factory.create(kind, params, style)
            shape.layer = layer.name
            shape.z_index = self._top_z(layer.name) + 1
            shape = self._shapes.add(shape)
        return shape

    def move(self, shape_id: int, dx: float, dy: float) -> Shape:
        return self._change(shape_id, lambda shape: shape.move(dx, dy))

    def scale(self, shape_id: int, factor: float) -> Shape:
        return self._change(shape_id, lambda shape: shape.scale(factor))

    def recolor(self, shape_id: int, stroke: str | None = None, fill: str | None = None,
                remove_fill: bool = False) -> Shape:
        def apply(shape: Shape) -> None:
            if stroke:
                shape.style.stroke = Color.parse(stroke)
            if remove_fill:
                shape.style.fill = None
            elif fill:
                shape.style.fill = Color.parse(fill)
        return self._change(shape_id, apply)

    def rename(self, shape_id: int, name: str) -> Shape:
        def apply(shape: Shape) -> None:
            shape.name = name
        return self._change(shape_id, apply)

    def bring_to_front(self, shape_id: int) -> Shape:
        def apply(shape: Shape) -> None:
            shape.z_index = self._top_z(shape.layer) + 1
        return self._change(shape_id, apply)

    def send_to_back(self, shape_id: int) -> Shape:
        def apply(shape: Shape) -> None:
            layer_shapes = self._shapes.find_by_layer(shape.layer)
            lowest = min((s.z_index for s in layer_shapes), default=0)
            shape.z_index = lowest - 1
        return self._change(shape_id, apply)

    def duplicate(self, shape_id: int) -> Shape:
        """Копия фигуры со смещением, в том же слое, поверх остальных."""
        with self._history.track():
            original = self._editable(shape_id)
            duplicate = original.clone()
            duplicate.id = None
            duplicate.name = f"{original.name} (копия)"
            duplicate.move(self.DUPLICATE_OFFSET, self.DUPLICATE_OFFSET)
            duplicate.z_index = self._top_z(original.layer) + 1
            duplicate = self._shapes.add(duplicate)
        return duplicate

    def move_to_layer(self, shape_id: int, layer_name: str) -> Shape:
        """Переносит фигуру в другой слой (оба слоя должны быть не заблокированы)."""
        with self._history.track():
            shape = self._editable(shape_id)
            target = self._layers.get(layer_name)
            target.check_editable()
            shape.layer = target.name
            shape.z_index = self._top_z(target.name) + 1
            shape = self._shapes.update(shape)
        return shape

    def delete(self, shape_id: int) -> Shape:
        with self._history.track():
            self._editable(shape_id)
            shape = self._shapes.delete(shape_id)
        return shape

    # ---- вспомогательные методы ----
    @staticmethod
    def make_style(stroke: str | None, fill: str | None, stroke_width: float = 1) -> Style:
        return Style(Color.parse(stroke) if stroke else Color(0, 0, 0),
                     Color.parse(fill) if fill else None, stroke_width)

    def _editable(self, shape_id: int) -> Shape:
        """Фигура, которую разрешено менять (её слой не заблокирован)."""
        shape = self._shapes.get(shape_id)
        self._layers.get(shape.layer).check_editable()
        return shape

    def _change(self, shape_id: int, action) -> Shape:
        """Общий сценарий изменения: получить -> проверить -> изменить -> сохранить."""
        with self._history.track():
            shape = self._editable(shape_id)
            action(shape)
            shape = self._shapes.update(shape)
        return shape

    def _top_z(self, layer_name: str) -> int:
        layer_shapes = self._shapes.find_by_layer(layer_name)
        return max((shape.z_index for shape in layer_shapes), default=0)
