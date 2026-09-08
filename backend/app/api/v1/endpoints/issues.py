"""
Extraction Issues API Endpoints.
Exposes honest failure handling, OCR warnings, ungrounded claim rejections, and evidence discrepancies.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import ExtractionIssue
from app.schemas.issue import ExtractionIssueResponse

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("", response_model=List[ExtractionIssueResponse])
def list_issues(
    db: Session = Depends(get_db),
    document_id: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Lists recorded extraction and grounding issues."""
    query = db.query(ExtractionIssue)

    if document_id:
        query = query.filter(ExtractionIssue.document_id == document_id)
    if issue_type:
        query = query.filter(ExtractionIssue.issue_type == issue_type.upper())
    if status:
        query = query.filter(ExtractionIssue.status == status.upper())

    issues = query.order_by(ExtractionIssue.created_at.desc()).offset(offset).limit(limit).all()
    return issues


@router.get("/{issue_id}", response_model=ExtractionIssueResponse)
def get_issue(issue_id: str, db: Session = Depends(get_db)):
    """Retrieves metadata for a specific extraction issue."""
    issue = db.query(ExtractionIssue).filter(ExtractionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail=f"Extraction issue '{issue_id}' not found.")
    return issue


@router.post("/{issue_id}/resolve", response_model=ExtractionIssueResponse)
def resolve_issue(issue_id: str, resolution_note: Optional[str] = None, db: Session = Depends(get_db)):
    """Marks an extraction issue as manually resolved with an optional note."""
    issue = db.query(ExtractionIssue).filter(ExtractionIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail=f"Extraction issue '{issue_id}' not found.")

    issue.status = "RESOLVED"
    if resolution_note:
        issue.attempted_resolution = resolution_note
    db.commit()
    db.refresh(issue)
    return issue
