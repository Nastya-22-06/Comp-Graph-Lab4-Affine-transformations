import math
from typing import List

from geometry import Point


Matrix = List[List[float]]


def multiply_matrix(a: Matrix, b: Matrix) -> Matrix:
    rows = len(a)
    cols = len(b[0])
    middle = len(b)

    result = [[0.0 for _ in range(cols)] for _ in range(rows)]

    for i in range(rows):
        for j in range(cols):
            for k in range(middle):
                result[i][j] += a[i][k] * b[k][j]

    return result


def apply_matrix(point: Point, matrix: Matrix) -> Point:
    # Однородные координаты: [x, y, 1]^T.
    vector = [[point[0]], [point[1]], [1.0]]
    result = multiply_matrix(matrix, vector)

    w = result[2][0]
    if abs(w) < 1e-12:
        return result[0][0], result[1][0]

    return result[0][0] / w, result[1][0] / w


def translation(dx: float, dy: float) -> Matrix:
    return [
        [1.0, 0.0, dx],
        [0.0, 1.0, dy],
        [0.0, 0.0, 1.0],
    ]


def rotation(angle_deg: float) -> Matrix:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)

    return [
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ]


def scaling(sx: float, sy: float) -> Matrix:
    return [
        [sx, 0.0, 0.0],
        [0.0, sy, 0.0],
        [0.0, 0.0, 1.0],
    ]


def around_point(base: Matrix, cx: float, cy: float) -> Matrix:
    # T(cx, cy) * M * T(-cx, -cy)
    return multiply_matrix(
        translation(cx, cy),
        multiply_matrix(base, translation(-cx, -cy))
    )
