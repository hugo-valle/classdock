"""
UI Components for the GitHub Classroom Setup Wizard.

This module provides consistent user interface components including
colors, progress indicators, and display screens.
"""

import os
import sys


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[37m'
    NC = '\033[0m'  # No Color

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text if stdout is a TTY."""
        if sys.stdout.isatty():
            return f"{color}{text}{cls.NC}"
        return text


def print_colored(message: str, color: str = "", end: str = "\n") -> None:
    """Print colored message."""
    if color:
        if end == "\n":
            print(Colors.colorize(message, color))
        else:
            print(Colors.colorize(message, color), end=end)
    else:
        print(message, end=end)


def print_error(message: str) -> None:
    """Print error message in red."""
    print_colored(f"❌ ERROR: {message}", Colors.RED)


def print_success(message: str) -> None:
    """Print success message in green."""
    print_colored(f"✅ {message}", Colors.GREEN)


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print_colored(f"⚠️  {message}", Colors.YELLOW)


def print_status(message: str) -> None:
    """Print status message in blue."""
    print_colored(f"ℹ️  {message}", Colors.BLUE)


def print_header(message: str) -> None:
    """Print section header."""
    print_colored(f"\n🔹 {message}", Colors.CYAN)


class ProgressTracker:
    """Track and display progress through wizard steps."""

    def __init__(self, total_steps: int = 8):
        self.total_steps = total_steps
        self.current_step = 0

    def show_progress(self, step_name: str) -> None:
        """Display progress indicator."""
        self.current_step += 1
        print_colored("\n" + "━" * 79, Colors.CYAN)
        print_colored(
            f"📋 Step {self.current_step}/{self.total_steps}: {step_name}", Colors.PURPLE)
        print_colored("━" * 79, Colors.CYAN)


def show_welcome() -> None:
    """Show welcome screen."""
    if sys.stdout.isatty():
        os.system('clear' if os.name == 'posix' else 'cls')

    welcome_text = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.NC}
{Colors.CYAN}║                                                                              ║{Colors.NC}
{Colors.CYAN}║{Colors.NC}  {Colors.PURPLE}🚀 GitHub Classroom Assignment Setup Wizard{Colors.NC}
{Colors.CYAN}║                                                                              ║{Colors.NC}
{Colors.CYAN}║{Colors.NC}  Welcome! This wizard will help you configure your GitHub Classroom
{Colors.CYAN}║{Colors.NC}  assignment with automated tools for seamless management.
{Colors.CYAN}║                                                                              ║{Colors.NC}
{Colors.CYAN}║{Colors.NC}  {Colors.GREEN}✨ What this wizard will do:{Colors.NC}
{Colors.CYAN}║{Colors.NC}     • Create assignment configuration file
{Colors.CYAN}║{Colors.NC}     • Set up secure token files for GitHub API access
{Colors.CYAN}║{Colors.NC}     • Configure .gitignore to protect sensitive files
{Colors.CYAN}║{Colors.NC}     • Validate GitHub CLI access and permissions
{Colors.CYAN}║                                                                              ║{Colors.NC}
{Colors.CYAN}║{Colors.NC}  {Colors.BLUE}📋 You'll need:{Colors.NC}
{Colors.CYAN}║{Colors.NC}     • GitHub Classroom assignment URL
{Colors.CYAN}║{Colors.NC}     • Template repository URL (students fork this - has starter code)
{Colors.CYAN}║{Colors.NC}     • Classroom repository URL (optional - for pushing updates)
{Colors.CYAN}║{Colors.NC}     • GitHub personal access token with repo permissions
{Colors.CYAN}║                                                                              ║{Colors.NC}
{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.NC}
"""

    print(welcome_text)
    print_colored("Press Enter to continue...", Colors.GREEN)

    if sys.stdin.isatty():
        input()


def show_completion(config_values: dict, token_files: dict) -> None:
    """Show completion screen."""
    if sys.stdout.isatty():
        os.system('clear' if os.name == 'posix' else 'cls')

    completion_text = f"""
{Colors.GREEN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.NC}
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}  {Colors.PURPLE}🎉 Assignment Setup Complete!{Colors.NC}
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}  Your GitHub Classroom assignment has been successfully configured
{Colors.GREEN}║{Colors.NC}  with automated tools. Here's what was created:
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}  {Colors.CYAN}📁 Files Created:{Colors.NC}
{Colors.GREEN}║{Colors.NC}     • assignment.conf - Complete assignment configuration
"""

    # Token information - now using centralized token system
    if config_values.get('USE_SECRETS') == 'true':
        completion_text += f"{Colors.GREEN}║{Colors.NC}     • Secrets configured (using centralized GitHub token)\n"

    completion_text += f"""
{Colors.GREEN}║{Colors.NC}     • .gitignore - Updated to protect sensitive files
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}  {Colors.CYAN}🔑 Token Management:{Colors.NC}
{Colors.GREEN}║{Colors.NC}     • Centralized token: ~/.config/classdock/token_config.json
{Colors.GREEN}║{Colors.NC}     • No token files needed in repository
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}  {Colors.YELLOW}🚀 Next Steps:{Colors.NC}
{Colors.GREEN}║{Colors.NC}     1. Run the complete workflow:
{Colors.GREEN}║{Colors.NC}        python -m classdock run
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}     2. Or run individual tools:
{Colors.GREEN}║{Colors.NC}        python -m classdock discover
{Colors.GREEN}║{Colors.NC}        python -m classdock secrets
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}║{Colors.NC}  {Colors.BLUE}📚 Documentation:{Colors.NC}
{Colors.GREEN}║{Colors.NC}     • docs/ORCHESTRATOR-WORKFLOW.md - Complete workflow guide
{Colors.GREEN}║{Colors.NC}     • docs/TOOLS-USAGE.md - Individual tool documentation
{Colors.GREEN}║{Colors.NC}     • docs/SECRETS-MANAGEMENT.md - Secret management guide
{Colors.GREEN}║                                                                              ║{Colors.NC}
{Colors.GREEN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.NC}
"""

    print(completion_text)


def show_help():
    """Show help information."""
    help_text = """
GitHub Classroom Assignment Setup Wizard

DESCRIPTION:
    Interactive setup wizard for instructors to configure a new GitHub Classroom
    assignment with automated tools. Creates configuration files, sets up secure
    token storage, and configures .gitignore for instructor-only files.

USAGE:
    python -m classdock setup [options]

OPTIONS:
    --help              Show this help message
    --version           Show version information

FEATURES:
    • Interactive prompts with intelligent defaults
    • Centralized token management (no token files in repo)
    • Automatic .gitignore configuration
    • Configuration validation and GitHub access testing
    • Support for multiple custom secrets/tokens
    • Modern, elegant interface with progress indicators

REQUIREMENTS:
    • GitHub token configured (via ~/.config/classdock/ or environment)
    • Write access to repository root directory
    • GitHub organization access permissions

GENERATED FILES:
    • assignment.conf - Complete assignment configuration
    • .gitignore - Updated to protect sensitive files

TOKEN MANAGEMENT:
    • Centralized: ~/.config/classdock/token_config.json
    • Environment: GITHUB_TOKEN variable
    • No token files stored in repository

NEXT STEPS:
    After running this setup wizard, use:
    • python -m classdock run - Complete automation workflow
    • python -m classdock discover - Discover student repositories
    • python -m classdock secrets - Add secrets to student repos

DOCUMENTATION:
    • docs/ORCHESTRATOR-WORKFLOW.md - Complete workflow guide
    • docs/TOOLS-USAGE.md - Individual tool documentation
    • docs/SECRETS-MANAGEMENT.md - Secret management guide
"""
    print(help_text)


def show_version():
    """Show version information."""
    print("GitHub Classroom Assignment Setup Wizard v2.0.0")
    print("Part of the GitHub Classroom automation tools suite (Python version)")
