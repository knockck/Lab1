"""Сущность «Слой» рисунка."""

from __future__ import annotations

import copy

from exceptions import LayerLockedError


class Layer:
    """Слой: имя (уникальный ключ), видимость, блокировка и порядок отрисовки.

    Фигуры ссылаются на слой по имени (поле Shape.layer), сам слой их не хранит.
    """

    def __init__(self, name: str, visible: bool = True, locked: bool = False, order: int = 0):
        self.name = name
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.order = int(order)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        value = str(value).strip()
        if not value:
            raise ValueError("Имя слоя не может быть пустым")
        self._name = value

    def check_editable(self) -> None:
        """Проверяет, что слой можно изменять."""
        if self.locked:
            raise LayerLockedError(self.name)

    def clone(self) -> Layer:
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return {"name": self.name, "visible": self.visible, "locked": self.locked}

    @classmethod
    def from_dict(cls, data: dict, order: int = 0) -> Layer:
        return cls(data["name"], data.get("visible", True), data.get("locked", False), order)

    def __str__(self) -> str:
        flags = []
        if not self.visible:
            flags.append("скрыт")
        if self.locked:
            flags.append("заблокирован")
        suffix = f" ({', '.join(flags)})" if flags else ""
        return f"Слой «{self.name}»{suffix}"

    def __repr__(self) -> str:
        return f"<Layer {self.name!r} order={self.order}>"
