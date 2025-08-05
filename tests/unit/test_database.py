"""Tests for the database module."""

import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from floatctl.core.database import DatabaseManager, ProcessingStatus, FileRun, Base


class TestDatabaseManager:
    """Test the DatabaseManager class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        # Create database manager
        db_manager = DatabaseManager(db_path)
        
        yield db_manager
        
        # Cleanup
        db_path.unlink(missing_ok=True)
    
    def test_database_initialization(self, temp_db):
        """Test that database is properly initialized."""
        # Database should be created and tables should exist
        engine = create_engine(f"sqlite:///{temp_db.db_path}")
        
        # Check that tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        assert 'file_runs' in table_names
        assert 'processed_artifacts' in table_names
        assert 'processing_queue' in table_names
    
    def test_get_session(self, temp_db):
        """Test getting a database session."""
        session = temp_db.get_session()
        assert session is not None
        session.close()
    
    def test_get_file_history_empty(self, temp_db):
        """Test getting file history for non-existent file."""
        file_path = Path("/test/nonexistent.txt")
        history = temp_db.get_file_history(file_path)
        assert history == []
    
    def test_get_pending_files_empty(self, temp_db):
        """Test getting pending files when none exist."""
        pending = temp_db.get_pending_files()
        assert pending == []
    
    def test_get_pending_files_with_plugin_filter(self, temp_db):
        """Test getting pending files with plugin filter."""
        pending = temp_db.get_pending_files(plugin="test_plugin")
        assert pending == []
    
    def test_get_pending_files_with_limit(self, temp_db):
        """Test getting pending files with limit."""
        pending = temp_db.get_pending_files(limit=5)
        assert pending == []
    
    def test_queue_file(self, temp_db):
        """Test queuing a file for processing."""
        file_path = Path("/test/file.txt")
        plugin = "test_plugin"
        priority = 1
        
        # Queue a file
        temp_db.queue_file(
            file_path=file_path,
            plugin=plugin,
            priority=priority,
            metadata={"test": "data"}
        )
        
        # Should not raise any exceptions
        # Actual verification would require checking the processing_queue table
    
    def test_mark_for_reprocessing(self, temp_db):
        """Test marking a file for reprocessing."""
        file_path = Path("/test/file.txt")
        reason = "test reason"
        
        # Mark for reprocessing
        temp_db.mark_for_reprocessing(file_path, reason)
        
        # Should not raise any exceptions
        # Actual verification would require checking the database state


class TestFileRun:
    """Test the FileRun model."""
    
    def test_file_run_creation(self):
        """Test creating a FileRun instance."""
        file_run = FileRun(
            file_path="/test/file.txt",
            plugin="test_plugin",
            command="test_command",
            status=ProcessingStatus.PENDING,
            file_size=1024,
            file_hash="test_hash",
            extra_data={"key": "value"}
        )
        
        assert file_run.file_path == "/test/file.txt"
        assert file_run.plugin == "test_plugin"
        assert file_run.command == "test_command"
        assert file_run.status == ProcessingStatus.PENDING
        assert file_run.file_size == 1024
        assert file_run.file_hash == "test_hash"
        assert file_run.extra_data == {"key": "value"}
        # started_at should be set by default (func.now())
        # But since we're not inserting into DB, it won't be populated
        assert file_run.completed_at is None
    
    def test_file_run_repr(self):
        """Test FileRun string representation."""
        file_run = FileRun(
            file_path="/test/file.txt",
            plugin="test_plugin",
            command="test_command",
            status=ProcessingStatus.COMPLETED
        )
        
        repr_str = repr(file_run)
        assert "FileRun" in repr_str


class TestProcessingStatus:
    """Test the ProcessingStatus enum."""
    
    def test_processing_status_values(self):
        """Test ProcessingStatus enum values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.SKIPPED.value == "skipped"
        assert ProcessingStatus.NEEDS_REPROCESS.value == "needs_reprocess"
    
    def test_processing_status_comparison(self):
        """Test ProcessingStatus comparison."""
        assert ProcessingStatus.PENDING == ProcessingStatus.PENDING
        assert ProcessingStatus.PENDING != ProcessingStatus.COMPLETED
        assert ProcessingStatus.COMPLETED != ProcessingStatus.FAILED