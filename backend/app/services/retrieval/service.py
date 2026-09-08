"""
Candidate Retrieval Service providing high-level API to retrieve cross-document candidate pairs
from the database with multi-tier blocking and reduction metrics.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from app.models import Fact, FactContext, Document
from app.services.retrieval.blocking_engine import BlockingEngine
from app.services.retrieval.candidate_pair import CandidatePair, RetrievalMetrics
from app.core.logging import logger


class CandidateRetrievalService:
    def __init__(self):
        self.blocking_engine = BlockingEngine()

    def get_candidate_pairs(
        self,
        db: Session,
        document_ids: Optional[List[str]] = None,
        subject_filter: Optional[str] = None
    ) -> Tuple[List[CandidatePair], RetrievalMetrics]:
        """
        Loads facts from database, applies multi-tier blocking, and returns
        filtered candidate pairs along with search reduction metrics.
        """
        query = db.query(Fact).options(
            joinedload(Fact.context),
            joinedload(Fact.document),
            joinedload(Fact.evidence)
        )

        if document_ids:
            query = query.filter(Fact.document_id.in_(document_ids))

        if subject_filter:
            query = query.filter(Fact.subject_canonical == subject_filter)

        facts = query.all()
        logger.info(f"Loaded {len(facts)} facts for candidate retrieval.")

        candidate_pairs, metrics = self.blocking_engine.retrieve_candidate_pairs(facts)

        logger.info(
            f"Candidate Retrieval: {metrics.naive_comparisons} naive -> "
            f"{metrics.candidate_pairs_count} candidate pairs "
            f"({metrics.reduction_percent:.2f}% reduction)"
        )

        return candidate_pairs, metrics
