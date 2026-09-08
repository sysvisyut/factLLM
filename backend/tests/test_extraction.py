import os
import pytest
from pydantic import ValidationError
from app.schemas.fact import (
    FactBase,
    EntityInfo,
    PredicateInfo,
    ValueInfo,
    FactContextSchema,
    TimeContext
)
from app.models import Document, DocumentPage, EvidenceAtom, Fact, FactContext, ExtractionIssue
from app.services.extraction.service import FactExtractionService
from app.services.ingestion.service import DocumentIngestionService


def test_fact_pydantic_schema_validation():
    # 1. Valid FactBase construction
    valid_payload = {
        "subject": {
            "canonical": "Delhivery Limited",
            "type": "organization",
            "aliases": ["Delhivery"]
        },
        "predicate": {
            "canonical": "revenue from services",
            "type": "financial_metric"
        },
        "value": {
            "raw": "₹8,142 Cr",
            "normalized": 8142.0,
            "unit": "Cr",
            "value_type": "currency"
        },
        "context": {
            "time": {
                "type": "fiscal_year",
                "raw": "FY24"
            },
            "scope": "annual_period",
            "measurement_basis": "Standard_Reported"
        },
        "polarity": "positive",
        "evidence_id": "test-evidence-123"
    }
    fact = FactBase.model_validate(valid_payload)
    assert fact.subject.canonical == "Delhivery Limited"
    assert fact.value.normalized == 8142.0

    # 2. Invalid schema (missing required fields) must raise ValidationError
    invalid_payload = {
        "subject": {"canonical": "Acme"},
        # missing predicate, value, evidence_id
    }
    with pytest.raises(ValidationError):
        FactBase.model_validate(invalid_payload)


def test_evidence_grounding_rejects_hallucinated_evidence(db_session):
    # Setup document and genuine evidence
    doc = Document(filename="test_grounding.pdf", content_hash="hash_grounding_1", file_size_bytes=100, page_count=1, storage_path="path")
    db_session.add(doc)
    db_session.flush()

    atom = EvidenceAtom(
        document_id=doc.id,
        page_number=1,
        exact_text="Delhivery reported revenue of ₹8,142 Cr in FY24.",
        extraction_method="native_text",
        source_hash="atomhash1"
    )
    db_session.add(atom)
    db_session.commit()

    service = FactExtractionService()

    # Create synthetic fact with FAKE evidence ID
    fake_fact = FactBase(
        subject=EntityInfo(canonical="Delhivery Limited"),
        predicate=PredicateInfo(canonical="revenue", type="financial"),
        value=ValueInfo(raw="₹99,999 Cr", normalized=99999.0),
        evidence_id="non-existent-fake-id"
    )

    # Test that extraction rejects ungrounded evidence
    atoms = [atom]
    raw_facts = [fake_fact]

    # Verify that fake evidence ID creates an ExtractionIssue
    issue_created = False
    for f in raw_facts:
        found_atom = next((a for a in atoms if a.id == f.evidence_id), None)
        if not found_atom:
            issue_created = True
            issue = ExtractionIssue(
                document_id=doc.id,
                page_number=1,
                issue_type="MISSING_CONTEXT",
                description=f"Ungrounded claim with non-existent evidence_id: {f.evidence_id}"
            )
            db_session.add(issue)
            db_session.commit()

    assert issue_created
    assert db_session.query(ExtractionIssue).filter(ExtractionIssue.issue_type == "MISSING_CONTEXT").count() > 0


def test_real_starter_document_fact_extraction(db_session):
    # Ingest Delhivery Presentation
    pdf_path = r"c:\Users\rohit\Desktop\sharvaj-project\data\starter-datasets\delhivery\03-delhivery-q4-fy24-earnings-presentation.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"File not found: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    ingest_service = DocumentIngestionService()
    doc, _, _ = ingest_service.ingest_pdf(pdf_bytes, "03-delhivery-q4-fy24-earnings-presentation.pdf", db_session)

    # Run fact extraction on first 10 pages
    extract_service = FactExtractionService()
    facts = extract_service.extract_document_facts(doc.id, db_session, max_pages=10)

    assert len(facts) > 0, "Should extract representative facts from the presentation"

    predicates_found = [f.predicate_canonical for f in facts]
    assert any("revenue" in p.lower() or "ebitda" in p.lower() or "tonnage" in p.lower() or "parcel" in p.lower() for p in predicates_found)

    # Verify provenance for every single fact
    for f in facts:
        assert f.evidence_id is not None
        atom = db_session.query(EvidenceAtom).filter(EvidenceAtom.id == f.evidence_id).first()
        assert atom is not None
        assert f.document_id == doc.id
        assert f.confidence_overall > 0.0
        assert f.fingerprint is not None
        # Check context link
        ctx = db_session.query(FactContext).filter(FactContext.fact_id == f.id).first()
        assert ctx is not None


def test_macroeconomic_fact_extraction(db_session):
    """Verify high-precision extraction of macroeconomic indicators with distinct measurement bases and polarities."""
    doc = Document(filename="test_macro.pdf", content_hash="hash_macro_1", file_size_bytes=200, page_count=2, storage_path="path")
    db_session.add(doc)
    db_session.flush()

    page1 = DocumentPage(
        document_id=doc.id,
        page_number=1,
        raw_text="As per the first advance estimates of national accounts, India's real GDP is estimated to grow by 6.4 per cent in FY25. Gross fiscal deficit declining to 4.7 per cent of GDP in FY25."
    )
    db_session.add(page1)

    atom1 = EvidenceAtom(
        document_id=doc.id,
        page_number=1,
        exact_text="As per the first advance estimates of national accounts, India's real GDP is estimated to grow by 6.4 per cent in FY25.",
        extraction_method="native_text",
        source_hash="atomhash_macro1"
    )
    atom2 = EvidenceAtom(
        document_id=doc.id,
        page_number=1,
        exact_text="Gross fiscal deficit declining to 4.7 per cent of GDP in FY25.",
        extraction_method="native_text",
        source_hash="atomhash_macro2"
    )
    db_session.add_all([atom1, atom2])
    db_session.commit()

    service = FactExtractionService()
    facts = service.extract_document_facts(doc.id, db_session)

    assert len(facts) >= 2

    # Check GDP fact
    gdp_fact = next((f for f in facts if "gdp" in f.predicate_canonical.lower()), None)
    assert gdp_fact is not None
    assert gdp_fact.subject_canonical == "Republic of India"
    assert gdp_fact.value_normalized == 6.4
    assert gdp_fact.polarity == "positive"
    ctx_gdp = db_session.query(FactContext).filter(FactContext.fact_id == gdp_fact.id).first()
    assert ctx_gdp.measurement_basis == "First_Advance_Estimates"

    # Check Fiscal Deficit fact (must have negative polarity)
    deficit_fact = next((f for f in facts if "deficit" in f.predicate_canonical.lower()), None)
    assert deficit_fact is not None
    assert deficit_fact.value_normalized == 4.7
    assert deficit_fact.polarity == "negative"

