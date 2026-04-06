#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentMapping:
    name: str
    repo_path: Path
    system_path: Path


class SetupError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy each current system skills directory into this repo, back it up, "
            "and replace the system directory with a symlink back to the repo."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the setup without changing files or asking for confirmation.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def build_mappings(root: Path) -> list[AgentMapping]:
    home = Path.home()
    return [
        AgentMapping("claude", root / "claude", home / ".claude" / "skills"),
        AgentMapping("codex", root / "codex", home / ".codex" / "skills"),
        AgentMapping("copilot", root / "copilot", home / ".copilot" / "skills"),
        AgentMapping("cursor", root / "cursor", home / ".cursor" / "skills"),
        AgentMapping("gemini", root / "gemini", home / ".gemini" / "antigravity" / "skills"),
    ]


def managed_root(root: Path) -> Path:
    return root / ".agent-skills-setup"


def backup_root(root: Path) -> Path:
    return managed_root(root) / "backup"


def backup_dir(root: Path, agent_name: str) -> Path:
    return backup_root(root) / agent_name


def backup_readme_path(root: Path) -> Path:
    return backup_root(root) / "README.md"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def create_symlink(link_path: Path, target: Path) -> None:
    link_path.symlink_to(target)


def iter_entries(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.iterdir(), key=lambda entry: entry.name)


def format_entry_names(entries: list[Path]) -> str:
    if not entries:
        return "(empty)"
    return ", ".join(entry.name for entry in entries)


def copy_directory(src: Path, dst: Path) -> None:
    if not src.is_dir():
        raise SetupError(f"Expected a directory at {src}")

    ensure_dir(dst.parent)
    temp_dir = dst.parent / f".{dst.name}.tmp"
    old_dir = dst.parent / f".{dst.name}.old"

    remove_path(temp_dir)
    remove_path(old_dir)
    shutil.copytree(src, temp_dir)

    if dst.exists() or dst.is_symlink():
        shutil.move(str(dst), str(old_dir))

    shutil.move(str(temp_dir), str(dst))
    remove_path(old_dir)


def recreate_empty_directory(path: Path) -> None:
    remove_path(path)
    ensure_dir(path)


def describe_repo_state(path: Path) -> str:
    if path.is_symlink():
        return f"symlink -> {path.resolve()}"
    if path.exists() and not path.is_dir():
        return "exists but is not a directory"
    if not path.exists():
        return "missing"

    entries = iter_entries(path)
    if not entries:
        return "empty directory"

    return f"contains {len(entries)} item(s): {format_entry_names(entries)}"


def describe_system_state(path: Path) -> str:
    if path.is_symlink():
        return f"symlink -> {path.resolve()}"
    if path.exists() and not path.is_dir():
        return "exists but is not a directory"
    if not path.exists():
        return "missing"

    entries = iter_entries(path)
    return f"directory with {len(entries)} item(s): {format_entry_names(entries)}"


def collect_preflight_problems(mappings: list[AgentMapping]) -> list[str]:
    problems: list[str] = []

    for mapping in mappings:
        repo_path = mapping.repo_path
        system_path = mapping.system_path

        if repo_path.is_symlink():
            problems.append(
                f"Remove the repo symlink at {repo_path} before running setup again."
            )
        elif repo_path.exists() and not repo_path.is_dir():
            problems.append(
                f"Remove {repo_path} because setup expects that path to be missing or an empty directory."
            )
        elif repo_path.exists():
            for entry in iter_entries(repo_path):
                problems.append(
                    f"Remove {entry} because this repo must start with no skills in {repo_path}."
                )

        if system_path.is_symlink():
            problems.append(
                f"Remove the existing system symlink at {system_path} before running setup again."
            )
        elif system_path.exists() and not system_path.is_dir():
            problems.append(
                f"Remove {system_path} because setup expects that path to be a directory or be missing."
            )

    return problems


