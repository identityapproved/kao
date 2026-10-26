# Project Agent Instructions

These instructions refine the global OpenCode policy for this repository.

## Project

`kao`: kaomoji picker, curses TUI plus Neovim plugin. Python 3 standard library only; Lua only under `lua/` and `plugin/`. Design and performance rules: `agents/architecture.md`. Work queue: `agents/tasks/active.md`.

- Test: `python3 -m unittest -v`
- Rebuild data after editing `data/kaomoji.json` or `data/local/*.json`: `python3 tools/build_data.py`
- Local Gboard import (gitignored, license unknown): `python3 tools/import_gboard.py ~/downloads/kaomojis-gboard.txt`
- Run: `bin/kao`
- Startup check: `tools/bench.sh`
- Neovim check (must print only `ok` lines and exit 0): `nvim --headless -u NONE --cmd 'set rtp+=.' -c 'runtime plugin/kao.lua' -c 'luafile tools/nvim_check.lua'`

Hard constraints:

- No third-party Python packages, no `pip`, no `pyproject.toml`.
- No external programs at runtime: no `subprocess`, no wl-copy/wtype/xclip/fzf. Clipboard is OSC 52. The only runtime requirements are python3 and a terminal (plus Neovim for the plugin).
- Edit existing files in place; do not rewrite a working file from scratch. A rewrite of `lua/kao/init.lua` once dropped working fixes and broke the picker (`vim.system` objects have no `.stdin` field; write with `obj:write()`).
- TUI and Neovim keys are vim-style and modal; follow the key lists in `agents/architecture.md` exactly instead of inventing bindings.
- Never edit `kao/_data.py` or `kao/_data_local.py` by hand; they are generated.
- Never commit `data/local/` or `kao/_data_local.py` (gitignored): their license is not settled.
- Runtime modules import only `sys` (and the builtin `posix`) at top level. Everything else, `os` included, is imported inside the function that needs it: under `python3 -I -S`, `import os` alone costs ~14 ms. No `argparse`, `random`, `re`, `unicodedata`, `pathlib`, `typing` at runtime.
- No network access: do not clone, download or scrape. Datasets are fetched by the user.
- Do one task from `agents/tasks/active.md` per session, then stop and report what was checked.
- Interactive TUI and Neovim behaviour cannot be verified headless; list exactly what the user should try instead of claiming it works.

## Workflow

- Inspect the repository, current branch, worktree, and existing instructions before editing.
- Preserve unrelated work and prefer minimal, targeted changes.
- Discover and run the repository's documented validation commands before declaring work complete.
- Do not create, switch, merge, or push branches unless the user requests it.
- Record project-specific branch policy in `agents/memory/branches.md` instead of assuming a universal main branch.

## Project Context

- Current progress: `agents/memory/progress.md`
- History: `agents/memory/history.md`
- Decisions: `agents/memory/decisions.md`
- Branch context: `agents/memory/branches.md`
- Architecture: `agents/architecture.md`
- Active tasks: `agents/tasks/active.md`
- Backlog: `agents/tasks/backlog.md`
- Completed tasks: `agents/tasks/done.md`
- Repository-specific rules: `agents/rules.md`
- Follow-up instruction work: `agents/next-steps.md`

Read the relevant supporting files before changing behavior they describe. When
the user says `update memory`, update all affected `AGENTS.md` and `agents/`
state files, then stage or commit only when requested.

## Path Hygiene

- Use relative paths when practical and `~` or `$HOME` for home paths.
- Data stores live under `$HOME`. Write their paths as `~` or `$HOME`.
- Check changed files for username-bearing paths and secrets before sharing or staging.
