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
