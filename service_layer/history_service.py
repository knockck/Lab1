"""История изменений: снимки состояния, отмена действий и откат при ошибке."""

from __future__ import annotations

from contextlib import contextmanager

from data_layer import Drawing
from repository_layer import CanvasRepository, LayerRepository, ShapeRepository


class HistoryService:
    """Хранит снимки рисунка до изменений и умеет восстанавливать их."""

    HISTORY_LIMIT = 50

    def __init__(self, canvas: CanvasRepository, layers: LayerRepository,
                 shapes: ShapeRepository):
        self._canvas = canvas
        self._layers = layers
        self._shapes = shapes
        self._undo_stack: list[Drawing] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def snapshot(self) -> Drawing:
        """Текущее состояние всех репозиториев одним объектом."""
        return Drawing(self._canvas.get(), self._layers.get_all(), self._shapes.get_all())

    def restore(self, drawing: Drawing) -> None:
        """Заменяет содержимое репозиториев содержимым снимка."""
        self._shapes.clear()
        self._layers.clear()
        for layer in drawing.layers:
            self._layers.add(layer)
        for shape in drawing.shapes:
            self._shapes.add(shape)
        self._canvas.save(drawing.canvas)

    @contextmanager
    def track(self):
        """Выполняет изменение как одну операцию.

        При успехе запоминает состояние «до» (его можно отменить),
        при любой ошибке возвращает репозитории в исходное состояние.
        """
        before = self.snapshot()
        try:
            yield
        except Exception:
            self.restore(before)
            raise
        self._undo_stack.append(before)
        if len(self._undo_stack) > self.HISTORY_LIMIT:
            self._undo_stack.pop(0)

    def undo(self) -> None:
        if not self._undo_stack:
            raise RuntimeError("Нечего отменять")
        self.restore(self._undo_stack.pop())

    def clear(self) -> None:
        self._undo_stack.clear()
