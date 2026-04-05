# AGENTS.md

## Project Instructions

## Project Overview

- Repository for coding-agent skills across multiple tools.
- Top-level agent folders (`claude/`, `codex/`, `copilot/`, `cursor/`, `gemini/`) are intended to become symlinks to each tool's native skill directory after setup.
- Committed sample skills currently live under `claude/`.

## Repo Shape

- `setup_symlinks.py`: bootstrap script that seeds native skill directories, swaps repo folders for symlinks, and manages collision handling.
- `claude/*/SKILL.md`: committed skill definitions in this repo.
- `.agent-skills-setup/`: local setup state for pending and staging copies; gitignored.

## Development Commands

- `python3 setup_symlinks.py`: run normal bootstrap from the repo root.
- `python3 setup_symlinks.py --dry-run`: preview symlink and copy actions without changing files.
- `python3 setup_symlinks.py --force`: overwrite same-name native skills, but only after a prior normal run created pending entries.

## Important Notes

- Normal setup copies repo skills into each native directory, then replaces each top-level repo folder with a symlink to that native directory.
- On name collisions without `--force`, the script preserves the repo copy under `.agent-skills-setup/pending/<agent>/` instead of overwriting the native skill.
- `--force` is intentionally refused unless pending entries already exist.
- After setup, edits inside top-level agent folders modify the real native skill directories through the symlinks.

## Validation

- Use `python3 setup_symlinks.py --dry-run` first when changing setup logic.
- After a real `--force` run, `.agent-skills-setup/pending/` should be empty.
