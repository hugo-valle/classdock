"""
Shared CLI helpers used by multiple command modules.
"""

from pathlib import Path
from typing import List, Optional

import typer

from ..utils import get_logger

logger = get_logger("cli")


def get_global_options(ctx: typer.Context) -> tuple[bool, bool]:
    """Return (verbose, dry_run) from the root context."""
    root_ctx = ctx.find_root()
    return (
        root_ctx.obj.get('verbose', False) if root_ctx.obj else False,
        root_ctx.obj.get('dry_run', False) if root_ctx.obj else False,
    )


def load_student_repos(file_path: str = "student-repos.txt") -> List[str]:
    """Load student repository URLs from file."""
    repo_file = Path(file_path)
    if not repo_file.exists():
        raise FileNotFoundError(f"Repository file not found: {file_path}")

    repos = []
    with open(repo_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                repos.append(line)
    return repos


def select_student_repo_interactive(repos: List[str]) -> Optional[str]:
    """Interactively select a repository from a list."""
    import sys

    if not repos:
        return None

    if sys.stdin.isatty():
        from ..utils.prompt import prompt_select
        choices = [repo.split('/')[-1] + "  (" + repo + ")" for repo in repos]
        choices.append("Cancel")
        result = prompt_select("Select a student repository:", choices)
        if result is None or result == "Cancel":
            logger.info("Cancelled")
            return None
        for repo in repos:
            if repo in result:
                logger.info(f"Selected: {repo.split('/')[-1]}")
                return repo
        return None

    # Non-TTY fallback
    print("\n📚 Available student repositories:\n")
    for i, repo in enumerate(repos, 1):
        student_name = repo.split('/')[-1]
        print(f"  {i}. {student_name}")
        print(f"     {repo}")
    print("  0. Cancel")

    while True:
        try:
            choice = input("\n👉 Select a repository (enter number): ").strip()
            if not choice:
                continue
            choice_num = int(choice)
            if choice_num == 0:
                print("❌ Cancelled")
                return None
            if 1 <= choice_num <= len(repos):
                selected = repos[choice_num - 1]
                print(f"✅ Selected: {selected.split('/')[-1]}")
                return selected
            print(f"⚠️  Please enter a number between 0 and {len(repos)}")
        except ValueError:
            print("⚠️  Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return None
