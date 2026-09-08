"""
Relationship Explainer.
Generates human-readable, grounded narrative explanations for resolved cross-document relationships,
citing document provenance, page numbers, verbatim evidence text, and dimensional reasoning.
"""

from typing import Any
from app.services.resolver.matrix import ResolutionResult


class RelationshipExplainer:
    @classmethod
    def generate_explanation(cls, fact_a: Any, fact_b: Any, resolution: ResolutionResult) -> str:
        """Constructs a comprehensive, grounded explanation for the relationship."""
        doc_a_name = fact_a.document.filename if fact_a.document else "Document A"
        doc_b_name = fact_b.document.filename if fact_b.document else "Document B"
        page_a = fact_a.evidence.page_number if fact_a.evidence else "?"
        page_b = fact_b.evidence.page_number if fact_b.evidence else "?"

        entity = fact_a.subject_canonical
        pred = fact_a.predicate_canonical
        raw_a = fact_a.value_raw
        raw_b = fact_b.value_raw
        ctx_a = fact_a.context
        ctx_b = fact_b.context

        time_a = ctx_a.time_raw if ctx_a else "unspecified period"
        time_b = ctx_b.time_raw if ctx_b else "unspecified period"
        scope_a = ctx_a.scope if ctx_a else "consolidated"
        scope_b = ctx_b.scope if ctx_b else "consolidated"
        basis_a = ctx_a.measurement_basis if ctx_a else "standard"
        basis_b = ctx_b.measurement_basis if ctx_b else "standard"

        rtype = resolution.relationship_type

        if rtype == "CORROBORATES":
            return (
                f"Both documents corroborate '{entity} - {pred}'. "
                f"'{doc_a_name}' (Page {page_a}) reports '{raw_a}', while "
                f"'{doc_b_name}' (Page {page_b}) independently confirms '{raw_b}' "
                f"for {time_a} under identical operational scope ({scope_a}) and measurement basis ({basis_a})."
            )

        elif rtype == "UNIT_EQUIVALENT":
            norm_val = f"{fact_a.value_normalized:,.2f}" if fact_a.value_normalized else str(fact_a.value_normalized)
            return (
                f"Unit scale equivalence established for '{entity} - {pred}'. "
                f"'{doc_a_name}' (Page {page_a}) reports '{raw_a}' while "
                f"'{doc_b_name}' (Page {page_b}) reports '{raw_b}'. "
                f"When standardized to base {fact_a.unit_canonical}, both resolve to the identical figure ({norm_val} {fact_a.unit_canonical})."
            )

        elif rtype == "RECONCILES":
            return (
                f"The apparent numerical discrepancy for '{entity} - {pred}' ('{raw_a}' vs '{raw_b}') is reconciled by context. "
                f"'{doc_a_name}' (Page {page_a}) measures under '{basis_a}', whereas "
                f"'{doc_b_name}' (Page {page_b}) reports under '{basis_b}'. "
                f"This reflects differing revision stages or reporting conventions rather than a factual disagreement."
            )

        elif rtype == "TEMPORALLY_EVOLVES":
            return (
                f"Temporal evolution observed for '{entity} - {pred}'. "
                f"'{doc_a_name}' (Page {page_a}) records '{raw_a}' for {time_a}, whereas "
                f"'{doc_b_name}' (Page {page_b}) reflects progression to '{raw_b}' for {time_b}."
            )

        elif rtype == "SCOPE_DIFFERENCE":
            return (
                f"Scope boundary difference explains the variation in '{entity} - {pred}'. "
                f"'{doc_a_name}' (Page {page_a}) covers '{scope_a}' ('{raw_a}'), whereas "
                f"'{doc_b_name}' (Page {page_b}) represents '{scope_b}' ('{raw_b}')."
            )

        elif rtype == "CONTRADICTS":
            return (
                f"Direct factual contradiction detected for '{entity} - {pred}' during {time_a}. "
                f"'{doc_a_name}' (Page {page_a}) claims '{raw_a}', whereas "
                f"'{doc_b_name}' (Page {page_b}) conflicts with '{raw_b}'. "
                f"Both sources share identical scope ({scope_a}) and measurement basis ({basis_a}) with no reconciling contextual factors."
            )

        else:
            return (
                f"Uncertain relationship between '{entity} - {pred}' in '{doc_a_name}' ('{raw_a}') and "
                f"'{doc_b_name}' ('{raw_b}'). Contextual boundaries require further clarification."
            )
