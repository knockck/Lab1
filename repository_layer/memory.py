"""Реализации репозиториев в оперативной памяти (словари).

Репозиторий хранит собственные копии сущностей и отдаёт наружу копии,
как это делает база данных: изменения попадают в хранилище только
через вызов update().
"""

from __future__ import annotations

from data_layer import Canvas, Layer, Shape
from exceptions import (DuplicateLayerError, EditorOperationError,
                        LayerNotFoundError, ShapeNotFoundError)
from .interfaces import CanvasRepository, LayerRepository, ShapeRepository


class InMemoryShapeRepository(ShapeRepository):
    """Фигуры в словаре {id: фигура}; id назначаются автоматически."""

    def __init__(self):
        self._items: dict[int, Shape] = {}
        self._next_id = 1

    def add(self, entity: Shape) -> Shape:
        if entity.id is None:
            entity.id = self._next_id
        elif entity.id in self._items:
            raise EditorOperationError(f"Фигура с id={entity.id} уже существует")
        self._next_id = max(self._next_id, entity.id + 1)
        self._items[entity.id] = entity.clone()
        return entity.clone()

    def get(self, key: int) -> Shape:
        if key not in self._items:
            raise ShapeNotFoundError(key)
        return self._items[key].clone()

    def get_all(self) -> list[Shape]:
        return [shape.clone() for shape in self._items.values()]

    def update(self, entity: Shape) -> Shape:
        if entity.id not in self._items:
            raise ShapeNotFoundError(entity.id)
        self._items[entity.id] = entity.clone()
        return entity.clone()

    def delete(self, key: int) -> Shape:
        if key not in self._items:
            raise ShapeNotFoundError(key)
        return self._items.pop(key)

    def exists(self, key: int) -> bool:
        return key in self._items

    def clear(self) -> None:
        self._items.clear()
        self._next_id = 1

    def find_by_layer(self, layer_name: str) -> list[Shape]:
        return [shape.clone() for shape in self._items.values() if shape.layer == layer_name]


class InMemoryLayerRepository(LayerRepository):
    """Слои в словаре {имя: слой}."""

    def __init__(self):
        self._items: dict[str, Layer] = {}

    def add(self, entity: Layer) -> Layer:
        if entity.name in self._items:
            raise DuplicateLayerError(entity.name)
        self._items[entity.name] = entity.clone()
        return entity.clone()

    def get(self, key: str) -> Layer:
        if key not in self._items:
            raise LayerNotFoundError(key)
        return self._items[key].clone()

    def get_all(self) -> list[Layer]:
        return [layer.clone() for layer in self._items.values()]

    def update(self, entity: Layer) -> Layer:
        if entity.name not in self._items:
            raise LayerNotFoundError(entity.name)
        self._items[entity.name] = entity.clone()
        return entity.clone()

    def delete(self, key: str) -> Layer:
        if key not in self._items:
            raise LayerNotFoundError(key)
        return self._items.pop(key)

    def exists(self, key: str) -> bool:
        return key in self._items

    def clear(self) -> None:
        self._items.clear()


class InMemoryCanvasRepository(CanvasRepository):
    """Параметры холста в памяти."""

    def __init__(self, canvas: Canvas | None = None):
        self._canvas = (canvas or Canvas()).clone()

    def get(self) -> Canvas:
        return self._canvas.clone()

    def save(self, canvas: Canvas) -> None:
        self._canvas = canvas.clone()
