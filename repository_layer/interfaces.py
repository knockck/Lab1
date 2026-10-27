"""Интерфейсы репозиториев (абстракции, от которых зависит сервисный слой).

Сервисы работают только с этими интерфейсами. Чтобы хранить сущности
по-другому (в базе данных, в файлах, на сервере), достаточно написать новую
реализацию интерфейса — бизнес-логику менять не нужно.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from data_layer import Canvas, Layer, Shape

K = TypeVar("K")   # тип ключа сущности
E = TypeVar("E")   # тип сущности


class Repository(ABC, Generic[K, E]):
    """Общий интерфейс CRUD-репозитория."""

    @abstractmethod
    def add(self, entity: E) -> E:
        """Create: добавляет сущность и возвращает её сохранённую версию."""

    @abstractmethod
    def get(self, key: K) -> E:
        """Read: возвращает сущность по ключу."""

    @abstractmethod
    def get_all(self) -> list[E]:
        """Read: все сущности."""

    @abstractmethod
    def update(self, entity: E) -> E:
        """Update: сохраняет изменения существующей сущности."""

    @abstractmethod
    def delete(self, key: K) -> E:
        """Delete: удаляет сущность и возвращает её."""

    @abstractmethod
    def exists(self, key: K) -> bool:
        """Есть ли сущность с таким ключом."""

    @abstractmethod
    def clear(self) -> None:
        """Удаляет все сущности."""

    def count(self) -> int:
        return len(self.get_all())


class ShapeRepository(Repository[int, Shape]):
    """Репозиторий фигур (ключ — id фигуры)."""

    @abstractmethod
    def find_by_layer(self, layer_name: str) -> list[Shape]:
        """Фигуры, принадлежащие слою."""


class LayerRepository(Repository[str, Layer]):
    """Репозиторий слоёв (ключ — имя слоя)."""


class CanvasRepository(ABC):
    """Хранилище параметров холста (одна запись на рисунок)."""

    @abstractmethod
    def get(self) -> Canvas:
        """Текущие параметры холста."""

    @abstractmethod
    def save(self, canvas: Canvas) -> None:
        """Сохраняет параметры холста."""
