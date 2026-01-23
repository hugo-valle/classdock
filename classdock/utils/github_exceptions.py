"""
GitHub API Exception Handling and Resilience System.

This module provides comprehensive error handling, retry logic, and resilience
patterns for GitHub API operations across the ClassDock project. It includes
custom exception classes, retry decorators with exponential backoff, rate limiting
handling, and network resilience patterns.

Key Features:
- Hierarchical exception classes for different error types
- Automatic retry logic with exponential backoff
- GitHub API rate limiting detection and handling
- Network timeout and connection error recovery
- Authentication failure detection and token refresh
- Comprehensive logging and error reporting
- Graceful degradation for non-critical operations

Usage:
    from classdock.utils.github_exceptions import (
        github_api_retry, GitHubAPIError, handle_github_errors
    )
    
    @github_api_retry(max_attempts=3)
    def fetch_repositories(github_client):
        # GitHub API calls with automatic retry
        return github_client.get_organization("org").get_repos()
"""

import time
import logging
import random
from functools import wraps
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime

# Try to import GitHub-specific exceptions
try:
    from github import GithubException, RateLimitExceededException, BadCredentialsException
    from github import UnknownObjectException, GithubIntegrationException
    GITHUB_AVAILABLE = True
except ImportError:
    # Create placeholder classes for when PyGithub is not available
    class GithubException(Exception):
        """Placeholder for GitHub exception when PyGithub not available."""
        pass

    class RateLimitExceededException(GithubException):
        """Placeholder for rate limit exception."""
        pass

    class BadCredentialsException(GithubException):
        """Placeholder for bad credentials exception."""
        pass

    class UnknownObjectException(GithubException):
        """Placeholder for unknown object exception."""
        pass

    class GithubIntegrationException(GithubException):
        """Placeholder for integration exception."""
        pass

    GITHUB_AVAILABLE = False

logger = logging.getLogger("utils.github_exceptions")


# ========================================================================================
# Core Exception Hierarchy
# ========================================================================================

class GitHubAPIError(Exception):
    """
    Base exception for all GitHub API related errors.

    Provides common functionality for error tracking, logging, and context information
    that can be used across all GitHub API operations in the project.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None,
                 error_code: Optional[str] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error
        self.error_code = error_code
        self.retry_after = retry_after
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        base_msg = f"GitHub API Error: {self.message}"
        if self.error_code:
            base_msg += f" (Code: {self.error_code})"
        if self.original_error:
            base_msg += f" | Original: {self.original_error}"
        return base_msg


class GitHubAuthenticationError(GitHubAPIError):
    """
    Raised when GitHub authentication fails.

    This includes invalid tokens, expired tokens, insufficient permissions,
    and authentication method failures. Provides specific context for
    authentication troubleshooting.
    """

    def __init__(self, message: str, token_type: Optional[str] = None,
                 permissions_required: Optional[List[str]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.token_type = token_type
        self.permissions_required = permissions_required or []


class GitHubRateLimitError(GitHubAPIError):
    """
    Raised when GitHub API rate limits are exceeded.

    Includes information about rate limit reset times and provides
    automatic retry scheduling information.
    """

    def __init__(self, message: str, reset_time: Optional[datetime] = None,
                 remaining_requests: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.reset_time = reset_time
        self.remaining_requests = remaining_requests

        # Calculate retry_after based on reset_time
        if reset_time and not kwargs.get('retry_after'):
            self.retry_after = max(
                1, int((reset_time - datetime.now()).total_seconds()))


class GitHubRepositoryError(GitHubAPIError):
    """
    Raised when repository operations fail.

    This includes repository not found, access denied, repository creation
    failures, and other repository-specific operations.
    """

    def __init__(self, message: str, repository_name: Optional[str] = None,
                 operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.repository_name = repository_name
        self.operation = operation


class GitHubNetworkError(GitHubAPIError):
    """
    Raised when network-related GitHub API operations fail.

    This includes timeouts, connection errors, DNS failures, and other
    network-related issues that may be temporary.
    """

    def __init__(self, message: str, is_timeout: bool = False,
                 is_connection_error: bool = False, **kwargs):
        super().__init__(message, **kwargs)
        self.is_timeout = is_timeout
        self.is_connection_error = is_connection_error


class GitHubDiscoveryError(GitHubAPIError):
    """
    Raised when repository discovery operations fail.

    This includes organization scanning failures, repository filtering issues,
    and classroom URL parsing problems.
    """

    def __init__(self, message: str, organization: Optional[str] = None,
                 assignment_prefix: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.organization = organization
        self.assignment_prefix = assignment_prefix


# ========================================================================================
# Retry Configuration and State Management
# ========================================================================================

@dataclass
class RetryConfig:
    """Configuration for retry logic and resilience patterns."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    respect_rate_limits: bool = True
    timeout_seconds: float = 30.0

    # Exception types that should trigger retries
    retryable_exceptions: tuple = (
        GitHubRateLimitError,
        GitHubNetworkError,
        ConnectionError,
        TimeoutError,
    )

    # Exception types that should never be retried
    non_retryable_exceptions: tuple = (
        GitHubAuthenticationError,
    )


