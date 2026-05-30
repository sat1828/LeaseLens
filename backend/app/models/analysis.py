from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.session import Base


class LeaseType(str, enum.Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    UNKNOWN = "UNKNOWN"


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Input
    jurisdiction = Column(String(255), nullable=False)
    original_filename = Column(String(500))
    lease_type = Column(Enum(LeaseType), default=LeaseType.UNKNOWN)
    pages_analyzed = Column(Integer, default=0)

    # Results
    fairness_score = Column(Integer)
    lease_summary = Column(JSONB)
    risk_summary = Column(JSONB)
    clauses = Column(JSONB)
    top_3_priorities = Column(JSONB)
    counter_proposal_letter = Column(Text)

    # Performance
    processing_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    model_used = Column(String(100))

    # Lifecycle
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    purge_after = Column(DateTime(timezone=True))

    user = relationship("User", backref="analyses")


class LegalChunk(Base):
    """RAG vector store — populated by scripts/ingest_laws.py"""
    __tablename__ = "legal_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=False)
    section_ref = Column(String(200))
    jurisdiction_tag = Column(String(100), index=True)
    chunk_index = Column(Integer)
    # embedding vector(1024) added via Alembic migration — pgvector type
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(200))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    extra_data = Column(JSONB)  # renamed from 'metadata' — reserved by SQLAlchemy
    created_at = Column(DateTime(timezone=True), server_default=func.now())
