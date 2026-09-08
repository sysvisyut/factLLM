import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class Fact(Base):
    __tablename__ = "facts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(36), ForeignKey("evidence_atoms.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_entity_id = Column(String(36), ForeignKey("entities.id"), nullable=True, index=True)
    
    # Subject & Predicate
    subject_raw = Column(Text, nullable=False)
    subject_canonical = Column(String(255), nullable=False, index=True)
    predicate_raw = Column(Text, nullable=False)
    predicate_canonical = Column(String(255), nullable=False, index=True)
    predicate_type = Column(String(100), nullable=False, index=True)  # 'financial', 'operational', 'macroeconomic', 'governance'
    
    # Value & Units
    value_raw = Column(Text, nullable=False)
    value_normalized = Column(Float, nullable=True)  # Numeric float for calculation/comparison
    value_type = Column(String(50), nullable=False)  # 'numeric', 'text', 'ratio', 'currency'
    unit_raw = Column(String(50), nullable=True)
    unit_canonical = Column(String(50), nullable=True, index=True)  # 'INR', 'USD', 'tonnes', 'shipments', 'percent', 'days'
    polarity = Column(String(20), default="positive")  # 'positive', 'negative'
    
    # Candidate Blocking
    fingerprint = Column(String(128), nullable=False, index=True)
    
    # Confidence breakdown
    confidence_extraction = Column(Float, nullable=False, default=1.0)
    confidence_normalization = Column(Float, nullable=False, default=1.0)
    confidence_overall = Column(Float, nullable=False, default=1.0)
    confidence_level = Column(String(20), nullable=False, default="HIGH")  # 'HIGH', 'MEDIUM', 'LOW', 'UNCERTAIN'
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    document = relationship("Document", back_populates="facts")
    evidence = relationship("EvidenceAtom", back_populates="facts")
    subject_entity = relationship("Entity", back_populates="facts")
    context = relationship("FactContext", back_populates="fact", uselist=False, cascade="all, delete-orphan")
    embedding = relationship("FactEmbedding", back_populates="fact", uselist=False, cascade="all, delete-orphan")
    
    relationships_as_a = relationship("Relationship", foreign_keys="Relationship.fact_a_id", back_populates="fact_a", cascade="all, delete-orphan")
    relationships_as_b = relationship("Relationship", foreign_keys="Relationship.fact_b_id", back_populates="fact_b", cascade="all, delete-orphan")


class FactContext(Base):
    __tablename__ = "fact_contexts"

    fact_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), primary_key=True)
    time_type = Column(String(50), nullable=True)  # 'fiscal_year', 'quarter', 'exact_date', 'as_of', 'calendar_year'
    time_start = Column(Date, nullable=True, index=True)
    time_end = Column(Date, nullable=True, index=True)
    time_raw = Column(Text, nullable=True)
    geography = Column(String(100), nullable=True, index=True)
    scope = Column(String(100), nullable=True, index=True)  # 'consolidated_company', 'subsidiary', 'cumulative_since_inception', 'annual', etc.
    population = Column(Text, nullable=True)
    measurement_basis = Column(String(100), nullable=True, index=True)  # 'GAAP', 'Non-GAAP', 'Service_EBITDA', 'Pro_forma'
    qualifiers = Column(JSON, default=list)

    fact = relationship("Fact", back_populates="context")


class FactEmbedding(Base):
    __tablename__ = "fact_embeddings"

    fact_id = Column(String(36), ForeignKey("facts.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(JSON, nullable=False)  # List of floats (384-dim or similar)

    fact = relationship("Fact", back_populates="embedding")