def write_backup_readme(root: Path, mappings: list[AgentMapping], *, dry_run: bool) -> None:
    readme_path = backup_readme_path(root)

    if dry_run:
        print(f"Dry run: would write recovery notes to {readme_path}")
        return

    ensure_dir(readme_path.parent)

    lines = [
        "# Backup Recovery Notes",
        "",
        "This folder contains backups made by `setup_symlinks.py` before it changed your system skill directories.",
        "",
        "If setup stopped halfway through, use these steps for any agent you want to restore:",
        "",
        "1. Remove the system skills symlink if one exists.",
        "2. Remove the partially imported repo folder for that agent if you do not want to keep it.",
        "3. Copy the matching backup folder back to the original system path.",
        "",
        "A backup folder only exists for an agent after the script has successfully created it.",
        "",
        "Agent paths:",
        "",
    ]

    for mapping in mappings:
        lines.extend(
            [
                f"- {mapping.name}",
                f"  backup: {backup_dir(root, mapping.name)}",
                f"  system: {mapping.system_path}",
                f"  repo:   {mapping.repo_path}",
                "",
            ]
        )

    lines.extend(
        [
            "Example restore commands on macOS or Linux:",
            "",
            "```sh",
            "rm -rf ~/.codex/skills",
            "cp -R /path/to/agent-skills/.agent-skills-setup/backup/codex ~/.codex/skills",
            "```",
            "",
            "After you restore a system directory, make sure the matching repo folder is either removed or reset to the state you want before running setup again.",
            "",
        ]
    )

    readme_path.write_text("\n".join(lines), encoding="utf-8")


