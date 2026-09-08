import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    stage = Column(String(50), nullable=False, default="QUEUED")
    status = Column(String(50), nullable=False, default="QUEUED", index=True)  # 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL'
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="jobs")
