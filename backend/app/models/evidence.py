import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class EvidenceAtom(Base):
    __tablename__ = "evidence_atoms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    section_heading = Column(Text, nullable=True)
    exact_text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    bbox = Column(JSON, nullable=True)  # [x0, y0, x1, y1]
    table_cell_info = Column(JSON, nullable=True)  # {"table_index": 0, "row": 1, "col": 2, "headers": [...]}
    extraction_method = Column(String(50), nullable=False)  # 'native_text', 'table_parser', 'ocr'
    source_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="evidence_atoms")
    facts = relationship("Fact", back_populates="evidence")
