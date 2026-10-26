# Progress

Current focus:

- T9 (OSC 52 clipboard, drop wl-copy/wtype), then T10 (vim modal keys), then T8 (README). T1-T7 done by the free lane and reviewed by Claude Code on 2026-10-26.

Blocked:

- None.

Waiting on the user (cannot be checked headless):

- After T10: TUI modes and keys per architecture.md, `y` puts the face on the clipboard via OSC 52, `bin/kao | cat` still draws on the terminal.
- Neovim after T10: `{ dir = "~/github/kao" }` in lazy.nvim, then `:Kao` from normal and insert mode, insert-mode movement, `<Esc>` to normal, `j`/`k`/`gg`/`G`, `<CR>` inserts, `q` closes. Headless check passed: `:Kao` fills the results float and leaves no serve process.

Measurements (2026-10-26, Python 3.14.8, `tools/bench.sh`, 50 runs):

- `python3 -I -S -c pass` 42-52 ms (noisy), `bin/kao list` ~50 ms, `bin/kao --random` ~49 ms.
- `import os` under `-I -S` costs ~14 ms on this host; keep it out of non-TUI paths.
