import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fact_a_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), nullable=False, index=True)
    fact_b_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Allowed types:
    # CORROBORATES, CONTRADICTS, RECONCILES, TEMPORALLY_EVOLVES, SCOPE_DIFFERENCE, UNIT_EQUIVALENT, POSSIBLE_DUPLICATE, UNCERTAIN
    relationship_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=1.0)
    explanation = Column(Text, nullable=False)
    
    # Multidimensional comparison audit
    # e.g. {"subject": "same", "predicate": "same", "value": "different", "time": "different", "scope": "same"}
    dimensions = Column(JSON, nullable=False)
    important_differences = Column(JSON, default=list)
    reasoning_basis = Column(String(50), nullable=False, default="deterministic")  # 'deterministic', 'llm_reasoning', 'hybrid'
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    fact_a = relationship("Fact", foreign_keys=[fact_a_id], back_populates="relationships_as_a")
    fact_b = relationship("Fact", foreign_keys=[fact_b_id], back_populates="relationships_as_b")
