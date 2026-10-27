"""Файловые хранилища рисунка: сохранение в файл и загрузка из файла (JSON).

Отвечают только за формат файла; что именно сохранять, решает сервисный слой.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from data_layer import Drawing
from data_layer.primitives import compact
from exceptions import DocumentFormatError, GraphicEditorError


class DrawingStorage(ABC):
    """Абстрактное файловое хранилище рисунка.

    Общий алгоритм загрузки (обработка ошибок) описан здесь, а чтение
    и запись конкретного формата реализуют наследники.
    """

    EXTENSION = ""
    FORMAT_NAME = "graphic-editor"
    FORMAT_VERSION = 1

    def save(self, drawing: Drawing, path) -> Path:
        path = Path(path)
        if path.parent != Path(""):
            path.parent.mkdir(parents=True, exist_ok=True)
        self._write(drawing, path)
        return path

    def load(self, path) -> Drawing:
        path = Path(path)
        try:
            return self._read(path)
        except DocumentFormatError:
            raise
        except KeyError as error:
            reason = f"нет обязательного поля {error.args[0]!r}"
            raise DocumentFormatError(path, reason) from error
        except (TypeError, ValueError, GraphicEditorError) as error:
            raise DocumentFormatError(path, str(error)) from error

    @abstractmethod
    def _write(self, drawing: Drawing, path: Path) -> None:
        """Записывает рисунок в файл."""

    @abstractmethod
    def _read(self, path: Path) -> Drawing:
        """Читает рисунок из файла."""


class JsonDrawingStorage(DrawingStorage):
    """Хранение рисунка в формате JSON."""

    EXTENSION = ".json"

    def _write(self, drawing: Drawing, path: Path) -> None:
        data = {
            "format": self.FORMAT_NAME,
            "version": self.FORMAT_VERSION,
            "document": drawing.to_dict(),
        }
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _read(self, path: Path) -> Drawing:
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as error:
                reason = f"ошибка синтаксиса JSON (строка {error.lineno}): {error.msg}"
                raise DocumentFormatError(path, reason) from error
        if not isinstance(data, dict) or data.get("format") != self.FORMAT_NAME:
            raise DocumentFormatError(path, "это не файл графического редактора")
        return Drawing.from_dict(data["document"])
