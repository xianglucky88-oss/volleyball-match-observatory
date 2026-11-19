from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3

from . import PIPELINES, process
from .storage import canonical_json, store


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_json_number(value):
    raise ValueError(f"invalid JSON number: {value}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__package__.replace("_", " "))
    parser.add_argument("pipeline", choices=sorted(PIPELINES))
    parser.add_argument("input", type=Path, help="UTF-8 JSON input")
    parser.add_argument("--sqlite", type=Path, help="append the validated batch and facts to SQLite")
    args = parser.parse_args(argv)
    try:
        source = json.loads(
            args.input.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_non_json_number,
        )
        facts = process(args.pipeline, source)
        result = {"pipeline": args.pipeline, "facts": facts}
        if args.sqlite is not None:
            result["source_sha256"] = store(args.sqlite, args.pipeline, source, facts)
        print(canonical_json(result))
    except (OSError, ValueError, KeyError, TypeError, ArithmeticError, sqlite3.Error) as error:
        parser.exit(2, f"{args.pipeline}: {error}\n")


if __name__ == "__main__":
    main()
