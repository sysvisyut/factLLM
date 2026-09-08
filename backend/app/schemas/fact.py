from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from app.schemas.evidence import EvidenceAtomResponse


class EntityInfo(BaseModel):
    canonical: str
    type: str = "organization"
    aliases: List[str] = Field(default_factory=list)


class PredicateInfo(BaseModel):
    canonical: str
    type: str = "metric"


class ValueInfo(BaseModel):
    raw: str
    normalized: Optional[float] = None
    unit: Optional[str] = None
    value_type: str = "numeric"  # 'numeric', 'text', 'ratio', 'currency'


class TimeContext(BaseModel):
    type: Optional[str] = None  # 'fiscal_year', 'quarter', 'exact_date', 'as_of', 'calendar_year'
    start: Optional[date] = None
    end: Optional[date] = None
    raw: Optional[str] = None


class FactContextSchema(BaseModel):
    time: Optional[TimeContext] = None
    geography: Optional[str] = None
    scope: Optional[str] = None  # 'consolidated_company', 'subsidiary', 'cumulative_since_inception', 'annual', 'quarterly'
    population: Optional[str] = None
    measurement_basis: Optional[str] = None  # 'GAAP', 'Non-GAAP', 'Service_EBITDA', 'Pro_forma'
    qualifiers: List[str] = Field(default_factory=list)


class ConfidenceBreakdown(BaseModel):
    extraction: float = 1.0
    normalization: float = 1.0
    overall: float = 1.0
    level: str = "HIGH"  # 'HIGH', 'MEDIUM', 'LOW', 'UNCERTAIN'


class FactBase(BaseModel):
    subject: EntityInfo
    predicate: PredicateInfo
    value: ValueInfo
    context: FactContextSchema = Field(default_factory=FactContextSchema)
    polarity: str = "positive"
    confidence: ConfidenceBreakdown = Field(default_factory=ConfidenceBreakdown)
    evidence_id: str


class FactResponse(BaseModel):
    id: str
    document_id: str
    evidence_id: str
    subject_raw: str
    subject_canonical: str
    predicate_raw: str
    predicate_canonical: str
    predicate_type: str
    value_raw: str
    value_normalized: Optional[float] = None
    value_type: str
    unit_raw: Optional[str] = None
    unit_canonical: Optional[str] = None
    polarity: str
    fingerprint: str
    confidence_extraction: float
    confidence_normalization: float
    confidence_overall: float
    confidence_level: str
    created_at: datetime
    
    # Nested Context and Evidence
    context: Optional[FactContextSchema] = None
    evidence: Optional[EvidenceAtomResponse] = None

    model_config = {"from_attributes": True}