def print_intro(root: Path, mappings: list[AgentMapping], *, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "LIVE RUN"
    print(f"== {mode} ==")
    print(f"Repo root:   {root}")
    print(f"Backup root: {backup_root(root)}")
    print()
    print("Current state:")

    for mapping in mappings:
        print(f"- {mapping.name}")
        print(f"  repo path:   {mapping.repo_path}")
        print(f"  repo state:  {describe_repo_state(mapping.repo_path)}")
        print(f"  system path: {mapping.system_path}")
        print(f"  system state: {describe_system_state(mapping.system_path)}")

    print()


def confirm_or_exit(message: str) -> None:
    answer = input(f"{message} [y/N]: ").strip().lower()
    if answer in {"y", "yes"}:
        return

    print("Setup cancelled. No more changes will be made.")
    raise SystemExit(1)


def rollback_agent(
    mapping: AgentMapping,
    root: Path,
    *,
    repo_existed_before: bool,
    system_existed_before: bool,
) -> None:
    print(f"Attempting rollback for {mapping.name}...")

    remove_path(mapping.system_path)

    agent_backup = backup_dir(root, mapping.name)
    if system_existed_before and agent_backup.exists():
        copy_directory(agent_backup, mapping.system_path)
        print(f"Restored the original system directory from {agent_backup}")

    remove_path(mapping.repo_path)
    if repo_existed_before:
        ensure_dir(mapping.repo_path)

    print(f"Rollback finished for {mapping.name}.")


def setup_agent(mapping: AgentMapping, root: Path) -> None:
    repo_path = mapping.repo_path
    system_path = mapping.system_path
    agent_backup = backup_dir(root, mapping.name)

    repo_existed_before = repo_path.exists()
    system_existed_before = system_path.exists()
    system_entries = iter_entries(system_path) if system_existed_before else []

    print(f"== Setting up {mapping.name} ==")
    print(f"Repo folder:   {repo_path}")
    print(f"System folder: {system_path}")

    if system_existed_before:
        print(
            f"I found {len(system_entries)} item(s) in the current system directory: "
            f"{format_entry_names(system_entries)}"
        )
        print(f"I will back that directory up to {agent_backup}.")
        print(f"I will then copy it into {repo_path} and replace {system_path} with a symlink.")
    else:
        print("I did not find an existing system skills directory.")
        print(f"I will create an empty repo folder at {repo_path}.")
        print(f"I will then create {system_path} as a symlink back to the repo.")

    confirm_or_exit(f"Proceed with {mapping.name}?")

    try:
        if system_existed_before:
            print(f"Creating backup at {agent_backup}...")
            copy_directory(system_path, agent_backup)
            print("Backup created.")

            print(f"Copying the current system skills into {repo_path}...")
            copy_directory(system_path, repo_path)
            print("Import complete.")
        else:
            print(f"Creating an empty repo directory at {repo_path}...")
            recreate_empty_directory(repo_path)
            print("Empty repo directory created.")

        ensure_dir(system_path.parent)

        if system_existed_before:
            print(f"Removing the original system directory at {system_path}...")
            remove_path(system_path)
            print("Original system directory removed.")

        print(f"Creating a symlink from {system_path} to {repo_path}...")
        create_symlink(system_path, repo_path)

        if not system_path.is_symlink() or system_path.resolve() != repo_path.resolve():
            raise SetupError(
                f"Created {system_path}, but it does not point to {repo_path}."
            )

        print("Symlink created successfully.")
        print()
    except Exception as exc:
        print()
        print(f"Setup failed while working on {mapping.name}.")
        try:
            rollback_agent(
                mapping,
                root,
                repo_existed_before=repo_existed_before,
                system_existed_before=system_existed_before,
            )
        except Exception as rollback_exc:
            raise SetupError(
                f"Setup failed for {mapping.name}, and rollback also failed: {rollback_exc}"
            ) from exc
        raise


def print_failure_help(root: Path) -> None:
    readme_path = backup_readme_path(root)
    print(file=sys.stderr)
    print("Setup did not finish cleanly.", file=sys.stderr)
    print(
        f"Any backups that were created are under {backup_root(root)}.",
        file=sys.stderr,
    )
    print(
        f"Recovery instructions are in {readme_path}.",
        file=sys.stderr,
    )
    if not readme_path.exists():
        print(
            "That README was not written yet, which usually means the script stopped before any backup work began.",
            file=sys.stderr,
        )


def main() -> int:
    args = parse_args()
    root = repo_root()
    mappings = build_mappings(root)

    print_intro(root, mappings, dry_run=args.dry_run)

    problems = collect_preflight_problems(mappings)
    if problems:
        message_lines = [
            "Setup can only run when this repo has no pre-existing skills and none of the system skill paths are already symlinks.",
            "Remove these paths first:",
            "",
        ]
        message_lines.extend(f"- {problem}" for problem in problems)
        raise SetupError("\n".join(message_lines))

    write_backup_readme(root, mappings, dry_run=args.dry_run)

    if args.dry_run:
        print("Dry run summary:")
        for mapping in mappings:
            if mapping.system_path.exists():
                print(f"- {mapping.name}: would back up {mapping.system_path}")
                print(f"  would copy it into {mapping.repo_path}")
                print(f"  would replace {mapping.system_path} with a symlink to {mapping.repo_path}")
            else:
                print(f"- {mapping.name}: no existing system directory found")
                print(f"  would create an empty repo folder at {mapping.repo_path}")
                print(f"  would create a symlink at {mapping.system_path} -> {mapping.repo_path}")

        print()
        print("Dry run complete. No files were changed.")
        return 0

    print("This script will now work through each agent one at a time.")
    print("For each agent, it may create a backup, import the current system skills into this repo, and then swap the system path to a symlink.")
    print()
    confirm_or_exit("Start setup?")
    print()

    for mapping in mappings:
        setup_agent(mapping, root)

    print("Setup complete.")
    print(f"Backups are stored under {backup_root(root)}.")
    print("Keep those backups until you have confirmed everything is working.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:
        traceback.print_exc()
        print_failure_help(repo_root())
        raise SystemExit(1)
