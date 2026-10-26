import unittest

from kao.tui import (
    adjust_scroll,
    clamp_cursor,
    cycle_category,
    move_cursor,
)


class TestTUIHelpers(unittest.TestCase):
    def test_clamp_cursor(self):
        self.assertEqual(clamp_cursor(0, 5), 0)
        self.assertEqual(clamp_cursor(10, 5), 4)
        self.assertEqual(clamp_cursor(-1, 5), 0)
        self.assertEqual(clamp_cursor(2, 0), 0)

    def test_move_cursor(self):
        self.assertEqual(move_cursor(0, 1, 5), 1)
        self.assertEqual(move_cursor(4, 1, 5), 4)
        self.assertEqual(move_cursor(0, -1, 5), 0)

    def test_adjust_scroll(self):
        self.assertEqual(adjust_scroll(0, 0, 3, 10), 0)
        self.assertEqual(adjust_scroll(4, 0, 3, 10), 2)
        self.assertEqual(adjust_scroll(1, 2, 3, 10), 1)

    def test_cycle_category(self):
        cats = ("a", "b")
        self.assertEqual(cycle_category(None, cats), "a")
        self.assertEqual(cycle_category("a", cats), "b")
        self.assertIsNone(cycle_category("b", cats))


if __name__ == "__main__":
    unittest.main()
