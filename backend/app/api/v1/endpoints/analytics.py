"""
Analytics API Endpoints.
Computes and serves system-wide knowledge layer metrics, search reduction rates,
relationship breakdowns, and provenance integrity stats.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter
from app.db.session import get_db
from app.models import Document, DocumentPage, EvidenceAtom, Fact, Relationship, ExtractionIssue
from app.services.retrieval.service import CandidateRetrievalService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns high-level analytical metrics across documents, facts, relationships,
    search space reduction, and extraction issues.
    """
    # 1. Document metrics
    total_docs = db.query(Document).count()
    total_pages = db.query(DocumentPage).count()
    total_atoms = db.query(EvidenceAtom).count()

    # 2. Fact metrics
    total_facts = db.query(Fact).count()
    confidence_counts = Counter(
        f.confidence_level for f in db.query(Fact.confidence_level).all()
    )

    # 3. Relationship metrics
    total_relationships = db.query(Relationship).count()
    rel_counts = Counter(
        r.relationship_type for r in db.query(Relationship.relationship_type).all()
    )

    # 4. Search space reduction metrics
    retrieval_svc = CandidateRetrievalService()
    _, retrieval_metrics = retrieval_svc.get_candidate_pairs(db)

    # 5. Issues metrics
    total_issues = db.query(ExtractionIssue).count()
    issue_counts = Counter(
        i.issue_type for i in db.query(ExtractionIssue.issue_type).all()
    )

    return {
        "documents": {
            "total_documents": total_docs,
            "total_pages": total_pages,
            "total_evidence_atoms": total_atoms
        },
        "facts": {
            "total_facts": total_facts,
            "confidence_breakdown": dict(confidence_counts)
        },
        "relationships": {
            "total_relationships": total_relationships,
            "breakdown": dict(rel_counts)
        },
        "retrieval_efficiency": retrieval_metrics.to_dict(),
        "issues": {
            "total_issues": total_issues,
            "breakdown": dict(issue_counts)
        }
    }
