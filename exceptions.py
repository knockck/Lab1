"""Собственные исключения графического редактора.

Все исключения наследуются от общего базового класса GraphicEditorError,
поэтому в интерфейсе их можно перехватывать одним блоком except.
"""


class GraphicEditorError(Exception):
    """Базовое исключение графического редактора."""


class InvalidColorError(GraphicEditorError):
    """Цвет задан в неверном формате или компоненты вне диапазона 0..255."""

    def __init__(self, value):
        self.value = value
        super().__init__(
            f"Некорректный цвет: {value!r}. Ожидается #RRGGBB, #RRGGBBAA "
            f"или название цвета (например, red, синий)"
        )


class InvalidShapeError(GraphicEditorError):
    """Недопустимые параметры фигуры (размер, количество точек, текст и т.п.)."""


class LayerNotFoundError(GraphicEditorError):
    """Слой с указанным именем не найден в документе."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Слой «{name}» не найден")


class DuplicateLayerError(GraphicEditorError):
    """Слой с таким именем уже существует."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Слой «{name}» уже существует")


class LayerLockedError(GraphicEditorError):
    """Попытка изменить заблокированный слой."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Слой «{name}» заблокирован для изменений")


class ShapeNotFoundError(GraphicEditorError):
    """Фигура с указанным идентификатором не найдена."""

    def __init__(self, shape_id):
        self.shape_id = shape_id
        super().__init__(f"Фигура с id={shape_id} не найдена")


class UnknownShapeTypeError(GraphicEditorError):
    """Неизвестный тип фигуры (например, при чтении из файла)."""

    def __init__(self, type_name):
        self.type_name = type_name
        super().__init__(f"Неизвестный тип фигуры: {type_name!r}")


class EditorOperationError(GraphicEditorError):
    """Операция невозможна в текущем состоянии редактора."""
