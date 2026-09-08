import time
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models import Document, DocumentPage, EvidenceAtom, ExtractionIssue, ProcessingJob
from app.services.ingestion.hasher import compute_sha256
from app.services.ingestion.pdf_extractor import PDFExtractor
from app.services.storage.local import storage_service
from app.core.logging import logger, log_stage


class DocumentIngestionService:
    """Orchestrates document intake, deduplication, atomic storage, page parsing, and EvidenceAtom generation."""

    def __init__(self):
        self.extractor = PDFExtractor()

    def ingest_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        db: Session
    ) -> Tuple[Document, bool, Optional[ProcessingJob]]:
        """
        Ingests a PDF file:
        - Computes SHA-256
        - Idempotently checks for duplicates
        - Saves to persistent storage
        - Extracts pages, tables, layout, and generates EvidenceAtoms
        Returns (document, is_duplicate, job).
        """
        start_time = time.time()
        content_hash = compute_sha256(file_bytes)
        file_size = len(file_bytes)

        # 1. Deduplication check
        existing_doc = db.query(Document).filter(Document.content_hash == content_hash).first()
        if existing_doc:
            logger.info(f"Duplicate document detected for {filename} (hash: {content_hash[:12]}...). Returning existing record.")
            return existing_doc, True, None

        # 2. Save file via StorageService
        storage_path = storage_service.save_file(file_bytes, filename)

        # 3. Create Document record
        doc = Document(
            filename=filename,
            content_hash=content_hash,
            file_size_bytes=file_size,
            page_count=0,
            storage_path=storage_path
        )
        db.add(doc)
        db.flush()  # populate doc.id

        # 4. Create ProcessingJob
        job = ProcessingJob(
            document_id=doc.id,
            stage="INGESTION",
            status="PROCESSING",
            progress_percentage=10
        )
        db.add(job)
        db.commit()

        log_stage(
            stage="INGESTION",
            status="STARTED",
            message=f"Beginning ingestion of {filename} ({file_size} bytes)",
            job_id=job.id,
            document_id=doc.id
        )

        try:
            # 5. Extract pages, evidence atoms, and layout
            pages_data, total_pages = self.extractor.extract_document(file_bytes)
            doc.page_count = total_pages
            job.progress_percentage = 40
            db.flush()

            total_evidence_count = 0
            total_issues_count = 0

            for p_data in pages_data:
                # Save DocumentPage
                page_record = DocumentPage(
                    document_id=doc.id,
                    page_number=p_data.page_number,
                    raw_text=p_data.raw_text,
                    has_tables=p_data.has_tables,
                    is_scanned=p_data.is_scanned
                )
                db.add(page_record)

                # Save EvidenceAtoms
                for atom_dict in p_data.evidence_atoms:
                    atom_record = EvidenceAtom(
                        document_id=doc.id,
                        page_number=atom_dict["page_number"],
                        section_heading=atom_dict.get("section_heading"),
                        exact_text=atom_dict["exact_text"],
                        char_start=atom_dict.get("char_start"),
                        char_end=atom_dict.get("char_end"),
                        bbox=atom_dict.get("bbox"),
                        table_cell_info=atom_dict.get("table_cell_info"),
                        extraction_method=atom_dict["extraction_method"],
                        source_hash=atom_dict["source_hash"]
                    )
                    db.add(atom_record)
                    total_evidence_count += 1

                # Save any extraction issues detected
                for issue_dict in p_data.issues:
                    issue_record = ExtractionIssue(
                        document_id=doc.id,
                        page_number=issue_dict.get("page_number", p_data.page_number),
                        issue_type=issue_dict["issue_type"],
                        description=issue_dict["description"],
                        affected_text=issue_dict.get("affected_text"),
                        attempted_resolution=issue_dict.get("attempted_resolution"),
                        status=issue_dict.get("status", "DETECTED")
                    )
                    db.add(issue_record)
                    total_issues_count += 1

            # 6. Complete job
            duration_ms = round((time.time() - start_time) * 1000, 2)
            job.stage = "INGESTION_COMPLETED"
            job.status = "COMPLETED"
            job.progress_percentage = 100
            db.commit()

            log_stage(
                stage="INGESTION",
                status="COMPLETED",
                message=f"Successfully ingested {filename}: {total_pages} pages, {total_evidence_count} evidence atoms, {total_issues_count} issues recorded.",
                job_id=job.id,
                document_id=doc.id,
                duration_ms=duration_ms,
                extra={"evidence_count": total_evidence_count, "issues_count": total_issues_count}
            )

            return doc, False, job

        except Exception as e:
            db.rollback()
            job.status = "FAILED"
            job.error_message = str(e)
            db.commit()
            logger.error(f"Ingestion failed for {filename}: {e}", exc_info=True)
            raise e


ingestion_service = DocumentIngestionService()
