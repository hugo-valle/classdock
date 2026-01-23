"""
Bash script wrapper module for executing existing bash scripts.

This module provides a BashWrapper class that handles subprocess execution 
of scripts in the scripts/ directory, maintaining compatibility with the 
existing bash script functionality.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Import for resource management (Python 3.9+)
try:
    from importlib.resources import files, as_file
except ImportError:
    # Fallback for Python 3.8
    try:
        from importlib_resources import files, as_file
    except ImportError:
        # Final fallback - disable importlib.resources functionality
        files = None
        as_file = None

from .utils import get_logger

logger = get_logger("bash_wrapper")


class BashWrapper:
    """
    Wrapper class for executing bash scripts with proper environment setup
    and error handling.
    """

    def __init__(
        self,
        config: Dict[str, str],
        dry_run: bool = False,
        verbose: bool = False,
        auto_yes: bool = False
    ):
        """
        Initialize bash wrapper.

        Args:
            config: Configuration dictionary
            dry_run: Enable dry-run mode
            verbose: Enable verbose output
            auto_yes: Automatically answer yes to prompts
        """
        self.config = config
        self.dry_run = dry_run
        self.verbose = verbose
        self.auto_yes = auto_yes

    def _get_script_path(self, script_name: str) -> Path:
        """
        Get the path to a script using importlib.resources for proper resolution
        in both installed packages and source checkouts.

        Args:
            script_name: Name of the script file

        Returns:
            Path to the script file

        Raises:
            FileNotFoundError: If script cannot be found
        """
        # Try using importlib.resources first (for installed packages)
        if files is not None and as_file is not None:
            try:
                script_ref = files("classdock") / "scripts" / script_name

                # Use as_file context manager for proper resource handling
                with as_file(script_ref) as script_path:
                    if script_path.exists():
                        # Return the actual path for use outside the context
                        # Note: This works for both installed packages and source checkouts
                        return Path(script_path)
                    else:
                        raise FileNotFoundError(
                            f"Script not found in package: {script_name}")

            except (ImportError, FileNotFoundError, AttributeError) as e:
                logger.debug(
                    f"importlib.resources approach failed: {e}, using fallback")

        # Fallback to direct filesystem access (for source checkouts or when importlib.resources fails)
        logger.debug("Using fallback filesystem access for script resolution")
        fallback_path = Path(__file__).parent.parent / "scripts" / script_name

        if fallback_path.exists():
            return fallback_path

        # Try the current package directory as final fallback
        package_scripts_path = Path(__file__).parent / "scripts" / script_name
        if package_scripts_path.exists():
            return package_scripts_path

        raise FileNotFoundError(
            f"Script not found: {script_name} (tried importlib.resources and filesystem fallbacks)")

    def _prepare_environment(self) -> Dict[str, str]:
        """
        Prepare environment variables for bash script execution.

        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()

        # Add configuration variables
        if hasattr(self.config, 'to_env_dict'):
            # Legacy Configuration object
            config_env = self.config.to_env_dict()
        else:
            # Plain dictionary from new ConfigLoader
            config_env = {}
            for key, value in self.config.items():
                if isinstance(value, list):
                    # Convert arrays to bash array format
                    config_env[key] = ' '.join(f'"{item}"' for item in value)
                else:
                    config_env[key] = str(value)

        env.update(config_env)

        # Add wrapper-specific variables
        if self.dry_run:
            env['DRY_RUN'] = 'true'
        if self.verbose:
            env['VERBOSE'] = 'true'
        if self.auto_yes:
            env['AUTO_YES'] = 'true'

        return env

    def _execute_script(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None
    ) -> bool:
        """
        Execute a bash script with proper environment and error handling.

        Args:
            script_name: Name of the script to execute
            args: Additional arguments to pass to the script
            cwd: Working directory for script execution

        Returns:
            True if script executed successfully, False otherwise
        """
        try:
            script_path = self._get_script_path(script_name)
        except FileNotFoundError as e:
            logger.error(f"Script not found: {e}")
            return False

        # Prepare command
        cmd = ["bash", str(script_path)]
        if args:
            cmd.extend(args)

        # Prepare environment
        env = self._prepare_environment()

        # Set working directory (use current working directory by default)
        if cwd is None:
            cwd = Path.cwd()

        logger.debug(f"Executing: {' '.join(cmd)}")
        logger.debug(f"Working directory: {cwd}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
            return True

        try:
            # Execute script
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=not self.verbose,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.debug(f"Script {script_name} completed successfully")
                if not self.verbose and result.stdout:
                    logger.info(result.stdout.strip())
                return True
            else:
                logger.error(
                    f"Script {script_name} failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr.strip()}")
                if result.stdout:
                    logger.error(f"Standard output: {result.stdout.strip()}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_name} timed out after 1 hour")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Script {script_name} failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error executing {script_name}: {e}")
            return False

    def assignment_orchestrator(self, workflow_type: str = "run") -> bool:
        """
        Execute the assignment orchestrator script.

        Args:
            workflow_type: Type of workflow to run (run, sync, discover, secrets, assist)

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            f"🎯 Running assignment orchestrator workflow: {workflow_type}")

        args = []
        if workflow_type != "run":
            args.append(workflow_type)

        return self._execute_script("assignment-orchestrator.sh", args)

    def push_to_classroom(self) -> bool:
        """
        Execute the push to classroom script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🚀 Pushing template to classroom")
        return self._execute_script("push-to-classroom.sh")

    def fetch_student_repos(self) -> bool:
        """
        Execute the fetch student repositories script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("📥 Fetching student repositories")
        return self._execute_script("fetch-student-repos.sh")

    def add_secrets_to_students(self, assignment_root: Optional[Path] = None) -> bool:
        """
        Execute the add secrets to students functionality using Python implementation.

        Args:
            assignment_root: Root directory of assignment template repository
                           (where assignment.conf and assignment files are located)

        Returns:
            True if successful, False otherwise
        """
        logger.info("🔐 Adding secrets to student repositories")

        # Use Python implementation instead of bash script
        try:
            from .secrets.github_secrets import add_secrets_to_students

            # Change to assignment root directory if specified
            original_cwd = None
            if assignment_root:
                original_cwd = Path.cwd()
                os.chdir(assignment_root)

            try:
                # Use the Python implementation
                success = add_secrets_to_students(
                    config=self.config,
                    dry_run=self.dry_run
                )
                return success
            finally:
                # Restore original working directory
                if original_cwd:
                    os.chdir(original_cwd)

        except ImportError as e:
            logger.error(
                f"Failed to import Python secrets implementation: {e}")
            logger.info("Falling back to bash script implementation")
            # Fallback to bash script
            return self._execute_script("add-secrets-to-students.sh", cwd=assignment_root)

    def student_update_helper(self) -> bool:
        """
        Execute the student update helper script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🆘 Running student update helper")
        return self._execute_script("student-update-helper.sh")

    def setup_assignment(self) -> bool:
        """
        Execute the setup assignment script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("⚙️ Setting up assignment")
        return self._execute_script("setup-assignment.sh")

    def update_assignment(self) -> bool:
        """
        Execute the update assignment script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🔄 Updating assignment")
        return self._execute_script("update-assignment.sh")

    def manage_cron(self, action: str = "status") -> bool:
        """
        Execute the manage cron script.

        Args:
            action: Cron action (status, enable, disable, etc.)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"⏰ Managing cron: {action}")
        return self._execute_script("manage-cron.sh", [action])

    def cron_sync(self) -> bool:
        """
        Execute the cron sync script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("🔄 Running cron sync")
        return self._execute_script("cron-sync.sh")

    def cycle_collaborator(
        self,
        assignment_prefix: Optional[str] = None,
        username: Optional[str] = None,
        organization: Optional[str] = None,
        batch_file: Optional[str] = None,
        config_file: Optional[str] = None,
        list_mode: bool = False,
        force_cycle: bool = False,
        repo_url_mode: bool = False
    ) -> bool:
        """
        Execute the cycle collaborator script to manage repository collaborator permissions.

        This method wraps the cycle-collaborator.sh script which can cycle through
        collaborators on GitHub repositories, either for a single user or in batch mode.
        It supports listing current collaborators, forcing permission changes, and
        operating on repository URLs directly.

        Args:
            assignment_prefix: Optional assignment prefix for repository filtering
            username: Optional single username for individual user mode
            organization: Optional GitHub organization name
            batch_file: Optional path to batch file containing multiple operations
            config_file: Optional path to configuration file
            list_mode: If True, only list current collaborators without making changes
            force_cycle: If True, force permission cycling even if already at target level
            repo_url_mode: If True, operate on repository URLs instead of assignment prefix

        Returns:
            True if successful, False otherwise
        """
        logger.info("🔄 Cycling repository collaborator permissions")

        args = []

        # Add flags first
        if list_mode:
            args.append("--list")
        if force_cycle:
            args.append("--force")
        if repo_url_mode:
            args.append("--repo-urls")

        # Add options with values
        if batch_file:
            args.extend(["--batch", batch_file])
        if config_file:
            args.extend(["--config", config_file])

        # Add positional arguments for single user mode
        if username and organization:
            if assignment_prefix:
                args.append(assignment_prefix)
            args.append(username)
            args.append(organization)
        elif assignment_prefix and not batch_file:
            args.append(assignment_prefix)

        return self._execute_script("cycle-collaborator.sh", args)
