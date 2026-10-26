# kao

Kaomoji picker: a fast curses TUI with search by tag, category and emotion, plus a Neovim plugin. Python 3 standard library only.

MIT licensed; bundled data credits are in `NOTICE`.

## Install

```sh
ln -s ~/github/kao/bin/kao ~/.local/bin/kao
```

Runtime dependencies: Python 3.11 or newer and a terminal that supports OSC 52 clipboard writes. Nothing else is required.

## Usage

```sh
kao                 # open the TUI
kao cat             # open the TUI with a prefilled query
kao --random        # print one random face
kao --random happy  # print one random happy face
kao list            # print tags<TAB>category<TAB>face
kao --json happy    # print a JSON array of matches (limit 50)
kao --serve         # Neovim protocol on stdin/stdout
kao --help
kao --version
```

Exit codes: 0 ok, 1 no match or cancelled, 2 usage error.

## Keys

The TUI shows only the faces, in a grid that fills the window; wide faces take several cells instead of being cut. It starts in INSERT mode, which is for searching only, so h / j / k / l type letters there.

INSERT mode:

- printable chars edit the query
- Backspace deletes a character
- Ctrl-W deletes the previous word
- Ctrl-U clears the query
- Enter selects the highlighted face
- Esc switches to NORMAL mode
- Ctrl-C cancels

NORMAL mode:

- h / j / k / l and the arrow keys move left / down / up / right in the grid
- gg top, G bottom
- Ctrl-D / Ctrl-U half page down / up
- Ctrl-F / Ctrl-B and PgDn / PgUp full page down / up
- i, a, / back to INSERT (`/` also clears the query)
- x clears the query
- ]c / [c next / previous category filter
- r random entry
- Enter selects
- y yanks (OSC 52) and quits
- Y yanks (OSC 52) and stays open
- q, Esc, Ctrl-C cancel

A pending `g`, `]`, or `[` is shown on the status line.

Inside tmux (`$TMUX` set) kao sends the sequence only through tmux passthrough, which needs `set -g allow-passthrough on`.

## Neovim

lazy.nvim:

```lua
{ dir = "~/github/kao" }
```

Then run `:Kao`. The default command resolves to this repository's `bin/kao`; override with `require("kao").setup({ cmd = { "kao" } })`.

The prompt starts in insert mode:

- typing filters; `<C-n>` / `<C-j>` / `<Down>` and `<C-p>` / `<C-k>` / `<Up>` move the selection
- `<CR>` inserts the face at the cursor you started from
- `<Esc>` switches the prompt to normal mode: `j` / `k` move, `gg` / `G` jump, `<CR>` inserts, `i` / `a` back to insert, `q` / `<Esc>` close
- `<C-c>` closes from either mode

## Data

`data/kaomoji.json` is the source of truth. Rebuild the runtime data after editing it:

```sh
python3 tools/build_data.py
```

Larger datasets whose license is not settled stay local: they live in the gitignored `data/local/` and build into the gitignored `kao/_data_local.py`, which kao prefers when it exists. For the Gboard kaomoji list (`label<TAB>face`):

```sh
python3 tools/import_gboard.py ~/downloads/kaomojis-gboard.txt
python3 tools/build_data.py
```

The build keeps kaomoji only: it drops faces containing emoji, Japanese phrases (3+ kana/kanji in a row) or Latin words (4+ letters), and prints how many it dropped.

Run the tests:

```sh
python3 -m unittest -v
```

Startup benchmark:

```sh
tools/bench.sh
```

Neovim headless check:

```sh
nvim --headless -u NONE --cmd 'set rtp+=.' -c 'runtime plugin/kao.lua' -c 'luafile tools/nvim_check.lua'
```

## Attribution

Seed data is hand-picked. Imported faces and tags come from kaomojidict (MIT, Copyright (c) 2026 netrom, github.com/netromdk/kaomojidict); see `NOTICE`.
