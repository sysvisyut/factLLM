import time
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import (
    Document,
    DocumentPage,
    EvidenceAtom,
    Entity,
    Fact,
    FactContext,
    ExtractionIssue,
    ProcessingJob
)
from app.schemas.fact import FactBase
from app.services.llm.factory import get_llm_provider
from app.services.normalization.service import FactNormalizationService
from app.services.normalization.fingerprint import FactFingerprintGenerator
from app.core.logging import logger, log_stage
from datetime import datetime


class FactExtractionService:
    """Orchestrates fact extraction from page evidence, enforces Pydantic validation, and verifies source grounding."""

    def __init__(self, provider_name: Optional[str] = None):
        self.provider = get_llm_provider(provider_name)
        self.normalization_service = FactNormalizationService()

    def extract_document_facts(
        self,
        document_id: str,
        db: Session,
        max_pages: Optional[int] = None
    ) -> List[Fact]:
        """
        Extracts, validates, and stores structured facts for an ingested document.
        Ensures 100% grounding in source EvidenceAtoms.
        """
        start_time = time.time()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        # Find or create processing job
        job = db.query(ProcessingJob).filter(ProcessingJob.document_id == document_id).first()
        if job:
            job.stage = "FACT_EXTRACTION"
            job.status = "PROCESSING"
            db.commit()

        log_stage(
            stage="FACT_EXTRACTION",
            status="STARTED",
            message=f"Beginning fact extraction for {doc.filename}",
            document_id=doc.id
        )

        pages_query = db.query(DocumentPage).filter(DocumentPage.document_id == document_id).order_by(DocumentPage.page_number)
        if max_pages:
            pages_query = pages_query.limit(max_pages)
        pages = pages_query.all()

        extracted_facts: List[Fact] = []
        issues_recorded: List[ExtractionIssue] = []

        for page in pages:
            # Fetch evidence atoms for this page
            atoms = db.query(EvidenceAtom).filter(
                EvidenceAtom.document_id == document_id,
                EvidenceAtom.page_number == page.page_number
            ).all()

            if not atoms:
                continue

            # Call provider to extract structured claims
            try:
                raw_facts: List[FactBase] = self.provider.extract_facts(
                    text=page.raw_text,
                    page_number=page.page_number,
                    evidence_atoms=atoms
                )
            except Exception as extract_err:
                logger.error(f"Error calling LLM provider for page {page.page_number}: {extract_err}")
                issue = ExtractionIssue(
                    document_id=doc.id,
                    page_number=page.page_number,
                    issue_type="LLM_EXTRACTION_FAILURE",
                    description=f"Fact extraction failed on page {page.page_number}: {str(extract_err)}",
                    attempted_resolution="Captured raw text and skipped ungrounded extraction.",
                    status="DETECTED"
                )
                db.add(issue)
                issues_recorded.append(issue)
                continue

            # Process and validate each fact
            for fact_schema in raw_facts:
                # 1. Grounding check: verify evidence_id exists and belongs to this document
                atom = next((a for a in atoms if a.id == fact_schema.evidence_id), None)
                if not atom:
                    issue = ExtractionIssue(
                        document_id=doc.id,
                        page_number=page.page_number,
                        issue_type="MISSING_CONTEXT",
                        description=f"Fact for predicate '{fact_schema.predicate.canonical}' referenced invalid evidence_id '{fact_schema.evidence_id}'.",
                        attempted_resolution="Discarded fact to prevent synthetic fabrication.",
                        status="RESOLVED"
                    )
                    db.add(issue)
                    issues_recorded.append(issue)
                    continue

                # 2. Text Grounding verification: ensure raw value or number appears in atom text
                raw_val = fact_schema.value.raw
                norm_val = str(fact_schema.value.normalized) if fact_schema.value.normalized is not None else ""
                
                # Check if numbers or key tokens match evidence
                num_token_match = False
                for token in raw_val.split():
                    clean_token = token.replace(",", "").replace("₹", "").replace("%", "")
                    if clean_token and (clean_token in atom.exact_text or clean_token in atom.exact_text.replace(",", "")):
                        num_token_match = True
                        break

                if not num_token_match and norm_val not in atom.exact_text:
                    issue = ExtractionIssue(
                        document_id=doc.id,
                        page_number=page.page_number,
                        issue_type="CONFLICTING_EVIDENCE",
                        description=f"Extracted value '{raw_val}' not explicitly found in evidence atom '{atom.id}'.",
                        affected_text=atom.exact_text[:200],
                        attempted_resolution="Flagged as low-confidence claim.",
                        status="DETECTED"
                    )
                    db.add(issue)
                    issues_recorded.append(issue)
                    # Downgrade confidence
                    fact_schema.confidence.overall = 0.4
                    fact_schema.confidence.level = "LOW"

                # 3. Apply comprehensive fact normalization (numbers, units, time, entities)
                fact_schema = self.normalization_service.normalize_fact_base(fact_schema)

                # 4. Create or resolve Entity
                entity_canonical = fact_schema.subject.canonical
                entity = db.query(Entity).filter(Entity.canonical_name == entity_canonical).first()
                if not entity:
                    entity = Entity(
                        canonical_name=entity_canonical,
                        entity_type=fact_schema.subject.type,
                        aliases=fact_schema.subject.aliases
                    )
                    db.add(entity)
                    db.flush()

                # 5. Parse date objects for temporal boundaries
                time_start_obj = None
                time_end_obj = None
                if fact_schema.context and fact_schema.context.time:
                    if fact_schema.context.time.start:
                        try:
                            time_start_obj = datetime.strptime(fact_schema.context.time.start, "%Y-%m-%d").date()
                        except ValueError:
                            pass
                    if fact_schema.context.time.end:
                        try:
                            time_end_obj = datetime.strptime(fact_schema.context.time.end, "%Y-%m-%d").date()
                        except ValueError:
                            pass

                # 6. Generate Deterministic Fact Fingerprint
                scope_str = fact_schema.context.scope if fact_schema.context else "consolidated"
                basis_str = fact_schema.context.measurement_basis if fact_schema.context else "standard"
                unit_str = fact_schema.value.unit

                fingerprint = FactFingerprintGenerator.generate_fingerprint(
                    subject_canonical=entity.canonical_name,
                    predicate_canonical=fact_schema.predicate.canonical,
                    scope=scope_str,
                    time_start=time_start_obj,
                    time_end=time_end_obj,
                    unit_canonical=unit_str,
                    measurement_basis=basis_str
                )

                # 7. Persist Fact
                fact_record = Fact(
                    document_id=doc.id,
                    evidence_id=atom.id,
                    subject_entity_id=entity.id,
                    subject_raw=fact_schema.subject.canonical,
                    subject_canonical=entity.canonical_name,
                    predicate_raw=fact_schema.predicate.canonical,
                    predicate_canonical=fact_schema.predicate.canonical,
                    predicate_type=fact_schema.predicate.type,
                    value_raw=fact_schema.value.raw,
                    value_normalized=fact_schema.value.normalized,
                    value_type=fact_schema.value.value_type,
                    unit_raw=atom.exact_text,
                    unit_canonical=unit_str,
                    polarity=fact_schema.polarity,
                    fingerprint=fingerprint,
                    confidence_extraction=fact_schema.confidence.extraction,
                    confidence_normalization=fact_schema.confidence.normalization,
                    confidence_overall=fact_schema.confidence.overall,
                    confidence_level=fact_schema.confidence.level
                )
                db.add(fact_record)
                db.flush()

                # 8. Persist FactContext
                ctx = fact_schema.context
                fact_ctx = FactContext(
                    fact_id=fact_record.id,
                    time_type=ctx.time.type if ctx and ctx.time else None,
                    time_start=time_start_obj,
                    time_end=time_end_obj,
                    time_raw=ctx.time.raw if ctx and ctx.time else None,
                    geography=ctx.geography if ctx else None,
                    scope=ctx.scope if ctx else None,
                    population=ctx.population if ctx else None,
                    measurement_basis=ctx.measurement_basis if ctx else None,
                    qualifiers=ctx.qualifiers if ctx else []
                )
                db.add(fact_ctx)
                extracted_facts.append(fact_record)

        db.commit()

        duration_ms = round((time.time() - start_time) * 1000, 2)
        if job:
            job.stage = "FACT_EXTRACTION_COMPLETED"
            job.status = "COMPLETED"
            job.progress_percentage = 100
            db.commit()

        log_stage(
            stage="FACT_EXTRACTION",
            status="COMPLETED",
            message=f"Extracted {len(extracted_facts)} grounded facts from {len(pages)} pages of {doc.filename}.",
            document_id=doc.id,
            duration_ms=duration_ms,
            extra={"fact_count": len(extracted_facts), "issues_count": len(issues_recorded)}
        )

        return extracted_facts


fact_extraction_service = FactExtractionService()
