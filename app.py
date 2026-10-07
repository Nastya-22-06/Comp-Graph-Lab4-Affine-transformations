import math
import tkinter as tk
from tkinter import ttk, messagebox

from algorithms import (
    point_in_polygon,
    segment_intersection,
    side_of_edge,
)
from geometry import Polygon
from transformations import (
    apply_matrix,
    around_point,
    rotation,
    scaling,
    translation,
)


class GeometryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Полигоны и аффинные преобразования")
        self.root.geometry("1180x760")

        self.polygons = []
        self.current_points = []
        self.selected_polygon = None

        self.mode = "create"

        self.selected_edge = None
        self.test_edge_start = None
        self.preview_point = None
        self.intersection_point = None

        self.last_test_point = None
        self._build_ui()
        self._bind_events()
        self.redraw()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        self.canvas = tk.Canvas(
            main,
            width=850,
            height=720,
            bg="white",
            highlightthickness=1,
            highlightbackground="#888",
        )
        self.canvas.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Инструменты", font=("Arial", 12, "bold")).pack(
            anchor="w", pady=(0, 6)
        )

        ttk.Button(
            left, text="Создание полигона", command=lambda: self.set_mode("create")
        ).pack(fill="x", pady=2)

        ttk.Button(
            left, text="Выбрать полигон", command=lambda: self.set_mode("select")
        ).pack(fill="x", pady=2)

        ttk.Button(
            left, text="Проверка точки", command=lambda: self.set_mode("point_test")
        ).pack(fill="x", pady=2)

        ttk.Button(
            left, text="Справа / слева от ребра",
            command=lambda: self.set_mode("edge_side")
        ).pack(fill="x", pady=2)

        ttk.Button(
            left, text="Пересечение рёбер",
            command=lambda: self.set_mode("intersection")
        ).pack(fill="x", pady=2)

        ttk.Button(left, text="Очистить сцену", command=self.clear_scene).pack(
            fill="x", pady=(8, 12)
        )

        ttk.Separator(left).pack(fill="x", pady=6)

        ttk.Label(left, text="Перенос", font=("Arial", 10, "bold")).pack(anchor="w")
        self.dx = self._entry_row(left, "dx", "20")
        self.dy = self._entry_row(left, "dy", "20")
        ttk.Button(left, text="Применить перенос", command=self.move_selected).pack(
            fill="x", pady=3
        )

        ttk.Separator(left).pack(fill="x", pady=6)

        ttk.Label(left, text="Поворот", font=("Arial", 10, "bold")).pack(anchor="w")
        self.angle = self._entry_row(left, "угол", "30")
        self.px = self._entry_row(left, "x точки", "400")
        self.py = self._entry_row(left, "y точки", "300")

        ttk.Button(
            left, text="Вокруг заданной точки", command=self.rotate_about_point
        ).pack(fill="x", pady=2)
        ttk.Button(
            left, text="Вокруг своего центра", command=self.rotate_about_center
        ).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=6)

        ttk.Label(left, text="Масштаб", font=("Arial", 10, "bold")).pack(anchor="w")
        self.sx = self._entry_row(left, "sx", "1.2")
        self.sy = self._entry_row(left, "sy", "1.2")
        self.msx = self._entry_row(left, "x точки", "400")   
        self.msy = self._entry_row(left, "y точки", "300") 

        ttk.Button(
            left, text="От заданной точки", command=self.scale_about_point
        ).pack(fill="x", pady=2)
        ttk.Button(
            left, text="От своего центра", command=self.scale_about_center
        ).pack(fill="x", pady=2)

        ttk.Separator(left).pack(fill="x", pady=8)

        self.status = ttk.Label(
            left,
            text="ЛКМ — вершины, ПКМ — закончить полигон",
            wraplength=260,
            justify="left",
        )
        self.status.pack(fill="x")

    def _entry_row(self, parent, label, default):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=1)

        ttk.Label(row, text=label, width=10).pack(side="left")

        entry = ttk.Entry(row, width=10)
        entry.insert(0, default)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def set_mode(self, mode):
        self.mode = mode
        self.current_points = []
        self.test_edge_start = None
        self.preview_point = None
        self.intersection_point = None
        self.last_test_point = None

        if mode == "create":
            text = "Создание: ЛКМ — добавить вершину, ПКМ — закончить."
        elif mode == "select":
            text = "Выбор: щёлкните по полигону или рядом с его ребром."
        elif mode == "point_test":
            text = "Проверка точки: выберите полигон, потом кликайте точки."
        elif mode == "edge_side":
            text = "Выберите направленное ребро A → B, потом кликайте точки. Слева/справа считаются относительно A → B."
        else:
            text = "Сначала выберите ребро полигона. Потом стройте второе ребро двумя кликами."

        self.set_status(text)
        self.redraw()

    def set_status(self, text):
        self.status.config(text=text)

    def on_left_click(self, event):
        p = (float(event.x), float(event.y))

        if self.mode == "create":
            self.current_points.append(p)
            self.redraw()
            return

        if self.mode == "select":
            self.select_polygon_at(p)
            return

        if self.mode == "point_test":
            if self.selected_polygon is None:
                self.select_polygon_at(p)
                return

            inside, kind = point_in_polygon(p, self.selected_polygon)
            self.last_test_point = p
            answer = "внутри" if inside else "снаружи"
            self.set_status(f"Точка {answer}. Полигон: {kind}.")
            self.redraw()
            return

        if self.mode == "edge_side":
            if self.selected_edge is None:
                self.selected_edge = self.find_edge_near(p)
                if self.selected_edge:
                    self.set_status("Ребро выбрано. Теперь можно проверять точки.")
                else:
                    self.set_status("Рядом с кликом ребро не найдено.")
                self.redraw()
                return

            self.last_test_point = p
            a, b = self.selected_edge
            result = side_of_edge(a, b, p)
            self.set_status(f"Точка находится: {result}.")
            self.redraw()
            return

        if self.mode == "intersection":
            if self.selected_edge is None:
                self.selected_edge = self.find_edge_near(p)
                if self.selected_edge:
                    self.set_status("Первое ребро выбрано. Задайте начало второго ребра.")
                else:
                    self.set_status("Рядом с кликом ребро не найдено.")
                self.redraw()
                return

            if self.test_edge_start is None:
                self.test_edge_start = p
                self.preview_point = p
                self.intersection_point = None
                self.set_status("Двигайте мышь и кликните конец второго ребра.")
            else:
                self.preview_point = p
                a, b = self.selected_edge
                self.intersection_point = segment_intersection(
                    a, b, self.test_edge_start, p
                )

                if self.intersection_point is None:
                    self.set_status("Отрезки не пересекаются. Можно сразу проверить новое ребро.")
                else:
                    x, y = self.intersection_point
                    self.set_status(
                        f"Пересечение: ({x:.1f}, {y:.1f}). Можно сразу проверить новое ребро."
                    )

                # Инструмент остается выбранным, меняем только тестовое ребро.
                self.test_edge_start = None

            self.redraw()

    def on_right_click(self, event):
        if self.mode != "create":
            return

        if not self.current_points:
            return

        number = len(self.polygons) + 1
        self.polygons.append(
            Polygon(self.current_points.copy(), f"Полигон {number}")
        )
        self.selected_polygon = self.polygons[-1]
        self.current_points = []

        self.set_status("Полигон добавлен. Можно рисовать следующий.")
        self.redraw()

    def on_mouse_move(self, event):
        if (
            self.mode == "intersection"
            and self.selected_edge is not None
            and self.test_edge_start is not None
        ):
            self.preview_point = (float(event.x), float(event.y))
            self.redraw()

    def clear_scene(self):
        self.polygons.clear()
        self.current_points.clear()
        self.selected_polygon = None
        self.selected_edge = None
        self.test_edge_start = None
        self.preview_point = None
        self.intersection_point = None
        self.last_test_point = None

        self.set_status("Сцена очищена.")
        self.redraw()

    def select_polygon_at(self, p):
        found = None

        for polygon in reversed(self.polygons):
            if self.point_near_polygon(p, polygon):
                found = polygon
                break

        self.selected_polygon = found
        self.selected_edge = None

        if found:
            self.set_status(f"Выбран: {found.name}.")
        else:
            self.set_status("Полигон не найден.")

        self.redraw()

    def point_near_polygon(self, p, polygon):
        if len(polygon.points) == 1:
            return self.distance(p, polygon.points[0]) <= 10

        for a, b in polygon.edges():
            if self.distance_to_segment(p, a, b) <= 8:
                return True

        if len(polygon.points) >= 3:
            inside, _ = point_in_polygon(p, polygon)
            return inside

        return False

    def find_edge_near(self, p):
        best = None
        best_distance = 10.0

        for polygon in self.polygons:
            for edge in polygon.edges():
                d = self.distance_to_segment(p, edge[0], edge[1])
                if d < best_distance:
                    best_distance = d
                    best = edge

        return best

    @staticmethod
    def distance(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])

    @staticmethod
    def distance_to_segment(p, a, b):
        ax, ay = a
        bx, by = b
        px, py = p

        dx = bx - ax
        dy = by - ay

        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)

        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))

        qx = ax + t * dx
        qy = ay + t * dy

        return math.hypot(px - qx, py - qy)

    def selected_or_warn(self):
        if self.selected_polygon is None:
            messagebox.showinfo("Полигон", "Сначала выберите полигон.")
            return None
        return self.selected_polygon

    def read_float(self, entry, name):
        try:
            return float(entry.get())
        except ValueError:
            raise ValueError(f"Поле '{name}' должно быть числом.")

    def transform_selected(self, matrix):
        polygon = self.selected_or_warn()
        if polygon is None:
            return

        polygon.points = [
            apply_matrix(point, matrix)
            for point in polygon.points
        ]

        # После преобразования старое выбранное ребро уже не актуально.
        self.selected_edge = None
        self.set_status("Преобразование применено матрицей.")
        self.redraw()

    def move_selected(self):
        try:
            dx = self.read_float(self.dx, "dx")
            dy = self.read_float(self.dy, "dy")
            self.transform_selected(translation(dx, dy))
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def rotate_about_point(self):
        try:
            angle = self.read_float(self.angle, "угол")
            px = self.read_float(self.px, "x точки")
            py = self.read_float(self.py, "y точки")

            matrix = around_point(rotation(angle), px, py)
            self.transform_selected(matrix)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def rotate_about_center(self):
        polygon = self.selected_or_warn()
        if polygon is None:
            return

        try:
            angle = self.read_float(self.angle, "угол")
            cx, cy = polygon.center()

            matrix = around_point(rotation(angle), cx, cy)
            self.transform_selected(matrix)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def scale_about_point(self):
        try:
            sx = self.read_float(self.sx, "sx")
            sy = self.read_float(self.sy, "sy")
            px = self.read_float(self.msx, "x точки")   # ← теперь свои поля
            py = self.read_float(self.msy, "y точки")   # ← теперь свои поля

            matrix = around_point(scaling(sx, sy), px, py)
            self.transform_selected(matrix)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def scale_about_center(self):
        polygon = self.selected_or_warn()
        if polygon is None:
            return

        try:
            sx = self.read_float(self.sx, "sx")
            sy = self.read_float(self.sy, "sy")
            cx, cy = polygon.center()

            matrix = around_point(scaling(sx, sy), cx, cy)
            self.transform_selected(matrix)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))

    def redraw(self):
        self.canvas.delete("all")

        for polygon in self.polygons:
            selected = polygon is self.selected_polygon
            line_width = 3 if selected else 2

            self.draw_polygon(polygon, line_width)

        self.draw_current_polygon()

        if self.selected_edge:
            a, b = self.selected_edge
            self.canvas.create_line(
                a[0], a[1], b[0], b[1],
                width=5,
                arrow=tk.LAST,
            )

        if self.mode == "intersection" and self.test_edge_start and self.preview_point:
            a = self.test_edge_start
            b = self.preview_point
            self.canvas.create_line(
                a[0], a[1], b[0], b[1],
                width=3,
                dash=(5, 3),
            )
            self.draw_point(a, radius=4)

        if self.intersection_point:
            self.draw_point(self.intersection_point, radius=7)
            x, y = self.intersection_point
            self.canvas.create_text(
                x + 12, y - 12,
                text="пересечение",
                anchor="w",
            )

        if self.last_test_point:
            self.draw_point(self.last_test_point, radius=6)

    def draw_polygon(self, polygon, width):
        pts = polygon.points

        if len(pts) == 1:
            self.draw_point(pts[0], radius=5)
            return

        if len(pts) == 2:
            a, b = pts
            self.canvas.create_line(
                a[0], a[1], b[0], b[1],
                width=width,
            )
            self.draw_point(a)
            self.draw_point(b)
            return

        flat = [coord for p in pts for coord in p]
        self.canvas.create_polygon(
            *flat,
            outline="black",
            fill="",
            width=width,
        )

        for p in pts:
            self.draw_point(p, radius=3)

        if polygon is self.selected_polygon:
            cx, cy = polygon.center()
            self.canvas.create_oval(
                cx - 4, cy - 4, cx + 4, cy + 4,
                outline="black",
                width=2,
            )
            self.canvas.create_text(
                cx + 8, cy + 8,
                text="центр",
                anchor="nw",
            )

    def draw_current_polygon(self):
        pts = self.current_points
        if not pts:
            return

        for p in pts:
            self.draw_point(p, radius=4)

        if len(pts) >= 2:
            flat = [coord for p in pts for coord in p]
            self.canvas.create_line(*flat, width=2, dash=(4, 2))

    def draw_point(self, p, radius=4):
        x, y = p
        self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill="black",
            outline="black",
        )
