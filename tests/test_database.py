"""
Tests for classdock.utils.database module.

Tests database initialization, connection management, query execution,
and schema operations.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from classdock.utils.database import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance with temporary database."""
    return DatabaseManager(db_path=temp_db)


@pytest.fixture
def initialized_db(db_manager):
    """Create an initialized database."""
    db_manager.initialize_database()
    return db_manager


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_init_default_path(self):
        """Test initialization with default database path."""
        db = DatabaseManager()
        assert db.db_path == DatabaseManager.DEFAULT_DB_PATH
        assert db.db_path.parent == Path.home() / ".config" / "classdock"

    def test_init_custom_path(self, temp_db):
        """Test initialization with custom database path."""
        db = DatabaseManager(db_path=temp_db)
        assert db.db_path == temp_db

    def test_ensure_db_directory(self, tmp_path):
        """Test database directory creation."""
        db_path = tmp_path / "subdir" / "roster.db"
        assert not db_path.parent.exists()

        db = DatabaseManager(db_path=db_path)
        assert db_path.parent.exists()

    def test_database_exists(self, db_manager, temp_db):
        """Test database existence check."""
        # Ensure file doesn't exist initially
        if temp_db.exists():
            temp_db.unlink()

        assert not db_manager.database_exists()

        # Create empty file
        temp_db.touch()
        assert db_manager.database_exists()

    def test_initialize_database(self, db_manager):
        """Test database initialization creates all tables."""
        assert db_manager.initialize_database()

        # Verify tables exist
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'assignments',
            'schema_version',
            'students',
            'student_assignments',
            'sync_history'
        ]
        assert set(expected_tables).issubset(set(tables))

    def test_initialize_database_idempotent(self, db_manager):
        """Test database initialization is idempotent."""
        db_manager.initialize_database()
        # Should not raise error on second initialization
        assert db_manager.initialize_database()

    def test_get_connection(self, initialized_db):
        """Test database connection retrieval."""
        with initialized_db.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row

            # Test foreign key enforcement
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            assert result[0] == 1  # Foreign keys enabled

    def test_get_connection_closes_properly(self, initialized_db):
        """Test connection closes properly after context manager."""
        # Get connection and verify it works
        with initialized_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

        # After exiting context, connection should be closed
        # Attempting to use it should fail
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            conn.execute("SELECT 1")

    def test_execute_query(self, initialized_db):
        """Test SELECT query execution."""
        # Insert test data
        with initialized_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (email, name, github_organization)
                VALUES ('test@example.com', 'Test User', 'test-org')
            """)
            conn.commit()

        # Query data
        results = initialized_db.execute_query(
            "SELECT * FROM students WHERE email = ?",
            ('test@example.com',)
        )

        assert len(results) == 1
        assert results[0]['email'] == 'test@example.com'
        assert results[0]['name'] == 'Test User'
        assert results[0]['github_organization'] == 'test-org'

    def test_execute_query_empty_result(self, initialized_db):
        """Test query with no results."""
        results = initialized_db.execute_query(
            "SELECT * FROM students WHERE email = ?",
            ('nonexistent@example.com',)
        )
        assert len(results) == 0

    def test_execute_query_invalid_sql(self, initialized_db):
        """Test query with invalid SQL."""
        with pytest.raises(sqlite3.Error):
            initialized_db.execute_query("SELECT * FROM nonexistent_table")

    def test_execute_update_insert(self, initialized_db):
        """Test INSERT query execution."""
        row_id = initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('new@example.com', 'New User', 'test-org')
        )

        assert row_id > 0

        # Verify insertion
        results = initialized_db.execute_query(
            "SELECT * FROM students WHERE id = ?",
            (row_id,)
        )
        assert len(results) == 1
        assert results[0]['email'] == 'new@example.com'

    def test_execute_update_update(self, initialized_db):
        """Test UPDATE query execution."""
        # Insert test data
        row_id = initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('update@example.com', 'Old Name', 'test-org')
        )

        # Update data
        rows_affected = initialized_db.execute_update(
            "UPDATE students SET name = ? WHERE id = ?",
            ('New Name', row_id)
        )

        assert rows_affected == 1

        # Verify update
        results = initialized_db.execute_query(
            "SELECT * FROM students WHERE id = ?",
            (row_id,)
        )
        assert results[0]['name'] == 'New Name'

    def test_execute_update_delete(self, initialized_db):
        """Test DELETE query execution."""
        # Insert test data
        row_id = initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('delete@example.com', 'Delete User', 'test-org')
        )

        # Delete data
        rows_affected = initialized_db.execute_update(
            "DELETE FROM students WHERE id = ?",
            (row_id,)
        )

        assert rows_affected == 1

        # Verify deletion
        results = initialized_db.execute_query(
            "SELECT * FROM students WHERE id = ?",
            (row_id,)
        )
        assert len(results) == 0

    def test_execute_many(self, initialized_db):
        """Test batch insert execution."""
        students = [
            ('student1@example.com', 'Student 1', 'test-org'),
            ('student2@example.com', 'Student 2', 'test-org'),
            ('student3@example.com', 'Student 3', 'test-org'),
        ]

        rows_affected = initialized_db.execute_many(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            students
        )

        assert rows_affected == 3

        # Verify insertions
        results = initialized_db.execute_query(
            "SELECT * FROM students ORDER BY email"
        )
        assert len(results) == 3
        assert results[0]['email'] == 'student1@example.com'

    def test_composite_unique_constraint(self, initialized_db):
        """Test composite unique constraint (email, github_organization)."""
        # Insert first student
        initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('duplicate@example.com', 'User 1', 'org1')
        )

        # Same email, different org - should succeed
        initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('duplicate@example.com', 'User 2', 'org2')
        )

        # Same email and org - should fail
        with pytest.raises(sqlite3.IntegrityError):
            initialized_db.execute_update(
                """
                INSERT INTO students (email, name, github_organization)
                VALUES (?, ?, ?)
                """,
                ('duplicate@example.com', 'User 3', 'org1')
            )

    def test_foreign_key_cascade_delete(self, initialized_db):
        """Test foreign key cascade on delete."""
        # Insert student
        student_id = initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('student@example.com', 'Student', 'test-org')
        )

        # Insert assignment
        assignment_id = initialized_db.execute_update(
            """
            INSERT INTO assignments (name, github_organization)
            VALUES (?, ?)
            """,
            ('test-assignment', 'test-org')
        )

        # Link student to assignment
        link_id = initialized_db.execute_update(
            """
            INSERT INTO student_assignments (student_id, assignment_id)
            VALUES (?, ?)
            """,
            (student_id, assignment_id)
        )

        # Delete student - should cascade to student_assignments
        initialized_db.execute_update(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

        # Verify student_assignment was deleted
        results = initialized_db.execute_query(
            "SELECT * FROM student_assignments WHERE id = ?",
            (link_id,)
        )
        assert len(results) == 0

    def test_get_schema_version(self, initialized_db):
        """Test schema version retrieval."""
        version = initialized_db.get_schema_version()
        assert version == DatabaseManager.SCHEMA_VERSION

    def test_get_schema_version_no_database(self, db_manager):
        """Test schema version when database doesn't exist."""
        version = db_manager.get_schema_version()
        assert version is None

    def test_backup_database(self, initialized_db, tmp_path):
        """Test database backup creation."""
        # Insert test data
        initialized_db.execute_update(
            """
            INSERT INTO students (email, name, github_organization)
            VALUES (?, ?, ?)
            """,
            ('backup@example.com', 'Backup User', 'test-org')
        )

        # Create backup
        backup_path = tmp_path / "backup.db"
        assert initialized_db.backup_database(backup_path)
        assert backup_path.exists()

        # Verify backup contains data
        backup_db = DatabaseManager(db_path=backup_path)
        results = backup_db.execute_query(
            "SELECT * FROM students WHERE email = ?",
            ('backup@example.com',)
        )
        assert len(results) == 1

    def test_drop_all_tables(self, initialized_db):
        """Test dropping all tables."""
        assert initialized_db.drop_all_tables()

        # Verify tables are gone
        with initialized_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            assert len(tables) == 0

    def test_indexes_created(self, initialized_db):
        """Test that indexes are created properly."""
        with initialized_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'idx_students_email',
            'idx_students_org',
            'idx_students_email_org',
            'idx_students_github_username',
            'idx_assignments_name',
            'idx_assignments_org',
            'idx_student_assignments_student',
            'idx_student_assignments_assignment'
        ]

        for index in expected_indexes:
            assert index in indexes, f"Index {index} not found"
