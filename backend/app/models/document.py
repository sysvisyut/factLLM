import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_size_bytes = Column(BigInteger, nullable=False)
    page_count = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    evidence_atoms = relationship("EvidenceAtom", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("Fact", back_populates="document", cascade="all, delete-orphan")
    issues = relationship("ExtractionIssue", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    has_tables = Column(Boolean, default=False)
    is_scanned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="pages")
