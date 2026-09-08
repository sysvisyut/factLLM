"""
Tests asserting that all 4 required assignment demonstration cases are 
present, valid, and properly resolved in the FACTMESH knowledge base.
"""

import pytest
from app.db.session import SessionLocal
from app.models.relationship import Relationship
from app.models.fact import Fact
from app.models.issue import ExtractionIssue


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_case_1_corroboration_or_unit_equivalence(db):
    """Case 1: Direct Corroboration / Unit Equivalence across independent documents."""
    rels = (
        db.query(Relationship)
        .filter(Relationship.relationship_type.in_(["CORROBORATES", "UNIT_EQUIVALENT"]))
        .all()
    )
    assert len(rels) >= 1, "Expected at least 1 corroborating or unit-equivalent cross-document pair"
    
    # Verify properties of the match
    rel = rels[0]
    assert rel.confidence >= 0.85
    assert rel.fact_a_id != rel.fact_b_id
    assert rel.fact_a is not None
    assert rel.fact_b is not None
    assert rel.explanation is not None and len(rel.explanation) > 20
    # Both facts must be provenance-grounded with an evidence atom
    assert rel.fact_a.evidence_id is not None
    assert rel.fact_b.evidence_id is not None


def test_case_2_direct_contradiction(db):
    """Case 2: Direct Contradiction under identical context and measurement basis."""
    contradictions = (
        db.query(Relationship)
        .filter(Relationship.relationship_type == "CONTRADICTS")
        .all()
    )
    assert len(contradictions) >= 1, "Expected at least 1 direct factual contradiction"

    contra = contradictions[0]
    assert contra.confidence >= 0.85
    assert contra.dimensions["value_match"] is False
    assert contra.dimensions["scope_match"] is True
    assert contra.dimensions["basis_match"] is True
    assert contra.explanation is not None
    assert "contradiction" in contra.explanation.lower()


def test_case_3_reconciliation_by_context(db):
    """Case 3: Apparent contradiction reconciled by context (Scope, Basis, or Estimate stage)."""
    reconciled = (
        db.query(Relationship)
        .filter(Relationship.relationship_type == "RECONCILES")
        .all()
    )
    assert len(reconciled) >= 1, "Expected at least 1 context-reconciled relationship"

    rec = reconciled[0]
    assert rec.confidence >= 0.85
    # Context must differ (e.g. basis or scope)
    assert (rec.dimensions.get("basis_match") is False or rec.dimensions.get("scope_match") is False)
    assert "reconciled by context" in rec.explanation.lower()


def test_case_4_honest_extraction_failure_handling(db):
    """Case 4: Honest extraction failure handling without silent hallucination."""
    issues = db.query(ExtractionIssue).all()
    assert len(issues) >= 1, "Expected at least 1 registered extraction issue/warning"

    for iss in issues:
        assert iss.issue_type is not None
        assert iss.description is not None
        assert iss.document_id is not None
