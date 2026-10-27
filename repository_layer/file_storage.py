"""Файловые хранилища рисунка: сохранение в файл и загрузка из файла (JSON и XML).

Отвечают только за формат файла; что именно сохранять, решает сервисный слой.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
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


class XmlDrawingStorage(DrawingStorage):
    """Хранение рисунка в формате XML."""

    EXTENSION = ".xml"

    # ---------- запись ----------
    def _write(self, drawing: Drawing, path: Path) -> None:
        root = ET.Element("graphic_editor", version=str(self.FORMAT_VERSION))
        data = drawing.to_dict()
        doc_element = ET.SubElement(root, "document", {
            "title": data["title"],
            "width": str(data["width"]),
            "height": str(data["height"]),
            "background": data["background"],
            "active_layer": data["active_layer"],
        })
        for layer in data["layers"]:
            layer_element = ET.SubElement(doc_element, "layer", {
                "name": layer["name"],
                "visible": self._bool_to_text(layer["visible"]),
                "locked": self._bool_to_text(layer["locked"]),
            })
            for shape in layer["shapes"]:
                self._write_shape(layer_element, shape)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def _write_shape(self, parent: ET.Element, shape: dict) -> None:
        element = ET.SubElement(parent, "shape", {
            "type": shape["type"],
            "id": str(shape["id"]),
            "name": shape["name"],
            "visible": self._bool_to_text(shape["visible"]),
        })
        style = shape["style"]
        ET.SubElement(element, "style", {
            "stroke": style["stroke"],
            "fill": style["fill"] or "none",
            "stroke_width": str(style["stroke_width"]),
        })
        geometry = ET.SubElement(element, "geometry")
        for key, value in shape["geometry"].items():
            if key == "points":
                for point in value:
                    ET.SubElement(geometry, "point", x=str(point["x"]), y=str(point["y"]))
            else:
                geometry.set(key, str(value))
        if "text" in shape:
            text = ET.SubElement(element, "text", {
                "font_family": shape["text"]["font_family"],
                "font_size": str(shape["text"]["font_size"]),
            })
            text.text = shape["text"]["content"]

    # ---------- чтение ----------
    def _read(self, path: Path) -> Drawing:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as error:
            line, column = error.position
            reason = f"ошибка синтаксиса XML (строка {line}, столбец {column})"
            raise DocumentFormatError(path, reason) from error
        if root.tag != "graphic_editor":
            raise DocumentFormatError(path, f"неожиданный корневой элемент <{root.tag}>")
        doc_element = self._required(root, "document")
        data = {
            "title": doc_element.get("title", ""),
            "width": self._number(doc_element, "width"),
            "height": self._number(doc_element, "height"),
            "background": doc_element.get("background", "#FFFFFF"),
            "active_layer": doc_element.get("active_layer"),
            "layers": [self._read_layer(item) for item in doc_element.findall("layer")],
        }
        return Drawing.from_dict(data)

    def _read_layer(self, element: ET.Element) -> dict:
        return {
            "name": self._attr(element, "name"),
            "visible": self._text_to_bool(element.get("visible", "true")),
            "locked": self._text_to_bool(element.get("locked", "false")),
            "shapes": [self._read_shape(item) for item in element.findall("shape")],
        }

    def _read_shape(self, element: ET.Element) -> dict:
        style = self._required(element, "style")
        fill = style.get("fill", "none")
        geometry_element = self._required(element, "geometry")
        geometry = {key: self._number(geometry_element, key)
                    for key in geometry_element.attrib}
        points = geometry_element.findall("point")
        if points:
            geometry["points"] = [{"x": self._number(p, "x"), "y": self._number(p, "y")}
                                  for p in points]
        shape = {
            "type": self._attr(element, "type"),
            "id": int(self._attr(element, "id")),
            "name": element.get("name", ""),
            "visible": self._text_to_bool(element.get("visible", "true")),
            "style": {
                "stroke": self._attr(style, "stroke"),
                "fill": None if fill == "none" else fill,
                "stroke_width": self._number(style, "stroke_width"),
            },
            "geometry": geometry,
        }
        text = element.find("text")
        if text is not None:
            shape["text"] = {
                "content": text.text or "",
                "font_family": text.get("font_family", "Arial"),
                "font_size": self._number(text, "font_size"),
            }
        return shape

    # ---------- вспомогательные методы ----------
    @staticmethod
    def _required(parent: ET.Element, tag: str) -> ET.Element:
        element = parent.find(tag)
        if element is None:
            raise KeyError(f"<{tag}>")
        return element

    @staticmethod
    def _attr(element: ET.Element, name: str) -> str:
        value = element.get(name)
        if value is None:
            raise KeyError(f"<{element.tag} {name}=...>")
        return value

    @classmethod
    def _number(cls, element: ET.Element, name: str):
        return compact(float(cls._attr(element, name)))

    @staticmethod
    def _bool_to_text(value: bool) -> str:
        return "true" if value else "false"

    @staticmethod
    def _text_to_bool(text: str) -> bool:
        if text not in ("true", "false"):
            raise ValueError(f"ожидалось true/false, получено {text!r}")
        return text == "true"
