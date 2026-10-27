"""Слой репозиториев: CRUD-операции над сущностями и файловые хранилища."""

from .file_storage import DrawingStorage, JsonDrawingStorage, XmlDrawingStorage
from .interfaces import CanvasRepository, LayerRepository, Repository, ShapeRepository
from .memory import (InMemoryCanvasRepository, InMemoryLayerRepository,
                     InMemoryShapeRepository)
