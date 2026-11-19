from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date
from math import isfinite
from typing import Any

Row = dict[str, Any]


def read_rows(data: Row, field: str = "records") -> list[Row]:
    rows = data[field]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{field} must contain JSON objects")
    return rows


def text(row: Row, field: str) -> str:
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def number(row: Row, field: str, *, minimum: float | None = None) -> float:
    value = row[field]
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return float(value)


def integer(row: Row, field: str, *, minimum: int = 0) -> int:
    value = row[field]
    if type(value) is not int or value < minimum:
        raise ValueError(f"{field} must be an integer of at least {minimum}")
    return value


def flag(row: Row, field: str) -> bool:
    value = row[field]
    if type(value) is not bool:
        raise ValueError(f"{field} must be true or false")
    return value


def index_rows(rows: list[Row], field: str) -> dict[str, Row]:
    result = {}
    for row in rows:
        key = text(row, field)
        if key in result:
            raise ValueError(f"duplicate {field}: {key}")
        result[key] = row
    return result


def apply_rows(data: Row, transform: Callable[[Row], Row]) -> list[Row]:
    return [
        {"fact_id": key, **transform(row)}
        for key, row in index_rows(read_rows(data), "id").items()
    ]


def read_array(row: Row, field: str) -> list[Any]:
    value = row[field]
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def choice(row: Row, field: str, allowed: set[str]) -> str:
    value = text(row, field)
    if value not in allowed:
        raise ValueError(f"unexpected {field}: {value!r}")
    return value


def day(row: Row, field: str) -> date:
    value = text(row, field)
    result = date.fromisoformat(value)
    if result.isoformat() != value:
        raise ValueError(f"{field} must be YYYY-MM-DD")
    return result


def span(row: Row, start: str, end: str) -> tuple[int, int]:
    a = integer(row, start)
    return a, integer(row, end, minimum=a + 1)


def merge_spans(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


Rect = tuple[float, float, float, float]


def rectangle(row: Row, field: str) -> Rect:
    corners = read_array(row, field)
    if len(corners) != 4:
        raise ValueError(f"{field} must have four rectangle coordinates")
    x0, y0, x1, y1 = (number({field: value}, field) for value in corners)
    if x0 >= x1 or y0 >= y1:
        raise ValueError(f"{field} must have positive width and height")
    return x0, y0, x1, y1


def area(rect: Rect) -> float:
    x0, y0, x1, y1 = rect
    return (x1 - x0) * (y1 - y0)


def intersection_area(a: Rect, b: Rect) -> float:
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
