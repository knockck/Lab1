"""Точка входа: консольное приложение «Графический редактор».

Здесь только интерфейс пользователя — ввод, вывод и обработка исключений.
Бизнес-логика находится в service_layer, хранение — в repository_layer,
сущности — в data_layer. Функция build_app() собирает слои вместе.
"""

from __future__ import annotations

from exceptions import GraphicEditorError
from repository_layer import (InMemoryCanvasRepository, InMemoryLayerRepository,
                              InMemoryShapeRepository)
from service_layer import DrawingService, HistoryService, LayerService, Param, ShapeService


# ---------------- ввод данных ----------------
def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_float(prompt: str, default: float | None = None) -> float:
    text = ask(prompt)
    if not text and default is not None:
        return default
    try:
        return float(text.replace(",", "."))
    except ValueError:
        raise ValueError(f"«{text}» не является числом") from None


def ask_int(prompt: str) -> int:
    text = ask(prompt)
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"«{text}» не является целым числом") from None


def parse_point(text: str) -> tuple[float, float]:
    parts = text.replace(",", " ").split()
    if len(parts) != 2:
        raise ValueError(f"Точку нужно ввести как два числа через пробел, получено «{text}»")
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        raise ValueError(f"Координаты точки должны быть числами, получено «{text}»") from None


def ask_point(prompt: str) -> tuple[float, float]:
    return parse_point(ask(prompt + " (x y): "))


def ask_points(prompt: str) -> list[tuple[float, float]]:
    text = ask(prompt + " через «;» (например: 0 0; 100 0; 50 80): ")
    return [parse_point(part) for part in text.split(";") if part.strip()]


def ask_choice(prompt: str, options: dict):
    choice = ask(prompt)
    if choice not in options:
        raise ValueError(f"Нужно выбрать один из вариантов: {', '.join(options)}")
    return options[choice]


