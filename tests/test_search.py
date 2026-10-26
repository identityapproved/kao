import unittest

from kao import _data
from kao.search import search

DATA = _data.DATA


class TestSearch(unittest.TestCase):
    def test_empty_query(self):
        self.assertEqual(search("", DATA), list(DATA))
        self.assertEqual(search("   ", DATA), list(DATA))

    def test_plain_token(self):
        res = search("happy", DATA)
        self.assertTrue(len(res) > 0)
        for entry in res:
            self.assertTrue(
                "happy" in entry[2].split() or entry[3] == "happy" or "happy" in entry[0].lower()
            )

    def test_tag_filter(self):
        res = search("tag:happy", DATA)
        self.assertTrue(len(res) > 0)
        for entry in res:
            self.assertIn("happy", entry[2].split())

    def test_cat_filter(self):
        res = search("cat:happy", DATA)
        self.assertTrue(len(res) > 0)
        for entry in res:
            self.assertEqual(entry[3], "happy")

    def test_and_tokens(self):
        res = search("happy smile", DATA)
        for entry in res:
            text = (entry[2] + " " + entry[3] + " " + entry[0]).lower()
            self.assertIn("happy", text)
            self.assertIn("smile", text)

    def test_ranking(self):
        # exact tag should outrank prefix/substring if present
        data = (
            ("exact", 5, "zzz", "misc"),
            ("prefix", 5, "happyx", "misc"),
            ("sub", 5, "xhappyx", "misc"),
        )
        # make a tag exactly happy
        data2 = (
            ("a", 1, "happy", "misc"),
            ("b", 1, "happyday", "misc"),
            ("c", 1, "xhappyx", "misc"),
        )
        res = search("happy", data2)
        self.assertEqual([e[0] for e in res], ["a", "b", "c"])

    def test_category_argument(self):
        res = search("", DATA, category="happy")
        self.assertTrue(len(res) > 0)
        for entry in res:
            self.assertEqual(entry[3], "happy")
        res2 = search("happy", DATA, category="sad")
        self.assertEqual(res2, [])

    def test_limit(self):
        res = search("", DATA, limit=3)
        self.assertEqual(len(res), 3)

    def test_no_match(self):
        self.assertEqual(search("zzzznotaword", DATA), [])


if __name__ == "__main__":
    unittest.main()
