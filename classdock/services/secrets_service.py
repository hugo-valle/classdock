from typing import List, Optional, Tuple

from ..config.global_config import get_global_config
from ..utils import get_logger

logger = get_logger("services.secrets")


class SecretsService:
    """
    Service layer encapsulating secrets deployment logic.

    This class separates the business logic for preparing and deploying
    secrets from the CLI interface. It is intentionally small and testable.
    """

    def __init__(
        self, dry_run: bool = False, verbose: bool = False, secrets_manager_factory=None
    ):
        """
        Args:
            dry_run: If True, skip real API calls.
            verbose: Enable verbose logging.
            secrets_manager_factory: Optional callable ``(dry_run) ->
                GitHubSecretsManager``. Injecting a factory keeps this service
                testable without mocking deep import paths.
        """
        self.dry_run = dry_run
        self.verbose = verbose

        # When dry_run is True and no factory was supplied, use NullSecretsManager
        # so add_secrets doesn't need an explicit if self.dry_run guard.
        if secrets_manager_factory is not None:
            self._secrets_manager_factory = secrets_manager_factory
        elif dry_run:
            from ..secrets.github_secrets import NullSecretsManager

            self._secrets_manager_factory = lambda _: NullSecretsManager()
        else:
            self._secrets_manager_factory = None

    def add_secrets(
        self, repo_urls: Optional[List[str]] = None, force_update: bool = False
    ) -> Tuple[bool, str]:
        """
        Execute the secrets deployment flow using the global configuration.

        Args:
            repo_urls: Optional list of repository URLs to target. If None,
                auto-discovery will be attempted by the underlying manager.
            force_update: Force update secrets even if they already exist and are up to date.

        Returns:
            Tuple[bool, str]: (success, message). On success, success=True and
            message is informative. On failure, success=False and message contains an error.
        """
        target_repos = repo_urls

        try:
            if self._secrets_manager_factory is not None:
                # Either an injected test double or NullSecretsManager (dry_run=True).
                # Skip global_config checks so dry-run works without a loaded config.
                secrets_manager = self._secrets_manager_factory(self.dry_run)
            else:
                global_config = get_global_config()
                if not global_config:
                    return False, "Global configuration not loaded"

                if not global_config.secrets_config:
                    return False, "No secrets configuration found in assignment.conf"

                from ..secrets.github_secrets import GitHubSecretsManager

                secrets_manager = GitHubSecretsManager(dry_run=self.dry_run)
            # The GitHubSecretsManager implementation expects the argument
            # name `repo_urls` (not `repository_urls`) — pass the value
            # using the correct keyword to avoid TypeError.
            success = secrets_manager.add_secrets_from_global_config(
                repo_urls=target_repos, force_update=force_update
            )

            if not success:
                return False, "Secret management failed"

            return True, "Secret management completed successfully"

        except Exception as e:
            logger.error(f"SecretsService.add_secrets failed: {e}")
            return False, str(e)
