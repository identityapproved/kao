import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "tools" / "build_data.py"

spec = importlib.util.spec_from_file_location("build_data", BUILD)
build_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_data)


class TestBuildData(unittest.TestCase):
    def test_width(self):
        self.assertEqual(build_data.display_width("(^_^)"), 5)
        self.assertEqual(build_data.display_width("(＾▽＾)"), 7)

    def test_valid_build(self):
        proc = subprocess.run(
            [sys.executable, str(BUILD)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data_py = ROOT / "kao" / "_data.py"
        self.assertTrue(data_py.exists())
        ns = {}
        exec(data_py.read_text(encoding="utf-8"), ns)
        self.assertGreater(len(ns["DATA"]), 0)
        self.assertIn("CATEGORIES", ns)

    def _bad_entry_build(self, entry):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "data.json").write_text(json.dumps([entry]), encoding="utf-8")
            out = td / "_data.py"
            proc = subprocess.run(
                [sys.executable, str(BUILD), str(td / "data.json"), str(out)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertTrue(proc.stderr.strip())

    def test_validation_rules(self):
        base = {"text": "(^_^)", "tags": ["happy"], "category": "happy", "source": ["seed"]}
        # empty text
        e = dict(base, text="")
        self._bad_entry_build(e)
        # duplicate text handled in list; test via two entries
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "data.json").write_text(json.dumps([base, dict(base)]), encoding="utf-8")
            out = td / "_data.py"
            proc = subprocess.run(
                [sys.executable, str(BUILD), str(td / "data.json"), str(out)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
        # tab/newline in text
        self._bad_entry_build(dict(base, text="a\tb"))
        self._bad_entry_build(dict(base, text="a\nb"))
        # tab/newline in tags
        self._bad_entry_build(dict(base, tags=["a\tb"]))
        self._bad_entry_build(dict(base, tags=["a\nb"]))
        # missing/empty tags
        self._bad_entry_build(dict(base, tags=[]))
        self._bad_entry_build(dict(base, tags=[""]))
        no_tags = {k: v for k, v in base.items() if k != "tags"}
        self._bad_entry_build(no_tags)
        # missing category
        no_cat = {k: v for k, v in base.items() if k != "category"}
        self._bad_entry_build(no_cat)
        self._bad_entry_build(dict(base, category=""))

    def test_validate_entry_direct(self):
        with self.assertRaises(Exception):
            build_data.validate_entry({"text": "", "tags": ["x"], "category": "happy"})
        with self.assertRaises(Exception):
            build_data.validate_entry({"text": "a", "tags": [], "category": "happy"})
        with self.assertRaises(Exception):
            build_data.validate_entry({"text": "a", "tags": ["x"], "category": ""})


if __name__ == "__main__":
    unittest.main()
