import unittest

from kao.tui import cell_spans, face_x, grid_layout, grid_move, handle_key


def state(**kw):
    base = {
        "mode": "insert",
        "query": "",
        "cursor": 0,
        "category": None,
        "pending": "",
        "count": 10,
        "categories": ("a", "b"),
    }
    base.update(kw)
    return base


class TestTUIHelpers(unittest.TestCase):
    def test_typing_insert(self):
        s = state()
        s, out = handle_key(s, ord("a"), 5)
        self.assertEqual(s["query"], "a")
        self.assertEqual(out, None)

    def test_esc_enters_normal(self):
        s = state()
        s, out = handle_key(s, 27, 5)
        self.assertEqual(s["mode"], "normal")

    def test_j_k_clamp(self):
        s = state(mode="normal", cursor=0)
        s, _ = handle_key(s, ord("j"), 5)
        self.assertEqual(s["cursor"], 1)
        s, _ = handle_key(s, ord("k"), 5)
        self.assertEqual(s["cursor"], 0)
        s, _ = handle_key(s, ord("k"), 5)
        self.assertEqual(s["cursor"], 0)

    def test_gg_and_G(self):
        s = state(mode="normal", cursor=5)
        s, _ = handle_key(s, ord("g"), 5)
        self.assertEqual(s["pending"], "g")
        s, _ = handle_key(s, ord("g"), 5)
        self.assertEqual(s["cursor"], 0)
        self.assertEqual(s["pending"], "")
        s, _ = handle_key(s, ord("G"), 5)
        self.assertEqual(s["cursor"], 9)

    def test_g_then_x_clears_pending(self):
        s = state(mode="normal", cursor=5)
        s, _ = handle_key(s, ord("g"), 5)
        self.assertEqual(s["pending"], "g")
        s, _ = handle_key(s, ord("x"), 5)
        self.assertEqual(s["pending"], "")
        self.assertEqual(s["query"], "")

    def test_ctrl_d_half_page(self):
        s = state(mode="normal", cursor=0)
        s, _ = handle_key(s, 4, 10)
        self.assertEqual(s["cursor"], 5)

    def test_bracket_c_cycle(self):
        s = state(mode="normal", category=None)
        s, _ = handle_key(s, ord("]"), 5)
        self.assertEqual(s["pending"], "]")
        s, _ = handle_key(s, ord("c"), 5)
        self.assertEqual(s["category"], "a")
        s, _ = handle_key(s, ord("["), 5)
        self.assertEqual(s["pending"], "[")
        s, _ = handle_key(s, ord("c"), 5)
        self.assertEqual(s["category"], None)

    def test_slash_clears_and_insert(self):
        s = state(mode="normal", query="abc")
        s, _ = handle_key(s, ord("/"), 5)
        self.assertEqual(s["query"], "")
        self.assertEqual(s["mode"], "insert")

    def test_y_returns_yank(self):
        s = state(mode="normal")
        s, out = handle_key(s, ord("y"), 5)
        self.assertEqual(out, "yank")

    def test_q_returns_cancel(self):
        s = state(mode="normal")
        s, out = handle_key(s, ord("q"), 5)
        self.assertEqual(out, "cancel")

    def test_ctrl_w_deletes_word(self):
        s = state(mode="insert", query="hello world")
        s, _ = handle_key(s, 23, 5)
        self.assertEqual(s["query"], "hello ")

    def test_insert_hjkl_type_and_enter_selects(self):
        s = state()
        for ch in "hjkl":
            s, out = handle_key(s, ord(ch), 5)
        self.assertEqual((s["query"], s["cursor"], out), ("hjkl", 0, None))
        s, out = handle_key(s, 13, 5)
        self.assertEqual(out, "select")

    def test_insert_ignores_movement_keys(self):
        s = state(cursor=3)
        for key in (10, 14, 16, 11):
            s, out = handle_key(s, key, 5)
        self.assertEqual((s["cursor"], s["query"], out), (3, "", None))

    def test_grid_hjkl(self):
        # 10 one-cell items, 4 per row: rows 0-3, 4-7, 8-9
        pos = [(i // 4, i % 4, 1) for i in range(10)]
        s = state(mode="normal", cursor=5, pos=pos)
        s, _ = handle_key(s, ord("l"), 5)
        self.assertEqual(s["cursor"], 6)
        s, _ = handle_key(s, ord("k"), 5)
        self.assertEqual(s["cursor"], 2)
        s, _ = handle_key(s, ord("h"), 5)
        self.assertEqual(s["cursor"], 1)
        s, _ = handle_key(s, ord("j"), 5)
        self.assertEqual(s["cursor"], 5)
        s, out = handle_key(s, ord("l"), 5)
        self.assertEqual(out, None)

    def test_grid_edges(self):
        pos = [(i // 4, i % 4, 1) for i in range(10)]
        self.assertEqual(grid_move(4, "h", pos), 4)
        self.assertEqual(grid_move(3, "l", pos), 3)
        self.assertEqual(grid_move(9, "l", pos), 9)
        self.assertEqual(grid_move(1, "k", pos), 1)
        self.assertEqual(grid_move(9, "j", pos), 9)
        # below is past the end of the short last row: its last face
        self.assertEqual(grid_move(7, "j", pos), 9)

    def test_grid_spanning_vertical(self):
        # row 0: a (cell 0), b spans cells 1-2, c (cell 3); row 1: d spans 0-1, e (cell 2)
        pos = [(0, 0, 1), (0, 1, 2), (0, 3, 1), (1, 0, 2), (1, 2, 1)]
        self.assertEqual(grid_move(2, "j", pos), 4)
        self.assertEqual(grid_move(1, "j", pos), 3)
        self.assertEqual(grid_move(4, "k", pos), 1)
        self.assertEqual(grid_move(3, "k", pos), 0)

    def test_grid_page_moves_rows(self):
        pos = [(i // 4, i % 4, 1) for i in range(100)]
        s = state(mode="normal", cursor=1, count=100, pos=pos)
        s, _ = handle_key(s, 4, 10)
        self.assertEqual(s["cursor"], 21)
        s, _ = handle_key(s, 6, 10)
        self.assertEqual(s["cursor"], 61)
        s, _ = handle_key(s, 2, 10)
        self.assertEqual(s["cursor"], 21)

    def test_grid_layout_fits(self):
        self.assertEqual(grid_layout([], 80), (1, []))
        # median 5 -> cells of 5 plus gap 3 -> 3 per 21 columns; 12 spans 2 cells
        cell, pos = grid_layout([5, 12, 5, 3, 5], 21)
        self.assertEqual(cell, 5)
        self.assertEqual(pos, [(0, 0, 1), (0, 1, 2), (1, 0, 1), (1, 1, 1), (1, 2, 1)])
        for w, (_, c, span) in zip([5, 12, 5, 3, 5], pos):
            self.assertLessEqual(c + span, 3)
            self.assertGreaterEqual(span * cell + (span - 1) * 3, w)
        # wider than the screen: one per row, never more cells than exist
        cell, pos = grid_layout([30, 30], 20)
        self.assertEqual(pos, [(0, 0, 1), (1, 0, 1)])

    def test_cell_spans_reach_both_edges(self):
        # 4 cells in 40 columns: 31 free over 4 cells -> 8, 8, 8, 7
        cells = cell_spans(40, 4)
        self.assertEqual(cells, [(0, 8), (11, 8), (22, 8), (33, 7)])
        self.assertEqual(cells[-1][0] + cells[-1][1], 40)

    def test_face_x_centres(self):
        cells = [(0, 8), (11, 8), (22, 8), (33, 7)]
        self.assertEqual(face_x(cells, 0, 1, 4), 2)
        self.assertEqual(face_x(cells, 1, 1, 5), 12)
        # spanning cells 1-2 (x 11..30) with a 10-wide face
        self.assertEqual(face_x(cells, 1, 2, 10), 15)
        # wider than its slot: never left of the slot
        self.assertEqual(face_x(cells, 3, 1, 12), 33)


if __name__ == "__main__":
    unittest.main()
