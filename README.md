# Agent Skills Monorepo

A central, version-controlled home for coding agent skills across multiple tools.

> **Part of [zstack](https://github.com/zazencodes/zstack)**, the agentic system I use to run ZazenCodes.

> With ❤️ from [ZazenCodes](https://zazencodes.com/)

> [!NOTE]
> This setup currently supports macOS and Linux only.

## Benefits

- Keep all your agent skills for different tools in one Git repo.
- Your agents use those skills automatically, with no extra configuration.
- Changes stay in sync everywhere and are easy to version control:
    - Edit skills in this repo
    - Or edit them in the system skill folders
    - Either way, you're changing the same files

## How It Works

When you run `setup_symlinks.py` it will:

1. Ask which agents you want to manage. `agents/` and `claude/` are always included.
2. Back up your current system skills directories.
3. Copy them into this repo.
4. Replace each system skills directory with a symlink back to the matching folder in this repo.

`agents/` is the canonical user-skill folder and maps to `~/.agents/skills`. `claude/` is a required mirror that maps to `~/.claude/skills` because Claude Code doesn't read `~/.agents/skills`. Other agents (`codex`, `copilot`, `cursor`, `gemini`) are optional and you opt into them during setup.

## Setup

You'll use this Git repository directly to version control your skills.

### 1. Create and clone your own private copy

Open [this repository on GitHub](https://github.com/zazencodes/agent-skills) and use
the ["Use this template" button](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template#creating-a-repository-from-a-template) to create a new private repository in your own
account or organization.

> [!TIP]
> The "Use this template" button is right next to the "Star" button, so you may as well click that one too ⭐
> Thank you. It really helps me out.

Then clone your new private repo:

```sh
git clone <your-private-repo-url>
cd agent-skills
```

### 2. Choose your setup style

You have two ways to drive setup:

**A. Run the script directly** (classic flow):

```sh
# Preview without changing anything
python3 setup_symlinks.py --dry-run

# Run the interactive setup
python3 setup_symlinks.py
```

The script walks you through agent selection, prints a plan per agent, and asks you to confirm before changing anything.

**B. Let an agent drive it for you** (vibe flow):

Open any AI coding agent (Claude Code, Codex, etc.) in this repo and ask it to "set up agent skills." The agent will pick up the project-local `agent-skills-setup-manager` skill (shipped at `.agents/skills/agent-skills-setup-manager/` and `.claude/skills/agent-skills-setup-manager/`) and walk you through the flow conversationally — choosing agents, running the script, checking status, and adding more agents later.

> [!CAUTION]
> After running setup, your agent skills will live here in this repo. Your system skills directories will become symlinks. It's not dangerous, but it's important for you to understand this.

> [!NOTE]
> Setup is idempotent. Already-configured agents are skipped on re-run. You can run setup again later to add new agents, repair drift, or check status.
### 3. Commit Your Skills

Add this note at the top of your repo's `README.md` for future reference:

```md
# Agent Skills Monorepo

This repository was created from the [ZazenCodes Agent Skills](https://github.com/zazencodes/agent-skills) template repository.

My agent skills live here and my agent skill system directories are symlinked to this repo.
```

Stage and commit:

```sh
git status
git add README.md agents claude
git commit -m "Initial commit of agent skills after setup"
git push
```

Congratulations! You now have your own agent skills monorepo and you're ready to crush the [agentic coding era](https://zazencodes.com/relink).

## Additional Documentation

### Is this safe?

- This repository ships with empty top-level agent folders. The only skill it contains is `agent-skills-setup-manager`, scoped to this repo at `.agents/skills/` and `.claude/skills/`, which exists to help agents drive this repo's setup. Third-party skills in a template repo would be a security risk.
- Built-in [disaster recovery](#disaster-recovery): `setup_symlinks.py` creates per-agent backups under `.agent-skills-setup/backup/` before changing anything.

### Supported Agent Mappings

| Tool | System skill directory | Repo folder | Default? |
| --- | --- | --- | --- |
| Codex / AGENTS.md ecosystem | `~/.agents/skills/` | `./agents` | Required |
| Claude Code | `~/.claude/skills/` | `./claude` | Required |
| OpenAI Codex system skills | `~/.codex/skills/` | `./codex` | Optional |
| GitHub Copilot | `~/.copilot/skills/` | `./copilot` | Optional |
| Cursor | `~/.cursor/skills/` | `./cursor` | Optional |
| Google Antigravity | `~/.gemini/antigravity/skills/` | `./gemini` | Optional |

`agents/` is the canonical user-skill folder. `claude/` is a required mirror because Claude Code reads from `~/.claude/skills` rather than `~/.agents/skills`. The `codex/` folder is reserved for Codex system-skill content (e.g. `.system/`); put Codex user skills in `agents/` instead.

By convention, when you ask an agent to add a new skill, it should ask whether to install into `agents/`, `claude/`, or both. You can pin a default by editing `AGENTS.md`.

### What Setup Does

For each selected agent:

- If the system skills directory has content, the script backs it up under `.agent-skills-setup/backup/<agent>/` and imports it into the matching repo folder.
- If the system directory is missing or empty, the script creates an empty repo folder.
- If repo and system both already have content, the script stops on that agent and asks you to resolve it manually (pick one as source of truth, clear the other, re-run).
- The script replaces the system skills directory with a symlink pointing back to the repo folder.
- Already-configured agents are skipped automatically.

If anything fails partway through:

- The script prints the real traceback first.
- It then tells you where the backup folder lives.
- The backup folder contains a `README.md` with recovery steps.

### Backups

Backups are stored under `.agent-skills-setup/backup/`.

- Keep them until you have verified everything is working.
- Read `.agent-skills-setup/backup/README.md` if you need to restore an original system directory.

### Re-running Setup

`setup_symlinks.py` is idempotent. Re-run it any time to:

- Add a new agent to your setup (it remembers your previous selection).
- Repair drift if a symlink got removed or replaced.
- Run `python3 setup_symlinks.py --status` to see the current topology without changing anything.

The `agent-skills-setup-manager` skill is the recommended way to drive these flows once you're set up — just ask an agent for help.

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

## License

[GPLv3](LICENSE) covers this template and `setup_symlinks.py`. The skills you add to your own copy are yours.
