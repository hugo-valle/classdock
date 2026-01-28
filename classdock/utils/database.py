"""
SQLite database management for ClassDock roster system.

Provides a centralized database manager for student roster tracking, assignment
management, and GitHub integration. Uses a global database stored in the user's
config directory.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from ..utils.logger import get_logger

logger = get_logger("database")


class DatabaseManager:
    """
    Manages SQLite database connections and schema operations.

    The database is stored globally at ~/.config/classdock/roster.db to support
    tracking students across multiple GitHub organizations and assignments.
    """

    DEFAULT_DB_PATH = Path.home() / ".config" / "classdock" / "roster.db"

    # Schema version for migrations
    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to database file. Defaults to ~/.config/classdock/roster.db
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._ensure_db_directory()
        logger.debug(f"Database path: {self.db_path}")

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def database_exists(self) -> bool:
        """Check if database file exists."""
        return self.db_path.exists()

    @contextmanager
    def get_connection(self):
        """
        Get a database connection with row factory configured.

        Yields:
            sqlite3.Connection: Database connection with row factory

        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM students")
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def initialize_database(self) -> bool:
        """
        Create database tables if they don't exist.

        Returns:
            bool: True if initialization successful

        Raises:
            sqlite3.Error: If database initialization fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Create students table with composite unique constraint
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        name TEXT NOT NULL,
                        github_username TEXT,
                        github_id INTEGER,
                        github_organization TEXT NOT NULL,
                        enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(email, github_organization)
                    )
                """)

                # Create indexes for students table
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_students_email
                    ON students(email)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_students_org
                    ON students(github_organization)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_students_email_org
                    ON students(email, github_organization)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_students_github_username
                    ON students(github_username)
                """)

                # Create assignments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        classroom_id INTEGER,
                        classroom_url TEXT,
                        template_repo_url TEXT,
                        github_organization TEXT NOT NULL,
                        assignment_type TEXT DEFAULT 'individual',
                        deadline TIMESTAMP,
                        points_available INTEGER DEFAULT 100,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create index for assignments table
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_assignments_name
                    ON assignments(name)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_assignments_org
                    ON assignments(github_organization)
                """)

                # Create student_assignments junction table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS student_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        assignment_id INTEGER NOT NULL,
                        repository_url TEXT,
                        repository_name TEXT,
                        acceptance_status TEXT DEFAULT 'pending',
                        accepted_at TIMESTAMP,
                        last_commit_at TIMESTAMP,
                        last_synced_at TIMESTAMP,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                        FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
                        UNIQUE(student_id, assignment_id)
                    )
                """)

                # Create indexes for student_assignments table
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_student_assignments_student
                    ON student_assignments(student_id)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_student_assignments_assignment
                    ON student_assignments(assignment_id)
                """)

                # Create sync_history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sync_type TEXT NOT NULL,
                        assignment_id INTEGER,
                        records_processed INTEGER DEFAULT 0,
                        records_successful INTEGER DEFAULT 0,
                        records_failed INTEGER DEFAULT 0,
                        error_log TEXT,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE SET NULL
                    )
                """)

                # Create schema_version table for migrations
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert current schema version
                cursor.execute("""
                    INSERT OR IGNORE INTO schema_version (version)
                    VALUES (?)
                """, (self.SCHEMA_VERSION,))

                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                return True

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def execute_query(
        self,
        query: str,
        params: Tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries.

        Args:
            query: SQL SELECT query
            params: Query parameters as tuple

        Returns:
            List of dictionaries representing rows

        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}\nQuery: {query}")
            raise

    def execute_update(
        self,
        query: str,
        params: Tuple = ()
    ) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL INSERT/UPDATE/DELETE query
            params: Query parameters as tuple

        Returns:
            Number of rows affected (or last row ID for INSERT)

        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()

                # Return last row ID for INSERT, row count for UPDATE/DELETE
                if query.strip().upper().startswith("INSERT"):
                    return cursor.lastrowid
                return cursor.rowcount

        except sqlite3.Error as e:
            logger.error(f"Update execution failed: {e}\nQuery: {query}")
            raise

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Execute a query with multiple parameter sets (batch operation).

        Args:
            query: SQL query
            params_list: List of parameter tuples

        Returns:
            Number of rows affected

        Raises:
            sqlite3.Error: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount

        except sqlite3.Error as e:
            logger.error(f"Batch execution failed: {e}\nQuery: {query}")
            raise

    def get_schema_version(self) -> Optional[int]:
        """
        Get current schema version from database.

        Returns:
            Schema version number or None if not initialized
        """
        try:
            if not self.database_exists():
                return None

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
                )
                if not cursor.fetchone():
                    return None

                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                return result[0] if result else None

        except sqlite3.Error:
            return None

    def backup_database(self, backup_path: Path) -> bool:
        """
        Create a backup copy of the database.

        Args:
            backup_path: Path for backup file

        Returns:
            True if backup successful

        Raises:
            sqlite3.Error: If backup fails
        """
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            with self.get_connection() as source_conn:
                with sqlite3.connect(str(backup_path)) as backup_conn:
                    source_conn.backup(backup_conn)

            logger.info(f"Database backed up to {backup_path}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database backup failed: {e}")
            raise

    def drop_all_tables(self) -> bool:
        """
        Drop all tables from the database. Use with caution!

        Returns:
            True if successful

        Raises:
            sqlite3.Error: If drop operation fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Disable foreign key constraints temporarily
                cursor.execute("PRAGMA foreign_keys = OFF")

                # Get all table names
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]

                # Drop each table
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

                conn.commit()

                # Re-enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys = ON")

                logger.warning("All tables dropped from database")
                return True

        except sqlite3.Error as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
