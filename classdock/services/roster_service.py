"""
Service layer for roster management operations.

Provides high-level roster operations coordinating between the database,
roster manager, and importer components.
"""

from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..utils.database import DatabaseManager
from ..roster.manager import RosterManager
from ..roster.importer import RosterImporter
from ..roster.sync import RosterSynchronizer
from ..roster.models import Student, Assignment, SyncResult
from ..utils.logger import get_logger

logger = get_logger("roster_service")
console = Console()


class RosterService:
    """
    Service layer for roster management operations.

    Coordinates database, roster manager, and importer operations
    with rich console output.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize roster service.

        Args:
            db_path: Optional database path (defaults to global database)
        """
        self.db = DatabaseManager(db_path=db_path)
        self.manager = RosterManager(self.db)
        self.importer = RosterImporter(self.manager)
        self.synchronizer = RosterSynchronizer(self.manager)

    def initialize_database(self) -> bool:
        """
        Initialize the roster database.

        Returns:
            True if initialization successful
        """
        try:
            if self.db.database_exists():
                console.print(
                    f"✅ Database already exists at: {self.db.db_path}",
                    style="yellow"
                )
            else:
                self.db.initialize_database()
                console.print(
                    f"✅ Database initialized at: {self.db.db_path}",
                    style="green bold"
                )
            return True
        except Exception as e:
            console.print(f"❌ Failed to initialize database: {e}", style="red bold")
            logger.error(f"Database initialization failed: {e}")
            return False

    def import_students_from_csv(
        self,
        csv_path: Path,
        github_organization: str,
        skip_duplicates: bool = True
    ) -> bool:
        """
        Import students from CSV file.

        Args:
            csv_path: Path to CSV file
            github_organization: GitHub organization
            skip_duplicates: Skip duplicate students

        Returns:
            True if import was successful
        """
        try:
            console.print(
                f"\n📥 Importing students from: [cyan]{csv_path}[/cyan]",
                style="bold"
            )
            console.print(f"   Organization: [cyan]{github_organization}[/cyan]\n")

            result = self.importer.import_from_csv(
                csv_path,
                github_organization,
                skip_duplicates=skip_duplicates
            )

            # Display results
            self._display_import_result(result)

            return result.successful > 0

        except Exception as e:
            console.print(f"❌ Import failed: {e}", style="red bold")
            logger.error(f"CSV import failed: {e}")
            return False

    def _display_import_result(self, result) -> None:
        """Display import result summary."""
        # Create summary table
        table = Table(title="Import Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="magenta")

        table.add_row("Total Rows", str(result.total_rows))
        table.add_row("✅ Successful", str(result.successful))
        table.add_row("⏭️  Skipped", str(result.skipped))
        table.add_row("❌ Failed", str(result.failed))
        table.add_row("Success Rate", f"{result.success_rate:.1f}%")

        console.print(table)

        # Show errors if any
        if result.errors:
            console.print("\n❌ Errors:", style="red bold")
            for error in result.errors[:10]:  # Show first 10 errors
                console.print(f"   • {error}", style="red")
            if len(result.errors) > 10:
                console.print(
                    f"   ... and {len(result.errors) - 10} more errors",
                    style="red dim"
                )

    def list_students(
        self,
        github_organization: Optional[str] = None,
        status: str = "active",
        output_format: str = "table"
    ) -> bool:
        """
        List students in roster.

        Args:
            github_organization: Filter by organization
            status: Filter by status
            output_format: Output format (table, csv, json)

        Returns:
            True if students were listed successfully
        """
        try:
            students = self.manager.list_students(
                github_organization=github_organization,
                status=status
            )

            if not students:
                console.print(
                    "📭 No students found matching criteria",
                    style="yellow"
                )
                return False

            if output_format == "table":
                self._display_students_table(students, github_organization)
            elif output_format == "csv":
                self._display_students_csv(students)
            elif output_format == "json":
                self._display_students_json(students)

            return True

        except Exception as e:
            console.print(f"❌ Failed to list students: {e}", style="red bold")
            logger.error(f"Failed to list students: {e}")
            return False

    def _display_students_table(
        self,
        students: List[Student],
        github_organization: Optional[str]
    ) -> None:
        """Display students in a rich table."""
        org_str = github_organization or "All Organizations"
        title = f"Students Roster - {org_str}"

        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Email", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("GitHub", style="yellow")
        table.add_column("Organization", style="magenta")
        table.add_column("Status", style="blue")

        for student in students:
            table.add_row(
                student.email,
                student.name,
                student.github_username or "—",
                student.github_organization,
                student.status
            )

        console.print("\n")
        console.print(table)
        console.print(f"\nTotal: [bold]{len(students)}[/bold] students\n")

    def _display_students_csv(self, students: List[Student]) -> None:
        """Display students in CSV format."""
        console.print("email,name,github_username,github_organization,status")
        for student in students:
            console.print(
                f"{student.email},{student.name},"
                f"{student.github_username or ''},"
                f"{student.github_organization},{student.status}"
            )

    def _display_students_json(self, students: List[Student]) -> None:
        """Display students in JSON format."""
        import json
        data = {
            "total": len(students),
            "students": [student.to_dict() for student in students]
        }
        console.print(json.dumps(data, indent=2))

    def export_students(
        self,
        output_path: Path,
        github_organization: Optional[str] = None,
        output_format: str = "csv"
    ) -> bool:
        """
        Export students to file.

        Args:
            output_path: Output file path
            github_organization: Filter by organization
            output_format: Output format (csv, json)

        Returns:
            True if export successful
        """
        try:
            console.print(
                f"\n📤 Exporting students to: [cyan]{output_path}[/cyan]",
                style="bold"
            )

            if output_format == "csv":
                success = self.importer.export_to_csv(
                    output_path,
                    github_organization=github_organization
                )
            elif output_format == "json":
                success = self.importer.export_to_json(
                    output_path,
                    github_organization=github_organization
                )
            else:
                console.print(
                    f"❌ Invalid format: {output_format}",
                    style="red bold"
                )
                return False

            if success:
                console.print("✅ Export successful", style="green bold")
                return True
            return False

        except Exception as e:
            console.print(f"❌ Export failed: {e}", style="red bold")
            logger.error(f"Export failed: {e}")
            return False

    def add_student(
        self,
        email: str,
        name: str,
        github_organization: str,
        github_username: Optional[str] = None
    ) -> bool:
        """
        Add a single student to roster.

        Args:
            email: Student email
            name: Student name
            github_organization: GitHub organization
            github_username: Optional GitHub username

        Returns:
            True if student was added
        """
        try:
            student = Student(
                email=email,
                name=name,
                github_username=github_username,
                github_organization=github_organization
            )

            student_id = self.manager.add_student(student)
            console.print(
                f"✅ Added student: [cyan]{email}[/cyan] (ID: {student_id})",
                style="green bold"
            )
            return True

        except Exception as e:
            console.print(f"❌ Failed to add student: {e}", style="red bold")
            logger.error(f"Failed to add student: {e}")
            return False

    def link_github_username(
        self,
        email: str,
        github_organization: str,
        github_username: str
    ) -> bool:
        """
        Link a GitHub username to a student.

        Args:
            email: Student email
            github_organization: GitHub organization
            github_username: GitHub username to link

        Returns:
            True if link was successful
        """
        try:
            student = self.manager.get_student_by_email(email, github_organization)
            if not student:
                console.print(
                    f"❌ Student not found: {email} in {github_organization}",
                    style="red bold"
                )
                return False

            success = self.manager.link_github_username(student.id, github_username)
            if success:
                console.print(
                    f"✅ Linked [cyan]{email}[/cyan] to GitHub: [yellow]{github_username}[/yellow]",
                    style="green bold"
                )
                return True
            return False

        except Exception as e:
            console.print(f"❌ Failed to link GitHub username: {e}", style="red bold")
            logger.error(f"Failed to link GitHub username: {e}")
            return False

    def show_status(self, github_organization: Optional[str] = None) -> None:
        """
        Show roster status and statistics.

        Args:
            github_organization: Optional organization filter
        """
        try:
            # Get statistics
            total_students = self.manager.count_students(github_organization)
            total_assignments = self.manager.count_assignments(github_organization)

            students = self.manager.list_students(
                github_organization=github_organization,
                status="active"
            )

            students_with_github = sum(
                1 for s in students if s.github_username
            )
            students_without_github = total_students - students_with_github

            # Create status panel
            org_str = github_organization or "All Organizations"
            status_text = f"""
[bold cyan]Roster Status - {org_str}[/bold cyan]

Students:
  Total: [bold]{total_students}[/bold]
  With GitHub: [green]{students_with_github}[/green] ({students_with_github / total_students * 100 if total_students > 0 else 0:.1f}%)
  Without GitHub: [yellow]{students_without_github}[/yellow] ({students_without_github / total_students * 100 if total_students > 0 else 0:.1f}%)

Assignments:
  Total: [bold]{total_assignments}[/bold]

Database:
  Location: [cyan]{self.db.db_path}[/cyan]
  Schema Version: [green]{self.db.get_schema_version()}[/green]
"""

            console.print(Panel(status_text, title="📊 Roster Status", border_style="cyan"))

        except Exception as e:
            console.print(f"❌ Failed to show status: {e}", style="red bold")
            logger.error(f"Failed to show status: {e}")

    def sync_repositories(
        self,
        assignment_name: str,
        github_organization: str,
        repos: List[tuple]
    ) -> SyncResult:
        """
        Synchronize discovered repositories with roster.

        Args:
            assignment_name: Assignment name
            github_organization: GitHub organization
            repos: List of (repo_name, repo_url, student_identifier) tuples

        Returns:
            SyncResult with synchronization statistics
        """
        try:
            return self.synchronizer.sync_repositories(
                assignment_name,
                github_organization,
                repos
            )
        except Exception as e:
            console.print(f"❌ Sync failed: {e}", style="red bold")
            logger.error(f"Sync failed: {e}")
            # Return empty result on failure
            result = SyncResult(sync_type="repositories", total_repos=len(repos))
            result.add_error(str(e))
            return result
