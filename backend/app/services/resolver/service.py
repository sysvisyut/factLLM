"""
Master Relationship Resolver Service.
Coordinates candidate pair retrieval, multidimensional comparison, decision matrix resolution,
explanation generation, and database persistence.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models import Relationship, Fact
from app.services.retrieval.service import CandidateRetrievalService
from app.services.retrieval.candidate_pair import CandidatePair, RetrievalMetrics
from app.services.resolver.matrix import DecisionMatrixEngine, ResolutionResult
from app.services.resolver.explainer import RelationshipExplainer
from app.core.logging import logger


class RelationshipResolverService:
    def __init__(self):
        self.retrieval_service = CandidateRetrievalService()
        self.matrix_engine = DecisionMatrixEngine()
        self.explainer = RelationshipExplainer()

    def resolve_cross_document_relationships(
        self,
        db: Session,
        document_ids: Optional[List[str]] = None,
        candidate_pairs: Optional[List[CandidatePair]] = None
    ) -> Tuple[List[Relationship], Dict[str, Any]]:
        """
        Executes end-to-end cross-document relationship resolution.
        Loads candidate pairs, applies multidimensional decision matrix,
        generates grounded explanations, and persists relationships to DB.
        """
        if candidate_pairs is None:
            candidate_pairs, retrieval_metrics = self.retrieval_service.get_candidate_pairs(
                db=db,
                document_ids=document_ids
            )
        else:
            retrieval_metrics = None

        logger.info(f"Resolving relationships across {len(candidate_pairs)} candidate pairs.")

        resolved_records: List[Relationship] = []
        counts: Dict[str, int] = {
            "CORROBORATES": 0,
            "CONTRADICTS": 0,
            "RECONCILES": 0,
            "TEMPORALLY_EVOLVES": 0,
            "SCOPE_DIFFERENCE": 0,
            "UNIT_EQUIVALENT": 0,
            "UNCERTAIN": 0
        }

        for pair in candidate_pairs:
            fa = pair.fact_a
            fb = pair.fact_b

            # Check if relationship already exists
            existing = db.query(Relationship).filter(
                or_(
                    and_(Relationship.fact_a_id == fa.id, Relationship.fact_b_id == fb.id),
                    and_(Relationship.fact_a_id == fb.id, Relationship.fact_b_id == fa.id)
                )
            ).first()

            if existing:
                resolved_records.append(existing)
                counts[existing.relationship_type] = counts.get(existing.relationship_type, 0) + 1
                continue

            # Evaluate decision matrix
            resolution: ResolutionResult = self.matrix_engine.resolve_relationship(fa, fb)

            # Generate grounded human-readable explanation
            explanation = self.explainer.generate_explanation(fa, fb, resolution)

            rel_record = Relationship(
                fact_a_id=fa.id,
                fact_b_id=fb.id,
                relationship_type=resolution.relationship_type,
                confidence=resolution.confidence,
                explanation=explanation,
                dimensions=resolution.dimensions,
                important_differences=resolution.important_differences,
                reasoning_basis=resolution.reasoning_basis
            )

            db.add(rel_record)
            resolved_records.append(rel_record)
            counts[resolution.relationship_type] = counts.get(resolution.relationship_type, 0) + 1

        db.commit()

        summary = {
            "total_candidates_evaluated": len(candidate_pairs),
            "total_relationships_stored": len(resolved_records),
            "breakdown": counts,
            "retrieval_metrics": retrieval_metrics.to_dict() if retrieval_metrics else None
        }

        logger.info(f"Relationship resolution complete. Summary: {counts}")
        return resolved_records, summary
