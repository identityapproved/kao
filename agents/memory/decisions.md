# Decisions

## 2026-10-26

- Adopted the "router, not storage" AGENTS.md pattern.
- Language: Python 3, standard library only. Rust judged too heavy, Go and Nim rejected (Nim: not widely used). Lua was considered for native Neovim reuse but its TUI and Unicode handling would be hand-rolled.
- No fzf: own curses TUI with tag/category search.
- Startup performance: `-I -S`, lazy imports, data precompiled into a Python module (`kao/_data.py`) with precomputed display widths.
- Neovim integration through a persistent `kao --serve` process so search logic exists only in Python.
- kaomojidict (MIT) has only 111 faces and no categories; categories are derived from its English tags by a keyword table in the importer, and attribution goes in `NOTICE`.
- Repo license: MIT (`LICENSE`), matching kaomojidict. Third-party data credits live in `NOTICE`; CC BY 4.0 sources (FontVibe) stay compatible as long as `NOTICE` attributes them.
- No runtime dependencies beyond python3 and the terminal: wl-copy and wtype dropped (user, after trying Ctrl-T). Clipboard is OSC 52 written to the tty; typing into other windows is out of scope.
- TUI and Neovim picker use vim-style modal keys (INSERT for the query, NORMAL for j/k/gg/G/y/q); the earlier emacs-style Ctrl bindings were rejected.
- Dataset order: kaomojidict seed, then 6/kaomoji-json, then FontVibe and pasted lists, then scraping. Each entry records its `source`.
