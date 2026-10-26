# Active

Work the first unchecked task only. One task per session. Read `agents/architecture.md` before starting. When the task's checks pass, tick it, add a line to `agents/tasks/done.md` and `agents/memory/history.md`, and update `agents/memory/progress.md`. Do not commit unless the user asks.

- [x] T1 seed data and build step
  - Add `.gitignore` with `__pycache__/`.
  - Write `data/kaomoji.json` with about 30 hand-picked entries over at least 6 categories, schema as in architecture.md, `"source": ["seed"]`.
  - Write `tools/build_data.py` (stdlib; may use json and unicodedata) that validates and writes `kao/_data.py`; create empty `kao/__init__.py`.
  - Write `tests/test_build_data.py`: valid input builds; each validation rule rejects a bad entry; width of `(^_^)` is 5 and of a face with a wide char (for example `(＾▽＾)`) is counted as 2 per wide char.
  - Check: `python3 tools/build_data.py && python3 -m unittest -v` passes.

- [x] T1b import kaomojidict
  - Source (MIT, checked 2026-10-26): `~/.cache/kao-src/kaomojidict/kaomoji.json`, commit c4f408c. Read it, never copy the clone into the repo.
  - Shape: `{"version": 10, "kaomoji": {"<face>": {"en": [...], "da": [...], "*": [...]}}}`. 111 faces, all have `en` tags (438 distinct, already lowercase, no spaces). `*` is locale-neutral but sometimes Danish (`træt`); `da` is ignored.
  - Write `tools/import_kaomojidict.py <path-to-kaomoji.json>` (stdlib, run with `python3 -I`): tags = `en` plus ASCII-only `*` tags, deduped, sorted. There is no category upstream: derive it from the tags with a keyword table in the script (for example angry/mad/rage -> angry, sad/cry/tears -> sad, happy/joy/yay/woohoo -> happy, love/kiss/hug/heart -> love, shy/embarrassed/blush -> shy, surprised/shock/yikes/what -> surprise, peek/lurking/watching -> peek, tired/sleep -> tired, cat/dog/bear -> animal; first match in table order wins, else `misc`). Merge into `data/kaomoji.json` by `text`: union of tags, keep existing category, append `"kaomojidict"` to `source`.
  - Add `NOTICE` crediting kaomojidict (MIT, Copyright (c) 2026 netrom, github.com/netromdk/kaomojidict) with the full MIT text.
  - Write `tests/test_import_kaomojidict.py` with a small inline fixture: `*` non-ASCII tag dropped, category derivation, merge with an existing seed entry keeps its category and unions tags, rerunning the import is idempotent.
  - Check: `python3 -I tools/import_kaomojidict.py ~/.cache/kao-src/kaomojidict/kaomoji.json && python3 tools/build_data.py && python3 -m unittest -v`; `data/kaomoji.json` has at least 111 entries; report how many landed in `misc` (aim under 30%, extend the keyword table if higher).

- [x] T2 search
  - Write `kao/search.py` per architecture.md (only `os`/`sys` allowed at top; prefer none).
  - Write `tests/test_search.py`: empty query, plain token, `tag:`, `cat:`, AND of two tokens, ranking (exact > prefix > substring), category filter argument, limit, no match.
  - Check: `python3 -m unittest -v` passes.

- [x] T3 CLI and launcher
  - Write `bin/kao` (executable, shebang `#!/usr/bin/env -S python3 -I -S`, inserts repo root into `sys.path`, calls `kao.__main__.main()`) and `kao/__main__.py` with `list`, `--random`, `--json`, `--help`, `--version`; plain `kao` prints "tui not implemented" and exits 2 until T4.
  - Write `tests/test_cli.py` running `bin/kao` via subprocess: list line count equals entry count, `--random happy` prints one face from the happy matches, `--json` is valid JSON, unknown flag exits 2.
  - Check: unittest passes; `python3 -I -S -X importtime bin/kao list 2>&1 >/dev/null | grep -E 'curses|json|subprocess|random|argparse'` prints nothing.

- [x] T4 TUI
  - Write `kao/tui.py` per architecture.md, wire `kao` and `kao <query>` to it.
  - Keep logic that does not need curses (cursor/scroll math, category cycling) in plain functions and unit test them in `tests/test_tui.py`.
  - Check: unittest passes; the user runs `bin/kao` and `bin/kao cat` and confirms typing, navigation, Tab, Enter, Esc, resize.

