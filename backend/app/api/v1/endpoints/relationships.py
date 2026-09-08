"""
Relationships API Endpoints.
Provides access to cross-document knowledge relationships, conflict resolutions, and explanations.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from app.db.session import get_db
from app.models import Relationship, Fact, EvidenceAtom
from app.schemas.relationship import RelationshipResponse
from app.schemas.fact import FactResponse, FactContextSchema, EvidenceAtomResponse
from app.services.resolver.service import RelationshipResolverService

router = APIRouter(prefix="/relationships", tags=["Relationships"])


def _to_fact_response(f: Fact) -> Optional[FactResponse]:
    if not f:
        return None
    ctx_dict = None
    if f.context:
        ctx_dict = FactContextSchema(
            time={
                "type": f.context.time_type or "unspecified",
                "start": f.context.time_start.isoformat() if f.context.time_start else None,
                "end": f.context.time_end.isoformat() if f.context.time_end else None,
                "raw": f.context.time_raw or ""
            },
            geography=f.context.geography or "India",
            scope=f.context.scope or "consolidated",
            population=f.context.population,
            measurement_basis=f.context.measurement_basis or "standard",
            qualifiers=f.context.qualifiers or []
        )
    ev_dict = EvidenceAtomResponse.model_validate(f.evidence) if f.evidence else None
    return FactResponse(
        id=f.id,
        document_id=f.document_id,
        evidence_id=f.evidence_id,
        subject_raw=f.subject_raw,
        subject_canonical=f.subject_canonical,
        predicate_raw=f.predicate_raw,
        predicate_canonical=f.predicate_canonical,
        predicate_type=f.predicate_type,
        value_raw=f.value_raw,
        value_normalized=f.value_normalized,
        value_type=f.value_type,
        unit_raw=f.unit_raw,
        unit_canonical=f.unit_canonical,
        polarity=f.polarity,
        fingerprint=f.fingerprint,
        confidence_extraction=f.confidence_extraction,
        confidence_normalization=f.confidence_normalization,
        confidence_overall=f.confidence_overall,
        confidence_level=f.confidence_level,
        created_at=f.created_at,
        context=ctx_dict,
        evidence=ev_dict
    )


@router.get("", response_model=List[RelationshipResponse])
def list_relationships(
    db: Session = Depends(get_db),
    relationship_type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Returns list of cross-document relationships with filter options and side-by-side fact details.
    """
    query = db.query(Relationship).options(
        joinedload(Relationship.fact_a).joinedload(Fact.context),
        joinedload(Relationship.fact_a).joinedload(Fact.evidence),
        joinedload(Relationship.fact_b).joinedload(Fact.context),
        joinedload(Relationship.fact_b).joinedload(Fact.evidence)
    )

    if relationship_type:
        query = query.filter(Relationship.relationship_type == relationship_type.upper())

    if subject:
        query = query.join(Fact, Relationship.fact_a_id == Fact.id).filter(
            Fact.subject_canonical.ilike(f"%{subject}%")
        )

    if document_id:
        query = query.join(Fact, Relationship.fact_a_id == Fact.id).filter(
            Fact.document_id == document_id
        )

    rels = query.order_by(Relationship.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for r in rels:
        results.append(
            RelationshipResponse(
                id=r.id,
                fact_a_id=r.fact_a_id,
                fact_b_id=r.fact_b_id,
                relationship_type=r.relationship_type,
                confidence=r.confidence,
                explanation=r.explanation,
                dimensions=r.dimensions,
                important_differences=r.important_differences or [],
                reasoning_basis=r.reasoning_basis,
                created_at=r.created_at,
                fact_a=_to_fact_response(r.fact_a),
                fact_b=_to_fact_response(r.fact_b)
            )
        )
    return results


@router.post("/resolve")
def trigger_relationship_resolution(
    document_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Triggers multi-tier candidate retrieval and decision-matrix relationship resolution.
    Returns resolution metrics and breakdown.
    """
    resolver_service = RelationshipResolverService()
    resolved_records, summary = resolver_service.resolve_cross_document_relationships(
        db=db,
        document_ids=document_ids
    )

    return {
        "status": "SUCCESS",
        "relationships_resolved": len(resolved_records),
        "summary": summary
    }


@router.get("/{relationship_id}", response_model=RelationshipResponse)
def get_relationship(relationship_id: str, db: Session = Depends(get_db)):
    """Retrieves deep side-by-side audit of a single cross-document relationship."""
    r = db.query(Relationship).options(
        joinedload(Relationship.fact_a).joinedload(Fact.context),
        joinedload(Relationship.fact_a).joinedload(Fact.evidence),
        joinedload(Relationship.fact_b).joinedload(Fact.context),
        joinedload(Relationship.fact_b).joinedload(Fact.evidence)
    ).filter(Relationship.id == relationship_id).first()

    if not r:
        raise HTTPException(status_code=404, detail=f"Relationship '{relationship_id}' not found.")

    return RelationshipResponse(
        id=r.id,
        fact_a_id=r.fact_a_id,
        fact_b_id=r.fact_b_id,
        relationship_type=r.relationship_type,
        confidence=r.confidence,
        explanation=r.explanation,
        dimensions=r.dimensions,
        important_differences=r.important_differences or [],
        reasoning_basis=r.reasoning_basis,
        created_at=r.created_at,
        fact_a=_to_fact_response(r.fact_a),
        fact_b=_to_fact_response(r.fact_b)
    )
