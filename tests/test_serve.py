import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "kao"


class TestServe(unittest.TestCase):
    def test_two_queries_two_json_lines(self):
        proc = subprocess.Popen(
            [str(BIN), "--serve"],
            cwd=str(ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        proc.stdin.write("happy\nsad\n")
        proc.stdin.close()
        stdout, stderr = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 0, stderr)
        lines = stdout.splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        self.assertIsInstance(first, list)
        self.assertIsInstance(second, list)
        self.assertTrue(len(first) > 0)
        self.assertTrue(len(second) > 0)


if __name__ == "__main__":
    unittest.main()
