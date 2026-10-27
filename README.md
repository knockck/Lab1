# Графический редактор

Лабораторная работа по дисциплине «Прикладное программирование»:
«ООП в Python. Обработка исключительных ситуаций. Форматы XML и JSON».
Вариант 18 — предметная область графического редактора.

Консольное приложение для работы с рисунком: фигуры, слои, стили, отмена
действий, сохранение и загрузка в JSON и XML. Сторонние библиотеки не нужны.

## Возможности

- **Фигуры:** прямоугольник, эллипс, круг, линия, многоугольник, текстовая надпись.
  Для каждой фигуры считаются площадь и периметр.
- **Операции с фигурами:** перемещение, масштабирование, перекраска, дублирование,
  перенос в другой слой, вывод на передний или задний план, удаление.
- **Поиск фигур в точке.** Учитывается настоящая форма фигуры (круг, многоугольник,
  линия), а не только её прямоугольная рамка. Первой идёт верхняя видимая фигура.
- **Слои:** добавление, выбор активного слоя, блокировка, скрытие, порядок
  (выше или ниже), удаление вместе с фигурами.
- **Правила редактора:**
  - заблокированный слой нельзя менять;
  - нельзя удалить единственный слой;
  - имена слоёв уникальны;
  - если операция завершилась ошибкой, рисунок возвращается в исходное состояние.
- **Отмена последних действий** (до 50 шагов) и **статистика рисунка**: число фигур
  по типам и слоям, фигуры за границами холста, суммарная площадь.
- **Сохранение и загрузка** в форматах JSON и XML.
- **Обработка встроенных и собственных исключений.** Программа не завершается
  при ошибках пользователя.

## Архитектура

Приложение разделено на четыре слоя. Каждый слой обращается только к слоям
ниже себя:

```
 main.py           ConsoleApp — консольное приложение (21 действие),
   |               build_app() — сборка слоёв (внедрение зависимостей)
   v
 service_layer     бизнес-логика: DrawingService, LayerService, ShapeService,
   |               HistoryService, ShapeFactory
   v
 repository_layer  CRUD-операции над сущностями: интерфейсы Repository,
   |               ShapeRepository, LayerRepository, CanvasRepository,
   |               их реализации в памяти InMemory*Repository,
   |               файловые хранилища JsonDrawingStorage, XmlDrawingStorage
   v
 data_layer        сущности: Point, Color, Style, Shape и 6 фигур, Layer,
                   Canvas, Drawing

 exceptions.py     собственные исключения (используются всеми слоями)
```

| Слой | За что отвечает | Чего не делает |
|---|---|---|
| `main.py` | ввод и вывод, меню, перехват исключений | не содержит правил редактора и не знает, где хранятся данные |
| `service_layer` | сценарии и правила: блокировка слоёв, порядок отрисовки, отмена, поиск, проверка загруженных файлов | не знает, как устроено хранение |
| `repository_layer` | хранение сущностей: добавить, получить, изменить, удалить; запись и чтение файлов | не содержит бизнес-правил |
| `data_layer` | данные сущностей и их собственные инварианты (размеры > 0, корректный цвет), геометрия | не знает о репозиториях и сервисах |

Сервисы работают только с **интерфейсами** репозиториев. Конкретные реализации
передаются им в конструктор в функции `build_app()` (`main.py`). Поэтому если
сущности перестанут храниться в словарях в оперативной памяти и начнут храниться,
например, в базе данных, достаточно написать новую реализацию интерфейса.
Бизнес-логику и меню менять не придётся.

```python
class SqliteShapeRepository(ShapeRepository):
    def add(self, entity): ...        # INSERT
    def get(self, key): ...           # SELECT ... WHERE id = ?
    def update(self, entity): ...     # UPDATE
    def delete(self, key): ...        # DELETE
    ...

# в build_app():
shape_repository = SqliteShapeRepository("drawing.db")   # вместо InMemoryShapeRepository()
```

### Принципы SOLID

- **S — единственная ответственность.** У каждого класса одна задача:
  - сущность хранит данные и проверяет себя;
  - репозиторий хранит сущности;
  - `JsonDrawingStorage` и `XmlDrawingStorage` отвечают только за формат файла;
  - `HistoryService` отвечает только за историю изменений;
  - `ConsoleApp` отвечает только за диалог с пользователем.
- **O — открытость для расширения.** Новые возможности добавляются без изменения
  готового кода:
  - новая фигура — это наследник `Shape` и одна запись в `ShapeFactory.KINDS`
    (меню само спросит нужные параметры);
  - новый формат файла — это наследник `DrawingStorage` и одна строка в `build_app()`.
- **L — подстановка Лисков.** Наследники можно использовать вместо базового класса:
  - сервисы вызывают `area()`, `move()`, `scale()`, `contains_point()` у любой
    фигуры, не зная её класса;
  - любая реализация `ShapeRepository` подходит сервисам.
- **I — разделение интерфейсов.** Вместо одного «репозитория всего» есть
  отдельные интерфейсы: `ShapeRepository`, `LayerRepository` и `CanvasRepository`.
  У холста одна запись, поэтому полный CRUD ему не навязывается.
