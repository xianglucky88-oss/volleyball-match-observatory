from __future__ import annotations

from .contract import Row, apply_rows, number, read_rows, text


def transform(row: Row) -> Row:
    """用归一化单侧球场横坐标汇总一名接球队员的来球分区，单列未知落点。"""
    counts = [0, 0, 0]
    unknown = 0
    for ball in read_rows(row, "receptions"):
        if ball["x"] is None:
            unknown += 1
            continue
        x = number(ball, "x", minimum=0)
        if x > 9:
            raise ValueError("x is outside the 9 m court")
        counts[min(int(x // 3), 2)] += 1
    return {"player": text(row, "player"), "zone_counts": counts, "unknown": unknown}


def build_facts(data: Row) -> list[Row]:
    return apply_rows(data, transform)
