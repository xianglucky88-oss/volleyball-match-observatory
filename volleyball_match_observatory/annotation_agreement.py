from __future__ import annotations

from .contract import Row, apply_rows, index_rows, integer, read_rows, text


def transform(row: Row) -> Row:
    """比对一对观察员按稳定动作编号提供的标注，区分漏标、类别和边界分歧。"""
    left = index_rows(read_rows(row, "left"), "mark")
    right = index_rows(read_rows(row, "right"), "mark")
    tolerance = integer(row, "tolerance_ms")
    issues = {}
    for key in sorted(left.keys() | right.keys()):
        a, b = left.get(key), right.get(key)
        if a is None or b is None:
            issues[key] = ["missing"]
            continue
        labels = []
        if text(a, "label") != text(b, "label"):
            labels.append("label")
        if abs(integer(a, "onset_ms") - integer(b, "onset_ms")) > tolerance:
            labels.append("onset")
        if labels:
            issues[key] = labels
    return {"issues": issues}


def build_facts(data: Row) -> list[Row]:
    return apply_rows(data, transform)
