import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from volleyball_match_observatory import PIPELINES, process
from volleyball_match_observatory.storage import store

ROOT = Path(__file__).resolve().parent.parent


class BaselineTests(unittest.TestCase):
    def test_all_pipeline_outputs(self):
        self.assertEqual(len(PIPELINES), 5)
        for name in PIPELINES:
            with self.subTest(pipeline=name):
                source = json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8"))
                expected = json.loads((ROOT / "tests" / "expected" / f"{name}.json").read_text(encoding="utf-8"))
                self.assertEqual(process(name, source), expected)

    def test_cli_and_sqlite_replay(self):
        name = next(iter(PIPELINES))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "facts.sqlite"
            cmd = [sys.executable, "-m", "volleyball_match_observatory", name, str(ROOT / "examples" / f"{name}.json"), "--sqlite", str(dest)]
            first = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
            second = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertEqual(first.stdout, second.stdout)
            result = json.loads(first.stdout)
            with sqlite3.connect(dest) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM runs").fetchone(), (1,))
                stored = db.execute("SELECT fact_json FROM facts ORDER BY fact_id").fetchall()
                self.assertEqual([json.loads(raw) for raw, in stored], sorted(result["facts"], key=lambda f: f["fact_id"]))

    def test_duplicate_fact_rolls_back_new_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "facts.sqlite"
            store(dest, "test", {"batch": 1}, [{"fact_id": "ok"}])
            with self.assertRaises(sqlite3.IntegrityError):
                store(dest, "test", {"batch": 2}, [{"fact_id": "dup"}, {"fact_id": "dup"}])
            with sqlite3.connect(dest) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM runs").fetchone(), (1,))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM facts").fetchone(), (1,))

    def test_reject_invalid_input_before_database_write(self):
        name = next(iter(PIPELINES))
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text('{"records": [], "records": []}', encoding="utf-8")
            dest = Path(tmp) / "facts.sqlite"
            run = subprocess.run([sys.executable, "-m", "volleyball_match_observatory", name, str(bad), "--sqlite", str(dest)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("duplicate JSON key", run.stderr)
            self.assertFalse(dest.exists())
            with self.assertRaises(ValueError):
                process(name, [])
            with self.assertRaises((ValueError, KeyError)):
                process(name, {"records": [{"id": "missing-required-fields"}]})
