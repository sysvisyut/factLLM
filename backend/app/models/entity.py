import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_name = Column(String(255), nullable=False, unique=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # 'organization', 'country', 'person', etc.
    aliases = Column(JSON, default=list)  # ["Delhivery", "Delhivery Ltd."]
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    facts = relationship("Fact", back_populates="subject_entity")
