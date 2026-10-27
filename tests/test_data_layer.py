"""Тесты слоя данных: сущности и их правила."""

import math
import unittest

from data_layer import (Canvas, Circle, Color, Drawing, Ellipse, Layer, Line, Point, Polygon,
                        Rectangle, Shape, Style, TextLabel)
from exceptions import InvalidColorError, InvalidShapeError, LayerLockedError, UnknownShapeTypeError


class PrimitivesTest(unittest.TestCase):
    def test_color_from_hex_and_name(self):
        self.assertEqual(Color.parse("#ff8000").to_hex(), "#FF8000")
        self.assertEqual(Color.parse("красный"), Color(255, 0, 0))
        self.assertEqual(Color.from_hex("#00000080").a, 128)

    def test_invalid_color(self):
        with self.assertRaises(InvalidColorError):
            Color.parse("#12345")
        with self.assertRaises(InvalidColorError):
            Color(300, 0, 0)

    def test_point_requires_numbers(self):
        with self.assertRaises(ValueError):
            Point("abc", 1)
        with self.assertRaises(TypeError):
            Point(None, 1)

    def test_negative_stroke_width(self):
        with self.assertRaises(InvalidShapeError):
            Style(stroke_width=-1)


class ShapesTest(unittest.TestCase):
    def test_areas_and_perimeters(self):
        self.assertEqual(Rectangle(Point(0, 0), 4, 5).area(), 20)
        self.assertAlmostEqual(Circle(Point(0, 0), 1).perimeter(), 2 * math.pi)
        self.assertAlmostEqual(Ellipse(Point(0, 0), 2, 2).perimeter(), 4 * math.pi)
        self.assertEqual(Line(Point(0, 0), Point(3, 4)).perimeter(), 5)
        triangle = Polygon([Point(0, 0), Point(4, 0), Point(0, 3)])
        self.assertEqual(triangle.area(), 6)
        self.assertEqual(triangle.perimeter(), 12)

    def test_move_and_scale(self):
        rect = Rectangle(Point(10, 10), 20, 30)
        rect.move(5, -5)
        rect.scale(2)
        self.assertEqual(rect.top_left, Point(15, 5))
        self.assertEqual((rect.width, rect.height), (40, 60))

    def test_contains_point_is_polymorphic(self):
        circle = Circle(Point(0, 0), 10)
        self.assertTrue(circle.contains_point(Point(6, 6)))
        self.assertFalse(circle.contains_point(Point(9, 9)))      # угол рамки, но вне круга
        triangle = Polygon([Point(0, 0), Point(10, 0), Point(0, 10)])
        self.assertTrue(triangle.contains_point(Point(2, 2)))
        self.assertFalse(triangle.contains_point(Point(8, 8)))
        line = Line(Point(0, 0), Point(100, 0))
        self.assertTrue(line.contains_point(Point(50, 2)))
        self.assertFalse(line.contains_point(Point(50, 10)))

    def test_invalid_shapes(self):
        with self.assertRaises(InvalidShapeError):
            Rectangle(Point(0, 0), -10, 5)
        with self.assertRaises(InvalidShapeError):
            Polygon([Point(0, 0), Point(1, 1)])
        with self.assertRaises(InvalidShapeError):
            Polygon([Point(0, 0), Point(1, 1), Point(2, 2)])
        with self.assertRaises(InvalidShapeError):
            Line(Point(1, 1), Point(1, 1))
        with self.assertRaises(InvalidShapeError):
            TextLabel(Point(0, 0), "   ")
        with self.assertRaises(InvalidShapeError):
            Circle(Point(0, 0), 5).scale(0)

    def test_dict_round_trip(self):
        for shape in (Rectangle(Point(1, 2), 3, 4), Circle(Point(0, 0), 7),
                      Ellipse(Point(5, 5), 2, 3), Line(Point(0, 0), Point(9, 9)),
                      Polygon([Point(0, 0), Point(5, 0), Point(5, 5)]),
                      TextLabel(Point(1, 1), "Привет", 20)):
            shape.id = 1
            restored = Shape.from_dict(shape.to_dict())
            self.assertIs(type(restored), type(shape))
            self.assertEqual(restored.to_dict(), shape.to_dict())

    def test_unknown_type(self):
        data = Rectangle(Point(0, 0), 1, 1).to_dict()
        data["type"] = "Star"
        with self.assertRaises(UnknownShapeTypeError):
            Shape.from_dict(data)

    def test_clone_is_independent(self):
        rect = Rectangle(Point(0, 0), 10, 10)
        copy = rect.clone()
        copy.move(5, 5)
        self.assertEqual(rect.top_left, Point(0, 0))


class LayerCanvasDrawingTest(unittest.TestCase):
    def test_locked_layer(self):
        with self.assertRaises(LayerLockedError):
            Layer("Фон", locked=True).check_editable()
        with self.assertRaises(ValueError):
            Layer("   ")

    def test_canvas_bounds(self):
        canvas = Canvas(width=100, height=50)
        self.assertTrue(canvas.contains_box(Point(0, 0), Point(100, 50)))
        self.assertFalse(canvas.contains_box(Point(-1, 0), Point(10, 10)))
        with self.assertRaises(ValueError):
            Canvas(width=0)

    def test_drawing_nested_structure(self):
        shapes = [Rectangle(Point(0, 0), 1, 1, shape_id=1, layer="A", z_index=2),
                  Circle(Point(0, 0), 1, shape_id=2, layer="A", z_index=1),
                  Line(Point(0, 0), Point(1, 1), shape_id=3, layer="B")]
        drawing = Drawing(Canvas(active_layer="B"), [Layer("B", order=1), Layer("A", order=0)], shapes)
        data = drawing.to_dict()
        self.assertEqual([layer["name"] for layer in data["layers"]], ["A", "B"])
        self.assertEqual([shape["id"] for shape in data["layers"][0]["shapes"]], [2, 1])
        restored = Drawing.from_dict(data)
        self.assertEqual(restored.to_dict(), data)
        self.assertEqual(restored.shapes_of("A")[0].layer, "A")


if __name__ == "__main__":
    unittest.main()
