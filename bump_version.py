#!/usr/bin/env python3
"""
Bump semantic version from the latest v* git tag and create the new tag.

Usage:
  python bump_version.py [major|minor|patch] [--push] [--dry-run]

Examples:
  python bump_version.py patch        # 1.2.3 -> 1.2.4, tag v1.2.4
  python bump_version.py minor --push # 1.2.3 -> 1.3.0, tag v1.3.0, then push
  python bump_version.py major --dry-run  # Show what would happen only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=check,
        cwd=Path(__file__).resolve().parent,
    )


def get_latest_tag() -> str | None:
    """Return the latest tag matching v* (semver), or None if none exist."""
    result = run("git", "tag", "-l", "v*", "--sort=-version:refname", check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    first = result.stdout.strip().splitlines()[0]
    return first.strip()


def parse_version(tag: str) -> tuple[int, int, int]:
    """Parse vX.Y.Z or X.Y.Z into (major, minor, patch)."""
    s = tag.lstrip("v").strip()
    parts = s.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    return (major, minor, patch)


def fmt_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def bump(major: int, minor: int, patch: int, kind: str) -> tuple[int, int, int]:
    if kind == "major":
        return (major + 1, 0, 0)
    if kind == "minor":
        return (major, minor + 1, 0)
    if kind == "patch":
        return (major, minor, patch + 1)
    raise ValueError(f"Unknown bump kind: {kind}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Bump semver from latest v* tag and create the new tag.",
    )
    ap.add_argument(
        "bump",
        choices=["major", "minor", "patch"],
        help="Which component to increment",
    )
    ap.add_argument(
        "--push",
        action="store_true",
        help="Push the new tag to origin after creating it",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be done; do not create or push tags",
    )
    args = ap.parse_args()

    latest = get_latest_tag()
    if latest is None:
        major, minor, patch = 0, 0, 0
        print("No v* tags found. Starting from 0.0.0.")
    else:
        major, minor, patch = parse_version(latest)
        print(f"Latest tag: {latest} -> {fmt_version(major, minor, patch)}")

    nu = bump(major, minor, patch, args.bump)
    new_ver = fmt_version(*nu)
    new_tag = f"v{new_ver}"
    print(f"Bump {args.bump}: {fmt_version(major, minor, patch)} -> {new_ver}")
    print(f"New tag: {new_tag}")

    if args.dry_run:
        print("(dry-run: not creating or pushing tag)")
        return 0

    run("git", "tag", new_tag)
    print(f"Created tag {new_tag}.")

    if args.push:
        run("git", "push", "origin", new_tag)
        print(f"Pushed {new_tag} to origin.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
