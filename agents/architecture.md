# Architecture

`kao` is a kaomoji picker: a standalone curses TUI with search by tag, category and emotion, plus a Neovim plugin that reuses the same search through a long-running `kao --serve` process. Python standard library only, tuned for startup time.

## Layout

```
bin/kao                  launcher (shebang `#!/usr/bin/env -S python3 -I -S`)
kao/__init__.py          empty
kao/__main__.py          argv parsing and dispatch (no argparse)
kao/db.py                DB: views over the generated blobs (face(i), tags(i), ...); load() prefers _data_local
kao/search.py            query parsing and ranking over the inverted index; pure, no I/O
kao/tui.py               curses UI
kao/actions.py           clipboard via OSC 52 (no external programs)
kao/serve.py             line protocol for Neovim
kao/_data.py             GENERATED from data/kaomoji.json, committed
kao/_data_local.py       GENERATED from data/kaomoji.json + data/local/*.json, gitignored
data/kaomoji.json        source of truth for licensed data, edited by hand and by importers
data/local/*.json        gitignored imports whose license is not settled (gboard.json)
tools/build_data.py      filters, merges and packs the data into the modules above, validates
tools/import_<src>.py    one importer per upstream dataset
tools/bench.sh           startup timing
lua/kao/init.lua         Neovim picker (float + prompt)
tools/nvim_check.lua     headless picker check (query, j/k/gg/G, accept, close)
plugin/kao.lua           :Kao command
tests/test_*.py          unittest
```

## Data

`data/kaomoji.json` is a JSON array:

```json
[{"text": "(^_^)", "tags": ["happy", "smile"], "category": "happy", "source": ["seed"]}]
```

- `text`: the face, unique, no tab or newline.
- `tags`: lowercase English words, at least one, no tab or newline.
- `category`: one lowercase word (happy, sad, angry, love, surprise, animal, action, misc, ...).
- `source`: list of dataset ids the entry came from (for attribution).

`data/local/*.json` uses the same schema. Those files are gitignored because their license is unknown: `tools/import_gboard.py` writes `data/local/gboard.json` from the user's `~/downloads/kaomojis-gboard.txt` (`label<TAB>face`, ~55k lines; the label's words minus "kaomoji" become tags, the category comes from `import_kaomojidict.derive_category`). Commit any of it only once its license is known.

`tools/build_data.py` validates every file, then:

- Drops faces that are not pure kaomoji (`reject_reason`), for every source: any emoji (U+FE0F, U+20E3, U+1F000-U+1FAFF, or an East Asian Wide character in U+2300-U+2BFF, i.e. emoji presentation such as stars, sparkles, coffee; text symbols like hearts, notes and stars stay), 3+ kana/kanji in a row (a Japanese phrase), or 4+ Latin letters in a row (a word; z-only runs like `zzZZ` stay). It prints the count per reason.
- Writes `kao/_data.py` from `data/kaomoji.json` only, so a commit never carries local data, and `kao/_data_local.py` from that file plus every `data/local/*.json`, merged by face text (tags and sources unioned, the first category kept). Without local files a stale `_data_local.py` is deleted.

Both modules hold only `bytes`, so loading them is a near-memcpy unmarshal (38k entries: ~8 ms on this host, mostly page faults; a tuple-of-tuples module took ~96 ms):

```python
COUNT = 38279
CATEGORIES = ("action", "angry", ...)
WIDTHS = b"..."   # display width per entry, capped at 255 (precomputed, so runtime never imports unicodedata)
CATS = b"..."     # category index per entry
OFFS = b"..."     # native uint32 start of each face in FACES, plus one past the end
TOFFS = b"..."    # same for TAGS
WPOST = b"..."    # native uint32: POST[WPOST[w]:WPOST[w+1]] are the entries tagged WORDS[w]
CPOST = b"..."    # same per category
POST = b"..."     # native uint32 entry indices
WORDS = b"..."    # tag vocabulary, newline-joined
TAGS = b"..."     # per entry "w1 w2<TAB>category", newline-joined
FACES = b"..."    # faces, newline-joined UTF-8
```

uint32 arrays are in native byte order (built and read on x86_64); `kao/db.py` views them with `memoryview(...).cast("I")` (builtin, no `array` import) and decodes only the faces that are shown.

The build fails (non-zero exit, message naming the entry) on: empty text, duplicate text within one file, tab/newline in text or tags, missing or empty tags, missing category.

## Search (`kao/search.py`)

- Query is split on whitespace into tokens, lowercased.
- `tag:x` matches only tags, `cat:x` only the category, other tokens match tags, category, or the face text.
- Every token must match (AND).
- Score per token: exact tag or category = 3, tag prefix = 2, substring anywhere = 1. Entry score is the sum; sort by score descending, then original order (stable).
- Empty query returns `range(COUNT)` (data order, nothing materialized).
- `search(query, db, category=None, limit=None)` returns entry indices; `db.face(i)` etc. give the fields.
- Each token is matched against the tag vocabulary (`WORDS`, a few thousand words) and the category names, not against every entry; the matching words' postings are merged with C-level `dict.fromkeys`/`update`, lowest score first so the best score wins. Face text (score 1) is found with a `bytes.find` loop over `FACES` and is case-sensitive. Per-line Python loops over all entries are too slow here (~1.7 us per iteration on this Pentium N3540): a single letter took 380 ms that way, ~25 ms with the index.

## CLI (`kao/__main__.py`)

- `kao` - TUI
- `kao <query...>` - TUI with the query prefilled
- `kao --random [query...]` - print one random matching face; random index from `int.from_bytes(os.urandom(4))`, not the `random` module
- `kao list` - print `tags<TAB>category<TAB>face` lines
- `kao --json <query...>` - print a JSON array of `{"text", "tags", "category"}` (limit 50)
- `kao --serve` - Neovim protocol, see below
- `kao -h` / `--help`, `kao --version`
- Exit codes: 0 ok, 1 no match / cancelled, 2 usage error.

## TUI (`kao/tui.py`)

- `curses.wrapper`; `curses.set_escdelay(25)`; `curses.use_default_colors()`.
- Row 0: query prompt. Rows 1..h-2: faces only (no tags) in a grid that fills the window: `grid_layout` uses equal cells as wide as the median result width (from the precomputed widths), separated by a 3-wide gap with a dim `│` in the middle before each face that does not start a row, and packs results row by row in search order; a wider face spans as many cells as it needs, so no face is cut. `cell_spans` stretches the cells so the grid reaches both screen edges, and `face_x` centres each face in its slot (between separators or a separator and the screen edge). Last row: status (`-- MODE --  N matches  cat:<filter>`).
- Modal, vim-style. Starts in INSERT mode (query editing); the mode is shown at the left of the status line (`-- INSERT --` / `-- NORMAL --`).
- INSERT is for searching only: printable chars (hjkl included) edit the query; Backspace; Ctrl-W deletes the previous word; Ctrl-U clears the query; Enter selects the highlighted face; Esc switches to NORMAL; Ctrl-C cancels. No movement keys in INSERT.
- NORMAL keys: `h`/`j`/`k`/`l` and Left/Down/Up/Right move left/down/up/right in the grid (`h`/`l` stay within the row; `j`/`k` go to the face covering the same cell in the next row, else the last face starting left of it); `gg` top, `G` bottom; Ctrl-D/Ctrl-U half page down/up and Ctrl-F/Ctrl-B, PgDn/PgUp a full page, counted in grid rows; `i`, `a`, `/` back to INSERT (`/` also clears the query); `x` clears the query; `]c`/`[c` next/previous category filter (none -> each of `CATEGORIES`); `r` jumps to a random entry; Enter selects; `y` yanks (OSC 52) and quits; `Y` yanks and stays open with "yanked <face>" on the status line; `q`, Esc, Ctrl-C cancel (exit 1).
- A pending `g` (for `gg`) or `]`/`[` is shown on the status line and is cleared by any other key.
- Select prints the face to stdout after curses exits (exit 0). `y` copies and exits 0 without printing. Cancel exits 1.
- Search results are cached per (query, category) and the grid layout per (query, category, width); navigation keys do not re-search or re-layout.
- Output is printed after curses exits so `kao | some-command` works; the TUI draws on `/dev/tty` when stdout is not a tty.
- Window resize (`KEY_RESIZE`) redraws.

## Actions (`kao/actions.py`)

- `osc52(text)` returns the escape sequence `"\033]52;c;" + base64(utf-8 text) + "\a"` as bytes; use `binascii.b2a_base64(data, newline=False)` imported inside the function (builtin, cheap; not the `base64` module).
- `yank(text)` writes that sequence to `/dev/tty` (opened with `posix.open`, falling back to fd 2) and returns None, or a one-line error string if the tty cannot be opened.
- No `subprocess`, no external programs. Works in terminals that support OSC 52 clipboard writes (foot, kitty, alacritty, wezterm, ghostty); inside tmux (`TMUX` in `posix.environ`) `yank` sends only the copy wrapped in tmux DCS passthrough (`\ePtmux;` + sequence with ESC doubled + `\e\\`), which needs `allow-passthrough on`. Sending the plain sequence as well once left zsh stuck in a bracketed paste, and the user's tmux keeps `set-clipboard` off on purpose (it corrupts pastes in nvim and Claude Code), so do not add it back.

## Neovim (`kao --serve`, `lua/kao/`)

- `kao --serve` reads one query per line on stdin and writes one JSON line per query: `[{"text": ..., "tags": ..., "category": ...}, ...]` (limit 50), flushing after each line. EOF exits 0.
- `lua/kao/init.lua` starts `<cmd> --serve` per picker with `vim.system(cmd, {stdin = true, stdout = cb})` (`vim.system` has no `args` option; the flag goes in the command list), opens a centered prompt float and a non-focusable results float, sends the prompt line on `TextChanged(I)` (and once on open), highlights the selection. Prompt starts in insert mode: `<C-n>/<C-p>/<C-j>/<C-k>/<Down>/<Up>` move, `<CR>` accepts, `<Esc>` goes to normal mode in the prompt. Prompt normal mode: `j`/`k` move, `gg`/`G` top/bottom, `<CR>` accepts, `i`/`a` back to insert, `q`/`<Esc>`/`<C-c>` close. Accept inserts at the original cursor (after the cursor char when opened from normal mode, then back to normal mode). Leaving the prompt window also closes it and ends the serve process.
- Default `cmd` is this repo's `bin/kao`, resolved from the plugin file, so kao need not be on PATH. `setup({ cmd = {...}, width = 60, height = 12 })` overrides.
- `plugin/kao.lua` only defines `:Kao`; it must not call `setup()` (that would reset a user's config).
- Load with lazy.nvim: `{ dir = "~/github/kao" }`.

## Performance rules

- Run with `python3 -I -S` (isolated, no `site`): measured on this host ~40 ms bare vs ~62 ms default. `-I` drops the script directory from `sys.path`, so `bin/kao` inserts the repo root itself, following symlinks with `posix.readlink` (not `os.path.realpath`, see below).
- Module top level imports only `sys` (and the builtin `posix`). `os`, `curses`, `json` are imported inside the function that needs them.
- No `argparse`, `random`, `re`, `unicodedata`, `pathlib`, `typing` at runtime.
- Check with `python3 -I -S -X importtime bin/kao list > /dev/null` and `tools/bench.sh`.
- Budget on this host (Pentium N3540; bare ~44 ms): `kao --random` within 15 ms of bare `python3 -I -S -c pass` (~57 ms with 38k entries); TUI first frame within 40 ms of it; a search keystroke within ~30 ms for single letters. `kao list` prints every entry and is allowed more (~120 ms for 38k).
- The TUI packs grid rows on demand (`Grid.extend`): the rows on screen plus two pages past the cursor; `G` packs the rest (~40 ms for 38k).
