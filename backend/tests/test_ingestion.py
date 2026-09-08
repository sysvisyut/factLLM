import os
import io
import pymupdf
import pytest
from app.models import Document, DocumentPage, EvidenceAtom, ExtractionIssue
from app.services.ingestion.hasher import compute_sha256, compute_text_hash
from app.services.ingestion.service import DocumentIngestionService
from app.services.ingestion.pdf_extractor import PDFExtractor


def create_synthetic_pdf(text_pages: list) -> bytes:
    """Creates an in-memory PDF with specified text pages for synthetic testing."""
    doc = pymupdf.open()
    for text in text_pages:
        page = doc.new_page()
        page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_hashing_utilities():
    data = b"Hello FACTMESH Knowledge Layer"
    hash1 = compute_sha256(data)
    assert len(hash1) == 64
    assert hash1 == compute_sha256(data)

    # Text hash should ignore extraneous whitespace
    thash1 = compute_text_hash("Acme Corp revenue is $10M.")
    thash2 = compute_text_hash("  Acme  Corp  revenue is   $10M. \n")
    assert thash1 == thash2


def test_synthetic_pdf_ingestion(db_session):
    pages = [
        "FINANCIAL HIGHLIGHTS\nAcme Corporation achieved revenue of $500 million in fiscal year 2024.",
        "OPERATIONAL METRICS\nAcme deployed 1,200 vehicles across North America."
    ]
    pdf_bytes = create_synthetic_pdf(pages)

    service = DocumentIngestionService()
    doc, is_dup, job = service.ingest_pdf(pdf_bytes, "synthetic_test.pdf", db_session)

    assert not is_dup
    assert doc.filename == "synthetic_test.pdf"
    assert doc.page_count == 2
    assert job.status == "COMPLETED"

    # Verify pages in DB
    pages_db = db_session.query(DocumentPage).filter(DocumentPage.document_id == doc.id).order_by(DocumentPage.page_number).all()
    assert len(pages_db) == 2
    assert "revenue of $500 million" in pages_db[0].raw_text

    # Verify EvidenceAtoms in DB
    atoms = db_session.query(EvidenceAtom).filter(EvidenceAtom.document_id == doc.id).all()
    assert len(atoms) >= 2
    
    # Grounding check: ensure every atom's text is present in the page's raw text
    for atom in atoms:
        page = next(p for p in pages_db if p.page_number == atom.page_number)
        assert atom.exact_text in page.raw_text or atom.exact_text.replace(" ", "") in page.raw_text.replace(" ", "")


def test_duplicate_detection(db_session):
    pdf_bytes = create_synthetic_pdf(["Duplicate Document Test Content"])
    service = DocumentIngestionService()

    doc1, is_dup1, job1 = service.ingest_pdf(pdf_bytes, "doc1.pdf", db_session)
    assert not is_dup1

    doc2, is_dup2, job2 = service.ingest_pdf(pdf_bytes, "doc2_renamed.pdf", db_session)
    assert is_dup2
    assert doc1.id == doc2.id
    assert job2 is None


def test_real_starter_pdf_ingestion(db_session):
    pdf_path = r"c:\Users\rohit\Desktop\sharvaj-project\data\starter-datasets\delhivery\03-delhivery-q4-fy24-earnings-presentation.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"Starter PDF not found at {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    service = DocumentIngestionService()
    doc, is_dup, job = service.ingest_pdf(pdf_bytes, "03-delhivery-q4-fy24-earnings-presentation.pdf", db_session)

    assert not is_dup
    assert doc.page_count == 27
    assert job.status == "COMPLETED"

    # Check evidence atoms
    atoms = db_session.query(EvidenceAtom).filter(EvidenceAtom.document_id == doc.id).all()
    assert len(atoms) > 50

    # Ensure bounding boxes exist and are valid 4-element lists
    atoms_with_bbox = [a for a in atoms if a.bbox is not None]
    assert len(atoms_with_bbox) > 0
    assert len(atoms_with_bbox[0].bbox) == 4

    # Verify table extraction happened
    table_atoms = [a for a in atoms if a.extraction_method == "table_parser"]
    assert len(table_atoms) > 0
    assert table_atoms[0].table_cell_info is not None
    assert "headers" in table_atoms[0].table_cell_info
