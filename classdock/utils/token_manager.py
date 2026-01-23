#!/usr/bin/env python3
"""
Enhanced GitHub Token Management with Expiration Tracking
Follows industry best practices for secure token storage and lifecycle management.
"""

import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
import platform
import subprocess

from ..utils import get_logger

logger = get_logger("utils.token_manager")


class GitHubTokenManager:
    """
    Manages GitHub tokens with multiple storage options and comprehensive metadata.

    Priority order: 
    1. Config file (most control - expiration, type, scopes metadata)
    2. System keychain (OS-specific secure storage)  
    3. Environment variable (basic fallback)
    4. Interactive setup (if no token found)
    """

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "classdock"
        self.config_file = self.config_dir / "token_config.json"

    def get_github_token(self):
        """Get GitHub token with fallback strategy and expiration check.

        The lookup priority is:
        1. User config file (~/.config/classdock/token_config.json)
        2. System keychain (OS-specific secure storage)
        3. Environment variable GITHUB_TOKEN
        4. Interactive setup (prompts the user)

        Returns:
            Optional[str]: The GitHub token string when available, otherwise None.

        Notes:
            Callers should handle a None return value which indicates there is no
            token available and interactive setup may be required.
        """

        # 1. Check user config file first (most control and metadata)
        token_data = self._get_token_from_config()
        if token_data:
            logger.info("🔑 Using GitHub token from config file")
            self._check_expiration_warning(token_data)
            return token_data['token']

        # 2. Check system keychain (OS-specific, secure storage)
        token = self._get_token_from_keychain()
        if token:
            logger.info("🔑 Using GitHub token from system keychain")
            return token

        # 3. Check environment variable (fallback, basic storage)
        token = os.getenv('GITHUB_TOKEN')
        if token:
            logger.info("🔑 Using GitHub token from environment variable")
            token_data = self._verify_and_get_token_info(token)
            if token_data:
                self._check_expiration_warning(token_data)
            return token  # Return token even if verification failed

        # 4. No token found - guide user through setup
        logger.error("❌ No GitHub token found")
        return None  # Let caller handle the setup

    def save_token(self, token, expires_at=None, scopes=None):
        """
        Save a GitHub token to the config file with metadata.

        Args:
            token (str): The GitHub Personal Access Token
            expires_at (str, optional): ISO format expiration date (e.g., "2026-10-19T00:00:00+00:00")
                                       If provided, this OVERRIDES any expiration from GitHub API
            scopes (list, optional): List of token scopes

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Verify token is valid
            token_data = self._verify_and_get_token_info(token)
            if not token_data:
                logger.error("Failed to verify token")
                return False

            # IMPORTANT: Override expires_at if provided by user
            # This allows manual expiration tracking for classic tokens
            if expires_at:
                token_data['expires_at'] = expires_at
                # Mark that this was manually set
                token_data['expires_at_source'] = 'manual'
                logger.debug(
                    f"Using manually provided expiration: {expires_at}")
            elif token_data.get('expires_at'):
                # Mark that this came from GitHub API
                token_data['expires_at_source'] = 'github_api'
                logger.debug(
                    f"Using GitHub API expiration: {token_data['expires_at']}")
            else:
                # No expiration available
                token_data['expires_at_source'] = 'none'
                logger.debug("No expiration date available")

            # Override scopes if provided
            if scopes:
                token_data['scopes'] = scopes

            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Prepare config data
            config_data = {
                'github_token': token_data,
                'stored_at': datetime.now(timezone.utc).isoformat(),
                'storage_type': 'config_file'
            }

            # Write to config file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Set restrictive permissions (owner read/write only)
            self.config_file.chmod(0o600)

            logger.debug(f"Token saved to: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False

    def setup_new_token(self):
        """Guide user through setting up a new GitHub token.

        This interactive helper verifies the provided token against the GitHub
        API, optionally collects expiration metadata, and stores the token in
        the user's preferred secure location (env, keychain, or config file).

        Returns:
            Optional[str]: The saved token string on success, or None if the
            user aborted the setup.
        """
        from ..utils.ui_components import print_colored, Colors

        print_colored("🔐 GitHub Token Setup Required", Colors.CYAN)
        print_colored(
            "\nTo use classdock, you need a GitHub Personal Access Token.", "")
        print_colored("\n📋 Required token permissions:", Colors.YELLOW)
        print_colored("  • repo (full control of repositories)", "")
        print_colored(
            "  • read:org (read organization membership)", "")
        print_colored("  • admin:repo_hook (repository hooks)", "")
        print_colored(
            "  • workflow (update GitHub Actions workflows)", "")

        print_colored("\n🔗 Create a token at:", Colors.CYAN)
        print_colored("  https://github.com/settings/tokens", "")
        print_colored("💡 Type 'q' or 'quit' to exit", Colors.CYAN)

        while True:
            print_colored(
                "\n🔑 Enter your GitHub token (q to quit): ", Colors.GREEN, end="")

            try:
                token = input().strip()
            except (EOFError, KeyboardInterrupt):
                print_colored(
                    "\n� Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                return None

            # Handle quit commands
            if token.lower() in ['q', 'quit', 'exit']:
                print_colored(
                    "👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                return None

            # Clean up common issues with token input
            token = token.strip('\'"')  # Remove surrounding quotes
            token = token.replace(' ', '')  # Remove any spaces

            if not token:
                print_colored("❌ Token cannot be empty", Colors.RED)
                print_colored(
                    "💡 Type 'q' to quit if you need to exit", Colors.YELLOW)
                continue

            # Basic token format validation
            if not (token.startswith('ghp_') or token.startswith('github_pat_')):
                print_colored(
                    "⚠️ Token should start with 'ghp_' (classic) or 'github_pat_' (fine-grained)", Colors.YELLOW)
                proceed = input("Continue anyway? (y/n/q): ").strip().lower()
                if proceed == 'q':
                    print_colored(
                        "👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                    return None
                if proceed != 'y':
                    continue

            # Verify the token
            logger.debug(f"Verifying token: {token[:10]}...")
            token_data = self._verify_and_get_token_info(token)
            if token_data:
                print_colored("✅ Token verified successfully!", Colors.GREEN)
                logger.debug(
                    f"Token type: {token_data.get('token_type')}, expires_at: {token_data.get('expires_at')}")

                # For classic tokens, ask for expiration date if not provided by API
                if token_data.get('token_type') == 'classic' and not token_data.get('expires_at'):
                    print_colored(
                        "ℹ️ Classic token detected - API doesn't provide expiration info", Colors.CYAN)
                    token_data['expires_at'] = self._ask_token_expiration()
                elif token_data.get('token_type') == 'fine-grained':
                    print_colored(
                        "ℹ️ Fine-grained token detected - expiration tracked automatically", Colors.GREEN)

                # Ask where to store it
                storage_choice = self._ask_storage_preference()
                self._store_token(token, token_data, storage_choice)
                return token
            else:
                print_colored(
                    "❌ Token verification failed. Please check your token.", Colors.RED)
                retry = input("🔄 Try again? (y/n/q): ").strip().lower()
                if retry == 'q':
                    print_colored(
                        "👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                    return None
                if retry != 'y':
                    return None

    def _verify_and_get_token_info(self, token):
        """Verify token and get metadata including expiration."""
        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }

            # Get user info to verify token works
            user_response = requests.get(
                'https://api.github.com/user', headers=headers, timeout=10)
            if user_response.status_code != 200:
                logger.error(
                    f"Token verification failed: {user_response.status_code}")
                if user_response.status_code == 401:
                    logger.error(
                        "❌ Authentication failed - token may be invalid or expired")
                elif user_response.status_code == 403:
                    logger.error(
                        "❌ Forbidden - token may lack required permissions")
                logger.debug(f"Response: {user_response.text}")
                return None

            # Get token expiration info (different headers for different token types)
            token_expires = None
            if token.startswith('github_pat_'):
                # Fine-grained tokens use github-authentication-token-expiration header
                expires_header = user_response.headers.get(
                    'github-authentication-token-expiration')
                if expires_header:
                    try:
                        # Parse the expiration date format: "2026-05-31 00:00:00 -0600"
                        import re
                        # Remove timezone info for parsing, then add UTC
                        date_part = re.sub(r'\s[-+]\d{4}$', '', expires_header)
                        parsed_date = datetime.strptime(
                            date_part, '%Y-%m-%d %H:%M:%S')
                        token_expires = parsed_date.replace(
                            tzinfo=timezone.utc).isoformat()
                    except Exception as e:
                        logger.debug(
                            f"Failed to parse fine-grained token expiration: {e}")
                        token_expires = expires_header  # Store raw value if parsing fails
            else:
                # Classic tokens use X-OAuth-Token-Expires header (rarely populated)
                token_expires = user_response.headers.get(
                    'X-OAuth-Token-Expires')

            # Get token scopes (different for classic vs fine-grained tokens)
            if token.startswith('github_pat_'):
                # Fine-grained tokens - check permissions via different method
                scopes = self._get_fine_grained_permissions(headers)
            else:
                # Classic tokens - use X-OAuth-Scopes header
                scopes_header = user_response.headers.get('X-OAuth-Scopes', '')
                scopes = [scope.strip()
                          for scope in scopes_header.split(',') if scope.strip()]

            # Debug logging for scope parsing
            logger.debug(
                f"Token type: {'fine-grained' if token.startswith('github_pat_') else 'classic'}")
            logger.debug(f"Parsed scopes: {scopes}")

            user_data = user_response.json()

            # Create comprehensive token data structure
            token_data = {
                'token': token,
                'verified_at': datetime.now(timezone.utc).isoformat(),
                'username': user_data.get('login'),
                'user_type': user_data.get('type'),
                'user_id': user_data.get('id'),
                'scopes': scopes,
                'expires_at': token_expires,
                'rate_limit_remaining': user_response.headers.get('X-RateLimit-Remaining'),
                'rate_limit_limit': user_response.headers.get('X-RateLimit-Limit'),
                'rate_limit_reset': user_response.headers.get('X-RateLimit-Reset'),
                'token_type': self._detect_token_type(scopes, user_data, token),
                # Additional user information
                'user_info': {
                    'name': user_data.get('name'),
                    'email': user_data.get('email'),
                    'company': user_data.get('company'),
                    'public_repos': user_data.get('public_repos'),
                    'private_repos': user_data.get('total_private_repos'),
                    'plan': user_data.get('plan', {}).get('name') if user_data.get('plan') else None
                },
                # API response headers for debugging
                'api_headers': {
                    'server': user_response.headers.get('server'),
                    'x-github-media-type': user_response.headers.get('x-github-media-type'),
                    'x-github-enterprise-version': user_response.headers.get('x-github-enterprise-version'),
                    'github-authentication-token-expiration': user_response.headers.get('github-authentication-token-expiration'),
                    'x-oauth-token-expires': user_response.headers.get('X-OAuth-Token-Expires'),
                    'x-oauth-scopes': user_response.headers.get('X-OAuth-Scopes')
                }
            }

            return token_data

        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    def _detect_token_type(self, scopes, user_data, token):
        """Detect if token is classic or fine-grained."""
        # Check token prefix first (most reliable)
        if token.startswith('github_pat_'):
            return 'fine-grained'
        elif token.startswith('ghp_'):
            return 'classic'

        # Fallback to scope-based detection
        if 'contents:read' in scopes or 'metadata:read' in scopes:
            return 'fine-grained'
        elif 'repo' in scopes:
            return 'classic'
        else:
            return 'unknown'

    def _get_fine_grained_permissions(self, headers):
        """Get permissions for fine-grained tokens by testing API access."""
        permissions = []
        permission_details = {}

        # Test repository access (equivalent to 'repo' scope)
        try:
            response = requests.get(
                'https://api.github.com/user/repos', headers=headers, timeout=10)
            if response.status_code == 200:
                permissions.append('repo')
                permission_details['repo'] = {
                    'status': 'granted', 'tested_endpoint': '/user/repos'}
            else:
                permission_details['repo'] = {
                    'status': 'denied', 'code': response.status_code}
        except Exception as e:
            permission_details['repo'] = {'status': 'error', 'error': str(e)}

        # Test organization access (equivalent to 'read:org' scope)
        try:
            response = requests.get(
                'https://api.github.com/user/orgs', headers=headers, timeout=10)
            if response.status_code == 200:
                permissions.append('read:org')
                permission_details['read:org'] = {
                    'status': 'granted', 'tested_endpoint': '/user/orgs'}
            else:
                permission_details['read:org'] = {
                    'status': 'denied', 'code': response.status_code}
        except Exception as e:
            permission_details['read:org'] = {
                'status': 'error', 'error': str(e)}

        # Test webhook/admin access (equivalent to 'admin:repo_hook' scope)
        try:
            response = requests.get(
                'https://api.github.com/user/repos?type=owner&per_page=1', headers=headers, timeout=10)
            if response.status_code == 200:
                repos = response.json()
                if repos and len(repos) > 0:
                    repo_full_name = repos[0]['full_name']
                    # Test webhook access on the first owned repo
                    webhook_response = requests.get(
                        f'https://api.github.com/repos/{repo_full_name}/hooks', headers=headers, timeout=10)
                    if webhook_response.status_code == 200:
                        permissions.append('admin:repo_hook')
                        permission_details['admin:repo_hook'] = {
                            'status': 'granted', 'tested_repo': repo_full_name}
                    else:
                        permission_details['admin:repo_hook'] = {
                            'status': 'denied', 'code': webhook_response.status_code}
        except Exception as e:
            permission_details['admin:repo_hook'] = {
                'status': 'error', 'error': str(e)}

        # Test actions/workflow access
        try:
            response = requests.get(
                'https://api.github.com/user/repos?type=owner&per_page=1', headers=headers, timeout=10)
            if response.status_code == 200:
                repos = response.json()
                if repos and len(repos) > 0:
                    repo_full_name = repos[0]['full_name']
                    # Test actions access
                    actions_response = requests.get(
                        f'https://api.github.com/repos/{repo_full_name}/actions/workflows', headers=headers, timeout=10)
                    if actions_response.status_code == 200:
                        permissions.append('workflow')
                        permission_details['workflow'] = {
                            'status': 'granted', 'tested_repo': repo_full_name}
                    else:
                        permission_details['workflow'] = {
                            'status': 'denied', 'code': actions_response.status_code}
        except Exception as e:
            permission_details['workflow'] = {
                'status': 'error', 'error': str(e)}

        # Store detailed permission info for debugging
        logger.debug(
            f"Fine-grained token permission details: {permission_details}")

        return permissions

    def _check_expiration_warning(self, token_data):
        """Check token expiration and warn user if needed."""
        expires_at = token_data.get('expires_at')
        token_type = token_data.get('token_type', 'unknown')

        if not expires_at:
            if token_type == 'classic':
                logger.info(
                    "ℹ️ Token expiration info not available (classic token - consider adding expiration date)")
            else:
                logger.info("ℹ️ Token expiration info not available")
            return

        try:
            expiry_date = datetime.fromisoformat(
                expires_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_until_expiry = (expiry_date - now).days

            if days_until_expiry <= 7:
                logger.warning(
                    f"⚠️ Token expires in {days_until_expiry} days!")
                logger.warning("Consider renewing your token soon.")
            elif days_until_expiry <= 30:
                logger.info(f"ℹ️ Token expires in {days_until_expiry} days")

        except Exception as e:
            logger.debug(f"Could not parse expiration date: {e}")

    def _get_token_from_keychain(self):
        """Get token from system keychain."""
        try:
            if platform.system() == 'Darwin':  # macOS
                result = subprocess.run([
                    'security', 'find-generic-password',
                    '-s', 'classdock-github-token',
                    '-w'
                ], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Keychain access failed: {e}")
        return None

    def _get_token_from_config(self):
        """Get token from user config file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('github_token')
        except Exception as e:
            logger.debug(f"Config file access failed: {e}")
        return None

    def _ask_storage_preference(self):
        """Ask user where to store the token."""
        from ..utils.ui_components import print_colored, Colors

        print_colored(
            "\n💾 Where would you like to store your token?", Colors.CYAN)
        print_colored("1. Environment variable", "")
        print_colored("2. System keychain (macOS only)", "")
        print_colored(
            "3. Config file (~/.config/classdock/) (recommended)", "")

        while True:
            choice = input("\nEnter choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            print_colored("❌ Please enter 1, 2, or 3", Colors.RED)

    def _ask_token_expiration(self):
        """Ask user for token expiration date (for classic tokens)."""
        from ..utils.ui_components import print_colored, Colors

        print_colored(
            "\n📅 Classic tokens don't provide expiration info via API.", Colors.YELLOW)
        print_colored(
            "Please enter the expiration date you set when creating the token.", Colors.CYAN)
        print_colored("(This helps track when to renew your token)", "")

        while True:
            expiry_input = input(
                "\n📅 Enter expiration date (YYYY-MM-DD) or press Enter to skip: ").strip()

            if not expiry_input:
                print_colored(
                    "⚠️ Skipping expiration date - you won't get renewal reminders", Colors.YELLOW)
                return None

            try:
                # Validate date format
                expiry_date = datetime.strptime(expiry_input, '%Y-%m-%d')
                # Convert to ISO format with UTC timezone
                expiry_iso = expiry_date.replace(
                    tzinfo=timezone.utc).isoformat()
                print_colored(
                    f"✅ Expiration date set: {expiry_input}", Colors.GREEN)
                return expiry_iso
            except ValueError:
                print_colored(
                    "❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-12-31)", Colors.RED)

    def _store_token(self, token, token_data, storage_choice):
        """Store token based on user preference."""
        from ..utils.ui_components import print_colored, Colors

        if storage_choice == 1:
            # Environment variable
            print_colored("\n📝 To set environment variable:", Colors.CYAN)
            print_colored(f"export GITHUB_TOKEN={token}", "")
            print_colored(
                "\nAdd this to your shell profile (.bashrc, .zshrc, etc.)", Colors.YELLOW)

        elif storage_choice == 2:
            # System keychain (macOS)
            if platform.system() != 'Darwin':
                print_colored(
                    "❌ Keychain storage only available on macOS", Colors.RED)
                # Fallback to config
                return self._store_token(token, token_data, 3)

            try:
                subprocess.run([
                    'security', 'add-generic-password',
                    '-s', 'classdock-github-token',
                    '-a', token_data['username'],
                    '-w', token
                ], check=True)
                print_colored("✅ Token stored in keychain", Colors.GREEN)
            except Exception as e:
                logger.error(f"Failed to store in keychain: {e}")
                # Fallback to config
                return self._store_token(token, token_data, 3)

        elif storage_choice == 3:
            # Config file
            self.config_dir.mkdir(parents=True, exist_ok=True)

            config_data = {
                'github_token': token_data,
                'stored_at': datetime.now(timezone.utc).isoformat(),
                'storage_type': 'config_file'
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Set restrictive permissions
            self.config_file.chmod(0o600)

            print_colored(
                f"✅ Token stored in: {self.config_file}", Colors.GREEN)
            print_colored(
                "✅ Config file provides the best control with expiration tracking", Colors.GREEN)

    def validate_token_permissions(self, token):
        """Validate that token has required permissions for classroom operations."""
        required_scopes = ['repo', 'read:org']

        token_data = self._verify_and_get_token_info(token)
        if not token_data:
            return False, "Token verification failed"

        scopes = token_data.get('scopes', [])
        missing_scopes = [
            scope for scope in required_scopes if scope not in scopes]

        if missing_scopes:
            return False, f"Missing required scopes: {', '.join(missing_scopes)}"

        return True, "Token has required permissions"

    def get_token_info(self, token=None):
        """Get detailed information about the current token."""
        if not token:
            token = self.get_github_token()
            if not token:
                return None

        return self._verify_and_get_token_info(token)
