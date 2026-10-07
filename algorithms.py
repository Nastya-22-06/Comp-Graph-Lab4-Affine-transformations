from typing import Optional, Tuple

from geometry import Point, Polygon

EPS = 1e-9


def cross(a: Point, b: Point, p: Point) -> float:
    # Векторное произведение (b-a) x (p-a).
    return (
        (b[0] - a[0]) * (p[1] - a[1])
        - (b[1] - a[1]) * (p[0] - a[0])
    )


def side_of_edge(a: Point, b: Point, p: Point) -> str:
    # В Canvas ось Y направлена вниз, поэтому знак инвертируем.
    value = -cross(a, b, p)

    if abs(value) <= EPS:
        return "на ребре"

    return "слева" if value > 0 else "справа"


def point_on_segment(p: Point, a: Point, b: Point) -> bool:
    if abs(cross(a, b, p)) > EPS:
        return False

    return (
        min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS
        and min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS
    )


def segment_intersection(
    a: Point,
    b: Point,
    c: Point,
    d: Point,
) -> Optional[Point]:
    # Параметрическая форма из лекции: P(t) = a + t(b-a).
    rx = b[0] - a[0]
    ry = b[1] - a[1]
    sx = d[0] - c[0]
    sy = d[1] - c[1]

    denominator = rx * sy - ry * sx

    if abs(denominator) <= EPS:
        return None

    qpx = c[0] - a[0]
    qpy = c[1] - a[1]

    t = (qpx * sy - qpy * sx) / denominator
    u = (qpx * ry - qpy * rx) / denominator

    if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS:
        return a[0] + t * rx, a[1] + t * ry

    return None


def is_convex(polygon: Polygon) -> bool:
    pts = polygon.points
    n = len(pts)

    if n < 4:
        return n >= 3

    sign = 0

    for i in range(n):
        value = cross(pts[i], pts[(i + 1) % n], pts[(i + 2) % n])

        if abs(value) <= EPS:
            continue

        current = 1 if value > 0 else -1

        if sign == 0:
            sign = current
        elif sign != current:
            return False

    return True


def point_in_convex_polygon(p: Point, polygon: Polygon) -> bool:
    pts = polygon.points

    if len(pts) < 3:
        return any(point_on_segment(p, a, b) for a, b in polygon.edges())

    sign = 0

    for a, b in polygon.edges():
        if point_on_segment(p, a, b):
            return True

        value = cross(a, b, p)

        if abs(value) <= EPS:
            continue

        current = 1 if value > 0 else -1

        if sign == 0:
            sign = current
        elif sign != current:
            return False

    return True


def point_in_polygon_ray_casting(p: Point, polygon: Polygon) -> bool:
    # Метод лучей для произвольного простого полигона.
    pts = polygon.points
    n = len(pts)

    if n < 3:
        return any(point_on_segment(p, a, b) for a, b in polygon.edges())

    for a, b in polygon.edges():
        if point_on_segment(p, a, b):
            return True

    inside = False
    x, y = p

    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]

        intersects = (yi > y) != (yj > y)

        if intersects:
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside

        j = i

    return inside


def point_in_polygon(p: Point, polygon: Polygon):
    pts = polygon.points
    n = len(pts)

    # Вырожденные полигоны: 1-гон и 2-гон.
    if n == 0:
        return False, "пустой"

    if n == 1:
        same_point = (
            abs(p[0] - pts[0][0]) <= EPS
            and abs(p[1] - pts[0][1]) <= EPS
        )
        return same_point, "точка"

    if n == 2:
        return point_on_segment(p, pts[0], pts[1]), "ребро"

    if is_convex(polygon):
        return point_in_convex_polygon(p, polygon), "выпуклый"

    return point_in_polygon_ray_casting(p, polygon), "невыпуклый"
