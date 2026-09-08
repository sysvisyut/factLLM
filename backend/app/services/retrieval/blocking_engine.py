"""
Multi-tier Candidate Blocking Engine.
Groups facts into semantic blocks by entity and predicate family, enforces cross-document
boundaries, and filters candidate pairs to achieve >90% search-space reduction over naive O(N^2).
"""

from typing import List, Dict, Tuple, Any
from collections import defaultdict
from app.services.retrieval.predicate_clusters import get_predicate_family
from app.services.retrieval.candidate_pair import CandidatePair, RetrievalMetrics


class BlockingEngine:
    @staticmethod
    def generate_blocking_key(fact: Any) -> str:
        """
        Constructs the primary blocking key combining canonical subject and predicate family.
        Facts sharing this key describe the same conceptual dimension of the same entity.
        """
        subj = (fact.subject_canonical or "unknown").strip().lower()
        pred_fam = get_predicate_family(fact.predicate_canonical)
        return f"{subj}::{pred_fam.lower()}"

    def build_candidate_blocks(self, facts: List[Any]) -> Dict[str, List[Any]]:
        """Groups facts into inverted index blocks keyed by blocking key."""
        blocks = defaultdict(list)
        for f in facts:
            key = self.generate_blocking_key(f)
            blocks[key].append(f)
        return dict(blocks)

    def retrieve_candidate_pairs(self, facts: List[Any]) -> Tuple[List[CandidatePair], RetrievalMetrics]:
        """
        Executes multi-tier candidate blocking across facts.
        Returns:
            (candidate_pairs, retrieval_metrics)
        """
        n = len(facts)
        naive_comparisons = (n * (n - 1)) // 2 if n > 1 else 0

        if n < 2:
            metrics = RetrievalMetrics(
                total_facts=n,
                naive_comparisons=0,
                cross_document_pairs=0,
                candidate_pairs_count=0,
                reduction_percent=100.0
            )
            return [], metrics

        # Count total potential cross-document pairs for benchmarking
        cross_doc_count = 0
        for i in range(n):
            for j in range(i + 1, n):
                if facts[i].document_id != facts[j].document_id:
                    cross_doc_count += 1

        # Build blocks
        blocks = self.build_candidate_blocks(facts)

        candidate_pairs: List[CandidatePair] = []
        seen_pairs = set()

        for block_key, block_facts in blocks.items():
            b_len = len(block_facts)
            if b_len < 2:
                continue

            for i in range(b_len):
                fa = block_facts[i]
                for j in range(i + 1, b_len):
                    fb = block_facts[j]

                    # Rule 1: Exclude same-document facts (intra-document comparisons are not cross-doc)
                    if fa.document_id == fb.document_id:
                        continue

                    # Rule 2: Canonical deterministic ordering (pair_key)
                    pair_key = (min(fa.id, fb.id), max(fa.id, fb.id))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Determine ordering for candidate pair
                    fact_1 = fa if fa.id < fb.id else fb
                    fact_2 = fb if fa.id < fb.id else fa

                    pair = CandidatePair(
                        fact_a_id=fact_1.id,
                        fact_b_id=fact_2.id,
                        fact_a=fact_1,
                        fact_b=fact_2,
                        blocking_tier="PRIMARY_BLOCK",
                        blocking_key=block_key,
                        similarity_score=1.0
                    )
                    candidate_pairs.append(pair)

        # Compute reduction metric
        candidates_count = len(candidate_pairs)
        reduction_percent = (
            ((naive_comparisons - candidates_count) / naive_comparisons) * 100.0
            if naive_comparisons > 0 else 100.0
        )

        metrics = RetrievalMetrics(
            total_facts=n,
            naive_comparisons=naive_comparisons,
            cross_document_pairs=cross_doc_count,
            candidate_pairs_count=candidates_count,
            reduction_percent=reduction_percent
        )

        return candidate_pairs, metrics
