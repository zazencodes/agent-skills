#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from setup_symlinks import build_mappings, remove_path, repo_root


@dataclass
class CleanupResult:
    name: str
    repo_path: Path
    removed: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class CleanupError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Remove starter skills from the repo-owned agent folders before first setup. "
            "This script refuses to run after those folders become live symlink targets."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview which starter skills would be removed without changing files.",
    )
    return parser.parse_args()


def clear_agent(repo_path: Path, *, name: str, dry_run: bool) -> CleanupResult:
    result = CleanupResult(name=name, repo_path=repo_path)

    if repo_path.is_symlink():
        raise CleanupError(
            f"{repo_path} is a symlink. Run clear_repo_skills.py only before setup."
        )

    if repo_path.exists() and not repo_path.is_dir():
        raise CleanupError(f"{repo_path} exists but is not a directory")

    if not repo_path.exists():
        result.notes.append("Repo folder is missing. Nothing to remove.")
        return result

    entries = sorted(repo_path.iterdir(), key=lambda p: p.name)
    result.removed.extend(entry.name for entry in entries)

    if not entries:
        result.notes.append("Repo folder is already empty.")
        return result

    if dry_run:
        return result

    for entry in entries:
        remove_path(entry, dry_run=False)

    return result


def print_plan(result: CleanupResult, *, dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "DONE"
    print(f"[{mode}] {result.name}")
    print(f"  repo path: {result.repo_path}")

    if result.removed:
        label = "would remove" if dry_run else "removed"
        print(f"  {label}: {', '.join(result.removed)}")

    for note in result.notes:
        print(f"  note: {note}")


def main() -> int:
    args = parse_args()
    mappings = build_mappings(repo_root())

    for mapping in mappings:
        if mapping.repo_path.is_symlink():
            raise CleanupError(
                f"{mapping.repo_path} is a symlink. Run clear_repo_skills.py only before setup."
            )

    for mapping in mappings:
        result = clear_agent(mapping.repo_path, name=mapping.name, dry_run=args.dry_run)
        print_plan(result, dry_run=args.dry_run)
        print()

    if args.dry_run:
        print("Dry run complete. No files were changed.")
    else:
        print("Starter skill cleanup complete. Run python3 setup_symlinks.py next.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CleanupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
