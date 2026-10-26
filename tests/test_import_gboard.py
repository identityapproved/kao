import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_PATH = ROOT / "tools" / "import_gboard.py"

sys.path.insert(0, str(MOD_PATH.parent))
spec = importlib.util.spec_from_file_location("import_gboard", MOD_PATH)
import_gboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_gboard)


class TestImportGboard(unittest.TestCase):
    def test_tags(self):
        self.assertEqual(import_gboard.tags_for("cat kaomoji"), ["cat"])
        self.assertEqual(import_gboard.tags_for("Thank You"), ["thank", "you"])
        self.assertEqual(import_gboard.tags_for("kaomoji"), ["kaomoji"])

    def test_import(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in.txt"
            out = Path(td) / "local" / "gboard.json"
            src.write_text("crying\t(T_T)\nangry kaomoji\t(╬ಠ益ಠ)\ncrying\t(T_T)", encoding="utf-8")
            self.assertEqual(import_gboard.main([str(src), str(out)]), 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual([e["text"] for e in data], ["(T_T)", "(╬ಠ益ಠ)"])
            self.assertEqual(data[1], {"text": "(╬ಠ益ಠ)", "tags": ["angry"], "category": "angry", "source": ["gboard"]})

    def test_malformed(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in.txt"
            src.write_text("no tab here\n", encoding="utf-8")
            self.assertEqual(import_gboard.main([str(src), str(Path(td) / "o.json")]), 1)


if __name__ == "__main__":
    unittest.main()