@dataclass
class RetryState:
    """State tracking for retry operations."""

    attempt: int = 0
    total_delay: float = 0.0
    last_error: Optional[Exception] = None
    start_time: datetime = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


# ========================================================================================
# Error Context and Analysis
# ========================================================================================

class GitHubErrorAnalyzer:
    """
    Analyzes GitHub API errors to provide context and recovery suggestions.

    This class examines GitHub API errors and provides intelligent analysis
    including error categorization, recovery suggestions, and retry recommendations.
    """

    @staticmethod
    def analyze_github_exception(error: Exception) -> Dict[str, Any]:
        """
        Analyze a GitHub API exception and provide structured information.

        Args:
            error: The exception to analyze

        Returns:
            Dictionary containing error analysis including type, category,
            retry recommendation, and recovery suggestions.
        """
        analysis = {
            'error_type': type(error).__name__,
            'is_retryable': False,
            'is_authentication_error': False,
            'is_rate_limit_error': False,
            'is_network_error': False,
            'suggested_action': 'Manual intervention required',
            'retry_delay': None,
            'recovery_suggestions': []
        }

        if not GITHUB_AVAILABLE:
            analysis['suggested_action'] = 'Install PyGithub library'
            analysis['recovery_suggestions'].append('pip install PyGithub')
            return analysis

        # Check for our custom exception types first
        if isinstance(error, GitHubAuthenticationError):
            analysis.update({
                'is_authentication_error': True,
                'suggested_action': 'Check authentication credentials',
                'recovery_suggestions': [
                    'Verify GitHub token is correct and not expired',
                    'Check token permissions include required scopes',
                    'Regenerate GitHub token if necessary'
                ]
            })
            return analysis

        elif isinstance(error, GitHubRateLimitError):
            analysis.update({
                'is_retryable': True,
                'is_rate_limit_error': True,
                'suggested_action': 'Wait for rate limit reset',
                'retry_delay': getattr(error, 'retry_after', 3600),
                'recovery_suggestions': [
                    'Wait for rate limit to reset',
                    'Use a different authentication token',
                    'Implement request batching to reduce API calls'
                ]
            })
            return analysis

        elif isinstance(error, GitHubNetworkError):
            analysis.update({
                'is_retryable': True,
                'is_network_error': True,
                'suggested_action': 'Retry with exponential backoff',
                'retry_delay': 5,
                'recovery_suggestions': [
                    'Check internet connection',
                    'Retry the operation',
                    'Check GitHub status page for service issues'
                ]
            })
            return analysis

        elif isinstance(error, GitHubDiscoveryError):
            analysis.update({
                'is_retryable': False,  # Discovery errors usually require parameter fixes
                'suggested_action': 'Check discovery parameters and configuration',
                'recovery_suggestions': [
                    'Verify assignment prefix and organization parameters',
                    'Check configuration file for required settings',
                    'Ensure GitHub API access is properly configured'
                ]
            })
            return analysis

        # Analyze specific GitHub exception types
        if isinstance(error, RateLimitExceededException):
            analysis.update({
                'is_retryable': True,
                'is_rate_limit_error': True,
                'suggested_action': 'Wait for rate limit reset',
                'retry_delay': getattr(error, 'retry_after', 3600),
                'recovery_suggestions': [
                    'Wait for rate limit to reset',
                    'Use a different authentication token',
                    'Implement request batching to reduce API calls'
                ]
            })

        elif isinstance(error, BadCredentialsException):
            analysis.update({
                'is_authentication_error': True,
                'suggested_action': 'Check authentication credentials',
                'recovery_suggestions': [
                    'Verify GitHub token is correct and not expired',
                    'Check token permissions include required scopes',
                    'Regenerate GitHub token if necessary'
                ]
            })

        elif isinstance(error, UnknownObjectException):
            analysis.update({
                'suggested_action': 'Verify resource exists and permissions',
                'recovery_suggestions': [
                    'Check that the repository/organization exists',
                    'Verify you have access to the requested resource',
                    'Check spelling of organization/repository names'
                ]
            })

        elif 'timeout' in str(error).lower() or 'connection' in str(error).lower():
            analysis.update({
                'is_retryable': True,
                'is_network_error': True,
                'suggested_action': 'Retry with exponential backoff',
                'retry_delay': 5,
                'recovery_suggestions': [
                    'Check internet connection',
                    'Retry the operation',
                    'Check GitHub status page for service issues'
                ]
            })

        elif hasattr(error, 'status') and error.status >= 500:
            analysis.update({
                'is_retryable': True,
                'suggested_action': 'Retry due to server error',
                'retry_delay': 10,
                'recovery_suggestions': [
                    'Retry the operation (server error)',
                    'Check GitHub status page',
                    'Reduce request frequency'
                ]
            })

        return analysis

    @staticmethod
    def should_retry(error: Exception, attempt: int, max_attempts: int) -> bool:
        """
        Determine if an error should trigger a retry.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-based)
            max_attempts: Maximum number of attempts allowed

        Returns:
            True if the operation should be retried, False otherwise.
        """
        if attempt >= max_attempts:
            return False

        analysis = GitHubErrorAnalyzer.analyze_github_exception(error)
        return analysis['is_retryable']

    @staticmethod
    def calculate_delay(attempt: int, config: RetryConfig) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.

        Args:
            attempt: Current attempt number (1-based)
            config: Retry configuration

        Returns:
            Delay in seconds before next retry attempt.
        """
        # Exponential backoff: base_delay * (exponential_base ^ (attempt - 1))
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))

        # Cap at maximum delay
        delay = min(delay, config.max_delay)

        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


# ========================================================================================
# Retry Decorators and Context Managers
# ========================================================================================

def github_api_retry(max_attempts: int = 3, base_delay: float = 1.0,
                     max_delay: float = 60.0, respect_rate_limits: bool = True):
    """
    Decorator that adds retry logic with exponential backoff to GitHub API functions.

    This decorator automatically retries failed GitHub API calls with intelligent
    error analysis, exponential backoff, and rate limit handling.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds between retries
        respect_rate_limits: Whether to respect GitHub rate limit headers

    Returns:
        Decorated function with retry logic

    Example:
        @github_api_retry(max_attempts=5, base_delay=2.0)
        def fetch_repositories(github_client, org_name):
            return github_client.get_organization(org_name).get_repos()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                respect_rate_limits=respect_rate_limits
            )
            state = RetryState()

            for attempt in range(1, max_attempts + 1):
                state.attempt = attempt

                try:
                    logger.debug(
                        f"Attempting {func.__name__} (attempt {attempt}/{max_attempts})")
                    result = func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt}")

                    return result

                except Exception as error:
                    state.last_error = error

                    # Analyze the error
                    analysis = GitHubErrorAnalyzer.analyze_github_exception(
                        error)

                    # Check if we should retry
                    should_retry = GitHubErrorAnalyzer.should_retry(
                        error, attempt, max_attempts)

                    if not should_retry or attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {attempt} attempts: {error}")

                        # Convert to appropriate custom exception
                        if analysis['is_rate_limit_error']:
                            raise GitHubRateLimitError(
                                f"Rate limit exceeded in {func.__name__}",
                                original_error=error
                            )
                        elif analysis['is_authentication_error']:
                            raise GitHubAuthenticationError(
                                f"Authentication failed in {func.__name__}",
                                original_error=error
                            )
                        elif analysis['is_network_error']:
                            raise GitHubNetworkError(
                                f"Network error in {func.__name__}",
                                original_error=error
                            )
                        else:
                            raise GitHubAPIError(
                                f"GitHub API error in {func.__name__}",
                                original_error=error
                            )

                    # Calculate delay for next attempt
                    delay = GitHubErrorAnalyzer.calculate_delay(
                        attempt, config)

                    # Use error-specific delay if available
                    if analysis.get('retry_delay'):
                        delay = max(delay, analysis['retry_delay'])

                    state.total_delay += delay

                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {error}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

            # This should never be reached, but just in case
            raise GitHubAPIError(
                f"{func.__name__} exhausted all retry attempts")

        return wrapper
    return decorator


