import os
import glob
from app.db.session import SessionLocal, init_db
from app.services.ingestion.service import DocumentIngestionService
from app.models import Document, DocumentPage, EvidenceAtom, ExtractionIssue


def test_ingest_all_six_starter_pdfs():
    """Validates ingestion and EvidenceAtom extraction across all 6 starter PDFs."""
    init_db()
    db = SessionLocal()
    service = DocumentIngestionService()

    base_dir = r"c:\Users\rohit\Desktop\sharvaj-project\data\starter-datasets"
    pdf_files = glob.glob(os.path.join(base_dir, "**", "*.pdf"), recursive=True)
    assert len(pdf_files) == 6, f"Expected 6 starter PDFs, found {len(pdf_files)}"

    summary_results = []

    for fpath in sorted(pdf_files):
        fname = os.path.basename(fpath)
        with open(fpath, "rb") as f:
            pdf_bytes = f.read()

        doc, is_dup, job = service.ingest_pdf(pdf_bytes, fname, db)
        
        # Query results
        pages_count = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).count()
        evidence_count = db.query(EvidenceAtom).filter(EvidenceAtom.document_id == doc.id).count()
        table_atoms_count = db.query(EvidenceAtom).filter(
            EvidenceAtom.document_id == doc.id,
            EvidenceAtom.extraction_method == "table_parser"
        ).count()
        issues_count = db.query(ExtractionIssue).filter(ExtractionIssue.document_id == doc.id).count()
        scanned_pages_count = db.query(DocumentPage).filter(
            DocumentPage.document_id == doc.id,
            DocumentPage.is_scanned == True
        ).count()

        # Get sample evidence atom
        sample_atom = db.query(EvidenceAtom).filter(EvidenceAtom.document_id == doc.id).first()

        summary_results.append({
            "filename": fname,
            "document_id": doc.id,
            "page_count": doc.page_count,
            "pages_in_db": pages_count,
            "total_evidence_atoms": evidence_count,
            "table_evidence_atoms": table_atoms_count,
            "scanned_pages": scanned_pages_count,
            "issues_recorded": issues_count,
            "sample_evidence": sample_atom.exact_text[:120] if sample_atom else None
        })

    assert len(summary_results) == 6
    db.close()


if __name__ == "__main__":
    import json
    results = test_ingest_all_six_starter_pdfs()
    print(json.dumps(results, indent=2))
