"""
Tests for the Chain of Responsibility pattern applied to GitHub error handling.

Verifies that:
- Each concrete handler correctly identifies errors it owns.
- analyze_github_exception dispatches to the right handler.
- Earlier handlers take priority over later ones.
- Unknown errors return the default analysis dict.
- The GITHUB_AVAILABLE=False path is handled before the chain.
"""

import pytest
from unittest.mock import patch

from classdock.utils.github_exceptions import (
    GitHubErrorAnalyzer,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNetworkError,
    GitHubDiscoveryError,
    BadCredentialsException,
    RateLimitExceededException,
    UnknownObjectException,
    _AuthenticationHandler,
    _RateLimitHandler,
    _NetworkHandler,
    _DiscoveryHandler,
    _UnknownObjectHandler,
    _ServerErrorHandler,
    _HANDLER_CHAIN,
)


# ---------------------------------------------------------------------------
# Individual handler: can_handle
# ---------------------------------------------------------------------------

class TestHandlerCanHandle:
    def test_auth_handler_matches_custom_auth_error(self):
        h = _AuthenticationHandler()
        assert h.can_handle(GitHubAuthenticationError("bad token"))

    def test_auth_handler_matches_bad_credentials(self):
        h = _AuthenticationHandler()
        assert h.can_handle(BadCredentialsException())

    def test_auth_handler_rejects_other_errors(self):
        h = _AuthenticationHandler()
        assert not h.can_handle(ValueError("nope"))

    def test_rate_limit_handler_matches_custom_rate_limit_error(self):
        h = _RateLimitHandler()
        assert h.can_handle(GitHubRateLimitError("too many"))

    def test_rate_limit_handler_matches_pyghub_exception(self):
        h = _RateLimitHandler()
        assert h.can_handle(RateLimitExceededException())

    def test_network_handler_matches_custom_network_error(self):
        h = _NetworkHandler()
        assert h.can_handle(GitHubNetworkError("timeout"))

    def test_network_handler_matches_timeout_string(self):
        h = _NetworkHandler()
        assert h.can_handle(Exception("connection refused"))

    def test_network_handler_rejects_unrelated_error(self):
        h = _NetworkHandler()
        assert not h.can_handle(ValueError("something else"))

    def test_discovery_handler_matches_discovery_error(self):
        h = _DiscoveryHandler()
        assert h.can_handle(GitHubDiscoveryError("org not found"))

    def test_unknown_object_handler_matches(self):
        h = _UnknownObjectHandler()
        assert h.can_handle(UnknownObjectException())

    def test_server_error_handler_matches_500(self):
        h = _ServerErrorHandler()
        err = Exception("server error")
        err.status = 500
        assert h.can_handle(err)

    def test_server_error_handler_rejects_404(self):
        h = _ServerErrorHandler()
        err = Exception("not found")
        err.status = 404
        assert not h.can_handle(err)


# ---------------------------------------------------------------------------
# analyze_github_exception dispatch
# (patch GITHUB_AVAILABLE=True so the chain runs in the test environment)
# ---------------------------------------------------------------------------

GITHUB_AVAILABLE_PATCH = "classdock.utils.github_exceptions.GITHUB_AVAILABLE"


class TestAnalyzeGithubException:
    def test_authentication_error_sets_flag(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                GitHubAuthenticationError("bad token"))
        assert result["is_authentication_error"] is True
        assert result["is_retryable"] is False

    def test_bad_credentials_sets_auth_flag(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                BadCredentialsException())
        assert result["is_authentication_error"] is True

    def test_rate_limit_error_is_retryable(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                GitHubRateLimitError("rate limit"))
        assert result["is_rate_limit_error"] is True
        assert result["is_retryable"] is True
        assert result["retry_delay"] is not None

    def test_network_error_is_retryable(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                GitHubNetworkError("timeout"))
        assert result["is_network_error"] is True
        assert result["is_retryable"] is True

    def test_discovery_error_is_not_retryable(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                GitHubDiscoveryError("org missing"))
        assert result["is_retryable"] is False

    def test_unknown_object_sets_action(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                UnknownObjectException())
        assert "resource exists" in result["suggested_action"].lower() or \
               "verify" in result["suggested_action"].lower()

    def test_server_error_is_retryable(self):
        err = Exception("internal server error")
        err.status = 503
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(err)
        assert result["is_retryable"] is True

    def test_unknown_error_returns_default_analysis(self):
        with patch(GITHUB_AVAILABLE_PATCH, True):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                ValueError("something random"))
        assert result["is_retryable"] is False
        assert result["is_authentication_error"] is False
        assert result["suggested_action"] == "Manual intervention required"

    def test_github_unavailable_short_circuits_chain(self):
        with patch(GITHUB_AVAILABLE_PATCH, False):
            result = GitHubErrorAnalyzer.analyze_github_exception(
                GitHubAuthenticationError("bad token"))
        # Should return the PyGithub-unavailable message, not auth-specific one
        assert "PyGithub" in result["suggested_action"] or \
               "Install" in result["suggested_action"]


# ---------------------------------------------------------------------------
# Chain ordering: auth before rate-limit
# ---------------------------------------------------------------------------

class TestChainOrdering:
    def test_auth_handler_precedes_rate_limit_in_chain(self):
        auth_idx = next(
            i for i, h in enumerate(_HANDLER_CHAIN)
            if isinstance(h, _AuthenticationHandler)
        )
        rate_idx = next(
            i for i, h in enumerate(_HANDLER_CHAIN)
            if isinstance(h, _RateLimitHandler)
        )
        assert auth_idx < rate_idx

    def test_rate_limit_handler_precedes_server_error_in_chain(self):
        rate_idx = next(
            i for i, h in enumerate(_HANDLER_CHAIN)
            if isinstance(h, _RateLimitHandler)
        )
        server_idx = next(
            i for i, h in enumerate(_HANDLER_CHAIN)
            if isinstance(h, _ServerErrorHandler)
        )
        assert rate_idx < server_idx

    def test_all_six_handlers_present(self):
        handler_types = {type(h) for h in _HANDLER_CHAIN}
        assert _AuthenticationHandler in handler_types
        assert _RateLimitHandler in handler_types
        assert _NetworkHandler in handler_types
        assert _DiscoveryHandler in handler_types
        assert _UnknownObjectHandler in handler_types
        assert _ServerErrorHandler in handler_types
