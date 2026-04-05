#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class AgentMapping:
    name: str
    repo_path: Path
    system_path: Path


@dataclass
class AgentResult:
    name: str
    already_configured: bool = False
    system_missing: bool = False
    symlink_created: bool = False
    backup_path: Path | None = None
    imported_system: List[str] = field(default_factory=list)
    starter_copied: List[str] = field(default_factory=list)
    conflicts_preserved: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class SetupError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import current system skill directories into this repo, back them up, "
            "then replace the system directories with symlinks to the repo."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview import, backup, merge, and symlink actions without changing files.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def build_mappings(root: Path) -> List[AgentMapping]:
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


def backup_dir(root: Path, agent_name: str) -> Path:
    return managed_root(root) / "backup" / agent_name


def conflicts_dir(root: Path, agent_name: str) -> Path:
    return managed_root(root) / "conflicts" / agent_name


def staging_dir(root: Path, agent_name: str) -> Path:
    return managed_root(root) / "staging" / agent_name


def ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def remove_path(path: Path, dry_run: bool) -> None:
    if dry_run or (not path.exists() and not path.is_symlink()):
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def move_path(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def copy_path(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def create_symlink(link_path: Path, target: Path, dry_run: bool) -> None:
    if dry_run:
        return
    link_path.symlink_to(target)


def iter_entries(path: Path) -> List[Path]:
    if not path.exists():
        return []
    return sorted(path.iterdir(), key=lambda p: p.name)


def entry_names(path: Path) -> List[str]:
    return [entry.name for entry in iter_entries(path)]


def describe_merge(
    repo_path: Path,
    system_path: Path,
    result: AgentResult,
    conflicts_path: Path,
) -> None:
    system_exists = system_path.exists()
    repo_entries = entry_names(repo_path)
    system_entries = entry_names(system_path)

    result.imported_system.extend(system_entries)

    system_entry_names = set(system_entries)
    for entry_name in repo_entries:
        if entry_name in system_entry_names:
            result.conflicts_preserved.append(entry_name)
        else:
            result.starter_copied.append(entry_name)

    if system_entries:
        result.notes.append(
            f"Import the current system skills into the repo before linking {system_path}."
        )
    elif system_exists:
        result.notes.append(
            f"{system_path} already exists but is empty. Setup will back it up and then link it "
            "to the repo folder."
        )
    else:
        result.notes.append(
            "No existing system skills directory was found. Setup will create an empty repo "
            "folder before linking the system path."
        )

    if result.conflicts_preserved:
        result.notes.append(
            f"Preserve conflicting repo skills under {conflicts_path} for later review."
        )


def merge_staged_repo(
    staged_repo: Path,
    live_repo: Path,
    conflicts_path: Path,
    result: AgentResult,
    *,
    dry_run: bool,
) -> None:
    if not staged_repo.exists():
        return

    for entry in iter_entries(staged_repo):
        live_entry = live_repo / entry.name
        conflict_entry = conflicts_path / entry.name

        if live_entry.exists() or live_entry.is_symlink():
            remove_path(conflict_entry, dry_run)
            ensure_dir(conflicts_path, dry_run)
            copy_path(entry, conflict_entry, dry_run)
            continue

        copy_path(entry, live_entry, dry_run)


def rollback_agent(
    repo_path: Path,
    system_path: Path,
    staging_path: Path,
    backup_path: Path,
    *,
    repo_existed_before: bool,
    system_removed: bool,
    system_symlink_created: bool,
    repo_rebuilt: bool,
) -> None:
    if system_removed or system_symlink_created:
        remove_path(system_path, dry_run=False)
        if backup_path.exists():
            copy_path(backup_path, system_path, dry_run=False)

    if repo_rebuilt:
        remove_path(repo_path, dry_run=False)

    if repo_existed_before and staging_path.exists():
        move_path(staging_path, repo_path, dry_run=False)


def bootstrap_agent(
    mapping: AgentMapping,
    root: Path,
    *,
    dry_run: bool,
) -> AgentResult:
    result = AgentResult(name=mapping.name)
    repo_path = mapping.repo_path
    system_path = mapping.system_path
    backup_path = backup_dir(root, mapping.name)
    conflicts_path = conflicts_dir(root, mapping.name)
    staging_path = staging_dir(root, mapping.name)

    if repo_path.is_symlink():
        raise SetupError(
            f"{repo_path} is a symlink. This setup expects repo-owned folders. "
            "Clone a fresh repo or replace the symlink with a real directory first."
        )

    if repo_path.exists() and not repo_path.is_dir():
        raise SetupError(f"{repo_path} exists but is not a directory")

    if system_path.is_symlink():
        if system_path.resolve() == repo_path.resolve():
            result.already_configured = True
            result.notes.append("System skills directory already points to this repo.")
            return result
        raise SetupError(
            f"{system_path} is already a symlink to {system_path.resolve()}, expected {repo_path}"
        )

    if system_path.exists() and not system_path.is_dir():
        raise SetupError(f"{system_path} exists but is not a directory")

    result.system_missing = not system_path.exists()
    if not result.system_missing:
        result.backup_path = backup_path

    describe_merge(repo_path, system_path, result, conflicts_path)
    result.symlink_created = True

    if result.backup_path is not None:
        result.notes.append(
            f"Keep the backup at {result.backup_path} until you verify setup worked."
        )

    if dry_run:
        return result

    repo_existed_before = repo_path.exists()
    system_removed = False
    system_symlink_created = False
    repo_rebuilt = False

    try:
        remove_path(staging_path, dry_run=False)
        if repo_existed_before:
            move_path(repo_path, staging_path, dry_run=False)

        repo_rebuilt = True
        if system_path.exists():
            remove_path(backup_path, dry_run=False)
            copy_path(system_path, backup_path, dry_run=False)
            copy_path(system_path, repo_path, dry_run=False)
        else:
            ensure_dir(repo_path, dry_run=False)

        if repo_existed_before:
            remove_path(conflicts_path, dry_run=False)
            merge_staged_repo(
                staging_path,
                repo_path,
                conflicts_path,
                result,
                dry_run=False,
            )
            remove_path(staging_path, dry_run=False)

        ensure_dir(system_path.parent, dry_run=False)
        if system_path.exists() or system_path.is_symlink():
            remove_path(system_path, dry_run=False)
            system_removed = True

        create_symlink(system_path, repo_path, dry_run=False)
        system_symlink_created = True
        return result
    except Exception as exc:
        rollback_agent(
            repo_path,
            system_path,
            staging_path,
            backup_path,
            repo_existed_before=repo_existed_before,
            system_removed=system_removed,
            system_symlink_created=system_symlink_created,
            repo_rebuilt=repo_rebuilt,
        )
        raise SetupError(f"Failed while setting up {mapping.name}: {exc}") from exc


def print_plan(mapping: AgentMapping, result: AgentResult, *, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "DONE"
    print(f"[{mode}] {mapping.name}")
    print(f"  repo path:   {mapping.repo_path}")
    print(f"  system path: {mapping.system_path}")

    if result.already_configured:
        print("  symlink: already configured")
    else:
        print("  symlink: replace system skills dir with a symlink to the repo folder")

    if result.backup_path is not None:
        verb = "create" if dry_run else "created"
        print(f"  backup: {verb} at {result.backup_path}")

    if result.imported_system:
        print(f"  imported system skills: {', '.join(result.imported_system)}")
    if result.starter_copied:
        print(f"  starter skills copied in: {', '.join(result.starter_copied)}")
    if result.conflicts_preserved:
        print(f"  repo conflicts preserved: {', '.join(result.conflicts_preserved)}")

    for note in result.notes:
        print(f"  note: {note}")


def main() -> int:
    args = parse_args()
    root = repo_root()
    mappings = build_mappings(root)
    any_conflicts = False

    for mapping in mappings:
        result = bootstrap_agent(mapping, root, dry_run=args.dry_run)
        print_plan(mapping, result, dry_run=args.dry_run)
        print()
        any_conflicts = any_conflicts or bool(result.conflicts_preserved)

    if any_conflicts:
        print(
            "Some repo starter skills were preserved under .agent-skills-setup/conflicts/. "
            "Review them manually or with a coding agent after setup."
        )

    if args.dry_run:
        print("Dry run complete. No files were changed.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SetupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
