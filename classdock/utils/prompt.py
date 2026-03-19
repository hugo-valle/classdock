"""
Centralized interactive prompt utilities.

Wraps questionary for consistent, styled prompts across the CLI.
Degrades gracefully in non-TTY environments by returning None.
"""

import sys
from typing import Optional, List, Callable, Any


def _is_interactive() -> bool:
    """Return True when stdin is a real terminal."""
    return sys.stdin.isatty()


def prompt_select(message: str, choices: List[str]) -> Optional[str]:
    """Arrow-key selection menu. Returns None in non-TTY environments."""
    if not _is_interactive():
        return None
    try:
        import questionary
        return questionary.select(message, choices=choices).ask()
    except (ImportError, KeyboardInterrupt):
        return None


def prompt_fuzzy(message: str, choices: List[str]) -> Optional[str]:
    """Fuzzy-search selection menu. Returns None in non-TTY environments."""
    if not _is_interactive():
        return None
    try:
        import questionary
        return questionary.autocomplete(message, choices=choices).ask()
    except (ImportError, KeyboardInterrupt):
        return None


def prompt_text(
    message: str,
    default: str = "",
    validate: Optional[Callable[[str], Any]] = None,
) -> Optional[str]:
    """Text input prompt. Returns None in non-TTY environments."""
    if not _is_interactive():
        return None
    try:
        import questionary
        kwargs: dict = {"default": default}
        if validate:
            kwargs["validate"] = validate
        return questionary.text(message, **kwargs).ask()
    except (ImportError, KeyboardInterrupt):
        return None


def prompt_password(message: str) -> Optional[str]:
    """Hidden password/token input. Returns None in non-TTY environments."""
    if not _is_interactive():
        return None
    try:
        import questionary
        return questionary.password(message).ask()
    except (ImportError, KeyboardInterrupt):
        return None


def prompt_confirm(message: str, default: bool = True) -> Optional[bool]:
    """Yes/No confirmation prompt. Returns None in non-TTY environments."""
    if not _is_interactive():
        return None
    try:
        import questionary
        return questionary.confirm(message, default=default).ask()
    except (ImportError, KeyboardInterrupt):
        return None


def prompt_checkbox(message: str, choices: List[str]) -> Optional[List[str]]:
    """Multi-select checkbox prompt. Returns None in non-TTY environments."""
    if not _is_interactive():
        return None
    try:
        import questionary
        return questionary.checkbox(message, choices=choices).ask()
    except (ImportError, KeyboardInterrupt):
        return None
