from __future__ import annotations

from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from .contract import Row


DDL = (
    """CREATE TABLE IF NOT EXISTS runs (
        pipeline TEXT NOT NULL,
        source_sha256 TEXT NOT NULL,
        source_json TEXT NOT NULL CHECK (json_valid(source_json)),
        PRIMARY KEY (pipeline, source_sha256)
    )""",
    """CREATE TABLE IF NOT EXISTS facts (
        pipeline TEXT NOT NULL,
        source_sha256 TEXT NOT NULL,
        fact_id TEXT NOT NULL,
        fact_json TEXT NOT NULL CHECK (json_valid(fact_json)),
        PRIMARY KEY (pipeline, source_sha256, fact_id),
        FOREIGN KEY (pipeline, source_sha256) REFERENCES runs (pipeline, source_sha256)
    )""",
)


def canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)


def store(path: Path, pipeline: str, source: Row, facts: list[Row]) -> str:
    source_json = canonical_json(source)
    digest = sha256(source_json.encode("utf-8")).hexdigest()
    rows = sorted((pipeline, digest, fact["fact_id"], canonical_json(fact)) for fact in facts)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            for statement in DDL:
                conn.execute(statement)
            cursor = conn.execute(
                "INSERT INTO runs VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                (pipeline, digest, source_json),
            )
            if cursor.rowcount:
                conn.executemany("INSERT INTO facts VALUES (?, ?, ?, ?)", rows)
            elif conn.execute(
                "SELECT * FROM facts WHERE pipeline = ? AND source_sha256 = ? ORDER BY fact_id",
                (pipeline, digest),
            ).fetchall() != rows:
                raise ValueError("stored batch has different facts; use a fresh database for changed pipeline logic")
    return digest
