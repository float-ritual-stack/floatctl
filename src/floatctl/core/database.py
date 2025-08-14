"""Database models and operations for tracking file processing state."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func

from floatctl.core.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class ProcessingStatus(str, Enum):
    """Status of file processing."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_REPROCESS = "needs_reprocess"


class FileRun(Base):
    """Track processing runs for files."""
    
    __tablename__ = "file_runs"
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False, index=True)
    file_hash = Column(String, nullable=True)  # SHA256 hash for change detection
    file_size = Column(Integer, nullable=True)
    file_modified = Column(DateTime, nullable=True)
    
    # Processing information
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    plugin = Column(String, nullable=False)  # Which plugin processed this
    command = Column(String, nullable=False)  # Command that was run
    
    # Timing
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results and metadata
    output_path = Column(String, nullable=True)  # Where output was saved
    items_processed = Column(Integer, nullable=True)  # Number of items (conversations, artifacts, etc.)
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Flexible storage for plugin-specific data
    
    # Relationships
    artifacts = relationship("ProcessedArtifact", back_populates="file_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_file_path_status", "file_path", "status"),
        Index("idx_plugin_status", "plugin", "status"),
        Index("idx_started_at", "started_at"),
    )


class ProcessedArtifact(Base):
    """Track individual artifacts extracted from files."""
    
    __tablename__ = "processed_artifacts"
    
    id = Column(Integer, primary_key=True)
    file_run_id = Column(Integer, ForeignKey("file_runs.id"), nullable=False)
    
    # Artifact information
    artifact_type = Column(String, nullable=False)  # conversation, artifact, export, etc.
    artifact_id = Column(String, nullable=True)  # UUID or other identifier
    artifact_name = Column(String, nullable=True)
    artifact_path = Column(String, nullable=False)  # Where it was saved
    
    # Metadata
    created_at = Column(DateTime, nullable=True)  # Original creation time
    processed_at = Column(DateTime, default=func.now(), nullable=False)
    extra_data = Column(JSON, nullable=True)  # Flexible storage
    
    # Relationships
    file_run = relationship("FileRun", back_populates="artifacts")
    
    __table_args__ = (
        Index("idx_artifact_type", "artifact_type"),
        Index("idx_artifact_id", "artifact_id"),
    )


class ProcessingQueue(Base):
    """Queue for files to be processed."""
    
    __tablename__ = "processing_queue"
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False, unique=True)
    priority = Column(Integer, default=0, nullable=False)  # Higher = more urgent
    plugin = Column(String, nullable=True)  # Specific plugin to use, or null for auto
    added_at = Column(DateTime, default=func.now(), nullable=False)
    scheduled_for = Column(DateTime, nullable=True)  # Future processing
    extra_data = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("idx_priority_scheduled", "priority", "scheduled_for"),
    )


