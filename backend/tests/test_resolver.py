"""
Unit tests for Multidimensional Relationship Resolver.
Verifies decision matrix resolution for:
1. CORROBORATES
2. CONTRADICTS
3. RECONCILES (Apparent contradiction resolved via measurement basis/accounting standard)
4. TEMPORALLY_EVOLVES
5. SCOPE_DIFFERENCE
6. UNIT_EQUIVALENT
"""

import uuid
from datetime import date
from app.models import Document, EvidenceAtom, Fact, FactContext, Relationship
from app.services.resolver import (
    DimensionComparator,
    DecisionMatrixEngine,
    RelationshipExplainer,
    RelationshipResolverService
)
from app.services.retrieval.candidate_pair import CandidatePair


def build_test_fact(
    doc_id: str,
    subj: str,
    pred: str,
    raw_val: str,
    norm_val: float,
    unit: str,
    scope: str = "consolidated",
    t_start: date = None,
    t_end: date = None,
    t_raw: str = "FY24",
    basis: str = "standard",
    polarity: str = "positive"
) -> Fact:
    f = Fact(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        evidence_id=str(uuid.uuid4()),
        subject_raw=subj,
        subject_canonical=subj,
        predicate_raw=pred,
        predicate_canonical=pred,
        predicate_type="financial",
        value_raw=raw_val,
        value_normalized=norm_val,
        value_type="numeric",
        unit_raw=unit,
        unit_canonical=unit,
        polarity=polarity,
        fingerprint=str(uuid.uuid4())
    )
    f.context = FactContext(
        fact_id=f.id,
        time_start=t_start,
        time_end=t_end,
        time_raw=t_raw,
        scope=scope,
        measurement_basis=basis
    )
    return f


def test_corroborates_resolution():
    # Identical numbers, same period, same basis
    fa = build_test_fact("doc1", "Delhivery Limited", "revenue from services", "₹8,142 Cr", 81420000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), basis="Standard_Reported")
    fb = build_test_fact("doc2", "Delhivery Limited", "revenue from services", "₹8,142 Cr", 81420000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), basis="Standard_Reported")

    res = DecisionMatrixEngine.resolve_relationship(fa, fb)
    assert res.relationship_type == "CORROBORATES"
    assert res.confidence >= 0.95
    assert res.dimensions["value_match"] is True
    assert res.dimensions["temporal_match"] is True


def test_contradicts_resolution():
    # Same period, same basis, same scope, but conflicting numbers
    fa = build_test_fact("doc1", "Delhivery Limited", "revenue from services", "₹8,142 Cr", 81420000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), basis="Standard_Reported")
    fb = build_test_fact("doc2", "Delhivery Limited", "revenue from services", "₹9,500 Cr", 95000000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), basis="Standard_Reported")

    res = DecisionMatrixEngine.resolve_relationship(fa, fb)
    assert res.relationship_type == "CONTRADICTS"
    assert res.confidence >= 0.90
    assert res.dimensions["value_match"] is False


def test_reconciles_via_measurement_basis():
    # Apparent contradiction: 6.4% vs 6.5%, but different revision basis (FAE vs SAE)
    fa = build_test_fact("doc1", "Republic of India", "real GDP growth rate", "6.4%", 6.4, "percent",
                         t_start=date(2024, 4, 1), t_end=date(2025, 3, 31), basis="First_Advance_Estimates")
    fb = build_test_fact("doc2", "Republic of India", "real GDP growth rate", "6.5%", 6.5, "percent",
                         t_start=date(2024, 4, 1), t_end=date(2025, 3, 31), basis="Second_Advance_Estimates")

    res = DecisionMatrixEngine.resolve_relationship(fa, fb)
    assert res.relationship_type == "RECONCILES"
    assert res.reconciliation_variable == "measurement_basis"
    assert res.dimensions["basis_match"] is False


def test_temporally_evolves_resolution():
    # Different periods: FY22 vs FY24
    fa = build_test_fact("doc1", "Delhivery Limited", "revenue from services", "₹5,000 Cr", 50000000000.0, "INR",
                         t_start=date(2021, 4, 1), t_end=date(2022, 3, 31), t_raw="FY22")
    fb = build_test_fact("doc2", "Delhivery Limited", "revenue from services", "₹8,142 Cr", 81420000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), t_raw="FY24")

    res = DecisionMatrixEngine.resolve_relationship(fa, fb)
    assert res.relationship_type == "TEMPORALLY_EVOLVES"
    assert res.reconciliation_variable == "time_period"


def test_scope_difference_resolution():
    # Consolidated vs Subsidiary (Spoton)
    fa = build_test_fact("doc1", "Delhivery Limited", "express parcel shipments volume", "2.8 Bn", 2800000000.0, "shipments",
                         scope="consolidated_company")
    fb = build_test_fact("doc2", "Spoton Logistics", "express parcel shipments volume", "150 Mn", 150000000.0, "shipments",
                         scope="subsidiary")

    res = DecisionMatrixEngine.resolve_relationship(fa, fb)
    assert res.relationship_type == "SCOPE_DIFFERENCE"
    assert res.reconciliation_variable == "operational_scope"


def test_unit_equivalent_resolution():
    # Raw scales differ (Cr vs Mn), but normalized base values coincide
    fa = build_test_fact("doc1", "Delhivery Limited", "revenue from services", "₹8,142 Cr", 81420000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), basis="Standard_Reported")
    fa.unit_raw = "Cr"

    fb = build_test_fact("doc2", "Delhivery Limited", "revenue from services", "₹81,420 Mn", 81420000000.0, "INR",
                         t_start=date(2023, 4, 1), t_end=date(2024, 3, 31), basis="Standard_Reported")
    fb.unit_raw = "Mn"

    res = DecisionMatrixEngine.resolve_relationship(fa, fb)
    assert res.relationship_type == "UNIT_EQUIVALENT"


def test_resolver_service_end_to_end(db_session):
    doc1 = Document(filename="docA.pdf", content_hash="ha", file_size_bytes=100, page_count=1, storage_path="pA")
    doc2 = Document(filename="docB.pdf", content_hash="hb", file_size_bytes=100, page_count=1, storage_path="pB")
    db_session.add_all([doc1, doc2])
    db_session.flush()

    atom1 = EvidenceAtom(document_id=doc1.id, page_number=1, exact_text="Delivered >2.8 Bn parcels", extraction_method="native_text", source_hash="sa")
    atom2 = EvidenceAtom(document_id=doc2.id, page_number=5, exact_text="Over 2.8 Bn express parcel shipments", extraction_method="native_text", source_hash="sb")
    db_session.add_all([atom1, atom2])
    db_session.flush()

    fa = build_test_fact(doc1.id, "Delhivery Limited", "express parcel shipments volume", ">2.8 Bn", 2800000000.0, "shipments")
    fa.evidence_id = atom1.id
    fb = build_test_fact(doc2.id, "Delhivery Limited", "express parcel shipments volume", ">2.8 Bn", 2800000000.0, "shipments")
    fb.evidence_id = atom2.id

    db_session.add_all([fa, fb, fa.context, fb.context])
    db_session.commit()

    service = RelationshipResolverService()
    resolved, summary = service.resolve_cross_document_relationships(db_session)

    assert len(resolved) == 1
    assert resolved[0].relationship_type == "CORROBORATES"
    assert "corroborate" in resolved[0].explanation.lower()
    assert summary["breakdown"]["CORROBORATES"] == 1
