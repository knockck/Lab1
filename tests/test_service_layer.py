"""Тесты сервисного слоя: бизнес-правила редактора."""

import tempfile
import unittest
from pathlib import Path

from exceptions import (DocumentFormatError, EditorOperationError, InvalidShapeError,
                        LayerLockedError, ShapeNotFoundError, UnsupportedFormatError)
from repository_layer import (InMemoryCanvasRepository, InMemoryLayerRepository,
                              InMemoryShapeRepository, JsonDrawingStorage, XmlDrawingStorage)
from service_layer import DrawingService, HistoryService, LayerService, ShapeService

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
RECT = {"top_left": (10, 10), "width": 100, "height": 50}


class ServiceTestCase(unittest.TestCase):
    """Собирает сервисы так же, как build_app() в main.py."""

    def setUp(self):
        canvas, layers, shapes = (InMemoryCanvasRepository(), InMemoryLayerRepository(),
                                  InMemoryShapeRepository())
        self.history = HistoryService(canvas, layers, shapes)
        storages = {".json": JsonDrawingStorage(), ".xml": XmlDrawingStorage()}
        self.drawings = DrawingService(canvas, layers, shapes, self.history, storages)
        self.layers = LayerService(layers, shapes, canvas, self.history)
        self.shapes = ShapeService(shapes, layers, canvas, self.history)
        self.drawings.new_drawing("Тест", 800, 600)
        self.history.clear()


class ShapeServiceTest(ServiceTestCase):
    def test_create_in_active_layer_on_top(self):
        first = self.shapes.create("rectangle", RECT)
        second = self.shapes.create("circle", {"center": (0, 0), "radius": 5}, fill="red")
        self.assertEqual(first.layer, "Слой 1")
        self.assertGreater(second.z_index, first.z_index)
        self.assertEqual(second.style.fill.to_hex(), "#FF0000")

    def test_locked_layer_blocks_changes(self):
        shape = self.shapes.create("rectangle", RECT)
        self.layers.toggle_lock("Слой 1")
        for action in (lambda: self.shapes.move(shape.id, 1, 1),
                       lambda: self.shapes.delete(shape.id),
                       lambda: self.shapes.create("rectangle", RECT)):
            with self.assertRaises(LayerLockedError):
                action()

    def test_duplicate_and_z_order(self):
        shape = self.shapes.create("rectangle", RECT)
        copy = self.shapes.duplicate(shape.id)
        self.assertNotEqual(copy.id, shape.id)
        self.assertEqual(copy.bounding_box()[0].x, 30)
        self.shapes.bring_to_front(shape.id)
        self.assertEqual([s.id for s in self.shapes.list_by_layer("Слой 1")], [copy.id, shape.id])
        self.shapes.send_to_back(shape.id)
        self.assertEqual([s.id for s in self.shapes.list_by_layer("Слой 1")], [shape.id, copy.id])

    def test_find_at_returns_topmost_first(self):
        bottom = self.shapes.create("rectangle", RECT)
        self.layers.create("Верх")
        top = self.shapes.create("circle", {"center": (50, 30), "radius": 20})
        self.assertEqual([s.id for s in self.shapes.find_at(50, 30)], [top.id, bottom.id])
        self.layers.toggle_visibility("Верх")
        self.assertEqual([s.id for s in self.shapes.find_at(50, 30)], [bottom.id])

    def test_move_to_layer(self):
        shape = self.shapes.create("rectangle", RECT)
        self.layers.create("Второй")
        moved = self.shapes.move_to_layer(shape.id, "Второй")
        self.assertEqual(moved.layer, "Второй")

    def test_failed_operation_is_rolled_back(self):
        shape = self.shapes.create("rectangle", RECT)
        with self.assertRaises(InvalidShapeError):
            self.shapes.scale(shape.id, -2)
        self.assertEqual(self.shapes.get(shape.id).width, 100)
        with self.assertRaises(ShapeNotFoundError):
            self.shapes.move(999, 1, 1)


class LayerServiceTest(ServiceTestCase):
    def test_delete_layer_with_shapes(self):
        self.layers.create("Фон")
        self.shapes.create("rectangle", RECT)
        layer, count = self.layers.delete("Фон")
        self.assertEqual(count, 1)
        self.assertEqual(self.layers.active().name, "Слой 1")
        with self.assertRaises(EditorOperationError):
            self.layers.delete("Слой 1")

    def test_layer_order(self):
        self.layers.create("Верх")
        self.layers.move("Верх", -1)
        self.assertEqual([layer.name for layer in self.layers.list_layers()], ["Верх", "Слой 1"])
        with self.assertRaises(EditorOperationError):
            self.layers.move("Верх", -1)


class DrawingServiceTest(ServiceTestCase):
    def test_undo(self):
        shape = self.shapes.create("rectangle", RECT)
        self.shapes.move(shape.id, 10, 0)
        self.drawings.undo()
        self.assertEqual(self.shapes.get(shape.id).bounding_box()[0].x, 10)
        self.drawings.undo()
        self.assertEqual(self.drawings.statistics()["shapes"], 0)
        with self.assertRaises(EditorOperationError):
            self.drawings.undo()

    def test_statistics(self):
        self.drawings.load(EXAMPLES / "drawing.json")
        stats = self.drawings.statistics()
        self.assertEqual((stats["layers"], stats["shapes"], stats["outside"]), (3, 9, 0))
        self.assertEqual(stats["by_layer"], {"Фон": 4, "Дом": 4, "Подписи": 1})

    def test_save_and_load(self):
        self.drawings.load(EXAMPLES / "drawing.xml")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "copy.json"
            self.drawings.save(path)
            self.assertEqual(path.read_text(encoding="utf-8"),
                             (EXAMPLES / "drawing.json").read_text(encoding="utf-8"))
        with self.assertRaises(UnsupportedFormatError):
            self.drawings.save("drawing.txt")

    def test_invalid_file_keeps_current_drawing(self):
        self.shapes.create("rectangle", RECT)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.json"
            path.write_text('{"format": "graphic-editor", "document": {"width": 10, "height": 10, '
                            '"layers": [{"name": "A"}, {"name": "A"}]}}', encoding="utf-8")
            with self.assertRaises(DocumentFormatError):
                self.drawings.load(path)
        self.assertEqual(self.drawings.statistics()["shapes"], 1)


if __name__ == "__main__":
    unittest.main()
