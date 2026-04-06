# Agent Skills Monorepo

A central, version-controlled home for coding agent skills across multiple tools.

> With <3 from [ZazenCodes](https://zazencodes.com/)

## Benefits

- Keep all your agent skills for different tools in one Git repo.
- Your agents use those skills automatically, with no extra configuration.
- Changes stay in sync everywhere and are easy to version control:
    - Edit skills in this repo
    - Or edit them in the system skill folders
    - Either way, you're changing the same files

## How It Works

When you run `setup_symlinks.py` it will:

1. Copy your current system skills into this repo.
2. Replace each system skills directory with a symlink back to the corresponding folder in this repo.

## This doesn't sound safe

- There are no skills in here. 3rd party skills in a repository like this would be a huge security risk.
- There is built-in [disaster recovery](#backups-and-recovery). When you run `setup_symlinks.py` it first creates backups of your current agent skills under `.agent-skills-setup/backup/`.

## Supported Agent Mappings


| Tool | System skill directory | Repo folder |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `./claude` |
| OpenAI Codex | `~/.codex/skills/` | `./codex` |
| GitHub Copilot | `~/.copilot/skills/` | `./copilot` |
| Cursor | `~/.cursor/skills/` | `./cursor` |
| Google Antigravity | `~/.gemini/antigravity/skills/` | `./gemini` |


## Setup

You will use this git repo directly to version control your skills.

### 1. Fork and clone your own copy

Open [this repository on GitHub](https://github.com/zazencodes/agent-skills) and
click the "Fork" button

> [!INFO]   
> The fork button is beside the "Star" button --- you may as well hit that one too!

Then clone your forked repo:

```sh
git clone <your-fork-url>
cd agent-skills
```

You should also make your fork private unless you are comfortable open-sourcing all your skills.

### 2. Run the setup

> [!CAUTION]   
> After running this script, your agent skills will live here in this repo. Your system skills directories will become symlinks. It's not dangerous, but it's important for you to understand this.

```sh
# Run the preview
python setup_symlinks.py --dry-run

# Run the setup
python setup_symlinks.py
```

> [!NOTE]   
> Before setup:
> 
> - `claude/`, `codex/`, `copilot/`, `cursor/`, and `gemini/` should be missing or empty.
> - None of the system skill directories should already be symlinks.
> 
> If the script finds existing repo skills or existing symlinks, it will stop and tell you exactly which paths you need to remove first.


### 3. Commit Your Skills

Add this note at the top of your fork's `README.md` for future reference:

```md
# Agent Skills Monorepo

This repository is a fork of the [ZazenCodes Agent Skills](https://github.com/zazencodes/agent-skills) monorepo project.

My agent skills live here and my agent skill system directories are symlinked to this repo.
```

Stage and commit the changes:

```sh
git status
git add README.md claude codex copilot cursor gemini
git commit -m "Initial commit of agent skills after setup"
git push
```

Congratulations! You now have your own an agent skills monorepo and you're ready to crush the [agentic coding era](https://zazencodes.com/relink).

## Additional Documentation

### What Setup Does

For each agent:

- If a system skills directory exists, the script backs it up under `.agent-skills-setup/backup/<agent>/`.
- If a system skills directory exists, the script copies it into the matching repo folder.
- If a system skills directory does not exist, the script creates an empty repo folder for that agent.
- The script replaces the system skills directory with a symlink pointing back to the repo folder.

If anything fails partway through:

- The script prints the real traceback first.
- The script then tells you where the backup folder lives.
- The backup folder contains a `README.md` with recovery steps.

### Backups

Backups are stored under `.agent-skills-setup/backup/`.

- Keep them until you have verified everything is working.
- Read `.agent-skills-setup/backup/README.md` if you need to restore an original system directory.

### Disaster Recovery

If you want an agent to help with disaster recovery, start the agent from the root of this repo and use the following prompt:

```text
I need help with disaster recovery for this agent-skills monorepo setup.

Please inspect this repository, especially `setup_symlinks.py`, `.agent-skills-setup/backup/README.md`, and `.agent-skills-setup/backup/`.

Assume I most likely want to undo the symlinks and restore my coding-agent system skill directories from the disaster recovery backup, but keep the investigation open ended in case the safest recovery path is different.

As you work:
- Ask me questions whenever anything is uncertain.
- Explain your understanding of the current state before making changes.
- Confirm with me before running any command that changes files, symlinks, or directories.
- Prefer the safest reversible steps first.

Please walk me through the recovery and help me execute it carefully.
```