# ---------------- консольное приложение ----------------
class ConsoleApp:
    """Меню из n действий; каждое действие вызывает методы сервисов."""

    def __init__(self, drawings: DrawingService, layers: LayerService, shapes: ShapeService):
        self.drawings = drawings
        self.layers = layers
        self.shapes = shapes
        self.actions = [
            ("1", "Показать рисунок", self.show_drawing),
            ("2", "Новый рисунок", self.new_drawing),
            ("3", "Добавить фигуру", self.add_shape),
            ("4", "Переместить фигуру", self.move_shape),
            ("5", "Масштабировать фигуру", self.scale_shape),
            ("6", "Изменить цвет фигуры", self.recolor_shape),
            ("7", "Дублировать фигуру", self.duplicate_shape),
            ("8", "Перенести фигуру в слой", self.move_shape_to_layer),
            ("9", "На передний/задний план", self.change_z_order),
            ("10", "Удалить фигуру", self.delete_shape),
            ("11", "Найти фигуры в точке", self.find_shapes),
            ("12", "Добавить слой", self.add_layer),
            ("13", "Выбрать активный слой", self.select_layer),
            ("14", "Заблокировать/разблокировать", self.toggle_layer_lock),
            ("15", "Скрыть/показать слой", self.toggle_layer_visibility),
            ("16", "Поднять/опустить слой", self.move_layer),
            ("17", "Удалить слой", self.delete_layer),
            ("18", "Статистика", self.show_statistics),
            ("19", "Отменить последнее действие", self.undo),
        ]

    def menu_text(self) -> str:
        items = [f"{key:>2}. {title}" for key, title, _ in self.actions] + [" 0. Выход"]
        half = (len(items) + 1) // 2
        rows = [f"{left:<34}{right}" for left, right in
                zip(items[:half], items[half:] + [""] * (2 * half - len(items)))]
        line = "=" * 66
        return "\n".join([line, "ГРАФИЧЕСКИЙ РЕДАКТОР".center(66), line, *rows, line])

    def run(self) -> None:
        handlers = {key: action for key, _, action in self.actions}
        while True:
            print()
            print(self.menu_text())
            choice = ask("Выберите пункт меню: ")
            if choice == "0":
                break
            action = handlers.get(choice)
            if action is None:
                print("Нет такого пункта меню.")
                continue
            try:
                action()
            except GraphicEditorError as error:        # собственные исключения
                print(f"[Ошибка редактора] {error}")
            except ValueError as error:                # встроенные исключения
                print(f"[Ошибка ввода] {error}")
            except TypeError as error:
                print(f"[Ошибка типа] {error}")
            except Exception as error:                 # на случай непредвиденной ошибки
                print(f"[Непредвиденная ошибка] {type(error).__name__}: {error}")

    # ---------------- рисунок ----------------
    def show_drawing(self) -> None:
        canvas = self.drawings.canvas()
        print(canvas)
        for layer, shapes in reversed(self.drawings.overview()):
            marker = "*" if layer.name == canvas.active_layer else " "
            print(f" {marker} {layer}: фигур — {len(shapes)}")
            for shape in reversed(shapes):
                print(f"      {shape}")
                print(f"        стиль: {shape.style}")
        print("(слои и фигуры — сверху вниз, * — активный слой)")

    def new_drawing(self) -> None:
        title = ask("Название: ")
        width = ask_float("Ширина холста (Enter — 800): ", 800)
        height = ask_float("Высота холста (Enter — 600): ", 600)
        background = ask("Цвет фона (#RRGGBB или название, Enter — белый): ") or None
        print("Создан:", self.drawings.new_drawing(title, width, height, background))

    def show_statistics(self) -> None:
        stats = self.drawings.statistics()
        print(f"Слоёв: {stats['layers']}, фигур: {stats['shapes']} "
              f"(скрытых: {stats['hidden']}, за границей холста: {stats['outside']})")
        print(f"Суммарная площадь фигур: {stats['total_area']:.2f}")
        by_type = ", ".join(f"{name} — {count}" for name, count in stats["by_type"].items())
        by_layer = ", ".join(f"{name} — {count}" for name, count in stats["by_layer"].items())
        print("По типам:", by_type or "нет фигур")
        print("По слоям:", by_layer)

    def undo(self) -> None:
        self.drawings.undo()
        print("Последнее действие отменено.")

    # ---------------- фигуры ----------------
    def ask_param(self, param: Param):
        if param.kind == "number":
            hint = f" (Enter — {param.default})" if param.default is not None else ""
            return ask_float(f"{param.prompt}{hint}: ", param.default)
        if param.kind == "point":
            return ask_point(param.prompt)
        if param.kind == "points":
            return ask_points(param.prompt)
        return ask(f"{param.prompt}: ")

    def add_shape(self) -> None:
        factory = self.shapes.factory
        kinds = factory.kinds()
        print("Тип фигуры:", ", ".join(f"{i} — {t}" for i, (_, t) in enumerate(kinds, 1)))
        kind = ask_choice("> ", {str(i): key for i, (key, _) in enumerate(kinds, 1)})
        params = {param.name: self.ask_param(param) for param in factory.params(kind)}
        stroke = ask("Цвет контура (#RRGGBB или название, Enter — чёрный): ") or None
        fill = ask("Цвет заливки (Enter — без заливки): ") or None
        width = ask_float("Толщина линии (Enter — 1): ", 1)
        shape = self.shapes.create(kind, params, stroke, fill, width)
        print(f"Добавлено в слой «{shape.layer}»: {shape}")

    def move_shape(self) -> None:
        shape_id = ask_int("id фигуры: ")
        dx, dy = ask_float("Сдвиг по x: "), ask_float("Сдвиг по y: ")
        print("Перемещено:", self.shapes.move(shape_id, dx, dy))

    def scale_shape(self) -> None:
        shape_id = ask_int("id фигуры: ")
        print("Масштабировано:", self.shapes.scale(shape_id, ask_float("Коэффициент: ")))

    def recolor_shape(self) -> None:
        shape_id = ask_int("id фигуры: ")
        stroke = ask("Новый цвет контура (Enter — не менять): ") or None
        fill = ask("Новый цвет заливки (Enter — не менять, «нет» — убрать): ")
        remove_fill = fill.lower() in ("нет", "none")
        new_fill = None if remove_fill else fill or None
        shape = self.shapes.recolor(shape_id, stroke, new_fill, remove_fill)
        print("Новый стиль:", shape.style)

    def duplicate_shape(self) -> None:
        print("Создана копия:", self.shapes.duplicate(ask_int("id фигуры: ")))

    def move_shape_to_layer(self) -> None:
        shape_id = ask_int("id фигуры: ")
        shape = self.shapes.move_to_layer(shape_id, ask("Имя слоя: "))
        print(f"Фигура #{shape.id} перенесена в слой «{shape.layer}»")

    def change_z_order(self) -> None:
        shape_id = ask_int("id фигуры: ")
        to_front = ask_choice("1 — на передний план, 2 — на задний: ", {"1": True, "2": False})
        if to_front:
            shape = self.shapes.bring_to_front(shape_id)
        else:
            shape = self.shapes.send_to_back(shape_id)
        print(f"Фигура #{shape.id} перемещена на {'передний' if to_front else 'задний'} план")

    def delete_shape(self) -> None:
        print("Удалено:", self.shapes.delete(ask_int("id фигуры: ")))

    def find_shapes(self) -> None:
        x, y = ask_point("Точка")
        found = self.shapes.find_at(x, y)
        if not found:
            print("В этой точке нет видимых фигур.")
        for shape in found:
            print(f"  слой «{shape.layer}»: {shape}")

    # ---------------- слои ----------------
    def add_layer(self) -> None:
        print("Добавлен и выбран:", self.layers.create(ask("Имя нового слоя: ")))

    def select_layer(self) -> None:
        print("Активный слой:", self.layers.select(ask("Имя слоя: ")))

    def toggle_layer_lock(self) -> None:
        print(self.layers.toggle_lock(ask("Имя слоя: ")))

    def toggle_layer_visibility(self) -> None:
        print(self.layers.toggle_visibility(ask("Имя слоя: ")))

    def move_layer(self) -> None:
        name = ask("Имя слоя: ")
        step = ask_choice("1 — выше, 2 — ниже: ", {"1": 1, "2": -1})
        self.layers.move(name, step)
        names = ", ".join(layer.name for layer in self.layers.list_layers())
        print("Порядок слоёв снизу вверх:", names)

    def delete_layer(self) -> None:
        layer, count = self.layers.delete(ask("Имя слоя: "))
        print(f"Слой «{layer.name}» удалён вместе с фигурами ({count} шт.)")


# ---------------- сборка приложения ----------------
def build_app() -> ConsoleApp:
    """Создаёт репозитории и передаёт их в сервисы (внедрение зависимостей).

    Чтобы хранить данные по-другому, достаточно подставить сюда другие
    реализации интерфейсов репозиториев — сервисы и меню не меняются.
    """
    canvas_repository = InMemoryCanvasRepository()
    layer_repository = InMemoryLayerRepository()
    shape_repository = InMemoryShapeRepository()
    history = HistoryService(canvas_repository, layer_repository, shape_repository)

    drawings = DrawingService(canvas_repository, layer_repository, shape_repository,
                              history)
    layers = LayerService(layer_repository, shape_repository, canvas_repository, history)
    shapes = ShapeService(shape_repository, layer_repository, canvas_repository, history)

    drawings.new_drawing("Без названия", 800, 600)
    history.clear()
    return ConsoleApp(drawings, layers, shapes)


def main() -> None:
    app = build_app()
    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        print("\nРабота прервана пользователем.")
    finally:
        print("До свидания!")


if __name__ == "__main__":
    main()
