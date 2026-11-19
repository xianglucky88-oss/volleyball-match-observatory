from __future__ import annotations

from .contract import Row, apply_rows, read_rows, text


def transform(row: Row) -> Row:
    """按预标注接球质量统计二传直接过网、传球和未知的基本计数。"""
    groups = {}
    for play in read_rows(row, "plays"):
        quality = text(play, "receive_quality")
        action = text(play, "action")
        if action not in {"direct", "set", "unknown"}:
            raise ValueError("unknown setter action")
        counts = groups.setdefault(quality, {"direct": 0, "set": 0, "unknown": 0})
        counts[action] += 1
    return {"by_quality": groups}


def build_facts(data: Row) -> list[Row]:
    return apply_rows(data, transform)