class github_api_context:
    """
    Context manager for GitHub API operations with comprehensive error handling.

    Provides structured error handling, logging, and cleanup for GitHub API
    operations that need more control than the decorator approach.

    Example:
        with github_api_context("fetch repositories") as ctx:
            repos = github_client.get_organization("org").get_repos()
            ctx.success(f"Found {len(list(repos))} repositories")
    """

    def __init__(self, operation_name: str, logger_instance: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.start_time = None
        self.errors = []

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(
            f"Starting GitHub API operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time

        if exc_type is None:
            self.logger.debug(
                f"GitHub API operation completed: {self.operation_name} "
                f"(Duration: {duration.total_seconds():.2f}s)"
            )
        else:
            self.logger.error(
                f"GitHub API operation failed: {self.operation_name} "
                f"(Duration: {duration.total_seconds():.2f}s) - {exc_val}"
            )

            # Analyze the error and potentially convert it
            if GITHUB_AVAILABLE and isinstance(exc_val, GithubException):
                analysis = GitHubErrorAnalyzer.analyze_github_exception(
                    exc_val)
                self.logger.info(
                    f"Error analysis: {analysis['suggested_action']}")

                for suggestion in analysis['recovery_suggestions']:
                    self.logger.info(f"Recovery suggestion: {suggestion}")

        return False  # Don't suppress exceptions

    def success(self, message: str):
        """Log a success message for the operation."""
        self.logger.info(f"{self.operation_name}: {message}")

    def warning(self, message: str):
        """Log a warning message for the operation."""
        self.logger.warning(f"{self.operation_name}: {message}")

    def error(self, message: str, error: Optional[Exception] = None):
        """Log an error message for the operation."""
        self.logger.error(f"{self.operation_name}: {message}")
        if error:
            self.errors.append(error)


# ========================================================================================
# Utility Functions
# ========================================================================================

def handle_github_errors(func: Callable) -> Callable:
    """
    Simplified decorator for basic GitHub error handling without retry logic.

    This decorator converts GitHub exceptions to custom exceptions but does not
    implement retry logic. Useful for operations where retry is not appropriate.

    Args:
        func: Function to wrap with error handling

    Returns:
        Wrapped function with error conversion
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            analysis = GitHubErrorAnalyzer.analyze_github_exception(error)

            if analysis['is_rate_limit_error']:
                raise GitHubRateLimitError(
                    f"Rate limit exceeded in {func.__name__}",
                    original_error=error
                )
            elif analysis['is_authentication_error']:
                raise GitHubAuthenticationError(
                    f"Authentication failed in {func.__name__}",
                    original_error=error
                )
            elif analysis['is_network_error']:
                raise GitHubNetworkError(
                    f"Network error in {func.__name__}",
                    original_error=error
                )
            else:
                raise GitHubAPIError(
                    f"GitHub API error in {func.__name__}",
                    original_error=error
                )

    return wrapper


def is_github_available() -> bool:
    """
    Check if PyGithub library is available for GitHub API operations.

    Returns:
        True if PyGithub is available, False otherwise.
    """
    return GITHUB_AVAILABLE


def log_github_error_summary(errors: List[Exception], operation: str):
    """
    Log a summary of GitHub API errors for batch operations.

    Args:
        errors: List of exceptions that occurred
        operation: Name of the operation that generated errors
    """
    if not errors:
        return

    logger.error(
        f"GitHub API operation '{operation}' encountered {len(errors)} errors:")

    error_counts = {}
    for error in errors:
        error_type = type(error).__name__
        error_counts[error_type] = error_counts.get(error_type, 0) + 1

    for error_type, count in error_counts.items():
        logger.error(f"  {error_type}: {count} occurrences")

    # Log first few errors in detail
    for i, error in enumerate(errors[:3]):
        logger.error(f"  Example error {i+1}: {error}")

    if len(errors) > 3:
        logger.error(f"  ... and {len(errors) - 3} more errors")


# ========================================================================================
# Backwards Compatibility
# ========================================================================================

# For backwards compatibility with existing code
GitHubAuthenticationError = GitHubAuthenticationError
RepositoryDiscoveryError = GitHubDiscoveryError

# Export commonly used functions and classes
__all__ = [
    'GitHubAPIError',
    'GitHubAuthenticationError',
    'GitHubRateLimitError',
    'GitHubRepositoryError',
    'GitHubNetworkError',
    'GitHubDiscoveryError',
    'RetryConfig',
    'RetryState',
    'GitHubErrorAnalyzer',
    'github_api_retry',
    'github_api_context',
    'handle_github_errors',
    'is_github_available',
    'log_github_error_summary',
    'RepositoryDiscoveryError',  # Backwards compatibility
]
