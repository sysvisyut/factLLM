"""
Facts API Endpoints.
Provides filterable, paginated query access to the Fact Ledger and verbatim evidence provenance.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.db.session import get_db
from app.models import Fact, FactContext, EvidenceAtom, Relationship
from app.schemas.fact import FactResponse, FactContextSchema, EvidenceAtomResponse

router = APIRouter(prefix="/facts", tags=["Facts"])


@router.get("", response_model=List[FactResponse])
def list_facts(
    db: Session = Depends(get_db),
    document_id: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    predicate: Optional[str] = Query(None),
    predicate_type: Optional[str] = Query(None),
    confidence_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Returns filterable, paginated facts with attached evidence and context.
    """
    query = db.query(Fact).options(
        joinedload(Fact.context),
        joinedload(Fact.evidence)
    )

    if document_id:
        query = query.filter(Fact.document_id == document_id)
    if subject:
        query = query.filter(Fact.subject_canonical.ilike(f"%{subject}%"))
    if predicate:
        query = query.filter(Fact.predicate_canonical.ilike(f"%{predicate}%"))
    if predicate_type:
        query = query.filter(Fact.predicate_type == predicate_type)
    if confidence_level:
        query = query.filter(Fact.confidence_level == confidence_level.upper())
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Fact.predicate_canonical.ilike(search_pattern),
                Fact.subject_canonical.ilike(search_pattern),
                Fact.value_raw.ilike(search_pattern)
            )
        )

    facts = query.order_by(Fact.created_at.desc()).offset(offset).limit(limit).all()

    # Format responses
    results = []
    for f in facts:
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

        results.append(
            FactResponse(
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
        )
    return results


@router.get("/subjects/all")
def list_distinct_subjects(db: Session = Depends(get_db)):
    """Returns list of all distinct canonical subjects in the knowledge base."""
    subjects = db.query(Fact.subject_canonical).distinct().all()
    return [s[0] for s in subjects if s[0]]


@router.get("/predicates/all")
def list_distinct_predicates(db: Session = Depends(get_db)):
    """Returns list of all distinct canonical predicates in the knowledge base."""
    predicates = db.query(Fact.predicate_canonical).distinct().all()
    return [p[0] for p in predicates if p[0]]


@router.get("/{fact_id}", response_model=FactResponse)
def get_fact(fact_id: str, db: Session = Depends(get_db)):
    """Retrieves deep details for a single fact including its context and verbatim evidence atom."""
    f = db.query(Fact).options(
        joinedload(Fact.context),
        joinedload(Fact.evidence)
    ).filter(Fact.id == fact_id).first()

    if not f:
        raise HTTPException(status_code=404, detail=f"Fact '{fact_id}' not found.")

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
