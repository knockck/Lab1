"""Снимок рисунка целиком: холст, слои и фигуры.

Используется для сохранения в файл, загрузки из файла и для истории отмены.
"""

from __future__ import annotations

from .canvas import Canvas
from .layer import Layer
from .shapes import Shape


class Drawing:
    """Рисунок как единое целое (структура хранения в JSON и XML)."""

    def __init__(self, canvas: Canvas, layers: list[Layer], shapes: list[Shape]):
        self.canvas = canvas
        self.layers = sorted(layers, key=lambda layer: layer.order)
        self.shapes = list(shapes)

    def shapes_of(self, layer_name: str) -> list[Shape]:
        """Фигуры слоя в порядке отрисовки (снизу вверх)."""
        shapes = [shape for shape in self.shapes if shape.layer == layer_name]
        return sorted(shapes, key=lambda shape: shape.z_index)

    def to_dict(self) -> dict:
        """Вложенная структура: документ -> слои -> фигуры."""
        data = self.canvas.to_dict()
        data["layers"] = []
        for layer in self.layers:
            layer_data = layer.to_dict()
            layer_data["shapes"] = [shape.to_dict() for shape in self.shapes_of(layer.name)]
            data["layers"].append(layer_data)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Drawing:
        """Восстанавливает рисунок: порядок слоёв и фигур берётся из порядка в файле."""
        layers, shapes = [], []
        for order, layer_data in enumerate(data["layers"]):
            layer = Layer.from_dict(layer_data, order)
            layers.append(layer)
            for z_index, shape_data in enumerate(layer_data.get("shapes", [])):
                shapes.append(Shape.from_dict(shape_data, layer=layer.name, z_index=z_index))
        return cls(Canvas.from_dict(data), layers, shapes)
