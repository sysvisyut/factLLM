import sys
import os
import glob
import json

# Ensure python finds app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import init_db, SessionLocal
from app.services.ingestion.service import DocumentIngestionService
from app.services.extraction.service import FactExtractionService
from app.models import Document, Fact, EvidenceAtom, FactContext


def run_pipeline():
    init_db()
    db = SessionLocal()
    ingest_svc = DocumentIngestionService()
    extract_svc = FactExtractionService()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "starter-datasets"))
    pdf_files = sorted(glob.glob(os.path.join(base_dir, "**", "*.pdf"), recursive=True))
    
    print(f"Discovered {len(pdf_files)} PDFs in {base_dir}")

    for fpath in pdf_files:
        fname = os.path.basename(fpath)
        print(f"\n==================================================")
        print(f"Processing: {fname}")
        with open(fpath, "rb") as f:
            pdf_bytes = f.read()

        doc, is_dup, job = ingest_svc.ingest_pdf(pdf_bytes, fname, db)
        print(f"Ingested {fname} -> Document ID: {doc.id} (Pages: {doc.page_count}, Duplicate: {is_dup})")

        # Extract facts (first 25 pages to capture core financial & operational tables)
        facts = extract_svc.extract_document_facts(doc.id, db, max_pages=25)
        print(f"Extracted {len(facts)} facts from {fname}.")

        # Print representative facts
        for f in facts[:3]:
            atom = db.query(EvidenceAtom).filter(EvidenceAtom.id == f.evidence_id).first()
            ctx = db.query(FactContext).filter(FactContext.fact_id == f.id).first()
            print(f"  • [{f.predicate_canonical}]: Raw: '{f.value_raw}' -> Norm: {f.value_normalized} {f.unit_canonical}")
            print(f"    Context: Scope: {ctx.scope if ctx else 'N/A'} | Time: {ctx.time_raw} ({ctx.time_start} to {ctx.time_end}) | Basis: {ctx.measurement_basis}")
            print(f"    Fingerprint: {f.fingerprint[:16]}... | Evidence P.{atom.page_number if atom else '?'}: \"{atom.exact_text[:90] if atom else ''}\"")

    total_facts = db.query(Fact).count()
    total_docs = db.query(Document).count()
    total_atoms = db.query(EvidenceAtom).count()
    print("\n==================================================")
    print(f"PIPELINE SUMMARY: {total_docs} Documents | {total_atoms} Evidence Atoms | {total_facts} Grounded Facts")
    db.close()


if __name__ == "__main__":
    run_pipeline()