class DatabaseManager:
    """Manage database operations."""
    
    def __init__(self, db_path: Path):
        """Initialize database connection."""
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info("database_initialized", path=str(db_path))
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def record_file_run(
        self,
        file_path: Path,
        plugin: str,
        command: str,
        file_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileRun:
        """Record a new file processing run."""
        with self.get_session() as session:
            file_run = FileRun(
                file_path=str(file_path),
                file_hash=file_hash,
                file_size=file_path.stat().st_size if file_path.exists() else None,
                file_modified=datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else None,
                plugin=plugin,
                command=command,
                status=ProcessingStatus.PROCESSING,
                extra_data=metadata or {},
            )
            session.add(file_run)
            session.commit()
            
            logger.info(
                "file_run_started",
                file_run_id=file_run.id,
                file_path=str(file_path),
                plugin=plugin,
                command=command,
            )
            
            return file_run
    
    def complete_file_run(
        self,
        file_run_id: int,
        status: ProcessingStatus,
        output_path: Optional[Path] = None,
        items_processed: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark a file run as completed."""
        with self.get_session() as session:
            file_run = session.query(FileRun).filter_by(id=file_run_id).first()
            if not file_run:
                logger.error("file_run_not_found", file_run_id=file_run_id)
                return
            
            file_run.status = status
            file_run.completed_at = datetime.now()
            file_run.duration_seconds = int((file_run.completed_at - file_run.started_at).total_seconds())
            
            if output_path:
                file_run.output_path = str(output_path)
            if items_processed is not None:
                file_run.items_processed = items_processed
            if error_message:
                file_run.error_message = error_message
            if metadata:
                file_run.extra_data = {**(file_run.extra_data or {}), **metadata}
            
            session.commit()
            
            logger.info(
                "file_run_completed",
                file_run_id=file_run_id,
                status=status.value,
                duration_seconds=file_run.duration_seconds,
                items_processed=items_processed,
            )
    
    def add_artifact(
        self,
        file_run_id: int,
        artifact_type: str,
        artifact_path: Path,
        artifact_id: Optional[str] = None,
        artifact_name: Optional[str] = None,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a processed artifact record."""
        with self.get_session() as session:
            artifact = ProcessedArtifact(
                file_run_id=file_run_id,
                artifact_type=artifact_type,
                artifact_path=str(artifact_path),
                artifact_id=artifact_id,
                artifact_name=artifact_name,
                created_at=created_at,
                extra_data=metadata or {},
            )
            session.add(artifact)
            session.commit()
            
            logger.debug(
                "artifact_added",
                file_run_id=file_run_id,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
            )
    
    def get_file_history(self, file_path: Path, limit: int = 10) -> List[FileRun]:
        """Get processing history for a file."""
        with self.get_session() as session:
            return (
                session.query(FileRun)
                .filter_by(file_path=str(file_path))
                .order_by(FileRun.started_at.desc())
                .limit(limit)
                .all()
            )
    
    def get_pending_files(self, plugin: Optional[str] = None, limit: int = 100) -> List[str]:
        """Get files that need processing."""
        with self.get_session() as session:
            query = session.query(ProcessingQueue).filter(
                (ProcessingQueue.scheduled_for.is_(None)) |
                (ProcessingQueue.scheduled_for <= datetime.now())
            )
            
            if plugin:
                query = query.filter_by(plugin=plugin)
            
            return [
                item.file_path
                for item in query.order_by(
                    ProcessingQueue.priority.desc(),
                    ProcessingQueue.added_at.asc()
                ).limit(limit).all()
            ]
    
    def queue_file(
        self,
        file_path: Path,
        plugin: Optional[str] = None,
        priority: int = 0,
        scheduled_for: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a file to the processing queue."""
        with self.get_session() as session:
            # Check if already queued
            existing = session.query(ProcessingQueue).filter_by(file_path=str(file_path)).first()
            if existing:
                # Update priority if higher
                if priority > existing.priority:
                    existing.priority = priority
                session.commit()
                return
            
            queue_item = ProcessingQueue(
                file_path=str(file_path),
                plugin=plugin,
                priority=priority,
                scheduled_for=scheduled_for,
                extra_data=metadata or {},
            )
            session.add(queue_item)
            session.commit()
            
            logger.info(
                "file_queued",
                file_path=str(file_path),
                plugin=plugin,
                priority=priority,
            )
    
    def mark_for_reprocessing(self, file_path: Path, reason: str) -> None:
        """Mark a file as needing reprocessing."""
        with self.get_session() as session:
            # Update the most recent run
            file_run = (
                session.query(FileRun)
                .filter_by(file_path=str(file_path))
                .order_by(FileRun.started_at.desc())
                .first()
            )
            
            if file_run:
                file_run.status = ProcessingStatus.NEEDS_REPROCESS
                if file_run.extra_data is None:
                    file_run.extra_data = {}
                file_run.extra_data["reprocess_reason"] = reason
                session.commit()
            
            # Also queue it for reprocessing
            self.queue_file(file_path, priority=5)
            
            logger.info(
                "file_marked_for_reprocessing",
                file_path=str(file_path),
                reason=reason,
            )
    
    def execute_sql(self, query: str, params: tuple = None):
        """Execute parameterized SQL query safely using SQLAlchemy.
        
        Args:
            query: SQL query string with ? placeholders for parameters
            params: Tuple of parameters to bind to placeholders
            
        Returns:
            SQLAlchemy Result object with fetchall(), fetchone(), lastrowid etc.
        """
        with self.get_session() as session:
            try:
                if params:
                    # Convert ? placeholders to SQLAlchemy named parameters
                    param_dict = {}
                    safe_query = query
                    for i, param in enumerate(params):
                        param_name = f"param_{i}"
                        param_dict[param_name] = param
                        safe_query = safe_query.replace("?", f":{param_name}", 1)
                    
                    result = session.execute(text(safe_query), param_dict)
                else:
                    # For queries without parameters, wrap in text()
                    result = session.execute(text(query))
                
                session.commit()
                
                logger.debug(
                    "sql_executed",
                    query_preview=query[:100] + "..." if len(query) > 100 else query,
                    param_count=len(params) if params else 0
                )
                
                return result
                
            except Exception as e:
                session.rollback()
                logger.error(
                    "sql_execution_failed",
                    query_preview=query[:100] + "..." if len(query) > 100 else query,
                    error=str(e)
                )
                raise