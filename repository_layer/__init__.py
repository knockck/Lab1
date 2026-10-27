"""Слой репозиториев: CRUD-операции над сущностями и файловые хранилища."""

from .interfaces import CanvasRepository, LayerRepository, Repository, ShapeRepository
from .memory import (InMemoryCanvasRepository, InMemoryLayerRepository,
                     InMemoryShapeRepository)
