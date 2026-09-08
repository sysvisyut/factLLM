"""
Unit tests for Candidate Retrieval, Semantic Predicate Clustering,
Multi-tier Blocking, and Search Space Reduction Metrics.
"""

from datetime import date
import uuid
from app.services.retrieval import (
    PredicateClusterRegistry,
    get_predicate_family,
    CandidatePair,
    BlockingEngine,
    CandidateRetrievalService
)
from app.models import Document, EvidenceAtom, Fact, FactContext


def create_dummy_fact(doc_id: str, subj: str, pred: str, val: float, unit: str = "INR") -> Fact:
    f = Fact(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        evidence_id=str(uuid.uuid4()),
        subject_raw=subj,
        subject_canonical=subj,
        predicate_raw=pred,
        predicate_canonical=pred,
        predicate_type="financial",
        value_raw=str(val),
        value_normalized=val,
        value_type="numeric",
        unit_canonical=unit,
        polarity="positive",
        fingerprint=str(uuid.uuid4())
    )
    return f


def test_predicate_family_classification():
    assert get_predicate_family("revenue from services") == "REVENUE"
    assert get_predicate_family("total revenue") == "REVENUE"
    assert get_predicate_family("service EBITDA") == "EBITDA"
    assert get_predicate_family("adjusted EBITDA") == "EBITDA"
    assert get_predicate_family("ptl freight tonnage") == "FREIGHT_VOLUME"
    assert get_predicate_family("express parcel shipments volume") == "PARCEL_VOLUME"
    assert get_predicate_family("real GDP growth rate") == "GDP_GROWTH"
    assert get_predicate_family("gross fiscal deficit") == "FISCAL_DEFICIT"
    assert get_predicate_family("current account deficit") == "CURRENT_ACCOUNT_DEFICIT"


def test_blocking_engine_excludes_same_document():
    engine = BlockingEngine()
    doc1 = "doc-1"

    f1 = create_dummy_fact(doc1, "Delhivery Limited", "revenue from services", 81420000000.0)
    f2 = create_dummy_fact(doc1, "Delhivery Limited", "revenue from services", 81420000000.0)

    pairs, metrics = engine.retrieve_candidate_pairs([f1, f2])
    assert len(pairs) == 0
    assert metrics.naive_comparisons == 1
    assert metrics.candidate_pairs_count == 0


def test_blocking_engine_groups_same_entity_and_family():
    engine = BlockingEngine()
    doc1, doc2 = "doc-1", "doc-2"

    # Fact A in Doc 1 and Fact B in Doc 2 share entity and family (EBITDA)
    f1 = create_dummy_fact(doc1, "Delhivery Limited", "service EBITDA", 1270000000.0)
    f2 = create_dummy_fact(doc2, "Delhivery Limited", "adjusted EBITDA", 1270000000.0)

    pairs, metrics = engine.retrieve_candidate_pairs([f1, f2])
    assert len(pairs) == 1
    assert pairs[0].blocking_key == "delhivery limited::ebitda"
    assert pairs[0].fact_a_id in (f1.id, f2.id)
    assert pairs[0].fact_b_id in (f1.id, f2.id)


def test_blocking_engine_prunes_different_entities():
    engine = BlockingEngine()
    doc1, doc2 = "doc-1", "doc-2"

    f1 = create_dummy_fact(doc1, "Delhivery Limited", "revenue from services", 81420000000.0)
    f2 = create_dummy_fact(doc2, "Spoton Logistics", "revenue from services", 1000000000.0)

    pairs, metrics = engine.retrieve_candidate_pairs([f1, f2])
    assert len(pairs) == 0


def test_candidate_reduction_exceeds_90_percent():
    engine = BlockingEngine()
    
    # Create 30 diverse facts across 3 documents, 3 entities, and 5 metric families
    entities = ["Delhivery Limited", "Republic of India", "Reserve Bank of India"]
    metrics = [
        "revenue from services", "service EBITDA", "ptl freight tonnage",
        "real GDP growth rate", "gross fiscal deficit"
    ]
    docs = ["doc-1", "doc-2", "doc-3"]

    facts = []
    for d in docs:
        for ent in entities:
            for m in metrics:
                facts.append(create_dummy_fact(d, ent, m, 100.0))

    # Total facts = 3 * 3 * 5 = 45 facts
    # Naive pairs = 45 * 44 / 2 = 990 comparisons
    pairs, metrics_obj = engine.retrieve_candidate_pairs(facts)

    assert metrics_obj.naive_comparisons == 990
    assert metrics_obj.reduction_percent > 90.0, f"Expected >90% reduction, got {metrics_obj.reduction_percent:.2f}%"
    print(f"Reduction metric: {metrics_obj.reduction_percent:.2f}% ({metrics_obj.naive_comparisons} -> {metrics_obj.candidate_pairs_count} pairs)")


def test_candidate_retrieval_service_with_database(db_session):
    # Setup test documents and facts in DB
    doc1 = Document(filename="doc1.pdf", content_hash="h1", file_size_bytes=10, page_count=1, storage_path="p1")
    doc2 = Document(filename="doc2.pdf", content_hash="h2", file_size_bytes=10, page_count=1, storage_path="p2")
    db_session.add_all([doc1, doc2])
    db_session.flush()

    atom1 = EvidenceAtom(document_id=doc1.id, page_number=1, exact_text="text1", extraction_method="native_text", source_hash="sh1")
    atom2 = EvidenceAtom(document_id=doc2.id, page_number=1, exact_text="text2", extraction_method="native_text", source_hash="sh2")
    db_session.add_all([atom1, atom2])
    db_session.flush()

    f1 = Fact(
        id=str(uuid.uuid4()),
        document_id=doc1.id,
        evidence_id=atom1.id,
        subject_raw="Republic of India",
        subject_canonical="Republic of India",
        predicate_raw="real GDP growth rate",
        predicate_canonical="real GDP growth rate",
        predicate_type="macroeconomic",
        value_raw="6.4%",
        value_normalized=6.4,
        value_type="numeric",
        unit_canonical="percent",
        polarity="positive",
        fingerprint="fp1"
    )
    f2 = Fact(
        id=str(uuid.uuid4()),
        document_id=doc2.id,
        evidence_id=atom2.id,
        subject_raw="Republic of India",
        subject_canonical="Republic of India",
        predicate_raw="GDP growth",
        predicate_canonical="real GDP growth rate",
        predicate_type="macroeconomic",
        value_raw="6.5%",
        value_normalized=6.5,
        value_type="numeric",
        unit_canonical="percent",
        polarity="positive",
        fingerprint="fp2"
    )
    db_session.add_all([f1, f2])

    ctx1 = FactContext(fact_id=f1.id, scope="national_economy", measurement_basis="First_Advance_Estimates")
    ctx2 = FactContext(fact_id=f2.id, scope="national_economy", measurement_basis="Second_Advance_Estimates")
    db_session.add_all([ctx1, ctx2])
    db_session.commit()

    service = CandidateRetrievalService()
    candidate_pairs, metrics = service.get_candidate_pairs(db_session)

    assert len(candidate_pairs) == 1
    assert candidate_pairs[0].blocking_key == "republic of india::gdp_growth"
    assert candidate_pairs[0].fact_a.context is not None
    assert candidate_pairs[0].fact_b.context is not None
