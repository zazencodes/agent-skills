# Agent Skills Monorepo

A central, version-controlled home for coding agent skills across multiple tools.

> With <3 from [ZazenCodes](https://zazencodes.com/)

## Benefits

- You can keep your agent skills in this repo for version control.
- Each agent still reads its skills from its normal system directory.
- The repo paths and system paths stay in sync, so you can add, remove, or edit skills from either location.

## How it works

- The real skill files live in this repo under `./claude`, `./codex`, and the other top-level agent folders.
- `setup_symlinks.py` imports your current system skill directories into those repo folders.
- The script creates a backup of each original system skill directory under `.agent-skills-setup/backup/`.
- It then replaces each system skill directory with a symlink back to the matching repo folder.
- After setup, editing either path updates the same files.

## Agent mapping

| Tool | System skill directory | Repo folder |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `./claude` |
| OpenAI Codex | `~/.codex/skills/` | `./codex` |
| GitHub Copilot | `~/.copilot/skills/` | `./copilot` |
| Cursor | `~/.cursor/skills/` | `./cursor` |
| Google Antigravity | `~/.gemini/antigravity/skills/` | `./gemini` |

## Setup

This repo is meant to be forked and used from your own GitHub account.

### 1. Fork and clone your own copy

Fork this repo on GitHub, then clone your fork:

```sh
git clone <your-fork-url>
cd agent-skills
```

### 2. Decide whether to keep the starter skills

This repo can include starter skills as examples. You can keep any existing repo skills, learn from them, or remove them before setup.

If you want a blank repo for your own skills, run:

```sh
python3 clear_repo_skills.py --dry-run
python3 clear_repo_skills.py
```

Run `clear_repo_skills.py` only before setup. It refuses to run after the repo folders become live symlink targets.

### 3. Preview the setup

```sh
python3 setup_symlinks.py --dry-run
```

### 4. Run the setup

```sh
python3 setup_symlinks.py
```

### What setup does

- Moves the current repo skills for each agent into `.agent-skills-setup/staging/<agent>/`.
- Copies your current system skill directory into the repo.
- Backs up the original system skill directory under `.agent-skills-setup/backup/<agent>/`.
- Copies non-conflicting starter skills back into the repo.
- Preserves conflicting starter skills under `.agent-skills-setup/conflicts/<agent>/`.
- Replaces the system skill directory with a symlink to the repo folder.

### 5. Review any preserved conflicts

If a skill exists in both places with the same name:

- The current system skill stays live.
- The repo copy is preserved under `.agent-skills-setup/conflicts/<agent>/`.
- You can merge it manually or use a coding agent.

## Conflict Help

Paste this prompt into Codex or Claude Code if you want help reviewing preserved conflicts:

```text
I just ran setup on my Agent Skills Monorepo and I have preserved skill conflicts.

Please review the skills under `.agent-skills-setup/conflicts/` and compare them with the live skills in the matching repo folders (`claude/`, `codex/`, `copilot/`, `cursor/`, `gemini/`).

For each conflicting skill:
- treat the live repo version as the source of truth unless I approve a change
- inspect the conflict copy for anything useful
- merge useful content into the live skill carefully
- keep the skill format valid for that tool
- summarize the changes you made
- tell me which conflict copies are safe to delete afterward

Work one conflict at a time.
```

Manual fallback:

- Compare each folder under `.agent-skills-setup/conflicts/<agent>/` with the matching live skill folder in the repo.
- Copy across any changes you want to keep.
- Delete the conflict copy when you are done with it.

## Backups

Backups are stored under `.agent-skills-setup/backup/<agent>/`.

Keep them until you confirm the setup worked correctly, then delete them yourself.

## Commit Your Skills

After setup, commit your imported skills and future changes to your fork:

```sh
git add claude codex copilot cursor gemini
git commit -m "Import my agent skills"
git push
```

## Notes

- After setup, the repo folders remain the real skill folders.
- The system skill directories become symlinks to the repo folders.
- Re-running `setup_symlinks.py` on an already configured agent is a no-op.
- `.agent-skills-setup/` is local setup state and is gitignored.