- [x] T5 actions
  - Write `kao/actions.py`; wire Ctrl-Y and Ctrl-T in the TUI.
  - Test missing-binary handling by running with `PATH` set to an empty dir (expect exit 1 and a one-line message).
  - Check: unittest passes. Superseded by T9 (helpers removed).

- [x] T6 startup benchmark
  - Write `tools/bench.sh` (POSIX sh): 50 runs each of `python3 -I -S -c pass`, `bin/kao list >/dev/null`, `bin/kao --random >/dev/null`; print average ms per command. Use `hyperfine` if present, else a loop with `date +%s%N`.
  - Record results in `agents/memory/progress.md`.
  - Check: within the budget in architecture.md; if not, report the top entries of `-X importtime` and stop.

- [x] T7 serve mode and Neovim plugin
  - Write `kao/serve.py`, wire `--serve`; test it in `tests/test_serve.py` by writing two queries and reading two JSON lines.
  - Write `lua/kao/init.lua` and `plugin/kao.lua` per architecture.md.
  - Check: unittest passes; `nvim --headless -u NONE --cmd 'set rtp+=.' -c 'lua require("kao")' -c q` exits 0; the user tries `:Kao` interactively.

- [ ] T9 dependency-free clipboard (no wl-copy, no wtype)
  - Rewrite `kao/actions.py` per the Actions section of architecture.md: `osc52(text)` and `yank(text)` only. Delete `run`, `copy_cmd`, `type_cmd`, `copy`, `type_text` and every `subprocess` use.
  - In `kao/tui.py` remove the Ctrl-T (wtype) path and `result["action"] == "type"`; Ctrl-Y goes away too (T10 adds `y`/`Y`).
  - Replace `tests/test_actions.py`: `osc52("(^_^)")` equals `b"\x1b]52;c;KF5fXik=\x07"`; a non-ASCII face round-trips through base64 decode; `import kao.actions` does not import `subprocess` (check `sys.modules` in a fresh `python3 -I -S` subprocess).
  - Check: unittest passes; `grep -rn -E 'subprocess|wl-copy|wtype' kao/` prints nothing; the importtime check from T3 is still clean.

- [ ] T10 vim-style modal keys in the TUI
  - Implement the TUI key section of architecture.md (INSERT/NORMAL modes, `gg`/`G`, Ctrl-D/U/F/B, `]c`/`[c`, `y`/`Y`, `q`).
  - Put key handling in a pure function, e.g. `handle_key(state, key, page) -> (state, outcome)`, where `state` holds mode, query, cursor, category, pending prefix, and `outcome` is None, "select", "yank", "yank-stay" or "cancel". Curses code only draws and calls it. Use curses key constants passed in as ints so tests do not import curses (`KEY_UP` 259, `KEY_DOWN` 258, `KEY_BACKSPACE` 263, `KEY_NPAGE` 338, `KEY_PPAGE` 339, `KEY_ENTER` 343, `KEY_RESIZE` 410).
  - Extend `tests/test_tui.py`: typing in INSERT edits the query; Esc enters NORMAL; `j`/`k` clamp; `gg` and `G`; `g` then `x` clears pending without jumping; Ctrl-D moves half a page; `]c` then `[c` returns to no filter; `/` clears the query and enters INSERT; `y` returns "yank"; `q` returns "cancel"; Ctrl-W deletes one word.
  - Update the Neovim picker in `lua/kao/init.lua` to the keys in the Neovim section (Esc to prompt normal mode, `j`/`k`, `gg`/`G`, `q`).
  - Check: unittest passes; `nvim --headless -u NONE --cmd 'set rtp+=.' -c 'runtime plugin/kao.lua' -c Kao -c 'qa!'` exits 0. The user tries both by hand.

- [ ] T8 README
  - Usage, keys (both modes, table), install (`ln -s ~/github/kao/bin/kao ~/.local/bin/kao`), lazy.nvim spec, runtime deps (python3 >= 3.11 and a terminal with OSC 52; nothing else; tmux needs `set -g set-clipboard on`), data sources and attribution.
  - Check: every command in the README runs as written.
