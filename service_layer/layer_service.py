"""Бизнес-логика работы со слоями."""

from __future__ import annotations

from data_layer import Layer
from exceptions import EditorOperationError
from repository_layer import CanvasRepository, LayerRepository, ShapeRepository
from .history_service import HistoryService


class LayerService:
    """Создание, выбор, блокировка, порядок и удаление слоёв."""

    def __init__(self, layers: LayerRepository, shapes: ShapeRepository,
                 canvas: CanvasRepository, history: HistoryService):
        self._layers = layers
        self._shapes = shapes
        self._canvas = canvas
        self._history = history

    # ---- запросы ----
    def list_layers(self) -> list[Layer]:
        """Слои снизу вверх (в порядке отрисовки)."""
        return sorted(self._layers.get_all(), key=lambda layer: layer.order)

    def get(self, name: str) -> Layer:
        return self._layers.get(name)

    def active(self) -> Layer:
        return self._layers.get(self._canvas.get().active_layer)

    # ---- команды ----
    def create(self, name: str) -> Layer:
        """Новый слой кладётся поверх остальных и становится активным."""
        with self._history.track():
            top = max((layer.order for layer in self._layers.get_all()), default=-1)
            layer = self._layers.add(Layer(name, order=top + 1))
            self._set_active(layer.name)
        return layer

    def select(self, name: str) -> Layer:
        layer = self._layers.get(name)
        self._set_active(layer.name)
        return layer

    def toggle_lock(self, name: str) -> Layer:
        with self._history.track():
            layer = self._layers.get(name)
            layer.locked = not layer.locked
            self._layers.update(layer)
        return layer

    def toggle_visibility(self, name: str) -> Layer:
        with self._history.track():
            layer = self._layers.get(name)
            layer.visible = not layer.visible
            self._layers.update(layer)
        return layer

    def move(self, name: str, step: int) -> Layer:
        """Перемещает слой выше (step=1) или ниже (step=-1) соседнего."""
        with self._history.track():
            self._layers.get(name)                      # проверяем, что слой существует
            ordered = self.list_layers()
            index = [layer.name for layer in ordered].index(name)
            neighbour_index = index + step
            if not 0 <= neighbour_index < len(ordered):
                where = "выше" if step > 0 else "ниже"
                raise EditorOperationError(f"Слой «{name}» уже находится {where} всех")
            layer, neighbour = ordered[index], ordered[neighbour_index]
            layer.order, neighbour.order = neighbour.order, layer.order
            self._layers.update(layer)
            self._layers.update(neighbour)
        return layer

    def delete(self, name: str) -> tuple[Layer, int]:
        """Удаляет слой вместе с его фигурами. Возвращает слой и число удалённых фигур."""
        with self._history.track():
            layer = self._layers.get(name)
            if self._layers.count() == 1:
                raise EditorOperationError("Нельзя удалить единственный слой рисунка")
            layer.check_editable()
            shapes = self._shapes.find_by_layer(name)
            for shape in shapes:
                self._shapes.delete(shape.id)
            self._layers.delete(name)
            if self._canvas.get().active_layer == name:
                self._set_active(self.list_layers()[-1].name)
        return layer, len(shapes)

    def _set_active(self, name: str) -> None:
        canvas = self._canvas.get()
        canvas.active_layer = name
        self._canvas.save(canvas)
