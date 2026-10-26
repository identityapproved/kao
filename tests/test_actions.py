import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestActions(unittest.TestCase):
    def _run(self, code, env):
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env=env,
        )

    def test_missing_copy(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ)
            env["PATH"] = d
            proc = self._run("import kao.actions; kao.actions.copy('x')", env)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(len(proc.stderr.splitlines()), 1)
            self.assertIn("wl-copy", proc.stderr)

    def test_missing_type(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ)
            env["PATH"] = d
            proc = self._run("import kao.actions; kao.actions.type_text('x')", env)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(len(proc.stderr.splitlines()), 1)
            self.assertIn("wtype", proc.stderr)


if __name__ == "__main__":
    unittest.main()
