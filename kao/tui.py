import sys

KEY_UP = 259
KEY_DOWN = 258
KEY_LEFT = 260
KEY_RIGHT = 261
KEY_BACKSPACE = 263
KEY_NPAGE = 338
KEY_PPAGE = 339
KEY_ENTER = 343
KEY_RESIZE = 410


def clamp_cursor(position, count):
    if count <= 0 or position < 0:
        return 0
    if position >= count:
        return count - 1
    return position


def adjust_scroll(cursor, scroll, page_size, total=None):
    if page_size <= 0:
        return 0
    if cursor < scroll:
        scroll = cursor
    elif cursor >= scroll + page_size:
        scroll = cursor - page_size + 1
    if total is not None and total > page_size:
        scroll = min(scroll, total - page_size)
    return max(scroll, 0)


def cycle_category(current, categories, step=1):
    choices = [None] + list(categories)
    try:
        idx = choices.index(current)
    except ValueError:
        idx = -1
    return choices[(idx + step) % len(choices)]


class Grid:
    # equal cells (median face width) packed row by row; a wider face spans several cells, none is cut.
    # Rows are packed on demand: pos[i] = (row, first cell, span), starts[r] = first index of row r.
    def __init__(self, widths, width, gap=3):
        self.widths = widths
        self.n = len(widths)
        sample = sorted(widths[i] for i in range(min(self.n, 2000)))
        self.cell = max(sample[len(sample) // 2], 1) if sample else 1
        self.ncells = max(1, (width + gap) // (self.cell + gap))
        self.gap = gap
        self.pos = []
        self.starts = []
        self.row = -1
        self.used = self.ncells

    def done(self):
        return len(self.pos) == self.n

    def extend(self, index=-1, row=-1):
        # pack until entry `index` is placed and row `row` is complete
        pos, widths, ncells, step = self.pos, self.widths, self.ncells, self.cell + self.gap
        i = len(pos)
        while i < self.n and (i <= index or self.row <= row):
            span = min(ncells, -(-(widths[i] + self.gap) // step))
            if self.used + span > ncells:
                self.row += 1
                self.used = 0
                self.starts.append(i)
            pos.append((self.row, self.used, span))
            self.used += span
            i += 1


def grid_layout(widths, width, gap=3):
    grid = Grid(widths, width, gap)
    grid.extend(index=grid.n - 1)
    return grid.cell, grid.pos


def cell_spans(width, ncells, gap=3):
    # (x, width) per cell, stretched so the grid reaches both screen edges
    free = max(width - gap * (ncells - 1), ncells)
    base, extra = divmod(free, ncells)
    cells = []
    x = 0
    for i in range(ncells):
        cw = base + (i < extra)
        cells.append((x, cw))
        x += cw + gap
    return cells


def face_x(cells, first, span, face_width):
    # left edge that centres a face over cells first..first+span-1
    left = cells[first][0]
    last = cells[first + span - 1]
    return left + max((last[0] + last[1] - left - face_width) // 2, 0)


def grid_move(cursor, direction, pos, rows=1):
    # pos[i] = (row, first cell, span)
    count = len(pos)
    if count == 0:
        return 0
    row, cell, _ = pos[cursor]
    if direction == "h":
        return cursor - 1 if cursor > 0 and pos[cursor - 1][0] == row else cursor
    if direction == "l":
        return cursor + 1 if cursor + 1 < count and pos[cursor + 1][0] == row else cursor
    target = row + rows if direction == "j" else row - rows
    target = max(0, min(target, pos[-1][0]))
    if target == row:
        return cursor
    # the face covering this cell in the target row, else the last one starting left of it
    best = None
    for i, (r, c, _) in enumerate(pos):
        if r == target and (best is None or c <= cell):
            best = i
        elif r > target:
            break
    return best


def _delete_word(query):
    if not query:
        return query
    i = len(query)
    while i > 0 and query[i - 1].isspace():
        i -= 1
    while i > 0 and not query[i - 1].isspace():
        i -= 1
    return query[:i]


def handle_key(state, key, page):
    outcome = None
    mode = state.get("mode", "insert")
    if mode not in ("insert", "normal"):
        mode = "insert"
    query = state.get("query", "")
    cursor = state.get("cursor", 0)
    category = state.get("category", None)
    pending = state.get("pending", "")
    count = state["count"]
    categories = state["categories"]
    pos = state.get("pos") or [(i, 0, 1) for i in range(count)]
    page = max(page, 1)
    half = max(page // 2, 1)

    import os

    # INSERT mode
    if mode == "insert":
        if key == KEY_RESIZE:
            state.update(mode=mode, query=query, cursor=cursor, category=category, pending=pending)
            return state, None
        if key in (27,):
            mode = "normal"
            pending = ""
        elif key == 3:
            outcome = "cancel"
        elif key in (13, KEY_ENTER):
            outcome = "select"
        elif key == 21:  # Ctrl-U
            query = ""
            cursor = 0
            pending = ""
        elif key == 23:  # Ctrl-W
            query = _delete_word(query)
            cursor = 0
            pending = ""
        elif key in (KEY_BACKSPACE, 127, 8):
            if query:
                query = query[:-1]
            cursor = 0
            pending = ""
        elif isinstance(key, int) and 32 <= key <= 126:
            query += chr(key)
            cursor = 0
            pending = ""
        else:
            pending = ""
        state.update(mode=mode, query=query, cursor=cursor, category=category, pending=pending)
        return state, outcome

    # NORMAL mode pending prefix handling
    if pending == "g":
        if key == ord("g"):
            cursor = 0
            pending = ""
            state.update(mode=mode, query=query, cursor=cursor, category=category, pending=pending)
            return state, None
        pending = ""
    elif pending in ("]", "["):
        if key == ord("c"):
            if pending == "]":
                category = cycle_category(category, categories, 1)
            else:
                category = cycle_category(category, categories, -1)
            cursor = 0
            pending = ""
            state.update(mode=mode, query=query, cursor=cursor, category=category, pending=pending)
            return state, None
        pending = ""

    # NORMAL mode keys
    if key == KEY_RESIZE:
        pass
    elif key == ord("g"):
        pending = "g"
    elif key == ord("]"):
        pending = "]"
    elif key == ord("["):
        pending = "["
    elif key in (ord("h"), KEY_LEFT):
        cursor = grid_move(cursor, "h", pos)
    elif key in (ord("j"), KEY_DOWN, 10):  # 10 is Ctrl-J
        cursor = grid_move(cursor, "j", pos)
    elif key in (ord("k"), KEY_UP):
        cursor = grid_move(cursor, "k", pos)
    elif key in (ord("l"), KEY_RIGHT):
        cursor = grid_move(cursor, "l", pos)
    elif key == ord("G"):
        cursor = count - 1 if count > 0 else 0
    elif key == 4:  # Ctrl-D
        cursor = grid_move(cursor, "j", pos, half)
    elif key == 21:  # Ctrl-U
        cursor = grid_move(cursor, "k", pos, half)
    elif key in (6, KEY_NPAGE):  # Ctrl-F
        cursor = grid_move(cursor, "j", pos, page)
    elif key in (2, KEY_PPAGE):  # Ctrl-B
        cursor = grid_move(cursor, "k", pos, page)
    elif key in (ord("i"), ord("a")):
        mode = "insert"
        pending = ""
    elif key == ord("/"):
        query = ""
        cursor = 0
        mode = "insert"
        pending = ""
    elif key == ord("x"):
        query = ""
        cursor = 0
        pending = ""
    elif key == ord("r"):
        if count > 0:
            cursor = int.from_bytes(os.urandom(4), "big") % count
    elif key in (13, KEY_ENTER):
        outcome = "select"
    elif key == ord("y"):
        outcome = "yank"
    elif key == ord("Y"):
        outcome = "yank-stay"
    elif key in (ord("q"), 27, 3):
        outcome = "cancel"

    state.update(mode=mode, query=query, cursor=cursor, category=category, pending=pending)
    return state, outcome


def run(initial_query="", db=None):
    import os

    if db is None:
        from kao.db import load

        db = load()
    categories = db.categories

    import curses

    from kao import actions
    from kao.search import search

    result = {"text": "", "yanked": False}
    cancelled = {"value": False}
    orig_stdout = os.dup(1)
    tty = None
    if not sys.stdout.isatty():
        try:
            tty = open("/dev/tty", "r+")
            os.dup2(tty.fileno(), 1)
        except OSError:
            tty = None

    def _main(stdscr):
        curses.set_escdelay(25)
        curses.nonl()
        curses.use_default_colors()
        stdscr.keypad(True)

        query = initial_query or ""
        category = None
        cursor = 0
        scroll = 0
        mode = "insert"
        pending = ""
        message = ""
        cache_key = None
        results = []
        layout_key = None
        grid = None
        cells = [(0, 1)]
        yanked_stay_message = ""

        while True:
            if cache_key != (query, category):
                cache_key = (query, category)
                results = search(query, db, category=category)
            cursor = clamp_cursor(cursor, len(results))
            h, w = stdscr.getmaxyx()
            visible = max(h - 2, 1)
            if layout_key != (cache_key, w):
                layout_key = (cache_key, w)
                # a range (empty query) indexes the width bytes directly
                widths = db.widths if isinstance(results, range) else [db.widths[i] for i in results]
                grid = Grid(widths, w)
                cells = cell_spans(w, grid.ncells)
            grid.extend(index=cursor)
            pos = grid.pos
            # rows past the cursor so page keys and the scrolled view have their targets packed
            grid.extend(row=(pos[cursor][0] if pos else 0) + 2 * visible + 1)
            nrows = grid.row + 1 if grid.done() else None
            scroll = adjust_scroll(pos[cursor][0] if pos else 0, scroll, visible, nrows)

            stdscr.erase()
            try:
                stdscr.addstr(0, 0, ("> " + query)[: max(0, w - 1)])
            except curses.error:
                pass
            for r in range(scroll, min(scroll + visible, len(grid.starts))):
                i = grid.starts[r]
                while i < len(pos) and pos[i][0] == r:
                    _, c, span = pos[i]
                    attr = curses.A_REVERSE if i == cursor else curses.A_NORMAL
                    k = results[i]
                    try:
                        if c:
                            # separator in the middle of the 3-wide gap: faces have inner spaces, so blanks alone run together
                            stdscr.addstr(1 + r - scroll, cells[c][0] - 2, "\u2502", curses.A_DIM)
                        stdscr.addstr(1 + r - scroll, face_x(cells, c, span, db.widths[k]), db.face(k)[: max(0, w - 1)], attr)
                    except curses.error:
                        pass
                    i += 1

            mode_label = "-- INSERT --" if mode == "insert" else "-- NORMAL --"
            if pending:
                mode_label = mode_label + " " + pending
            status = yanked_stay_message or message or (
                "%s  %d matches  cat:%s" % (mode_label, len(results), category or "all")
            )
            yanked_stay_message = ""
            message = ""
            try:
                stdscr.addstr(h - 1, 0, status[: max(0, w - 1)])
            except curses.error:
                pass
            stdscr.move(0, min(len(query) + 2, w - 1))
            stdscr.refresh()

            key = stdscr.getch()
            current = db.face(results[cursor]) if results else None

            state = {
                "mode": mode,
                "query": query,
                "cursor": cursor,
                "category": category,
                "pending": pending,
                "count": len(results),
                "categories": categories,
                "pos": grid.pos,
            }
            state, outcome = handle_key(state, key, visible)
            mode = state["mode"]
            query = state["query"]
            cursor = state["cursor"]
            category = state["category"]
            pending = state["pending"]

            if outcome == "select":
                if current:
                    result["text"] = current
                return
            if outcome == "yank":
                if current:
                    err = actions.yank(current)
                    if err:
                        message = err
                    else:
                        result["yanked"] = True
                        result["text"] = ""
                        return
                continue
            if outcome == "yank-stay":
                if current:
                    err = actions.yank(current)
                    yanked_stay_message = err or ("yanked " + current)
                continue
            if outcome == "cancel":
                cancelled["value"] = True
                return

    try:
        curses.wrapper(_main)
    except KeyboardInterrupt:
        cancelled["value"] = True
    finally:
        if tty is not None:
            try:
                os.dup2(orig_stdout, 1)
                tty.close()
            except OSError:
                pass

    if cancelled["value"]:
        return 1
    if result.get("yanked"):
        return 0
    text = result["text"]
    if not text:
        return 1
    try:
        os.write(orig_stdout, (text + "\n").encode())
    except OSError:
        print(text)
    finally:
        try:
            os.close(orig_stdout)
        except OSError:
            pass
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    return run(" ".join(argv))
