"""Config command group."""

from typing import Optional

import typer

from ..utils import setup_logging, get_logger
from ._helpers import get_global_options

logger = get_logger("cli")

config_app = typer.Typer(help="Configuration and token management commands")


@config_app.callback()
def config_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
):
    """Configuration and token management commands."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


@config_app.command("set-token")
def config_set_token(
    token: str = typer.Argument(..., help="GitHub Personal Access Token (classic or fine-grained)"),
    expires_at: Optional[str] = typer.Option(
        None, "--expires-at", "-e",
        help="Token expiration date in ISO format (e.g., '2026-10-19T00:00:00+00:00')"),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Force update even if existing token is valid"),
):
    """
    Update the GitHub Personal Access Token used for API operations.

    This command validates and saves a new GitHub token to the token configuration file.
    The token is validated for required scopes and expiration before being saved.

    Required token scopes:
    - repo (Full control of private repositories)
    - read:org (Read organization data)

    Examples:
        classdock config set-token ghp_YourNewTokenHere
        classdock config set-token ghp_YourToken --expires-at "2026-10-19T00:00:00+00:00"
        classdock config set-token ghp_YourNewTokenHere --force

    Generate tokens at: https://github.com/settings/tokens
    """
    setup_logging()

    try:
        from ..utils.token_manager import GitHubTokenManager
        from ..utils.github_classroom_api import GitHubClassroomAPI

        logger.info("🔑 Updating GitHub Personal Access Token...")

        if not token.startswith(('ghp_', 'github_pat_')):
            logger.warning("⚠️ Token doesn't start with 'ghp_' or 'github_pat_'")
            logger.warning("This might not be a valid GitHub token format")
            if not force:
                from ..utils.prompt import prompt_confirm
                result = prompt_confirm("Continue anyway?", default=False)
                if result is None:
                    result = typer.confirm("Continue anyway?", default=False)
                if not result:
                    logger.info("Token update cancelled")
                    raise typer.Exit(0)

        if not force:
            logger.info("Validating token...")
            api_client = GitHubClassroomAPI(token)

            expiration_info = api_client.check_token_expiration()

            if expiration_info.get('is_expired'):
                logger.error("❌ Token has already expired!")
                logger.error(f"Expired on: {expiration_info.get('expires_at', 'unknown date')}")
                logger.error("Please generate a new token at: https://github.com/settings/tokens")
                raise typer.Exit(1)

            if not expiration_info.get('is_valid'):
                error_msg = expiration_info.get('error', 'Unknown error')
                logger.error(f"❌ Token validation failed: {error_msg}")
                raise typer.Exit(1)

            if expiration_info.get('days_remaining') is not None:
                days = expiration_info['days_remaining']
                if days <= 7:
                    logger.warning(f"⚠️ Token expires in {days} days!")
                elif days <= 30:
                    logger.info(f"ℹ️ Token expires in {days} days")
                else:
                    logger.info(f"✓ Token valid for {days} more days")
            else:
                logger.info("✓ Token is valid (classic token with no expiration)")

            scope_info = api_client.validate_token_scopes()

            if not scope_info.get('valid'):
                logger.error("❌ Token validation failed")
                raise typer.Exit(1)

            scopes = scope_info.get('scopes', [])
            logger.info(f"Token scopes: {', '.join(scopes) if scopes else 'none'}")

            if not scope_info.get('has_repo'):
                logger.warning("⚠️ Token lacks 'repo' scope - some operations may fail")
            else:
                logger.info("✓ Token has 'repo' scope")

            if not scope_info.get('has_read_org'):
                logger.warning("⚠️ Token lacks 'read:org' scope - organization access may be limited")
            else:
                logger.info("✓ Token has 'read:org' or 'admin:org' scope")

            if not scope_info.get('has_repo') or not scope_info.get('has_read_org'):
                logger.warning("")
                logger.warning("⚠️ IMPORTANT: This token is missing critical scopes!")
                logger.warning("You may experience authorization failures.")
                logger.warning("")
                logger.warning("Required scopes:")
                logger.warning("  ✓ repo - Full control of private repositories")
                logger.warning("  ✓ read:org - Read organization data")
                logger.warning("")
                from ..utils.prompt import prompt_confirm as _pconfirm
                _save = _pconfirm("Do you want to save this token anyway?", default=False)
                if _save is None:
                    _save = typer.confirm("Do you want to save this token anyway?", default=False)
                if not _save:
                    logger.info("Token update cancelled")
                    raise typer.Exit(0)

        validated_expires_at = None
        if expires_at:
            try:
                from datetime import datetime
                datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                validated_expires_at = expires_at
                logger.info(f"✓ Expiration date set to: {expires_at}")
            except ValueError as e:
                logger.error(f"❌ Invalid date format: {e}")
                logger.error("Expected ISO format: YYYY-MM-DDTHH:MM:SS+00:00")
                raise typer.Exit(1)

        token_manager = GitHubTokenManager()

        scopes_to_save = None
        if not force:
            scopes_to_save = scope_info.get('scopes', [])

        success = token_manager.save_token(
            token,
            expires_at=validated_expires_at,
            scopes=scopes_to_save,
        )

        if not success:
            logger.error("❌ Failed to save token")
            raise typer.Exit(1)

        logger.info("")
        logger.info("✅ Token updated successfully!")
        logger.info(f"Token saved to: {token_manager.config_file}")
        logger.info("")
        logger.info("You can now use classdock commands with the new token.")

    except Exception as e:
        logger.error(f"Failed to update token: {e}")
        raise typer.Exit(1)


@config_app.command("check-token")
def config_check_token(ctx: typer.Context):
    """
    Check the current GitHub token status, expiration, and scopes.

    This command validates the currently configured token and displays:
    - Token validity status
    - Expiration date (for fine-grained tokens)
    - Days until expiration
    - Configured scopes
    - Warnings for missing required scopes

    Example:
        classdock config check-token
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would check GitHub token status")
        return

    try:
        from ..utils.token_manager import GitHubTokenManager
        from ..utils.github_classroom_api import GitHubClassroomAPI

        logger.info("🔍 Checking GitHub token status...")
        logger.info("")

        token_manager = GitHubTokenManager()
        token = token_manager.get_github_token()

        if not token:
            logger.error("❌ No GitHub token found!")
            logger.error("")
            logger.error("To set a token:")
            logger.error("  classdock config set-token <your-token>")
            logger.error("")
            logger.error("Generate tokens at: https://github.com/settings/tokens")
            raise typer.Exit(1)

        api_client = GitHubClassroomAPI(token)

        logger.info("📅 Token Expiration:")
        expiration_info = api_client.check_token_expiration()

        if expiration_info.get('is_expired'):
            expires_at = expiration_info.get('expires_at')
            days_past = abs(expiration_info.get('days_remaining', 0))

            logger.error("  ❌ Token has EXPIRED!")
            if expires_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%B %d, %Y at %I:%M %p %Z')
                    logger.error(f"  Expired on: {formatted_date}")
                except Exception:
                    logger.error(f"  Expired on: {expires_at}")

                if days_past > 0:
                    logger.error(f"  ({days_past} day{'s' if days_past != 1 else ''} ago)")
            else:
                logger.error("  Expiration date: Not available in token config")
            logger.error("")
            logger.error("🔧 To fix:")
            logger.error("  1. Generate new token: https://github.com/settings/tokens")
            logger.error("  2. Update token: classdock config set-token <new-token>")
            raise typer.Exit(1)

        if not expiration_info.get('is_valid'):
            error_msg = expiration_info.get('error', 'Unknown error')
            logger.error(f"  ❌ Token is invalid: {error_msg}")
            raise typer.Exit(1)

        if expiration_info.get('days_remaining') is not None:
            days = expiration_info['days_remaining']
            exp_at = expiration_info.get('expires_at', 'unknown')
            if days <= 7:
                logger.warning(f"  ⚠️ Expires in {days} days (on {exp_at})")
                logger.warning("  Consider generating a new token soon!")
            elif days <= 30:
                logger.info(f"  ⏰ Expires in {days} days (on {exp_at})")
            else:
                logger.info(f"  ✓ Valid for {days} more days (until {exp_at})")
            logger.info(f"  Token type: {expiration_info.get('token_type', 'unknown')}")
        else:
            logger.info("  ✓ Token is valid")

            stored_expiration = None
            try:
                import json
                if token_manager.config_file.exists():
                    with open(token_manager.config_file, 'r') as f:
                        config_data = json.load(f)
                        stored_expiration = config_data.get('github_token', {}).get('expires_at')
            except Exception as e:
                logger.debug(f"Could not read stored expiration: {e}")

            if stored_expiration:
                try:
                    from datetime import datetime, timezone
                    expires_dt = datetime.fromisoformat(stored_expiration.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    days_remaining = (expires_dt - now).days
                    formatted_date = expires_dt.strftime('%B %d, %Y at %I:%M %p %Z')

                    if days_remaining < 0:
                        logger.error(f"  ❌ Token expired on: {formatted_date}")
                        logger.error(f"  ({abs(days_remaining)} days ago)")
                    elif days_remaining <= 7:
                        logger.warning(f"  ⚠️ Expires in {days_remaining} days")
                        logger.warning(f"  Expiration date: {formatted_date}")
                        logger.warning("  Consider generating a new token soon!")
                    elif days_remaining <= 30:
                        logger.info(f"  ⏰ Expires in {days_remaining} days")
                        logger.info(f"  Expiration date: {formatted_date}")
                    else:
                        logger.info(f"  ✓ Valid for {days_remaining} more days")
                        logger.info(f"  Expiration date: {formatted_date}")

                    logger.info("  Token type: classic (expiration set manually)")
                except Exception as e:
                    logger.debug(f"Could not parse stored expiration date: {e}")
                    logger.info(f"  Expiration date (manually set): {stored_expiration}")
                    logger.info("  Token type: classic")
            else:
                logger.info("  Token type: classic (no expiration set)")
                logger.warning("  ⚠️ Consider setting an expiration date for tracking:")
                logger.warning("     classdock config set-token <token> --expires-at <date>")

        logger.info("")

        logger.info("🔐 Token Scopes:")
        scope_info = api_client.validate_token_scopes()

        if not scope_info.get('valid'):
            logger.error("  ❌ Could not validate token scopes")
            raise typer.Exit(1)

        scopes = scope_info.get('scopes', [])
        if scopes:
            logger.info(f"  Configured scopes: {', '.join(scopes)}")
        else:
            logger.warning("  ⚠️ No scopes found (this is unusual)")

        logger.info("")
        logger.info("📋 Required Scopes Check:")

        if scope_info.get('has_repo'):
            logger.info("  ✓ repo - Full control of private repositories")
        else:
            logger.error("  ❌ repo - MISSING! (Required for repository operations)")

        if scope_info.get('has_read_org'):
            logger.info("  ✓ read:org - Read organization data")
        else:
            logger.error("  ❌ read:org - MISSING! (Required for organization access)")

        logger.info("")

        if scope_info.get('has_repo') and scope_info.get('has_read_org'):
            logger.info("✅ Token is properly configured with all required scopes!")
        else:
            logger.warning("⚠️ Token is missing some required scopes")
            logger.warning("Some operations may fail with authorization errors")
            logger.warning("")
            logger.warning("To fix:")
            logger.warning("  1. Generate new token with required scopes")
            logger.warning("  2. Update: classdock config set-token <new-token>")

    except Exception as e:
        logger.error(f"Failed to check token: {e}")
        raise typer.Exit(1)
