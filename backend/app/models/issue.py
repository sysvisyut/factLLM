import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ExtractionIssue(Base):
    __tablename__ = "extraction_issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    page_number = Column(Integer, nullable=True, index=True)
    
    # Allowed issue types:
    # AMBIGUOUS_TABLE_ASSOCIATION, OCR_FAILURE, MISSING_CONTEXT, ENTITY_AMBIGUITY,
    # UNIT_AMBIGUITY, TEMPORAL_AMBIGUITY, LLM_EXTRACTION_FAILURE, CONFLICTING_EVIDENCE
    issue_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    affected_text = Column(Text, nullable=True)
    attempted_resolution = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="DETECTED")  # 'DETECTED', 'RESOLVED', 'UNRESOLVED'
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="issues")
