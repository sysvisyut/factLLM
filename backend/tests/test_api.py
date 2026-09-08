"""
Comprehensive API integration tests for all FastAPI v1 endpoints.
Tests documents, facts, relationships, issues, and analytics overview.
"""

import io
import uuid
from datetime import date
from app.models import Document, DocumentPage, EvidenceAtom, Fact, FactContext, Relationship, ExtractionIssue


def test_api_documents_list_and_detail(client, db_session):
    # Setup test document
    doc = Document(filename="test_api.pdf", content_hash="hash_api_1", file_size_bytes=1024, page_count=2, storage_path="p")
    db_session.add(doc)
    db_session.commit()

    # Test list
    res = client.get("/api/v1/documents")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["filename"] == "test_api.pdf"

    # Test detail
    res_detail = client.get(f"/api/v1/documents/{doc.id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == doc.id

    # Test 404
    res_404 = client.get(f"/api/v1/documents/{uuid.uuid4()}")
    assert res_404.status_code == 404


def test_api_document_upload(client, db_session):
    # Create synthetic PDF in memory
    import pymupdf
    pdf_doc = pymupdf.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 50), "Delhivery reported revenue of INR 8,142 Cr in FY24.")
    pdf_bytes = pdf_doc.tobytes()

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("upload_test.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["filename"] == "upload_test.pdf"
    assert "document_id" in data


def test_api_facts_list_and_detail(client, db_session):
    doc = Document(filename="facts_doc.pdf", content_hash="h_fact", file_size_bytes=100, page_count=1, storage_path="p")
    db_session.add(doc)
    db_session.flush()

    atom = EvidenceAtom(document_id=doc.id, page_number=1, exact_text="Revenue was 8142 Cr", extraction_method="native_text", source_hash="ash")
    db_session.add(atom)
    db_session.flush()

    fact = Fact(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        evidence_id=atom.id,
        subject_raw="Delhivery Limited",
        subject_canonical="Delhivery Limited",
        predicate_raw="revenue from services",
        predicate_canonical="revenue from services",
        predicate_type="financial",
        value_raw="8,142 Cr",
        value_normalized=81420000000.0,
        value_type="numeric",
        unit_canonical="INR",
        polarity="positive",
        fingerprint="fp_fact"
    )
    db_session.add(fact)
    ctx = FactContext(fact_id=fact.id, time_raw="FY24", scope="consolidated_company", measurement_basis="Standard_Reported")
    db_session.add(ctx)
    db_session.commit()

    # List facts with search
    res = client.get("/api/v1/facts?search=revenue")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["predicate_canonical"] == "revenue from services"
    assert data[0]["context"]["scope"] == "consolidated_company"

    # Detail fact
    res_detail = client.get(f"/api/v1/facts/{fact.id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == fact.id
    assert res_detail.json()["value_normalized"] == 81420000000.0

    # Test subjects and predicates lookup
    res_subs = client.get("/api/v1/facts/subjects/all")
    assert res_subs.status_code == 200
    assert "Delhivery Limited" in res_subs.json()

    res_preds = client.get("/api/v1/facts/predicates/all")
    assert res_preds.status_code == 200
    assert "revenue from services" in res_preds.json()


def test_api_relationships_and_resolve(client, db_session):
    doc1 = Document(filename="doc1.pdf", content_hash="h1", file_size_bytes=10, page_count=1, storage_path="p1")
    doc2 = Document(filename="doc2.pdf", content_hash="h2", file_size_bytes=10, page_count=1, storage_path="p2")
    db_session.add_all([doc1, doc2])
    db_session.flush()

    atom1 = EvidenceAtom(document_id=doc1.id, page_number=1, exact_text="2.8 bn parcels", extraction_method="native_text", source_hash="a1")
    atom2 = EvidenceAtom(document_id=doc2.id, page_number=2, exact_text="2.8 bn parcels", extraction_method="native_text", source_hash="a2")
    db_session.add_all([atom1, atom2])
    db_session.flush()

    f1 = Fact(
        id=str(uuid.uuid4()), document_id=doc1.id, evidence_id=atom1.id,
        subject_raw="Delhivery Limited", subject_canonical="Delhivery Limited",
        predicate_raw="express parcel shipments volume", predicate_canonical="express parcel shipments volume",
        predicate_type="operational", value_raw="2.8 bn", value_normalized=2800000000.0,
        value_type="numeric", unit_canonical="shipments", polarity="positive", fingerprint="fp1"
    )
    f2 = Fact(
        id=str(uuid.uuid4()), document_id=doc2.id, evidence_id=atom2.id,
        subject_raw="Delhivery Limited", subject_canonical="Delhivery Limited",
        predicate_raw="express parcel shipments volume", predicate_canonical="express parcel shipments volume",
        predicate_type="operational", value_raw="2.8 bn", value_normalized=2800000000.0,
        value_type="numeric", unit_canonical="shipments", polarity="positive", fingerprint="fp2"
    )
    db_session.add_all([f1, f2])

    ctx1 = FactContext(fact_id=f1.id, time_type="cumulative", scope="cumulative_since_inception", measurement_basis="Standard_Reported")
    ctx2 = FactContext(fact_id=f2.id, time_type="cumulative", scope="cumulative_since_inception", measurement_basis="Standard_Reported")
    db_session.add_all([ctx1, ctx2])
    db_session.commit()

    # Trigger resolution
    res_resolve = client.post("/api/v1/relationships/resolve")
    assert res_resolve.status_code == 200
    data_resolve = res_resolve.json()
    assert data_resolve["status"] == "SUCCESS"
    assert data_resolve["relationships_resolved"] >= 1

    # Query relationships
    res_list = client.get("/api/v1/relationships?relationship_type=CORROBORATES")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert len(data_list) >= 1
    assert data_list[0]["relationship_type"] == "CORROBORATES"
    assert data_list[0]["fact_a"] is not None
    assert data_list[0]["fact_b"] is not None


def test_api_issues_and_analytics(client, db_session):
    doc = Document(filename="issue_doc.pdf", content_hash="h_iss", file_size_bytes=10, page_count=1, storage_path="p")
    db_session.add(doc)
    db_session.flush()

    issue = ExtractionIssue(
        document_id=doc.id,
        page_number=1,
        issue_type="OCR_LOW_QUALITY",
        description="Scanned page image quality degraded",
        status="DETECTED"
    )
    db_session.add(issue)
    db_session.commit()

    # List issues
    res_issues = client.get("/api/v1/issues?issue_type=OCR_LOW_QUALITY")
    assert res_issues.status_code == 200
    assert len(res_issues.json()) >= 1

    # Analytics overview
    res_analytics = client.get("/api/v1/analytics/overview")
    assert res_analytics.status_code == 200
    data = res_analytics.json()
    assert "documents" in data
    assert "facts" in data
    assert "relationships" in data
    assert "retrieval_efficiency" in data
    assert "issues" in data
    assert data["issues"]["total_issues"] >= 1
