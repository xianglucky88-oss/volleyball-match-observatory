from contextlib import closing
import hashlib
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


class PipelineRoundTripTests(unittest.TestCase):
    def test_every_pipeline_round_trips_in_same_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "facts.sqlite"
            for name in PIPELINES:
                with self.subTest(pipeline=name):
                    cmd = [sys.executable, "-m", "volleyball_match_observatory", name,
                           str(ROOT / "examples" / f"{name}.json"), "--sqlite", str(dest)]
                    first = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
                    second = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
                    self.assertEqual(first.stdout, second.stdout)
                    expected = json.loads((ROOT / "tests" / "expected" / f"{name}.json").read_text(encoding="utf-8"))
                    payload = json.loads(first.stdout)
                    self.assertEqual(payload["pipeline"], name)
                    self.assertEqual(payload["facts"], expected)
                    with closing(sqlite3.connect(dest)) as conn:
                        stored = conn.execute("SELECT fact_json FROM facts WHERE pipeline = ? ORDER BY fact_id", (name,)).fetchall()
                        self.assertEqual([json.loads(item[0]) for item in stored], expected)
                        runs = conn.execute("SELECT source_sha256, source_json FROM runs WHERE pipeline = ?", (name,)).fetchall()
                        self.assertEqual(len(runs), 1)
                        digest, source_json = runs[0]
                        self.assertEqual(hashlib.sha256(source_json.encode("utf-8")).hexdigest(), digest)
                        self.assertEqual(payload["source_sha256"], digest)
                        self.assertEqual(json.loads(source_json), json.loads((ROOT / "examples" / f"{name}.json").read_text(encoding="utf-8")))

    def test_empty_and_repeated_record_ids(self):
        for name in PIPELINES:
            with self.subTest(pipeline=name):
                self.assertEqual(process(name, {"records": []}), [])
                with self.assertRaisesRegex(ValueError, "duplicate id"):
                    process(name, {"records": [{"id": "dup"}, {"id": "dup"}]})

    def test_replay_rejects_changed_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "facts.sqlite"
            original = [{"fact_id": "record", "value": 1}]
            store(dest, "replay", {"batch": 1}, original)
            with self.assertRaisesRegex(ValueError, "different facts"):
                store(dest, "replay", {"batch": 1}, [{"fact_id": "record", "value": 2}])
            with closing(sqlite3.connect(dest)) as conn:
                self.assertEqual([json.loads(item[0]) for item in conn.execute("SELECT fact_json FROM facts")], original)
