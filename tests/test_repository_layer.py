"""Тесты слоя репозиториев: CRUD в памяти и файловые хранилища."""

import tempfile
import unittest
from pathlib import Path

from data_layer import Canvas, Layer, Point, Rectangle
from exceptions import (DocumentFormatError, DuplicateLayerError, LayerNotFoundError,
                        ShapeNotFoundError)
from repository_layer import (InMemoryCanvasRepository, InMemoryLayerRepository,
                              InMemoryShapeRepository, JsonDrawingStorage, XmlDrawingStorage)

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class InMemoryShapeRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryShapeRepository()

    def test_crud(self):
        shape = self.repo.add(Rectangle(Point(0, 0), 10, 10, layer="A"))      # create
        self.assertEqual(shape.id, 1)
        self.assertEqual(self.repo.get(1).width, 10)                         # read
        shape.width = 50
        self.repo.update(shape)                                              # update
        self.assertEqual(self.repo.get(1).width, 50)
        self.repo.delete(1)                                                  # delete
        self.assertFalse(self.repo.exists(1))
        with self.assertRaises(ShapeNotFoundError):
            self.repo.get(1)

    def test_returns_copies(self):
        self.repo.add(Rectangle(Point(0, 0), 10, 10))
        shape = self.repo.get(1)
        shape.width = 99                       # без update() хранилище не меняется
        self.assertEqual(self.repo.get(1).width, 10)

    def test_ids_and_find_by_layer(self):
        self.repo.add(Rectangle(Point(0, 0), 1, 1, layer="A"))
        self.repo.add(Rectangle(Point(0, 0), 1, 1, layer="B"))
        self.repo.add(Rectangle(Point(0, 0), 1, 1, shape_id=10, layer="A"))
        self.assertEqual(self.repo.add(Rectangle(Point(0, 0), 1, 1)).id, 11)
        self.assertEqual(sorted(s.id for s in self.repo.find_by_layer("A")), [1, 10])
        with self.assertRaises(ShapeNotFoundError):
            self.repo.update(Rectangle(Point(0, 0), 1, 1, shape_id=500))


class InMemoryLayerAndCanvasRepositoryTest(unittest.TestCase):
    def test_layer_crud(self):
        repo = InMemoryLayerRepository()
        repo.add(Layer("Фон"))
        with self.assertRaises(DuplicateLayerError):
            repo.add(Layer("Фон"))
        layer = repo.get("Фон")
        layer.locked = True
        repo.update(layer)
        self.assertTrue(repo.get("Фон").locked)
        repo.delete("Фон")
        with self.assertRaises(LayerNotFoundError):
            repo.delete("Фон")

    def test_canvas(self):
        repo = InMemoryCanvasRepository()
        canvas = repo.get()
        canvas.title = "Тест"
        self.assertEqual(repo.get().title, "Без названия")
        repo.save(canvas)
        self.assertEqual(repo.get().title, "Тест")


class FileStorageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_example_files_are_equal(self):
        from_json = JsonDrawingStorage().load(EXAMPLES / "drawing.json")
        from_xml = XmlDrawingStorage().load(EXAMPLES / "drawing.xml")
        self.assertEqual(from_json.to_dict(), from_xml.to_dict())
        self.assertEqual(len(from_json.shapes), 9)

    def test_round_trip_both_formats(self):
        drawing = JsonDrawingStorage().load(EXAMPLES / "drawing.json")
        for storage, name in ((JsonDrawingStorage(), "copy.json"), (XmlDrawingStorage(), "copy.xml")):
            storage.save(drawing, self.dir / name)
            self.assertEqual(storage.load(self.dir / name).to_dict(), drawing.to_dict())
        self.assertEqual((self.dir / "copy.json").read_text(encoding="utf-8"),
                         (EXAMPLES / "drawing.json").read_text(encoding="utf-8"))

    def test_broken_files(self):
        (self.dir / "bad.json").write_text('{"format": "graphic-editor", ', encoding="utf-8")
        (self.dir / "bad.xml").write_text("<graphic_editor><document>", encoding="utf-8")
        (self.dir / "no_layers.json").write_text(
            '{"format": "graphic-editor", "document": {"width": 10, "height": 10}}', encoding="utf-8")
        for storage, name in ((JsonDrawingStorage(), "bad.json"), (XmlDrawingStorage(), "bad.xml"),
                              (JsonDrawingStorage(), "no_layers.json")):
            with self.assertRaises(DocumentFormatError):
                storage.load(self.dir / name)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            JsonDrawingStorage().load(self.dir / "missing.json")


if __name__ == "__main__":
    unittest.main()
