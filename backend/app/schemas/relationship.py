from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.fact import FactResponse


class RelationshipDimensions(BaseModel):
    subject: str = "same"  # 'same', 'different', 'compatible'
    predicate: str = "same"
    value: str = "same"  # 'same', 'different', 'equivalent'
    time: str = "same"  # 'same', 'different', 'subset', 'evolves'
    scope: str = "same"  # 'same', 'different', 'subset'
    unit: str = "same"  # 'same', 'converted', 'incompatible'
    measurement_basis: str = "same"  # 'same', 'different'


class RelationshipCreate(BaseModel):
    fact_a_id: str
    fact_b_id: str
    relationship_type: str  # 'CORROBORATES', 'CONTRADICTS', 'RECONCILES', 'TEMPORALLY_EVOLVES', 'SCOPE_DIFFERENCE', 'UNIT_EQUIVALENT', 'POSSIBLE_DUPLICATE', 'UNCERTAIN'
    confidence: float = 1.0
    explanation: str
    dimensions: Dict[str, Any]
    important_differences: List[str] = Field(default_factory=list)
    reasoning_basis: str = "deterministic"


class RelationshipResponse(BaseModel):
    id: str
    fact_a_id: str
    fact_b_id: str
    relationship_type: str
    confidence: float
    explanation: str
    dimensions: Dict[str, Any]
    important_differences: List[str] = Field(default_factory=list)
    reasoning_basis: str
    created_at: datetime
    
    fact_a: Optional[FactResponse] = None
    fact_b: Optional[FactResponse] = None

    model_config = {"from_attributes": True}
