import sys


def clamp_cursor(position, count):
    if count <= 0 or position < 0:
        return 0
    if position >= count:
        return count - 1
    return position


def move_cursor(position, delta, count):
    return clamp_cursor(position + delta, count)


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


def tag_column(entries, width):
    """Column where tags start: after the widest visible face, capped at half the screen."""
    widest = max((e[1] for e in entries), default=0)
    return min(widest, width // 2) + 2


def run(initial_query="", data=None, categories=None):
    import os

    if data is None or categories is None:
        from kao import _data

        data = _data.DATA if data is None else data
        categories = _data.CATEGORIES if categories is None else categories

    import curses

    from kao import actions
    from kao.search import search

    result = {"text": "", "action": ""}
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
        curses.use_default_colors()
        stdscr.keypad(True)

        query = initial_query or ""
        category = None
        cursor = 0
        scroll = 0
        message = ""
        cache_key = None
        results = []

        while True:
            if cache_key != (query, category):
                cache_key = (query, category)
                results = search(query, data, category=category)
            cursor = clamp_cursor(cursor, len(results))
            h, w = stdscr.getmaxyx()
            visible = max(h - 2, 1)
            scroll = adjust_scroll(cursor, scroll, visible, len(results))
            shown = results[scroll : scroll + visible]
            col = tag_column(shown, w)

            stdscr.erase()
            try:
                stdscr.addstr(0, 0, ("> " + query)[: max(0, w - 1)])
                for i, entry in enumerate(shown):
                    attr = curses.A_REVERSE if scroll + i == cursor else curses.A_NORMAL
                    stdscr.addstr(1 + i, 0, entry[0][: max(0, w - 1)], attr)
                    tcol = max(col, entry[1] + 2)
                    if tcol < w - 1:
                        stdscr.addstr(1 + i, tcol, entry[2][: w - tcol - 1], curses.A_DIM)
            except curses.error:
                pass
            status = message or "%d matches  cat:%s  ^Y copy  ^T type  Tab category  Esc quit" % (
                len(results),
                category or "all",
            )
            message = ""
            try:
                stdscr.addstr(h - 1, 0, status[: max(0, w - 1)])
            except curses.error:
                pass
            stdscr.move(0, min(len(query) + 2, w - 1))
            stdscr.refresh()

            key = stdscr.getch()
            current = results[cursor][0] if results else None

            if key == curses.KEY_RESIZE:
                continue
            if key in (27, 3):  # Esc, Ctrl-C
                return
            if key in (10, 13, curses.KEY_ENTER):
                if current:
                    result["text"] = current
                return
            if key == 20:  # Ctrl-T: type after the TUI is gone so focus can return
                if current:
                    result["text"] = current
                    result["action"] = "type"
                return
            if key == 25:  # Ctrl-Y
                if current:
                    err = actions.run(*actions.copy_cmd(current))
                    message = err or "copied " + current
            elif key in (curses.KEY_UP, 16):  # Up, Ctrl-P
                cursor = move_cursor(cursor, -1, len(results))
            elif key in (curses.KEY_DOWN, 14):  # Down, Ctrl-N
                cursor = move_cursor(cursor, 1, len(results))
            elif key == curses.KEY_PPAGE:
                cursor = move_cursor(cursor, -visible, len(results))
            elif key == curses.KEY_NPAGE:
                cursor = move_cursor(cursor, visible, len(results))
            elif key in (9, curses.KEY_BTAB):  # Tab, Shift-Tab
                category = cycle_category(category, categories, 1 if key == 9 else -1)
                cursor = scroll = 0
            elif key == 21:  # Ctrl-U
                query = ""
                cursor = scroll = 0
            elif key == 18:  # Ctrl-R
                if results:
                    cursor = int.from_bytes(os.urandom(4), "big") % len(results)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if query:
                    query = query[:-1]
                    cursor = scroll = 0
            elif 32 <= key <= 126:
                query += chr(key)
                cursor = scroll = 0

    try:
        curses.wrapper(_main)
    except KeyboardInterrupt:
        result["text"] = ""
    finally:
        if tty is not None:
            os.dup2(orig_stdout, 1)
            tty.close()

    text = result["text"]
    try:
        if not text:
            return 1
        if result["action"] == "type":
            err = actions.run(*actions.type_cmd(text))
            if err:
                print(err, file=sys.stderr)
                return 1
            return 0
        os.write(orig_stdout, (text + "\n").encode())
        return 0
    finally:
        os.close(orig_stdout)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    return run(" ".join(argv))


if __name__ == "__main__":
    raise SystemExit(main())
