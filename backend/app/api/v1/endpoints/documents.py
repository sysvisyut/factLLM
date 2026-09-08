"""
Documents API Endpoints.
Handles PDF uploading, document metadata retrieval, and reprocessing.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Document, DocumentPage, Fact, ExtractionIssue, ProcessingJob
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.ingestion.service import DocumentIngestionService
from app.services.extraction.service import FactExtractionService
from app.core.logging import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Lists all ingested documents with page counts and associated fact/issue tallies."""
    docs = db.query(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    
    results = []
    for d in docs:
        fact_cnt = db.query(Fact).filter(Fact.document_id == d.id).count()
        issue_cnt = db.query(ExtractionIssue).filter(ExtractionIssue.document_id == d.id).count()
        results.append(
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                content_hash=d.content_hash,
                file_size_bytes=d.file_size_bytes,
                page_count=d.page_count,
                storage_path=d.storage_path,
                created_at=d.created_at,
                fact_count=fact_cnt,
                issue_count=issue_cnt
            )
        )
    return results


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieves metadata for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    fact_cnt = db.query(Fact).filter(Fact.document_id == doc.id).count()
    issue_cnt = db.query(ExtractionIssue).filter(ExtractionIssue.document_id == doc.id).count()

    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        content_hash=doc.content_hash,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        storage_path=doc.storage_path,
        created_at=doc.created_at,
        fact_count=fact_cnt,
        issue_count=issue_cnt
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts arbitrary PDF upload, ingests evidence atoms, extracts structured facts,
    and applies normalization in a single unified pipeline.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    ingestion_service = DocumentIngestionService()
    extraction_service = FactExtractionService()

    # 1. Ingestion
    doc, is_dup, job = ingestion_service.ingest_pdf(
        file_bytes=content,
        filename=file.filename,
        db=db
    )

    # 2. Fact extraction & normalization (if not a duplicate)
    if not is_dup:
        facts = extraction_service.extract_document_facts(doc.id, db)
        msg = f"Document ingested successfully. Extracted {len(facts)} grounded facts."
    else:
        msg = f"Duplicate document detected. Loaded existing record with ID {doc.id}."

    return DocumentUploadResponse(
        document_id=doc.id,
        job_id=job.id if job else "N/A",
        filename=doc.filename,
        status="SUCCESS",
        message=msg
    )


@router.post("/{document_id}/reprocess")
def reprocess_document(document_id: str, db: Session = Depends(get_db)):
    """Re-runs fact extraction and normalization for an existing document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    # Delete existing facts for this document to prevent duplicate entries
    db.query(Fact).filter(Fact.document_id == doc.id).delete()
    db.commit()

    extraction_service = FactExtractionService()
    facts = extraction_service.extract_document_facts(doc.id, db)

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "status": "SUCCESS",
        "facts_extracted": len(facts)
    }
