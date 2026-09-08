"""
Decision Matrix Engine for Multidimensional Relationship Resolution.
Determines whether two candidate facts corroborate, contradict, reconcile,
temporally evolve, differ in scope, or are unit equivalent.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from app.services.resolver.dimensions import DimensionComparator, ComparisonResult


@dataclass
class ResolutionResult:
    relationship_type: str          # 'CORROBORATES', 'CONTRADICTS', 'RECONCILES', 'TEMPORALLY_EVOLVES', 'SCOPE_DIFFERENCE', 'UNIT_EQUIVALENT', 'UNCERTAIN'
    confidence: float
    dimensions: Dict[str, Any]
    important_differences: List[str]
    reasoning_basis: str            # 'deterministic', 'context_matrix', 'llm_reasoning'
    reconciliation_variable: Optional[str] = None


class DecisionMatrixEngine:
    @classmethod
    def resolve_relationship(cls, fact_a: Any, fact_b: Any) -> ResolutionResult:
        """
        Evaluates the multidimensional comparison result through the decision matrix.
        """
        comp: ComparisonResult = DimensionComparator.compare_facts(fact_a, fact_b)
        dims = comp.to_dimensions_dict()
        diffs = list(comp.important_differences)

        # 1. SCOPE DIFFERENCE CHECK
        # If the claims measure different scopes (e.g. consolidated vs subsidiary),
        # this is fundamentally a scope boundary distinction.
        if not comp.scope_match:
            return ResolutionResult(
                relationship_type="SCOPE_DIFFERENCE",
                confidence=0.92,
                dimensions=dims,
                important_differences=diffs,
                reasoning_basis="context_matrix",
                reconciliation_variable="operational_scope"
            )

        # 2. TEMPORAL EVOLUTION CHECK
        # If the claims refer to different time periods or a sub-period (e.g. Q1 vs FY, FY22 vs FY24)
        if not comp.temporal_match and comp.temporal_relation in ("DIFFERENT_PERIOD", "SUB_PERIOD"):
            return ResolutionResult(
                relationship_type="TEMPORALLY_EVOLVES",
                confidence=0.90,
                dimensions=dims,
                important_differences=diffs,
                reasoning_basis="context_matrix",
                reconciliation_variable="time_period"
            )

        # 3. UNIT EQUIVALENCE CHECK
        # If values match after normalization, and native raw strings used different scales (e.g. Cr vs Mn)
        is_diff_raw_scale = (
            fact_a.unit_raw and fact_b.unit_raw and
            fact_a.unit_raw.strip().lower() != fact_b.unit_raw.strip().lower()
        )
        if comp.value_match and is_diff_raw_scale and comp.basis_match:
            return ResolutionResult(
                relationship_type="UNIT_EQUIVALENT",
                confidence=0.98,
                dimensions=dims,
                important_differences=diffs,
                reasoning_basis="deterministic",
                reconciliation_variable="unit_scale"
            )

        # 4. CORROBORATION CHECK
        # Same period, same scope, same basis, and normalized values coincide within tolerance
        if comp.value_match and comp.basis_match and comp.polarity_match:
            return ResolutionResult(
                relationship_type="CORROBORATES",
                confidence=0.96,
                dimensions=dims,
                important_differences=diffs,
                reasoning_basis="deterministic",
                reconciliation_variable=None
            )

        # 5. RECONCILIATION CHECK (Apparent Contradiction resolved by Context)
        # Same period, same scope, but values differ AND measurement basis differs
        if not comp.value_match and not comp.basis_match:
            return ResolutionResult(
                relationship_type="RECONCILES",
                confidence=0.93,
                dimensions=dims,
                important_differences=diffs,
                reasoning_basis="context_matrix",
                reconciliation_variable="measurement_basis"
            )

        # 6. DIRECT CONTRADICTION CHECK
        # Same period, same scope, same measurement basis, but normalized values differ significantly
        if not comp.value_match and comp.basis_match:
            return ResolutionResult(
                relationship_type="CONTRADICTS",
                confidence=0.95,
                dimensions=dims,
                important_differences=diffs,
                reasoning_basis="deterministic",
                reconciliation_variable=None
            )

        # 7. Fallback for unclassified boundary conditions
        return ResolutionResult(
            relationship_type="UNCERTAIN",
            confidence=0.50,
            dimensions=dims,
            important_differences=diffs,
            reasoning_basis="context_matrix",
            reconciliation_variable=None
        )
