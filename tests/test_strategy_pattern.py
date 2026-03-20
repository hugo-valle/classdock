"""
Tests for the Strategy Pattern applied to interactive prompts.

Verifies that:
- NonInteractivePromptStrategy returns None/default for every prompt type.
- InteractivePromptStrategy delegates to questionary (mocked).
- get_prompt_strategy() selects the right concrete strategy.
- set_prompt_strategy() overrides the active strategy and None reverts it.
- Module-level prompt_* functions delegate to the active strategy.
"""

import pytest
from unittest.mock import MagicMock, patch

import classdock.utils.prompt as prompt_module
from classdock.utils.prompt import (
    NonInteractivePromptStrategy,
    InteractivePromptStrategy,
    get_prompt_strategy,
    set_prompt_strategy,
    prompt_select,
    prompt_fuzzy,
    prompt_text,
    prompt_password,
    prompt_confirm,
    prompt_checkbox,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_strategy():
    """Reset the module-level strategy to auto-detect after each test."""
    set_prompt_strategy(None)


# ---------------------------------------------------------------------------
# NonInteractivePromptStrategy
# ---------------------------------------------------------------------------

class TestNonInteractivePromptStrategy:
    def setup_method(self):
        self.s = NonInteractivePromptStrategy()

    def test_select_returns_none(self):
        assert self.s.select("Pick one", ["a", "b"]) is None

    def test_fuzzy_returns_none(self):
        assert self.s.fuzzy("Search", ["x", "y"]) is None

    def test_text_returns_none(self):
        assert self.s.text("Enter text", default="default") is None

    def test_password_returns_none(self):
        assert self.s.password("Enter password") is None

    def test_confirm_returns_none(self):
        assert self.s.confirm("Are you sure?") is None

    def test_checkbox_returns_none(self):
        assert self.s.checkbox("Select items", ["a", "b", "c"]) is None


# ---------------------------------------------------------------------------
# InteractivePromptStrategy (questionary mocked)
# ---------------------------------------------------------------------------

class TestInteractivePromptStrategy:
    def setup_method(self):
        self.s = InteractivePromptStrategy()

    def _mock_questionary(self, method_name, return_value):
        """Return a context manager that patches questionary.<method_name>."""
        fake_question = MagicMock()
        fake_question.ask.return_value = return_value
        fake_q = MagicMock()
        getattr(fake_q, method_name).return_value = fake_question
        return patch.dict("sys.modules", {"questionary": fake_q})

    def test_select_delegates_to_questionary(self):
        with self._mock_questionary("select", "b") as ctx:
            result = self.s.select("Pick one", ["a", "b"])
        assert result == "b"

    def test_fuzzy_delegates_to_questionary(self):
        with self._mock_questionary("autocomplete", "x"):
            result = self.s.fuzzy("Search", ["x", "y"])
        assert result == "x"

    def test_text_delegates_to_questionary(self):
        with self._mock_questionary("text", "hello"):
            result = self.s.text("Enter text")
        assert result == "hello"

    def test_password_delegates_to_questionary(self):
        with self._mock_questionary("password", "s3cr3t"):
            result = self.s.password("Token")
        assert result == "s3cr3t"

    def test_confirm_delegates_to_questionary(self):
        with self._mock_questionary("confirm", True):
            result = self.s.confirm("Are you sure?")
        assert result is True

    def test_checkbox_delegates_to_questionary(self):
        with self._mock_questionary("checkbox", ["a", "c"]):
            result = self.s.checkbox("Choose", ["a", "b", "c"])
        assert result == ["a", "c"]

    def test_import_error_returns_none(self):
        with patch.dict("sys.modules", {"questionary": None}):
            result = self.s.select("Pick", ["a"])
        assert result is None

    def test_keyboard_interrupt_returns_none(self):
        fake_q = MagicMock()
        fake_q.select.side_effect = KeyboardInterrupt
        with patch.dict("sys.modules", {"questionary": fake_q}):
            result = self.s.select("Pick", ["a"])
        assert result is None


# ---------------------------------------------------------------------------
# get_prompt_strategy factory
# ---------------------------------------------------------------------------

class TestGetPromptStrategy:
    def test_returns_interactive_when_tty(self):
        with patch("classdock.utils.prompt._is_interactive", return_value=True):
            s = get_prompt_strategy()
        assert isinstance(s, InteractivePromptStrategy)

    def test_returns_non_interactive_when_not_tty(self):
        with patch("classdock.utils.prompt._is_interactive", return_value=False):
            s = get_prompt_strategy()
        assert isinstance(s, NonInteractivePromptStrategy)


# ---------------------------------------------------------------------------
# set_prompt_strategy and module-level delegation
# ---------------------------------------------------------------------------

class TestModuleLevelPrompts:
    def teardown_method(self):
        _reset_strategy()

    def test_set_strategy_overrides_tty_detection(self):
        fake = MagicMock(spec=NonInteractivePromptStrategy)
        fake.select.return_value = "injected"
        set_prompt_strategy(fake)
        result = prompt_select("Pick", ["a", "b"])
        assert result == "injected"
        fake.select.assert_called_once_with("Pick", ["a", "b"])

    def test_set_strategy_none_reverts_to_auto(self):
        set_prompt_strategy(NonInteractivePromptStrategy())
        set_prompt_strategy(None)
        # After reset, strategy is chosen based on actual TTY state — just
        # verify no exception is raised and a strategy is returned.
        import classdock.utils.prompt as m
        assert m._strategy() is not None

    def test_prompt_text_delegates(self):
        fake = MagicMock(spec=NonInteractivePromptStrategy)
        fake.text.return_value = "answer"
        set_prompt_strategy(fake)
        result = prompt_text("Enter", default="d")
        fake.text.assert_called_once_with("Enter", default="d", validate=None)
        assert result == "answer"

    def test_prompt_password_delegates(self):
        fake = MagicMock(spec=NonInteractivePromptStrategy)
        fake.password.return_value = "secret"
        set_prompt_strategy(fake)
        assert prompt_password("Token") == "secret"

    def test_prompt_confirm_delegates(self):
        fake = MagicMock(spec=NonInteractivePromptStrategy)
        fake.confirm.return_value = False
        set_prompt_strategy(fake)
        assert prompt_confirm("Sure?", default=True) is False

    def test_prompt_checkbox_delegates(self):
        fake = MagicMock(spec=NonInteractivePromptStrategy)
        fake.checkbox.return_value = ["x"]
        set_prompt_strategy(fake)
        assert prompt_checkbox("Choose", ["x", "y"]) == ["x"]

    def test_non_interactive_strategy_used_in_non_tty(self):
        # Force non-interactive strategy and verify all prompts return None
        set_prompt_strategy(NonInteractivePromptStrategy())
        assert prompt_select("A", ["a"]) is None
        assert prompt_fuzzy("B", ["b"]) is None
        assert prompt_text("C") is None
        assert prompt_password("D") is None
        assert prompt_confirm("E") is None
        assert prompt_checkbox("F", ["f"]) is None
