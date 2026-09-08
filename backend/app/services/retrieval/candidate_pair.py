"""
Candidate Pair and Retrieval Metrics definitions.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class CandidatePair:
    fact_a_id: str
    fact_b_id: str
    fact_a: Any                     # Fact ORM model or schema
    fact_b: Any                     # Fact ORM model or schema
    blocking_tier: str              # 'PRIMARY_BLOCK', 'PREDICATE_FAMILY', 'EMBEDDING_SIMILARITY'
    blocking_key: str
    similarity_score: float = 1.0


@dataclass
class RetrievalMetrics:
    total_facts: int
    naive_comparisons: int          # N * (N - 1) / 2
    cross_document_pairs: int       # Total pairs from different documents
    candidate_pairs_count: int      # Pairs retained after multi-tier blocking
    reduction_percent: float        # (1 - candidate_pairs / naive_comparisons) * 100%

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_facts": self.total_facts,
            "naive_comparisons": self.naive_comparisons,
            "cross_document_pairs": self.cross_document_pairs,
            "candidate_pairs_count": self.candidate_pairs_count,
            "reduction_percent": round(self.reduction_percent, 2),
            "efficiency_multiplier": round(self.naive_comparisons / max(self.candidate_pairs_count, 1), 2)
        }
