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
    symlink_created: bool = False
    symlink_already_ok: bool = False
    copied: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    restored_pending: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class SetupError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Seed native coding-agent skill directories from this repo, "
            "then replace the repo agent folders with symlinks."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing same-name skills in the native agent directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without changing any files.",
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


def pending_dir(root: Path, agent_name: str) -> Path:
    return managed_root(root) / "pending" / agent_name


def staging_dir(root: Path, agent_name: str) -> Path:
    return managed_root(root) / "staging" / agent_name


def list_pending_entries(root: Path) -> List[Path]:
    pending_root = managed_root(root) / "pending"
    if not pending_root.exists():
        return []

    entries: List[Path] = []
    for agent_dir in sorted(pending_root.iterdir(), key=lambda p: p.name):
        if not agent_dir.is_dir():
            continue
        entries.extend(sorted(agent_dir.iterdir(), key=lambda p: p.name))
    return entries


def ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def remove_path(path: Path, dry_run: bool) -> None:
    if dry_run or not path.exists() and not path.is_symlink():
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


def copy_entry(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        return
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


def sync_entries(
    source_dir: Path,
    target_dir: Path,
    pending: Path,
    result: AgentResult,
    *,
    force: bool,
    dry_run: bool,
    label: str,
) -> None:
    if not source_dir.exists():
        return

    for entry in iter_entries(source_dir):
        target_entry = target_dir / entry.name
        pending_entry = pending / entry.name

        if target_entry.exists() or target_entry.is_symlink():
            if force:
                result.overwritten.append(entry.name)
                remove_path(target_entry, dry_run)
                copy_entry(entry, target_entry, dry_run)
                remove_path(pending_entry, dry_run)
            else:
                result.skipped.append(entry.name)
                ensure_dir(pending, dry_run)
                remove_path(pending_entry, dry_run)
                copy_entry(entry, pending_entry, dry_run)
                result.notes.append(
                    f"Skipped existing {label} '{entry.name}' and preserved the repo copy in "
                    f"{pending_entry}"
                )
            continue

        result.copied.append(entry.name)
        copy_entry(entry, target_entry, dry_run)
        remove_path(pending_entry, dry_run)


def restore_pending_entries(
    pending: Path,
    target_dir: Path,
    result: AgentResult,
    *,
    force: bool,
    dry_run: bool,
) -> None:
    if not pending.exists():
        return

    for entry in iter_entries(pending):
        target_entry = target_dir / entry.name
        if target_entry.exists() or target_entry.is_symlink():
            if force:
                result.restored_pending.append(entry.name)
                remove_path(target_entry, dry_run)
                copy_entry(entry, target_entry, dry_run)
                remove_path(entry, dry_run)
            else:
                result.notes.append(
                    f"Pending repo copy for '{entry.name}' is still preserved in {entry}"
                )
            continue

        result.restored_pending.append(entry.name)
        copy_entry(entry, target_entry, dry_run)
        remove_path(entry, dry_run)

    if dry_run:
        return

    for current in [pending, pending.parent]:
        try:
            current.rmdir()
        except OSError:
            break


def bootstrap_agent(
    mapping: AgentMapping,
    root: Path,
    *,
    force: bool,
    dry_run: bool,
) -> AgentResult:
    result = AgentResult(name=mapping.name)
    repo_path = mapping.repo_path
    system_path = mapping.system_path
    pending = pending_dir(root, mapping.name)
    staging = staging_dir(root, mapping.name)

    repo_exists = repo_path.exists() or repo_path.is_symlink()

    ensure_dir(system_path.parent, dry_run)
    ensure_dir(system_path, dry_run)

    if repo_path.is_symlink():
        target = repo_path.resolve()
        if target != system_path.resolve():
            raise SetupError(
                f"{repo_path} is already a symlink to {target}, expected {system_path}"
            )
        result.symlink_already_ok = True
        restore_pending_entries(
            pending,
            system_path,
            result,
            force=force,
            dry_run=dry_run,
        )
        return result

    staged_repo_contents = False
    original_repo_missing = not repo_exists
    staged_source: Path | None = None

    try:
        if repo_exists:
            if not repo_path.is_dir():
                raise SetupError(f"{repo_path} exists but is not a directory")
            remove_path(staging, dry_run)
            move_path(repo_path, staging, dry_run)
            staged_repo_contents = True
            staged_source = repo_path if dry_run else staging

        create_symlink(repo_path, system_path, dry_run)
        result.symlink_created = True

        if staged_repo_contents:
            sync_entries(
                staged_source,
                system_path,
                pending,
                result,
                force=force,
                dry_run=dry_run,
                label=f"{mapping.name} skill",
            )

        restore_pending_entries(
            pending,
            system_path,
            result,
            force=force,
            dry_run=dry_run,
        )

        if staged_repo_contents:
            remove_path(staging, dry_run)

        if original_repo_missing:
            result.notes.append("Created a new repo symlink because no repo folder existed yet.")

        return result
    except Exception as exc:
        if dry_run:
            raise

        if staged_repo_contents and staging.exists() and not repo_path.exists():
            try:
                move_path(staging, repo_path, dry_run=False)
            except Exception as rollback_exc:  # pragma: no cover - defensive cleanup
                raise SetupError(
                    f"{exc} (rollback also failed: {rollback_exc})"
                ) from rollback_exc
        raise


def print_plan(mapping: AgentMapping, result: AgentResult, *, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "DONE"
    print(f"[{mode}] {mapping.name}")
    print(f"  repo path:   {mapping.repo_path}")
    print(f"  system path: {mapping.system_path}")

    if result.symlink_created:
        print("  symlink: create repo folder symlink to system skills dir")
    if result.symlink_already_ok:
        print("  symlink: already configured")
    if result.copied:
        print(f"  copied: {', '.join(result.copied)}")
    if result.overwritten:
        print(f"  overwritten: {', '.join(result.overwritten)}")
    if result.restored_pending:
        print(f"  restored pending: {', '.join(result.restored_pending)}")
    if result.skipped:
        print(f"  skipped: {', '.join(result.skipped)}")
    for note in result.notes:
        print(f"  note: {note}")


def main() -> int:
    args = parse_args()
    root = repo_root()
    mappings = build_mappings(root)
    pending_before = list_pending_entries(root)

    if args.force and not pending_before:
        print(
            'Error: "--force" is only for a follow-up run after a normal setup created pending '
            "skipped skills.\n"
            "Run the setup once without --force first. If there are name collisions, the script "
            "will preserve the repo copies under .agent-skills-setup/pending/ and tell you to "
            're-run with "--force".',
            file=sys.stderr,
        )
        return 1

    any_skipped = False

    for mapping in mappings:
        result = bootstrap_agent(
            mapping,
            root,
            force=args.force,
            dry_run=args.dry_run,
        )
        print_plan(mapping, result, dry_run=args.dry_run)
        print()
        any_skipped = any_skipped or bool(result.skipped)

    if any_skipped:
        print(
            'Some same-name skills were skipped to avoid overwriting local system skills. '
            'Review them, then re-run this setup with "--force" if you want the repo versions '
            'to win and clear the pending copies.'
        )

    pending_after = list_pending_entries(root)

    if args.force and not args.dry_run and pending_after:
        print(
            "Error: --force completed but some pending skills still remain:\n"
            + "\n".join(f"  - {path}" for path in pending_after),
            file=sys.stderr,
        )
        return 1

    if args.force and args.dry_run and pending_before:
        print(
            "Dry run note: pending skills were detected, so a real --force run would attempt to "
            "apply them and clear the pending area."
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
