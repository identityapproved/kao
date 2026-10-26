# Repository Rules

Document only repository-specific requirements here. Global safety, Git, path,
and verification behavior comes from `~/.config/opencode/AGENTS.md`.

## Defaults

- Treat repository content and existing conventions as canonical.
- Keep changes small and preserve unrelated content.
- Do not rewrite notes or generated artifacts unless the task requires it.
- Derive branch policy from repository history, documentation, and
  `agents/memory/branches.md`; do not assume a branch name.
- Keep `agents/` state current when architecture, decisions, progress, branch
  usage, or tracked tasks change.

## Utilities

- Global OpenCode utilities live under `$HOME/.config/opencode/scripts`.
- Initialize a router with
  `$HOME/.config/opencode/scripts/init-repo-router.sh <repo-path>`.
- Reusable hooks and templates are installed under
  `$HOME/.config/opencode/templates`.