- **D — инверсия зависимостей.** Сервисы зависят от абстракций и получают
  реализации через конструктор.

## Структура проекта

```
main.py                         точка входа: ConsoleApp и build_app()
exceptions.py                   собственные исключения
data_layer/
  primitives.py                 Point, Color, Style
  shapes.py                     Shape (абстрактный) и Rectangle, Ellipse, Circle,
                                Line, Polygon, TextLabel
  layer.py                      Layer
  canvas.py                     Canvas — параметры холста
  drawing.py                    Drawing — снимок рисунка целиком
repository_layer/
  interfaces.py                 Repository[K, E], ShapeRepository, LayerRepository,
                                CanvasRepository
  memory.py                     InMemoryShapeRepository, InMemoryLayerRepository,
                                InMemoryCanvasRepository
  file_storage.py               DrawingStorage, JsonDrawingStorage, XmlDrawingStorage
service_layer/
  history_service.py            HistoryService — снимки, отмена, откат при ошибке
  shape_factory.py              ShapeFactory — создание фигур по типу и параметрам
  shape_service.py              ShapeService — операции с фигурами
  layer_service.py              LayerService — операции со слоями
  drawing_service.py            DrawingService — рисунок, статистика, файлы
examples/
  drawing.json, drawing.xml     пример рисунка в двух форматах
docs/uml/
  class_diagram.drawio          UML-диаграмма классов (draw.io)
  *.png                         части диаграммы
tests/                          модульные тесты по слоям (unittest)
```

## Запуск

Нужен Python 3.9 или новее.

```bash
python main.py              # консольное приложение
python -m unittest -v       # тесты
```

Пункт меню 21 без ввода пути открывает пример `examples/drawing.json`.

## Обработка исключений

Все собственные исключения наследуются от `GraphicEditorError`:

| Исключение | Когда возникает |
|---|---|
| `InvalidColorError` | неверный формат цвета |
| `InvalidShapeError` | недопустимые параметры фигуры |
| `LayerNotFoundError`, `ShapeNotFoundError` | нет слоя или фигуры с таким ключом |
| `DuplicateLayerError` | слой с таким именем уже есть |
| `LayerLockedError` | попытка изменить заблокированный слой |
| `UnknownShapeTypeError` | неизвестный тип фигуры |
| `EditorOperationError` | операция невозможна (удалить единственный слой, отменить при пустой истории) |
| `UnsupportedFormatError` | расширение файла не `.json` и не `.xml` |
| `DocumentFormatError` | файл повреждён или нарушает правила рисунка |

`ConsoleApp.run()` выполняет каждое действие внутри `try`. Порядок перехвата:
сначала собственные исключения, затем встроенные (`ValueError`, `TypeError`,
`FileNotFoundError`, `PermissionError`), последним — `Exception`.

`HistoryService.track()` выполняет каждую операцию сервиса как транзакцию:
если внутри возникло исключение, все изменения откатываются.

## Форматы файлов

Обе структуры описывают один и тот же рисунок: документ → слои → фигуры.
Порядок слоёв и фигур в файле — это порядок отрисовки, снизу вверх.

**JSON**

```json
{
  "format": "graphic-editor",
  "version": 1,
  "document": {
    "title": "Домик у озера", "width": 800, "height": 600,
    "background": "#FFFFFF", "active_layer": "Дом",
    "layers": [
      {
        "name": "Дом", "visible": true, "locked": false,
        "shapes": [
          {
            "type": "Rectangle", "id": 5, "name": "Стены", "visible": true,
            "style": {"stroke": "#8B4513", "fill": "#FFE0B2", "stroke_width": 2},
            "geometry": {"x": 380, "y": 260, "width": 240, "height": 180}
          }
        ]
      }
    ]
  }
}
```

**XML**

```xml
<graphic_editor version="1">
  <document title="Домик у озера" width="800" height="600" background="#FFFFFF" active_layer="Дом">
    <layer name="Дом" visible="true" locked="false">
      <shape type="Polygon" id="6" name="Крыша" visible="true">
        <style stroke="#8B4513" fill="#C62828" stroke_width="2" />
        <geometry>
          <point x="360" y="260" />
          <point x="500" y="150" />
          <point x="640" y="260" />
        </geometry>
      </shape>
    </layer>
  </document>
</graphic_editor>
```

Поле `geometry` зависит от типа фигуры:

| Тип | Параметры |
|---|---|
| `Rectangle` | `x`, `y`, `width`, `height` |
| `Ellipse` | `cx`, `cy`, `rx`, `ry` |
| `Circle` | `cx`, `cy`, `r` |
| `Line` | `x1`, `y1`, `x2`, `y2` |
| `Polygon` | `points` — список вершин; в XML это элементы `<point>` |
| `TextLabel` | `x`, `y` и отдельный объект `text` (`content`, `font_family`, `font_size`); в XML это элемент `<text>` |

Если у фигуры нет заливки, в JSON пишется `"fill": null`, а в XML — `fill="none"`.
