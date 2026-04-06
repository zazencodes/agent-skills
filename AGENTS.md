# AGENTS.md

## Project Instructions

## Project Overview

- Repository for coding-agent skills across multiple tools.
- Top-level agent folders (`claude/`, `codex/`, `copilot/`, `cursor/`, `gemini/`) become the live skill directories after setup.
- This repo should start blank. Do not keep starter skills in the repo.

## Repo Shape

- `setup_symlinks.py`: import script that validates the repo is blank, backs up current system skills, copies them into the repo, and replaces system directories with symlinks to the repo.
- `.agent-skills-setup/backup/`: local backup state created by setup.
- `.agent-skills-setup/backup/README.md`: recovery instructions written by the setup script before live changes begin.

## Development Commands

- `python3 setup_symlinks.py --dry-run`: preview validation, backup, import, and symlink actions.
- `python3 setup_symlinks.py`: run the interactive setup flow.

## Important Notes

- `setup_symlinks.py` should fail fast if any repo agent folder already contains skills.
- `setup_symlinks.py` should fail fast if any system skill directory is already a symlink.
- The script should stay simple and readable: no starter-skill merge logic, no conflict preservation flow, and no force mode.
- Backups under `.agent-skills-setup/backup/<agent>/` are important and are not auto-deleted.
- After setup, edits inside the repo folders or the system skill directories both modify the same files.

## Validation

- Use `python3 setup_symlinks.py --dry-run` first when changing setup logic.
- After a real setup, each configured system skill directory should resolve to the matching repo folder.
