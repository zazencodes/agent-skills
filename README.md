# Agent Skills

A central, version-controlled home for coding agent skills across multiple tools.

> With <3 from [ZazenCodes](https://zazencodes.com/)

## Benefits

- You can keep your agent skills in this repo for version control.
- Each agent still reads its skills from its normal system directory.
- The repo paths and system paths stay in sync, so you can add, remove, or edit skills from either location.

## How it works

- Each top-level agent folder in this repo, like `./claude` or `./codex`, becomes a symlink.
- Each symlink points to that agent's real system skill directory.
- Before creating the symlink, the setup script copies any skills from this repo into the system directory.

## Agent mapping

| Tool | System-wide source | Repo symlink path |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `./claude` |
| OpenAI Codex | `~/.codex/skills/` | `./codex` |
| GitHub Copilot | `~/.copilot/skills/` | `./copilot` |
| Cursor | `~/.cursor/skills/` | `./cursor` |
| Google Antigravity | `~/.gemini/antigravity/skills/` | `./gemini` |


## Setup

Run the bootstrap script from the repo root:

```sh
python3 setup_symlinks.py
```

What it does:

- creates the native agent skill directories if needed
- temporarily moves the repo's current agent folders aside
- creates folder-level symlinks at `./claude`, `./codex`, and so on
- copies repo skills into the native system directory
- skips same-name skills that already exist in the native system directory

Skill collision handling is done at the top-level skill folder name. If `claude/fs-cleanup` already exists in `~/.claude/skills/fs-cleanup`, the setup script will skip the repo copy instead of overwriting it.

## Expected flow

The intended flow is:

1. Run setup normally:

```sh
python3 setup_symlinks.py
```

2. If the script reports skipped same-name skills, review them and then run:

```sh
python3 setup_symlinks.py --force
```

That second run applies the pending repo copies and clears the pending area.

If the first run has no collisions, you are done and do not need `--force`.

## Dry run

Preview changes without modifying anything:

```sh
python3 setup_symlinks.py --dry-run
```

## Force overwrite

`--force` is intentionally only allowed after a normal setup run has already created pending skipped skills.

If the script reports skipped skills and you want the repo version to win, re-run with:

```sh
python3 setup_symlinks.py --force
```

If no pending skipped skills exist yet, the script will refuse to run with `--force` and tell you to run normal setup first.

## Skipped skill preservation

When a same-name skill is skipped, the repo copy is preserved under:

```sh
.agent-skills-setup/pending/
```

That lets a later `--force` run apply the repo version even after the repo folder itself has already become a symlink.

After a successful real `--force` run, there should be no pending files left.

## Notes

- After setup, edits made in this repo are edits to the real native skill directories because the top-level agent folders are symlinks.
- The hidden `.agent-skills-setup/` directory is local setup state and is gitignored.
