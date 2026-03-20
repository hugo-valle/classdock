"""
Centralized interactive prompt utilities.

Uses the Strategy Pattern to decouple TTY detection from prompt rendering.
Two concrete strategies are provided:

- InteractivePromptStrategy  — wraps questionary; used when stdin is a TTY.
- NonInteractivePromptStrategy — returns None/empty for every prompt; used in
  non-TTY environments (CI, pipes, tests).

``get_prompt_strategy()`` selects the right strategy automatically.
Callers may inject a custom strategy (e.g. in tests) via the module-level
``set_prompt_strategy()`` helper.
"""

import sys
from typing import Any, Callable, List, Optional

# ========================================================================================
# Abstract strategy interface
# ========================================================================================


class PromptStrategy:
    """
    Abstract base for all prompt strategies.

    Each method mirrors a public prompt function and should return the user's
    answer, or ``None`` when the strategy cannot (or should not) ask.
    """

    def select(self, message: str, choices: List[str]) -> Optional[str]:
        raise NotImplementedError

    def fuzzy(self, message: str, choices: List[str]) -> Optional[str]:
        raise NotImplementedError

    def text(
        self,
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], Any]] = None,
    ) -> Optional[str]:
        raise NotImplementedError

    def password(self, message: str) -> Optional[str]:
        raise NotImplementedError

    def confirm(self, message: str, default: bool = True) -> Optional[bool]:
        raise NotImplementedError

    def checkbox(self, message: str, choices: List[str]) -> Optional[List[str]]:
        raise NotImplementedError


# ========================================================================================
# Concrete: interactive (questionary)
# ========================================================================================


class InteractivePromptStrategy(PromptStrategy):
    """Prompt strategy backed by questionary (requires a real TTY)."""

    def select(self, message: str, choices: List[str]) -> Optional[str]:
        try:
            import questionary

            return questionary.select(message, choices=choices).ask()
        except (ImportError, KeyboardInterrupt):
            return None

    def fuzzy(self, message: str, choices: List[str]) -> Optional[str]:
        try:
            import questionary

            return questionary.autocomplete(message, choices=choices).ask()
        except (ImportError, KeyboardInterrupt):
            return None

    def text(
        self,
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], Any]] = None,
    ) -> Optional[str]:
        try:
            import questionary

            kwargs: dict = {"default": default}
            if validate:
                kwargs["validate"] = validate
            return questionary.text(message, **kwargs).ask()
        except (ImportError, KeyboardInterrupt):
            return None

    def password(self, message: str) -> Optional[str]:
        try:
            import questionary

            return questionary.password(message).ask()
        except (ImportError, KeyboardInterrupt):
            return None

    def confirm(self, message: str, default: bool = True) -> Optional[bool]:
        try:
            import questionary

            return questionary.confirm(message, default=default).ask()
        except (ImportError, KeyboardInterrupt):
            return None

    def checkbox(self, message: str, choices: List[str]) -> Optional[List[str]]:
        try:
            import questionary

            return questionary.checkbox(message, choices=choices).ask()
        except (ImportError, KeyboardInterrupt):
            return None


# ========================================================================================
# Concrete: non-interactive (fallback)
# ========================================================================================


class NonInteractivePromptStrategy(PromptStrategy):
    """
    Prompt strategy for non-TTY environments.

    Every method returns ``None`` (or the provided default where one is
    meaningful), so callers can detect and handle the non-interactive case.
    """

    def select(self, message: str, choices: List[str]) -> Optional[str]:
        return None

    def fuzzy(self, message: str, choices: List[str]) -> Optional[str]:
        return None

    def text(
        self,
        message: str,
        default: str = "",
        validate: Optional[Callable[[str], Any]] = None,
    ) -> Optional[str]:
        return None

    def password(self, message: str) -> Optional[str]:
        return None

    def confirm(self, message: str, default: bool = True) -> Optional[bool]:
        return None

    def checkbox(self, message: str, choices: List[str]) -> Optional[List[str]]:
        return None


# ========================================================================================
# Strategy factory and module-level state
# ========================================================================================


def _is_interactive() -> bool:
    """Return True when stdin is a real terminal."""
    return sys.stdin.isatty()


def get_prompt_strategy() -> PromptStrategy:
    """Return the appropriate strategy based on the current environment."""
    return (
        InteractivePromptStrategy()
        if _is_interactive()
        else NonInteractivePromptStrategy()
    )


# Module-level active strategy — resolved lazily on first call and replaceable
# via set_prompt_strategy() for testing or forced non-interactive mode.
_active_strategy: Optional[PromptStrategy] = None


def set_prompt_strategy(strategy: Optional[PromptStrategy]) -> None:
    """
    Override the active prompt strategy.

    Pass ``None`` to revert to automatic environment detection.
    Useful in tests and when a command explicitly needs non-interactive
    behaviour regardless of TTY state.
    """
    global _active_strategy
    _active_strategy = strategy


def _strategy() -> PromptStrategy:
    """Return the active strategy, resolving it lazily if not yet set."""
    return _active_strategy if _active_strategy is not None else get_prompt_strategy()


# ========================================================================================
# Public API — thin wrappers that delegate to the active strategy
# ========================================================================================


def prompt_select(message: str, choices: List[str]) -> Optional[str]:
    """Arrow-key selection menu. Returns None in non-TTY environments."""
    return _strategy().select(message, choices)


def prompt_fuzzy(message: str, choices: List[str]) -> Optional[str]:
    """Fuzzy-search selection menu. Returns None in non-TTY environments."""
    return _strategy().fuzzy(message, choices)


def prompt_text(
    message: str,
    default: str = "",
    validate: Optional[Callable[[str], Any]] = None,
) -> Optional[str]:
    """Text input prompt. Returns None in non-TTY environments."""
    return _strategy().text(message, default=default, validate=validate)


def prompt_password(message: str) -> Optional[str]:
    """Hidden password/token input. Returns None in non-TTY environments."""
    return _strategy().password(message)


def prompt_confirm(message: str, default: bool = True) -> Optional[bool]:
    """Yes/No confirmation prompt. Returns None in non-TTY environments."""
    return _strategy().confirm(message, default=default)


def prompt_checkbox(message: str, choices: List[str]) -> Optional[List[str]]:
    """Multi-select checkbox prompt. Returns None in non-TTY environments."""
    return _strategy().checkbox(message, choices)
