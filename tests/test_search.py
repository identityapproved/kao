import importlib.util
import types
import unittest
from pathlib import Path

from kao import _data
from kao.db import DB
from kao.search import search

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_data", ROOT / "tools" / "build_data.py")
build_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_data)


def make_db(rows):
    # rows: (text, "tag words", category)
    entries = [{"text": t, "tags": tags.split(), "category": c} for t, tags, c in rows]
    return DB(types.SimpleNamespace(**build_data.pack(entries)))


# the committed set, so results do not depend on data/local/
DB_ = DB(_data)


def faces(db, result):
    return [db.face(i) for i in result]


class TestSearch(unittest.TestCase):
    def test_empty_query(self):
        self.assertEqual(search("", DB_), range(DB_.count))
        self.assertEqual(search("   ", DB_), range(DB_.count))

    def test_plain_token(self):
        res = search("happy", DB_)
        self.assertTrue(len(res) > 0)
        for i in res:
            self.assertTrue(
                "happy" in DB_.tags(i) or "happy" in DB_.category(i) or "happy" in DB_.face(i)
            )

    def test_tag_filter(self):
        res = search("tag:happy", DB_)
        self.assertTrue(len(res) > 0)
        for i in res:
            self.assertIn("happy", DB_.tags(i))

    def test_cat_filter(self):
        res = search("cat:happy", DB_)
        self.assertTrue(len(res) > 0)
        for i in res:
            self.assertEqual(DB_.category(i), "happy")

    def test_and_tokens(self):
        res = search("happy smile", DB_)
        self.assertTrue(len(res) > 0)
        for i in res:
            text = DB_.tags(i) + " " + DB_.category(i)
            self.assertIn("happy", text)
            self.assertIn("smile", text)

    def test_ranking(self):
        db = make_db([("c", "xhappyx", "misc"), ("b", "happyday", "misc"), ("a", "happy", "misc")])
        self.assertEqual(faces(db, search("happy", db)), ["a", "b", "c"])

    def test_scope_prefixes(self):
        db = make_db([("t", "sad", "happy"), ("c", "happy", "sad")])
        self.assertEqual(faces(db, search("tag:happy", db)), ["c"])
        self.assertEqual(faces(db, search("cat:happy", db)), ["t"])
        self.assertEqual(sorted(faces(db, search("happy", db))), ["c", "t"])

    def test_face_text_and_line_boundaries(self):
        db = make_db([("(^_^)", "one", "misc"), ("(T_T)", "two", "misc"), ("(^o^)", "three", "misc")])
        self.assertEqual(faces(db, search("^_^", db)), ["(^_^)"])
        self.assertEqual(faces(db, search("two", db)), ["(T_T)"])
        self.assertEqual(faces(db, search("three", db)), ["(^o^)"])

    def test_category_argument(self):
        res = search("", DB_, category="happy")
        self.assertTrue(len(res) > 0)
        for i in res:
            self.assertEqual(DB_.category(i), "happy")
        self.assertEqual(search("happy", DB_, category="nope"), [])

    def test_limit(self):
        self.assertEqual(len(search("", DB_, limit=3)), 3)
        self.assertLessEqual(len(search("happy", DB_, limit=2)), 2)

    def test_no_match(self):
        self.assertEqual(search("zzzznotaword", DB_), [])


if __name__ == "__main__":
    unittest.main()
