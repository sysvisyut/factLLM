from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.fact import FactBase
from app.schemas.relationship import RelationshipCreate
from app.models.evidence import EvidenceAtom


class LLMProvider(ABC):
    """Abstract interface for fact extraction, cross-document relationship reasoning, and explanation generation."""

    @abstractmethod
    def extract_facts(
        self,
        text: str,
        page_number: int,
        evidence_atoms: List[EvidenceAtom]
    ) -> List[FactBase]:
        """Extract structured facts from text or table evidence, adhering to Pydantic FactBase."""
        pass

    @abstractmethod
    def resolve_relationship(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any]
    ) -> RelationshipCreate:
        """Determines relationship between two facts across multiple dimensions."""
        pass

    @abstractmethod
    def generate_explanation(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any],
        dimensions: Dict[str, str],
        rel_type: str
    ) -> str:
        """Produces a grounded, auditable explanation detailing dimensional similarities and differences."""
        pass
