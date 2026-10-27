"""Бизнес-логика уровня всего рисунка: создание, статистика, отмена."""

from __future__ import annotations

from data_layer import Canvas, Color, Drawing, Layer, Shape
from repository_layer import CanvasRepository, LayerRepository, ShapeRepository
from .history_service import HistoryService


class DrawingService:
    """Операции над рисунком целиком."""

    DEFAULT_LAYER = "Слой 1"

    def __init__(self, canvas: CanvasRepository, layers: LayerRepository,
                 shapes: ShapeRepository, history: HistoryService):
        self._canvas = canvas
        self._layers = layers
        self._shapes = shapes
        self._history = history

    # ---- запросы ----
    def canvas(self) -> Canvas:
        return self._canvas.get()

    def overview(self) -> list[tuple[Layer, list[Shape]]]:
        """Слои снизу вверх и фигуры каждого слоя в порядке отрисовки."""
        drawing = self._history.snapshot()
        return [(layer, drawing.shapes_of(layer.name)) for layer in drawing.layers]

    def statistics(self) -> dict:
        drawing = self._history.snapshot()
        by_type: dict[str, int] = {}
        for shape in drawing.shapes:
            by_type[shape.TITLE] = by_type.get(shape.TITLE, 0) + 1
        return {
            "layers": len(drawing.layers),
            "shapes": len(drawing.shapes),
            "hidden": sum(1 for shape in drawing.shapes if not shape.visible),
            "outside": sum(1 for shape in drawing.shapes
                           if not drawing.canvas.contains_box(*shape.bounding_box())),
            "total_area": sum(shape.area() for shape in drawing.shapes),
            "by_type": by_type,
            "by_layer": {layer.name: len(drawing.shapes_of(layer.name))
                         for layer in drawing.layers},
        }

    @property
    def can_undo(self) -> bool:
        return self._history.can_undo

    # ---- команды ----
    def new_drawing(self, title: str, width: float, height: float,
                    background: str | None = None) -> Canvas:
        """Новый пустой рисунок с одним слоем."""
        canvas = Canvas(title, width, height, Color.parse(background) if background else None,
                        self.DEFAULT_LAYER)
        with self._history.track():
            self._history.restore(Drawing(canvas, [Layer(self.DEFAULT_LAYER)], []))
        return self._canvas.get()

    def undo(self) -> None:
        self._history.undo()
