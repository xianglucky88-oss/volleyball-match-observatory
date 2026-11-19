from __future__ import annotations

from .contract import Row, apply_rows, index_rows, read_rows, text


def transform(row: Row) -> Row:
    """保留官方得分，独立判断同一回合的最后触球标注是否一致。"""
    marks = index_rows(read_rows(row, "marks"), "observer")
    teams = sorted({text(mark, "team") for mark in marks.values()})
    return {"point_team": text(row, "point_team"), "last_touch_team": teams[0] if len(teams) == 1 else None,
            "touch_status": {0: "unobserved", 1: "agreed"}.get(len(teams), "disputed")}


def build_facts(data: Row) -> list[Row]:
    return apply_rows(data, transform)
