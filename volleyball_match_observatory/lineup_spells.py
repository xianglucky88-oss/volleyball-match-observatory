from __future__ import annotations

from .contract import Row, apply_rows, integer, read_array, read_rows, text


def transform(row: Row) -> Row:
    """将已核对换人记录应用到各次开球，输出被换球员及替补的在场事实。"""
    starters = [text({"player": p}, "player") for p in read_array(row, "starting_players")]
    active = set(starters)
    if len(active) != len(starters):
        raise ValueError("duplicate starter")
    serves = sorted({integer(s, "serve") for s in read_rows(row, "serves")})
    swaps = sorted(read_rows(row, "swaps"), key=lambda r: integer(r, "before_serve"))
    facts = []
    cursor = 0
    for serve in serves:
        while cursor < len(swaps) and swaps[cursor]["before_serve"] <= serve:
            out = text(swaps[cursor], "out")
            substitute = text(swaps[cursor], "in")
            if out not in active or substitute in active:
                raise ValueError("substitution conflicts with the active lineup")
            active.remove(out)
            active.add(substitute)
            cursor += 1
        facts.append({"serve": serve, "players": sorted(active)})
    return {"lineups": facts}


def build_facts(data: Row) -> list[Row]:
    return apply_rows(data, transform)
