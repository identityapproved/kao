import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "kao"


class TestCLI(unittest.TestCase):
    def test_list_count(self):
        proc = subprocess.run([str(BIN), "list"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = proc.stdout.splitlines()
        from kao.db import load

        self.assertEqual(len(lines), load().count)

    def test_random_happy(self):
        from kao.db import load
        from kao.search import search

        db = load()
        happy_faces = {db.face(i) for i in search("happy", db)}
        proc = subprocess.run([str(BIN), "--random", "happy"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(proc.stdout.strip(), happy_faces)

    def test_json_valid(self):
        proc = subprocess.run([str(BIN), "--json"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, list)
        if data:
            self.assertIn("text", data[0])
            self.assertIn("tags", data[0])
            self.assertIn("category", data[0])

    def test_unknown_flag(self):
        proc = subprocess.run([str(BIN), "--nope"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
