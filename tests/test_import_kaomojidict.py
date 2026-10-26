import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_PATH = ROOT / "tools" / "import_kaomojidict.py"

spec = importlib.util.spec_from_file_location("import_kaomojidict", MOD_PATH)
import_kaomojidict = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_kaomojidict)


class TestImportKaomojidict(unittest.TestCase):
    def _upstream(self, td, faces):
        path = Path(td) / "kaomoji.json"
        path.write_text(json.dumps({"version": 1, "kaomoji": faces}), encoding="utf-8")
        return path

    def test_category_derivation(self):
        self.assertEqual(import_kaomojidict.derive_category(["angry"]), "angry")
        self.assertEqual(import_kaomojidict.derive_category(["mad"]), "angry")
        self.assertEqual(import_kaomojidict.derive_category(["sad", "tears"]), "sad")
        self.assertEqual(import_kaomojidict.derive_category(["happy", "joy"]), "happy")
        self.assertEqual(import_kaomojidict.derive_category(["love", "kiss"]), "love")
        self.assertEqual(import_kaomojidict.derive_category(["shy", "blush"]), "shy")
        self.assertEqual(import_kaomojidict.derive_category(["shock", "what"]), "surprise")
        self.assertEqual(import_kaomojidict.derive_category(["peek", "watching"]), "peek")
        self.assertEqual(import_kaomojidict.derive_category(["tired", "sleep"]), "tired")
        self.assertEqual(import_kaomojidict.derive_category(["cat"]), "animal")
        self.assertEqual(import_kaomojidict.derive_category(["nothing"]), "misc")

    def test_nonascii_star_dropped(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            up = self._upstream(td, {"( ^_^ )": {"en": ["happy"], "*": ["træt", "ok"]}})
            data_path = td / "data.json"
            data_path.write_text(json.dumps([]), encoding="utf-8")
            import_kaomojidict.import_kaomojidict(up, data_path)
            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(data[0]["tags"], ["happy", "ok"])

    def test_merge_keeps_category_and_unions_tags(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            seed = [{"text": "(^_^)", "tags": ["smile"], "category": "happy", "source": ["seed"]}]
            data_path = td / "data.json"
            data_path.write_text(json.dumps(seed), encoding="utf-8")
            up = self._upstream(td, {"(^_^)": {"en": ["happy"], "*": ["ok"]}})
            import_kaomojidict.import_kaomojidict(up, data_path)
            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["category"], "happy")
            self.assertEqual(data[0]["tags"], ["happy", "ok", "smile"])
            self.assertIn("kaomojidict", data[0]["source"])

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            seed = [{"text": "(^_^)", "tags": ["smile"], "category": "happy", "source": ["seed"]}]
            data_path = td / "data.json"
            data_path.write_text(json.dumps(seed), encoding="utf-8")
            up = self._upstream(td, {"(^_^)": {"en": ["happy"]}, "(T_T)": {"en": ["sad"]}})
            proc1 = subprocess.run(
                [sys.executable, "-I", str(MOD_PATH), str(up), str(data_path)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc1.returncode, 0, proc1.stderr)
            first = data_path.read_bytes()
            proc2 = subprocess.run(
                [sys.executable, "-I", str(MOD_PATH), str(up), str(data_path)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc2.returncode, 0, proc2.stderr)
            second = data_path.read_bytes()
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
