# AGENTS.md

## Project Instructions

## Project Overview

- Repository for coding-agent skills across multiple tools.
- Top-level agent folders (`claude/`, `codex/`, `copilot/`, `cursor/`, `gemini/`) are repo-owned skill directories.
- After setup, each tool's native system skill directory becomes a symlink back to the matching repo folder.
- Starter skills may live in the top-level agent folders.

## Repo Shape

- `setup_symlinks.py`: first-run import script that backs up system skills, imports them into the repo, preserves repo conflicts, and replaces system directories with symlinks to the repo.
- `clear_repo_skills.py`: helper script that removes starter skills from the repo before first setup.
- `*/SKILL.md`: starter skill definitions in this repo.
- `.agent-skills-setup/`: local setup state for backups, staging, and conflict copies; gitignored.

## Development Commands

- `python3 clear_repo_skills.py --dry-run`: preview removal of starter repo skills before setup.
- `python3 clear_repo_skills.py`: remove starter repo skills before setup.
- `python3 setup_symlinks.py --dry-run`: preview import, backup, merge, and symlink actions.
- `python3 setup_symlinks.py`: import current system skills into the repo and link system directories back to it.

## Important Notes

- Normal setup copies current system skill directories into the repo, backs them up, merges in non-conflicting starter skills, and then replaces the system directories with symlinks to the repo.
- On same-name conflicts, the current system skill stays live and the repo copy is preserved under `.agent-skills-setup/conflicts/<agent>/`.
- Backups under `.agent-skills-setup/backup/<agent>/` are not auto-deleted.
- After setup, edits inside the repo folders or the system skill directories both modify the same files.
- `clear_repo_skills.py` is only for pre-setup cleanup and refuses to run once a repo folder is a symlink target.

## Validation

- Use `python3 setup_symlinks.py --dry-run` first when changing setup logic.
- Use `python3 clear_repo_skills.py --dry-run` before real starter-skill cleanup.
- After a real setup, each configured system skill directory should resolve to the matching repo folder.
