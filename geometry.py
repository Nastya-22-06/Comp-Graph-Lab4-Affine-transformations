from dataclasses import dataclass, field
from typing import List, Tuple

Point = Tuple[float, float]


@dataclass
class Polygon:
    points: List[Point] = field(default_factory=list)
    name: str = "Полигон"

    def center(self) -> Point:
        # Для лабораторной берем среднее по вершинам.
        if not self.points:
            return 0.0, 0.0

        sx = sum(p[0] for p in self.points)
        sy = sum(p[1] for p in self.points)
        n = len(self.points)
        return sx / n, sy / n

    def edges(self):
        n = len(self.points)

        if n < 2:
            return []

        if n == 2:
            return [(self.points[0], self.points[1])]

        return [
            (self.points[i], self.points[(i + 1) % n])
            for i in range(n)
        ]
