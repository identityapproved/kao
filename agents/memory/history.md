# History

## 2026-10-26

- Repo cloned from github.com/identityapproved/kao (README only).
- Initialized repo router structure; wrote architecture and task queue.
- T1 complete: seed data and build step; 30 entries, 8 categories; tests pass.
- T1b complete: kaomojidict import; data now 140 entries; misc 30/111 (27.0%).
- T2 complete: search implementation.
- T3 complete: CLI and launcher.
- T4 complete: TUI implemented (interactive verification pending).
- T5 complete: actions implemented.
- T6 complete: startup benchmark.
- T7 complete: serve mode and Neovim plugin.
- Review (Claude Code): free lane ran T1-T7 in one session despite the one-task rule. Fixed: Neovim plugin never started serve mode (`vim.system` has no `args` option); `bin/kao` broke when symlinked; Ctrl-T typed into kao's own terminal; copy errors swallowed silently; serve traceback on closed pipe; width counted variation selectors/ZWJ; dead search branch and alias clutter in tui.py and build_data.py. Corrected the import rule: `os` is not free under `-S`.
- User rejected wl-copy/wtype (wants no dependencies) and non-vim keys; spec rewritten: OSC 52 clipboard (T9), vim modal keys in TUI and Neovim picker (T10), README moved last.
- T9 complete: dependency-free clipboard.
- T10 complete: modal TUI.
- T8 complete: README.
- Review of T8-T10 (Claude Code): free lane again ran several tasks in one session and rewrote `lua/kao/init.lua` from scratch, using a nonexistent `job.stdin` field so no query reached serve mode and each open leaked a serve process; restored the working plugin and added the vim keys to it. TUI: Enter and Ctrl-J were both 10, fixed with `curses.nonl()`; removed fallback/alias clutter in `handle_key`; stopped replacing `sys.stdout` with the tty. Added `tools/nvim_check.lua` (real headless picker test) and `.luarc.json`.
- OSC 52 yank worked in bare foot but not in tmux (`set-clipboard external`, foot lacks the `clipboard` feature); added tmux passthrough wrapping in `kao/actions.py` (user's tmux has `allow-passthrough on`). Sending both the plain and wrapped sequence once left zsh stuck in a bracketed paste, so inside tmux only the wrapped one is sent; tmux `set-clipboard` stays off (it corrupts pastes in nvim/Claude Code). Added the lazy.nvim spec `~/.config/nvim/lua/plugins/kao.lua` (`<leader>ik`).
- TUI redesign: faces only (tags dropped), cell grid filling the window (`grid_layout`: median-width cells, wide faces span cells, nothing cut);  Faces ran together with a 2-space gap, so the gap is 3 with a dim `│` separator; `build_data.py` now counts prepended concatenation marks (U+0600-0605...) as width 1 like wcwidth (ncurses agreed on all 140 widths after that). NORMAL hjkl/arrows move in the grid, `l` no longer selects; INSERT is search-only (movement keys removed). The Neovim float still lists faces with tags.
- Library expansion: user supplied the Gboard kaomoji list (55,327 `label<TAB>face`, license unknown) -> `tools/import_gboard.py` into gitignored `data/local/`, built into gitignored `kao/_data_local.py` (38,279 after dropping emoji 13,064, Japanese phrases 3,349, Latin words 731; user asked for kaomoji only, no emoji). Data modules switched from tuples to bytes blobs plus an inverted index (`kao/db.py`); search uses the index because per-line Python loops cost ~1.7 us/iteration on this Pentium N3540 (single letter 380 ms -> ~25 ms). TUI grid packs rows lazily. Committed `_data.py` now has 129 entries (emoji ones dropped).
